from datetime import timedelta

from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from .models import Dht11, Incident
from .serializers import DHT11Serializer, IncidentSerializer
from .services import handle_measurement_alerts


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "1", "yes", "y", "on"):
            return True
        if v in ("false", "0", "no", "n", "off", ""):
            return False
    return default


class DList(generics.ListAPIView):
    serializer_class = DHT11Serializer

    def get_queryset(self):
        return Dht11.objects.order_by("-dt")[:200]


class DhtCreateView(generics.CreateAPIView):
    queryset = Dht11.objects.all()
    serializer_class = DHT11Serializer

    def perform_create(self, serializer):
        obj = serializer.save()

        # Anti-doublon DB (3 secondes)
        last = Dht11.objects.exclude(id=obj.id).order_by("-dt").first()
        if last and last.temp == obj.temp and last.hum == obj.hum:
            if last.dt and obj.dt and (obj.dt - last.dt) <= timedelta(seconds=3):
                obj.delete()
                return

        # ✅ logique incident + alertes (email + telegram)
        handle_measurement_alerts(obj.temp, obj.hum, obj.dt)


class IncidentStatus(APIView):
    def get(self, request):
        incident = Incident.objects.filter(is_open=True).order_by("-start_at").first()
        if not incident:
            return Response({"is_open": False, "counter": 0, "id": None})
        return Response(IncidentSerializer(incident).data)


class IncidentUpdateOperator(APIView):
    def post(self, request):
        try:
            op = int(request.data.get("op", 1))
        except Exception:
            return Response({"error": "op doit être un entier (1/2/3)"}, status=400)

        if op not in (1, 2, 3):
            return Response({"error": "op invalide. Utilise 1, 2 ou 3."}, status=400)

        ack = parse_bool(request.data.get("ack", False), default=False)
        comment = (request.data.get("comment", "") or "").strip()

        with transaction.atomic():
            incident = (
                Incident.objects.select_for_update()
                .filter(is_open=True)
                .order_by("-start_at")
                .first()
            )
            if not incident:
                return Response({"error": "Aucun incident ouvert"}, status=400)

            now = timezone.now()

            # ✅ On enregistre les actions opérateurs
            if op == 1:
                incident.op1_ack = ack
                incident.op1_comment = comment
                incident.op1_saved_at = now
            elif op == 2:
                incident.op2_ack = ack
                incident.op2_comment = comment
                incident.op2_saved_at = now
            else:
                incident.op3_ack = ack
                incident.op3_comment = comment
                incident.op3_saved_at = now

            # ❌ IMPORTANT: NE PAS fermer ici !
            # incident se ferme uniquement quand température redevient normale (services.py)

            incident.save()

        return Response(IncidentSerializer(incident).data)

