import csv
import json
from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive

from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from .models import Dht11, Incident


# =========================
# PAGES
# =========================

def home(request):
    # ✅ prendre les derniers enregistrements
    latest_data = Dht11.objects.order_by("-dt")[:10]
    return render(request, "home.html", {"latest_data": latest_data})


# ✅ IMPORTANT : force la création du cookie csrftoken pour que dashboard.js puisse POST correctement
@ensure_csrf_cookie
@login_required
def dashboard(request):
    operator = getattr(request.user, "operator_profile", None)
    return render(request, "dashboard.html", {"operator": operator})


def my_chart_temp(request):
    return render(request, "graph_temp.html")


def my_chart_hum(request):
    return render(request, "graph_hum.html")


def data_table(request):
    # ✅ prendre les derniers enregistrements
    latest_data = Dht11.objects.order_by("-dt")[:50]
    return render(request, "value.html", {"data_list": latest_data})


@login_required
def incident_archive(request):
    incidents = Incident.objects.filter(is_open=False).order_by("-start_at")
    return render(request, "incident_archive.html", {"incidents": incidents})


@login_required
def incident_detail(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    return render(request, "incident_detail.html", {"incident": incident})

@login_required
def test_api(request):
    return render(request, "test_api.html")


# =========================
# API - LATEST DATA
# =========================

def latest_json(request):
    last_dht = (
        Dht11.objects
        .order_by("-dt")
        .values("temp", "hum", "dt")
        .first()
    )

    if not last_dht:
        return JsonResponse({"detail": "no data"}, status=404)

    incident = Incident.objects.filter(is_open=True).order_by("-start_at").first()
    alert_count = incident.counter if incident else 0
    incident_type = incident.incident_type if incident else None

    dt = last_dht.get("dt")

    return JsonResponse({
        "temperature": last_dht.get("temp"),
        "humidity": last_dht.get("hum"),
        "timestamp": dt.isoformat() if dt else None,
        "alert_count": alert_count,
        "is_open": bool(incident),
        "incident_type": incident_type,
    })


# ✅ Alias (si tu l’utilises ailleurs)
def latest_data(request):
    return latest_json(request)


# =========================
# CHART DATA
# =========================

def chart_data(request, period):
    data = Dht11.objects.all().order_by("dt")
    now = timezone.now()

    start_custom = request.GET.get("start")
    end_custom = request.GET.get("end")

    if start_custom and end_custom:
        start_dt = parse_datetime(start_custom)
        end_dt = parse_datetime(end_custom)

        if start_dt and end_dt:
            if is_naive(start_dt):
                start_dt = make_aware(start_dt)
            if is_naive(end_dt):
                end_dt = make_aware(end_dt)

            data = data.filter(dt__range=[start_dt, end_dt])
    else:
        if period == "jour":
            data = data.filter(dt__gte=now - timedelta(hours=24))
        elif period == "semaine":
            data = data.filter(dt__gte=now - timedelta(days=7))
        elif period == "mois":
            data = data.filter(dt__gte=now - timedelta(days=30))
        else:
            return JsonResponse({"error": "period must be: jour | semaine | mois"}, status=400)

    labels = [entry.dt.strftime("%H:%M %d/%m") for entry in data]
    temp_data = [entry.temp for entry in data]
    hum_data = [entry.hum for entry in data]

    return JsonResponse({
        "labels": labels,
        "temp_data": temp_data,
        "hum_data": hum_data,
    })


# =========================
# INCIDENT STATUS / UPDATE
# ⚠️ Chez toi, les vraies routes utilisent api.py (DRF)
# Je laisse ces fonctions pour compatibilité si tu les utilises un jour.
# =========================

def incident_status(request):
    incident = Incident.objects.filter(is_open=True).order_by("-start_at").first()
    if not incident:
        return JsonResponse({"is_open": False})

    return JsonResponse({
        "is_open": True,
        "incident_id": incident.id,
        "incident_type": incident.incident_type,
        "alert_count": incident.counter,
        "start_at": incident.start_at.isoformat() if incident.start_at else None,
        "max_temp": incident.max_temp,
    })


@csrf_exempt
@require_http_methods(["POST"])
def incident_update(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    incident_id = payload.get("incident_id")
    if not incident_id:
        incident = Incident.objects.filter(is_open=True).order_by("-start_at").first()
    else:
        incident = Incident.objects.filter(id=incident_id).first()

    if not incident:
        return JsonResponse({"error": "incident not found"}, status=404)

    if "op1_comment" in payload:
        incident.op1_comment = payload.get("op1_comment") or ""
    if "op2_comment" in payload:
        incident.op2_comment = payload.get("op2_comment") or ""
    if "op3_comment" in payload:
        incident.op3_comment = payload.get("op3_comment") or ""

    if payload.get("close") is True:
        incident.is_open = False
        incident.end_at = timezone.now()

    incident.save()

    return JsonResponse({"ok": True, "incident_id": incident.id, "is_open": incident.is_open})


# =========================
# API POST (si tu veux l’utiliser hors DRF)
# =========================

@csrf_exempt
@require_http_methods(["POST"])
def api_post(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    temp = payload.get("temp")
    hum = payload.get("hum")

    if temp is None or hum is None:
        return JsonResponse({"error": "temp and hum are required"}, status=400)

    try:
        temp = float(temp)
        hum = float(hum)
    except Exception:
        return JsonResponse({"error": "temp/hum must be numeric"}, status=400)

    row = Dht11.objects.create(temp=temp, hum=hum, dt=timezone.now())

    return JsonResponse({
        "ok": True,
        "id": row.id,
        "temp": row.temp,
        "hum": row.hum,
        "dt": row.dt.isoformat() if row.dt else None,
    })


# =========================
# EXPORTS
# =========================

def download_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="dht_data.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Température", "Humidité"])

    for item in Dht11.objects.all().order_by("-dt"):
        writer.writerow([
            item.dt.isoformat() if item.dt else "",
            item.temp,
            item.hum
        ])

    return response


def download_incident_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="incidents_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID", "Date Début", "Date Fin", "État", "Type", "Max Temp", "Min Temp", "Alertes",
        "Opérateur 1 (Comm)", "Opérateur 2 (Comm)", "Opérateur 3 (Comm)"
    ])

    incidents = Incident.objects.all().order_by("-start_at")

    for inc in incidents:
        end = inc.end_at.isoformat() if inc.end_at else "En cours"
        state = "Ouvert" if inc.is_open else "Fermé"

        writer.writerow([
            inc.id,
            inc.start_at.isoformat() if inc.start_at else "",
            end,
            state,
            inc.incident_type,
            inc.max_temp,
            inc.min_temp,
            inc.counter,
            inc.op1_comment,
            inc.op2_comment,
            inc.op3_comment,
        ])

    return response


def download_json(request):
    data = list(
        Dht11.objects.all()
        .order_by("-dt")
        .values("id", "temp", "hum", "dt")
    )

    for row in data:
        row["dt"] = row["dt"].isoformat() if row["dt"] else None

    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type="application/json"
    )
    response["Content-Disposition"] = 'attachment; filename="dht_data.json"'
    return response
