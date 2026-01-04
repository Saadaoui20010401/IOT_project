from django.db import models
from django.conf import settings


class Dht11(models.Model):
    temp = models.FloatField(null=True, blank=True)
    hum = models.FloatField(null=True, blank=True)
    dt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dt"]

    def __str__(self):
        return f"{self.dt} -> T={self.temp}°C, H={self.hum}%"


class Incident(models.Model):
    """
    Conforme consigne prof (modèle), sans casser ton projet :
    - start_at / end_at
    - max_temp observée
    - min_allowed_temp / max_allowed_temp
    - counter
    - is_open
    + tes champs (type, opérateurs, anti-spam...)
    """

    # --- Champs demandés ---
    start_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(null=True, blank=True)

    min_allowed_temp = models.FloatField(default=10.0)
    max_allowed_temp = models.FloatField(default=23.0)

    max_temp = models.FloatField(null=True, blank=True)

    # (utile pour incident froid)
    min_temp = models.FloatField(null=True, blank=True)

    counter = models.IntegerField(default=0)
    is_open = models.BooleanField(default=True, db_index=True)

    # --- Champs existants (on garde) ---
    INCIDENT_TYPES = (
        ("HOT", "Température haute"),
        ("COLD", "Température basse"),
    )
    incident_type = models.CharField(max_length=10, choices=INCIDENT_TYPES, default="HOT")

    last_alert_at = models.DateTimeField(null=True, blank=True)
        # --- VoIP: éviter de spammer les appels (1 seul appel par incident) ---
    voip_triggered_at = models.DateTimeField(null=True, blank=True)

    op1_ack = models.BooleanField(default=False)
    op2_ack = models.BooleanField(default=False)
    op3_ack = models.BooleanField(default=False)

    op1_comment = models.TextField(blank=True)
    op2_comment = models.TextField(blank=True)
    op3_comment = models.TextField(blank=True)

    op1_saved_at = models.DateTimeField(null=True, blank=True)
    op2_saved_at = models.DateTimeField(null=True, blank=True)
    op3_saved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-start_at"]

    def __str__(self):
        status = "OPEN" if self.is_open else "CLOSED"
        return f"Incident #{self.id} ({status}) counter={self.counter}"

    @property
    def is_active(self):
        return self.is_open


class OperatorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="operator_profile"
    )
    nom = models.CharField(max_length=80)
    prenom = models.CharField(max_length=80)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Operator Profile"
        verbose_name_plural = "Operator Profiles"

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.user.username})"
