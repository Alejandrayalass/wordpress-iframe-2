from django.contrib import admin
from .models import Cliente, ConfiguracionSistema, Auditoria

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_cliente', 'ruc_dni', 'telefono', 'activo', 'fecha_creacion']
    list_filter = ['tipo_cliente', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'ruc_dni', 'email']
    list_editable = ['activo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ['clave', 'valor', 'fecha_actualizacion']
    search_fields = ['clave', 'descripcion']
    readonly_fields = ['fecha_actualizacion']

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'accion', 'modelo', 'ip_address', 'fecha_creacion']
    list_filter = ['accion', 'modelo', 'fecha_creacion']
    search_fields = ['usuario__username', 'descripcion', 'ip_address']
    readonly_fields = ['usuario', 'accion', 'modelo', 'objeto_id', 'descripcion', 'ip_address', 'fecha_creacion']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False