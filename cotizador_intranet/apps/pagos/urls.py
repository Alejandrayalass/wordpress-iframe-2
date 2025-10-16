# apps/pagos/urls.py
from django.urls import path
from . import views

app_name = "pagos"

urlpatterns = [
    # Gestión de tarjetas
    path("tarjetas/", views.TarjetasListView.as_view(), name="lista_tarjetas"),
    path("tarjetas/agregar/", views.agregar_tarjeta, name="agregar_tarjeta"),
    path("tarjetas/<int:tarjeta_id>/eliminar/", views.eliminar_tarjeta, name="eliminar_tarjeta"),
    path("tarjetas/<int:tarjeta_id>/predeterminada/", views.marcar_predeterminada, name="marcar_predeterminada"),
    
    # Pagos One-Click
    path("oneclick/<int:cotizacion_id>/", views.pagar_oneclick, name="pagar_oneclick"),
    path("oneclick/procesar/", views.procesar_pago_oneclick, name="procesar_oneclick"),
    
    # Webpay (Chile)
    path("webpay/<int:cotizacion_id>/iniciar/", views.iniciar_webpay, name="iniciar_webpay"),
    path("webpay/retorno/", views.retorno_webpay, name="retorno_webpay"),
    path("webpay/final/", views.final_webpay, name="final_webpay"),
    
    # Transacciones
    path("transacciones/", views.TransaccionesListView.as_view(), name="lista_transacciones"),
    path("transacciones/<int:pk>/", views.TransaccionDetailView.as_view(), name="detalle_transaccion"),
    path("transacciones/<int:transaccion_id>/reembolsar/", views.reembolsar_transaccion, name="reembolsar"),
    
    # Reportes de pagos
    path("reportes/", views.ReportesPagosView.as_view(), name="reportes"),
]