# cotizador_intranet/cotizador_intranet/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("core/", include("apps.core.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
]
