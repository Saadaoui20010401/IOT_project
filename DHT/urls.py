from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from . import api

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Auth
    path(
        "login/",auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,  # ✅ si déjà connecté -> dashboard
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            next_page="login"  # ✅ redirection vers login après logout
        ),
        name="logout",
    ),

    # Dashboard (protégé)
    path("dashboard/", views.dashboard, name="dashboard"),

    # Graphiques
    path("myChartTemp/", views.my_chart_temp, name="my_chart_temp"),
    path("myChartHum/", views.my_chart_hum, name="my_chart_hum"),

    # Données
    path("data/", views.data_table, name="data_table"),
    path("index/", views.data_table, name="data_table"),

    # API
    path("api/post/", api.DhtCreateView.as_view(), name="json_post"),
    path("api/", api.DList.as_view(), name="json_list"),
    path("api/list/", api.DList.as_view(), name="json_list"),

    # API graphiques
    path("api/data/<str:period>/", views.chart_data, name="chart_data"),

    # API dashboard (latest)
    path("latest/", views.latest_json, name="latest_json"),

    # Incidents
    path("incident/status/", api.IncidentStatus.as_view(), name="incident_status"),
    path("incident/update/", api.IncidentUpdateOperator.as_view(), name="incident_update"),
    path("incident/archive/", views.incident_archive, name="incident_archive"),
    path("incident/<int:pk>/", views.incident_detail, name="incident_detail"),

    # Exports
    path("download_csv/", views.download_csv, name="download_csv"),
    path("download_incident_csv/", views.download_incident_csv, name="download_incident_csv"),
    path("download_json/", views.download_json, name="download_json"),

    # Page test
    path("test/", views.test_api, name="test_api"),
]
