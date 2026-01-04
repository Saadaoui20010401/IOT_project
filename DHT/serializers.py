from rest_framework import serializers
from .models import Dht11, Incident


class DHT11Serializer(serializers.ModelSerializer):
    class Meta:
        model = Dht11
        fields = ["id", "temp", "hum", "dt"]


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            "id",
            "start_at",
            "end_at",
            "is_open",
            "counter",
            "incident_type",
            "min_allowed_temp",
            "max_allowed_temp",
            "max_temp",
            "min_temp",
            "op1_ack", "op2_ack", "op3_ack",
            "op1_comment", "op2_comment", "op3_comment",
            "op1_saved_at", "op2_saved_at", "op3_saved_at",
        ]
