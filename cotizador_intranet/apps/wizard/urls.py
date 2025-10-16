# apps/wizard/urls.py
from django.urls import path
from . import views

app_name = 'wizard'

urlpatterns = [
    # WIZARD EMBEBIBLE (para WordPress)
    path('embed/', views.wizard_embed, name='embed'),
    path('embed/height.js', views.wizard_height_js, name='height_js'),
    
    # PASOS DEL WIZARD (AJAX)
    path('paso1/', views.wizard_paso1, name='paso1'),
    path('paso2/', views.wizard_paso2, name='paso2'),
    path('paso3/', views.wizard_paso3, name='paso3'),
    path('paso4/', views.wizard_paso4, name='paso4'),
    path('paso5/', views.wizard_paso5, name='paso5'),
    path('paso6/', views.wizard_paso6, name='paso6'),
    
    # UTILIDADES AJAX
    path('ajax/guardar-borrador/', views.wizard_guardar_borrador, name='guardar_borrador'),
    path('ajax/validar-rut/', views.wizard_validar_rut, name='validar_rut'),
    path('ajax/regiones/', views.wizard_obtener_regiones, name='regiones'),
    
    # ADMIN - COTIZACIONES
    path('admin/cotizaciones/', views.admin_cotizaciones_lista, name='admin_cotizaciones'),
    path('admin/cotizaciones/<str:folio>/', views.admin_cotizacion_detalle, name='admin_cotizacion_detalle'),
    path('admin/cotizaciones/<str:folio>/reenviar/', views.admin_cotizacion_reenviar, name='admin_cotizacion_reenviar'),
    path('admin/cotizaciones/exportar/csv/', views.admin_cotizaciones_exportar_csv, name='admin_exportar_csv'),
    
    # ADMIN - PRODUCTOS
    path('admin/productos/', views.admin_productos_lista, name='admin_productos'),
    path('admin/productos/<int:producto_id>/toggle/', views.admin_producto_toggle_activo, name='admin_producto_toggle'),
    
    # ADMIN - MÉTODOS DE PAGO
    path('admin/metodos-pago/', views.admin_metodos_pago_lista, name='admin_metodos_pago'),
    path('admin/metodos-pago/<int:metodo_id>/toggle/', views.admin_metodo_pago_toggle_visible, name='admin_metodo_toggle'),
]