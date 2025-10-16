# apps/wizard/admin.py
"""
Configuración del Django Admin para el MVP
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Cliente, DatosTecnicos, ArchivoBoleta, ProductoSolar,
    MetodoPago, Cotizacion, ItemCotizacion, EstadoWizard
)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'rut', 'email', 'telefono', 'region', 'creado']
    list_filter = ['region', 'creado']
    search_fields = ['nombre', 'apellido', 'rut', 'email']
    readonly_fields = ['creado', 'actualizado']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'rut')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono')
        }),
        ('Ubicación', {
            'fields': ('region', 'direccion')
        }),
        ('Metadata', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )


class ArchivBoletaInline(admin.TabularInline):
    model = ArchivoBoleta
    extra = 0
    readonly_fields = ['nombre_original', 'tamanio_mb', 'subido_en']
    fields = ['archivo', 'nombre_original', 'tamanio_mb', 'subido_en']


@admin.register(DatosTecnicos)
class DatosTecnicosAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo_techo', 'orientacion', 'superficie_aproximada', 'potencia_objetivo']
    list_filter = ['tipo_techo', 'orientacion']
    search_fields = ['cliente__nombre', 'cliente__apellido']
    inlines = [ArchivBoletaInline]
    
    fieldsets = (
        ('Cliente', {
            'fields': ('cliente',)
        }),
        ('Características del Techo', {
            'fields': ('tipo_techo', 'orientacion', 'superficie_aproximada')
        }),
        ('Consumo Energético', {
            'fields': ('potencia_objetivo', 'consumo_promedio')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )


@admin.register(ProductoSolar)
class ProductoSolarAdmin(admin.ModelAdmin):
    list_display = ['sku', 'nombre', 'categoria', 'precio_formato', 'stock', 'activo_badge', 'destacado']
    list_filter = ['categoria', 'activo', 'destacado', 'creado']
    search_fields = ['sku', 'nombre', 'descripcion']
    readonly_fields = ['creado', 'actualizado', 'imagen_preview']
    list_editable = ['activo', 'destacado']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('sku', 'nombre', 'categoria')
        }),
        ('Especificaciones', {
            'fields': ('descripcion', 'potencia', 'atributos')
        }),
        ('Precio e Inventario', {
            'fields': ('precio_clp', 'stock')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview')
        }),
        ('Estado', {
            'fields': ('activo', 'destacado')
        }),
        ('Metadata', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">●</span> Activo')
        return format_html('<span style="color: red;">●</span> Inactivo')
    activo_badge.short_description = 'Estado'
    
    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="200" height="200" style="object-fit: cover;"/>', obj.imagen.url)
        return "Sin imagen"
    imagen_preview.short_description = 'Vista previa'


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'visible_badge', 'orden']
    list_editable = ['orden']
    list_filter = ['visible']
    search_fields = ['nombre', 'descripcion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Datos Bancarios', {
            'fields': ('datos_transferencia',),
            'description': 'Formato JSON: {"banco": "BancoEstado", "titular": "...", "rut": "...", "cuenta": "..."}'
        }),
        ('Visualización', {
            'fields': ('icono', 'orden', 'visible')
        }),
    )
    
    def visible_badge(self, obj):
        if obj.visible:
            return format_html('<span style="color: green;">✓</span> Visible')
        return format_html('<span style="color: gray;">✗</span> Oculto')
    visible_badge.short_description = 'Visibilidad'


class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 0
    readonly_fields = ['nombre_producto', 'sku_producto', 'precio_unitario', 'total_item']
    fields = ['producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'descuento_porcentaje', 'total_item']


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['folio', 'cliente', 'estado_badge', 'total_formato', 'fecha_creacion', 'acciones']
    list_filter = ['estado', 'fecha_creacion', 'fecha_envio']
    search_fields = ['folio', 'cliente__nombre', 'cliente__apellido', 'cliente__rut']
    readonly_fields = ['folio', 'uuid', 'subtotal', 'iva', 'total', 'fecha_creacion', 'fecha_envio', 'fecha_actualizacion', 'pdf_link']
    inlines = [ItemCotizacionInline]
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Identificación', {
            'fields': ('folio', 'uuid', 'estado')
        }),
        ('Cliente', {
            'fields': ('cliente',)
        }),
        ('Totales', {
            'fields': ('subtotal', 'iva', 'descuento', 'total')
        }),
        ('Comentarios', {
            'fields': ('comentarios', 'notas_internas')
        }),
        ('PDF', {
            'fields': ('pdf_generado', 'pdf_link', 'pdf_fecha_generacion')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_envio', 'fecha_actualizacion', 'ip_cliente', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def estado_badge(self, obj):
        colors = {
            'BORRADOR': 'gray',
            'PENDIENTE': 'orange',
            'ENVIADA': 'blue',
            'APROBADA': 'green',
            'RECHAZADA': 'red',
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def total_formato(self, obj):
        return format_html('<strong>${:,.0f}</strong>', obj.total)
    total_formato.short_description = 'Total'
    
    def pdf_link(self, obj):
        if obj.pdf_generado:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Ver PDF</a>',
                obj.pdf_generado.url
            )
        return "No generado"
    pdf_link.short_description = 'PDF'
    
    def acciones(self, obj):
        url_detalle = reverse('wizard:admin_cotizacion_detalle', args=[obj.folio])
        url_reenviar = reverse('wizard:admin_cotizacion_reenviar', args=[obj.folio])
        
        return format_html(
            '<a href="{}" class="button">Ver</a> '
            '<a href="{}" class="button">Reenviar Email</a>',
            url_detalle,
            url_reenviar
        )
    acciones.short_description = 'Acciones'
    
    actions = ['exportar_csv', 'marcar_como_enviada', 'marcar_como_aprobada']
    
    def exportar_csv(self, request, queryset):
        # Implementar exportación CSV
        pass
    exportar_csv.short_description = "Exportar seleccionados a CSV"
    
    def marcar_como_enviada(self, request, queryset):
        queryset.update(estado='ENVIADA')
    marcar_como_enviada.short_description = "Marcar como Enviada"
    
    def marcar_como_aprobada(self, request, queryset):
        queryset.update(estado='APROBADA')