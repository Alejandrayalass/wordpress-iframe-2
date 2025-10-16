# apps/cotizaciones/urls.py
from django.urls import path
from . import views
from .pdf_generator import generar_pdf_cotizacion

app_name = "cotizaciones"

urlpatterns = [
    # Listado y CRUD
    path("", views.CotizacionListView.as_view(), name="lista"),
    path("crear/", views.CotizacionCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.CotizacionDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.CotizacionUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.CotizacionDeleteView.as_view(), name="eliminar"),
    
    # PDF
    path("<int:cotizacion_id>/pdf/", generar_pdf_cotizacion, name="generar_pdf"),
    path("<int:pk>/pdf/download/", views.descargar_pdf, name="descargar_pdf"),
    
    # Acciones especiales
    path("<int:pk>/duplicar/", views.duplicar_cotizacion, name="duplicar"),
    path("<int:pk>/enviar-email/", views.enviar_cotizacion_email, name="enviar_email"),
    path("<int:pk>/cambiar-estado/", views.cambiar_estado, name="cambiar_estado"),
    
    # Items de cotización (AJAX)
    path("<int:cotizacion_id>/items/agregar/", views.agregar_item, name="agregar_item"),
    path("items/<int:item_id>/eliminar/", views.eliminar_item, name="eliminar_item"),
    
    # Reportes
    path("reportes/", views.ReportesView.as_view(), name="reportes"),
    path("reportes/excel/", views.exportar_excel, name="exportar_excel"),
]