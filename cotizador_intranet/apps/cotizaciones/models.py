from django.db import models
from apps.usuarios.models import Cliente
from decimal import Decimal

class Cotizacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('ENVIADA', 'Enviada'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones')
    numero_cotizacion = models.CharField(max_length=20, unique=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notas = models.TextField(blank=True, default='')
    
    # Campos para PDF
    pdf_generado = models.FileField(upload_to='cotizaciones/pdf/', blank=True, null=True)
    pdf_fecha_generacion = models.DateTimeField(blank=True, null=True)
    
    # Campos para pagos
    pago_procesado = models.BooleanField(default=False)
    metodo_pago = models.CharField(max_length=50, blank=True, default='')
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
    
    def __str__(self):
        return f"Cotización {self.numero_cotizacion} - {self.cliente.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.numero_cotizacion:
            # Generar número único
            ultimo = Cotizacion.objects.order_by('-id').first()
            numero = (ultimo.id + 1) if ultimo else 1
            self.numero_cotizacion = f"COT-{numero:06d}"
        super().save(*args, **kwargs)
    
    def calcular_total(self):
        """Calcula subtotal, impuesto (19% IVA) y total"""
        items = self.items.all()
        self.subtotal = sum(item.subtotal for item in items)
        self.impuesto = self.subtotal * Decimal('0.19')
        self.total = self.subtotal + self.impuesto
        self.save()


class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                    help_text="Descuento en porcentaje")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Item de Cotización'
        verbose_name_plural = 'Items de Cotización'
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal con descuento
        precio_con_descuento = self.precio_unitario * (1 - self.descuento / 100)
        self.subtotal = precio_con_descuento * self.cantidad
        super().save(*args, **kwargs)
        # Actualizar total de la cotización
        self.cotizacion.calcular_total()