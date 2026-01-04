import json
import os
import atexit

import paho.mqtt.client as mqtt
import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Subscriber MQTT: reçoit DHT11 puis envoie vers l'API Django (/api/post/)"

    def add_arguments(self, parser):
        parser.add_argument("--host", type=str, default=getattr(settings, "MQTT_HOST", "127.0.0.1"))
        parser.add_argument("--port", type=int, default=int(getattr(settings, "MQTT_PORT", 1883)))
        parser.add_argument("--topic", type=str, default=getattr(settings, "MQTT_TOPIC_SENSOR", "sensors/+/dht11"))
        parser.add_argument("--api", type=str, default="http://127.0.0.1:8000/api/post/")

        # ✅ IMPORTANT: par défaut, ne pas throttler (0 = chaque message)
        parser.add_argument("--interval", type=int, default=0)

        # anti-doublon (secondes)
        parser.add_argument("--dedup", type=int, default=1)

        parser.add_argument("--timeout", type=int, default=5)

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]
        topic = options["topic"]
        api_url = options["api"]
        interval_s = int(options["interval"])
        dedup_s = int(options["dedup"])
        timeout_s = int(options["timeout"])

        # ✅ LOCK anti double lancement
        lock_path = os.path.join(getattr(settings, "BASE_DIR", "."), "mqtt_subscriber.lock")

        def cleanup_lock():
            try:
                if os.path.exists(lock_path):
                    os.remove(lock_path)
            except Exception:
                pass

        if os.path.exists(lock_path):
            self.stdout.write(self.style.ERROR("❌ mqtt_subscriber déjà en cours (lock trouvé)."))
            self.stdout.write(self.style.ERROR(f"➡️ Si faux lock, supprime: {lock_path}"))
            return

        with open(lock_path, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        atexit.register(cleanup_lock)

        last_payload = {"temp": None, "hum": None, "ts": None}
        last_sent_at = None

        self.stdout.write(self.style.WARNING("=== mqtt_subscriber START ==="))
        self.stdout.write(self.style.WARNING(f"MQTT Host={host} Port={port} Topic={topic}"))
        self.stdout.write(self.style.WARNING(f"API URL={api_url}"))
        self.stdout.write(self.style.WARNING(f"interval={interval_s}s | dedup={dedup_s}s | timeout={timeout_s}s"))
        self.stdout.write(self.style.WARNING("Stop = Ctrl+C"))

        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS("✅ MQTT connecté"))
                client.subscribe(topic)
                self.stdout.write(self.style.SUCCESS(f"📡 Abonné au topic : {topic}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Erreur connexion MQTT (rc={rc})"))

        def on_message(client, userdata, msg):
            nonlocal last_sent_at

            raw = msg.payload.decode("utf-8", errors="ignore").strip()
            self.stdout.write(self.style.WARNING(f"📩 {msg.topic}: {raw}"))

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"⚠️ JSON invalide: {e}"))
                return

            # ✅ Accepter 2 formats:
            # {"temp":..., "hum":...} OU {"temperature":..., "humidity":...}
            if "temp" in data and "hum" in data:
                t_key, h_key = "temp", "hum"
            elif "temperature" in data and "humidity" in data:
                t_key, h_key = "temperature", "humidity"
            else:
                self.stdout.write(self.style.ERROR(
                    f"⚠️ Clés manquantes. Attendu temp/hum OU temperature/humidity. Reçu: {data}"
                ))
                return

            try:
                temp = float(data.get(t_key))
                hum = float(data.get(h_key))
            except (TypeError, ValueError):
                self.stdout.write(self.style.ERROR(f"⚠️ Valeurs non numériques: {data}"))
                return

            now = timezone.now()

            # ✅ anti-doublon
            if last_payload["temp"] == temp and last_payload["hum"] == hum and last_payload["ts"]:
                if (now - last_payload["ts"]).total_seconds() <= dedup_s:
                    self.stdout.write(self.style.WARNING(f"⏭️ Doublon ignoré (≤ {dedup_s}s)"))
                    return

            last_payload.update({"temp": temp, "hum": hum, "ts": now})

            # ✅ throttle API (si interval > 0)
            if interval_s > 0 and last_sent_at is not None:
                dt = (now - last_sent_at).total_seconds()
                if dt < interval_s:
                    self.stdout.write(self.style.WARNING(
                        f"⏳ Throttle: prochain envoi dans {int(interval_s - dt)}s"
                    ))
                    return

            payload_api = {"temp": temp, "hum": hum}

            try:
                r = requests.post(api_url, json=payload_api, timeout=timeout_s)
                if r.ok:
                    last_sent_at = now
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ API OK: {payload_api} (HTTP {r.status_code})"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"❌ API HTTP {r.status_code}: {r.text}"
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ POST API impossible: {e}"))
                self.stdout.write(self.style.ERROR("➡️ Vérifie que runserver est lancé."))

        client = mqtt.Client(protocol=mqtt.MQTTv311)
        client.on_connect = on_connect
        client.on_message = on_message
        client.reconnect_delay_set(min_delay=1, max_delay=10)

        try:
            self.stdout.write(self.style.WARNING(f"Connexion au broker MQTT {host}:{port} ..."))
            client.connect(host, port, 60)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Impossible de se connecter au broker: {e}"))
            cleanup_lock()
            return

        try:
            self.stdout.write(self.style.SUCCESS("✅ Boucle MQTT active (loop_forever)..."))
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("🛑 Arrêt demandé (Ctrl+C)."))
        finally:
            cleanup_lock()
