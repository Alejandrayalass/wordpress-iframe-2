# cotizador_intranet/cotizador_intranet/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # Redirigir raíz a login o dashboard
    path("", RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    
    # Apps principales
    path("core/", include("apps.core.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
    
    # Descomentar cuando crees estas apps:
    # path("cotizaciones/", include("apps.cotizaciones.urls")),
    # path("inventario/", include("apps.inventario.urls")),
    # path("pagos/", include("apps.pagos.urls")),
    
    # API REST (para integración PHP y otros)
    # path("api/", include("apps.api.urls")),
    # path("api-auth/", include("rest_framework.urls")),
]

# Archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass

# Personalizar admin
admin.site.site_header = "Cotizador Intranet - Administración"
admin.site.site_title = "Cotizador Admin"
admin.site.index_title = "Panel de Administración"