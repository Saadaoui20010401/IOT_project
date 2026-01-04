import threading
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Incident
from .utils import send_telegram
from .voip import trigger_sip_alert




def _thresholds():
    tmin = float(getattr(settings, "TEMP_MIN_THRESHOLD", 10.0))
    tmax = float(getattr(settings, "TEMP_MAX_THRESHOLD", 23.0))
    cooldown = int(getattr(settings, "ALERT_COOLDOWN_SECONDS", 60))
    return tmin, tmax, cooldown


def handle_measurement_alerts(temp: float, hum: float, timestamp):
    if temp is None:
        return

    tmin, tmax, cooldown_s = _thresholds()

    is_hot = temp > tmax
    is_cold = temp < tmin
    is_alert = is_hot or is_cold
    current_type = "HOT" if is_hot else ("COLD" if is_cold else None)

    # Flags pour exécuter après transaction
    should_call_voip = False
    voip_target_ext = getattr(settings, "SIP_TARGET_EXTENSION", "6001")

    with transaction.atomic():
        incident = (
            Incident.objects.select_for_update()
            .filter(is_open=True)
            .order_by("-start_at")
            .first()
        )

        # ---- TEMP HORS PLAGE => incident ouvert + compteur ----
        if is_alert:
            if incident is None:
                incident = Incident.objects.create(
                    is_open=True,
                    counter=0,
                    incident_type=current_type,
                    min_allowed_temp=tmin,
                    max_allowed_temp=tmax,
                    max_temp=temp,
                    min_temp=temp,
                )
            else:
                # maj du type si ça change
                if current_type and incident.incident_type != current_type:
                    incident.incident_type = current_type

                # toujours garder les seuils (cohérence)
                incident.min_allowed_temp = tmin
                incident.max_allowed_temp = tmax

            # compteur
            incident.counter = (incident.counter or 0) + 1

            # --- VoIP (niveau critique) : déclencher 1 seule fois par incident ---
            critical_n = int(getattr(settings, "VOIP_CRITICAL_COUNTER", 7))
            if incident.counter >= critical_n and incident.voip_triggered_at is None:
                # On marque AVANT d'appeler pour éviter le spam (même si appel échoue)
                incident.voip_triggered_at = timezone.now()
                should_call_voip = bool(getattr(settings, "VOIP_ENABLED", False))

            # max/min observés
            if incident.max_temp is None or temp > incident.max_temp:
                incident.max_temp = temp
            if incident.min_temp is None or temp < incident.min_temp:
                incident.min_temp = temp

            now = timezone.now()

            # anti-spam email/telegram : si trop tôt => on sauvegarde et on sort
            if incident.last_alert_at and (now - incident.last_alert_at).total_seconds() < cooldown_s:
                incident.save()
                # On ne "return" pas ici dans le with: on sort juste après la transaction
            else:
                # message
                if is_hot:
                    subject = f"ALERTE TEMPÉRATURE HAUTE: {temp:.1f}°C"
                    message = (
                        f"Température élevée détectée.\n"
                        f"Temp: {temp:.1f}°C (max {tmax:.1f}°C)\n"
                        f"Hum: {hum}%\n"
                        f"Heure: {timestamp}\n"
                        f"Alertes consécutives: {incident.counter}\n"
                    )
                    tg = (
                        "🔥 ⚠️ ALERTE TEMPÉRATURE HAUTE (DHT11)\n"
                        f"Température: {temp:.1f} °C (max {tmax:.1f} °C)\n"
                        f"Humidité: {hum} %\n"
                        f"Heure: {timestamp}\n"
                        f"Alertes consécutives: {incident.counter}"
                    )
                else:
                    subject = f"ALERTE TEMPÉRATURE BASSE: {temp:.1f}°C"
                    message = (
                        f"Température basse détectée.\n"
                        f"Temp: {temp:.1f}°C (min {tmin:.1f}°C)\n"
                        f"Hum: {hum}%\n"
                        f"Heure: {timestamp}\n"
                        f"Alertes consécutives: {incident.counter}\n"
                    )
                    tg = (
                        "❄️ ⚠️ ALERTE TEMPÉRATURE BASSE (DHT11)\n"
                        f"Température: {temp:.1f} °C (min {tmin:.1f} °C)\n"
                        f"Humidité: {hum} %\n"
                        f"Heure: {timestamp}\n"
                        f"Alertes consécutives: {incident.counter}"
                    )

                # EMAIL
                try:
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [settings.EMAIL_HOST_USER],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"❌ Email error: {e}")

                # TELEGRAM
                try:
                    send_telegram(tg)
                except Exception as e:
                    print(f"❌ Telegram error: {e}")

                incident.last_alert_at = now
                incident.save()

            # fin "alert"
        else:
            # ---- TEMP OK => fermer l’incident (SEULEMENT ICI) ----
            if incident is not None:
                incident.is_open = False
                incident.end_at = timezone.now()
                incident.save()

    # ✅ Appel VoIP en DEHORS de la transaction (ne bloque pas la DB)
    if should_call_voip:
        def _call():
            trigger_sip_alert(voip_target_ext)
        threading.Thread(target=_call, daemon=True).start()
