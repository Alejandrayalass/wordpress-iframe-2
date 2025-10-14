# apps/usuarios/urls.py
from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("health/", views.health, name="health"),
]
