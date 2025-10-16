from django.db import transaction
from .models import Cotizacion, ItemCotizacion
from inventario.models import Producto

class CotizacionService:
    
    @transaction.atomic
    def crear_cotizacion_completa(self, datos_cliente, items_data):
        """Crea una cotización con todos sus items"""
        cotizacion = Cotizacion.objects.create(**datos_cliente)
        
        for item_data in items_data:
            producto = Producto.objects.get(id=item_data['producto_id'])
            ItemCotizacion.objects.create(
                cotizacion=cotizacion,
                producto=producto,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario']
            )
        
        # Calcular total
        cotizacion.calcular_total()
        return cotizacion
    
    def duplicar_cotizacion(self, cotizacion_id):
        """Duplica una cotización existente"""
        cotizacion_original = Cotizacion.objects.get(id=cotizacion_id)
        
        with transaction.atomic():
            # Crear nueva cotización
            nueva_cotizacion = Cotizacion.objects.create(
                cliente=cotizacion_original.cliente,
                fecha_vencimiento=cotizacion_original.fecha_vencimiento,
                estado='PENDIENTE',
                notas=f"Copia de cotización #{cotizacion_original.id}"
            )
            
            # Copiar items
            for item in cotizacion_original.items.all():
                ItemCotizacion.objects.create(
                    cotizacion=nueva_cotizacion,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario
                )
            
            nueva_cotizacion.calcular_total()
            return nueva_cotizacion