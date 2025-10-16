# apps/wizard/models.py
"""
Modelos para el formulario multi-step (wizard) del MVP
Sistema de cotización solar para instaladores
"""

from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator
from decimal import Decimal
import uuid

class Cliente(models.Model):
    """Datos personales del cliente - PASO 1"""
    # Datos personales
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    rut = models.CharField(max_length=12, verbose_name="RUT", help_text="Ej: 12345678-9")
    email = models.EmailField(verbose_name="Email")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    
    # Ubicación
    region = models.CharField(max_length=100, verbose_name="Región")
    direccion = models.TextField(verbose_name="Dirección completa")
    
    # Metadata
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-creado']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut})"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class DatosTecnicos(models.Model):
    """Información técnica del proyecto - PASO 2"""
    TIPO_TECHO_CHOICES = [
        ('PLANCHAS', 'Planchas'),
        ('TEJA', 'Teja'),
        ('LOSA', 'Losa'),
        ('FIBROCEMENTO', 'Fibrocemento'),
        ('METALICO', 'Metálico'),
        ('OTRO', 'Otro'),
    ]
    
    ORIENTACION_CHOICES = [
        ('NORTE', 'Norte'),
        ('SUR', 'Sur'),
        ('ESTE', 'Este'),
        ('OESTE', 'Oeste'),
        ('NORESTE', 'Noreste'),
        ('NOROESTE', 'Noroeste'),
        ('SURESTE', 'Sureste'),
        ('SUROESTE', 'Suroeste'),
    ]
    
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='datos_tecnicos')
    
    # Datos técnicos
    tipo_techo = models.CharField(max_length=20, choices=TIPO_TECHO_CHOICES)
    orientacion = models.CharField(max_length=20, choices=ORIENTACION_CHOICES)
    superficie_aproximada = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name="Superficie aprox. (m²)",
        validators=[MinValueValidator(0)]
    )
    potencia_objetivo = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name="Potencia objetivo (kW)",
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    consumo_promedio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Consumo promedio mensual (kWh)",
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    
    # Notas adicionales
    observaciones = models.TextField(blank=True, verbose_name="Observaciones técnicas")
    
    class Meta:
        verbose_name = "Datos Técnicos"
        verbose_name_plural = "Datos Técnicos"
    
    def __str__(self):
        return f"Datos técnicos - {self.cliente.nombre_completo}"


class ArchivoBoleta(models.Model):
    """Archivos adjuntos (boleta de luz) - PASO 2"""
    datos_tecnicos = models.ForeignKey(DatosTecnicos, on_delete=models.CASCADE, related_name='archivos')
    
    archivo = models.FileField(
        upload_to='boletas/%Y/%m/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        verbose_name="Boleta de luz"
    )
    nombre_original = models.CharField(max_length=255)
    tamanio = models.IntegerField(help_text="Tamaño en bytes")
    mime_type = models.CharField(max_length=100)
    subido_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Archivo Boleta"
        verbose_name_plural = "Archivos Boletas"
    
    def __str__(self):
        return f"Boleta - {self.nombre_original}"
    
    @property
    def tamanio_mb(self):
        return round(self.tamanio / (1024 * 1024), 2)


class ProductoSolar(models.Model):
    """Catálogo de productos solares - Administrable"""
    CATEGORIA_CHOICES = [
        ('PANEL', 'Panel Solar'),
        ('INVERSOR', 'Inversor'),
        ('BATERIA', 'Batería'),
        ('ESTRUCTURA', 'Estructura de montaje'),
        ('CABLEADO', 'Cableado'),
        ('PROTECCION', 'Protección eléctrica'),
        ('OTRO', 'Otro'),
    ]
    
    # Identificación
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del producto")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    
    # Especificaciones
    descripcion = models.TextField(verbose_name="Descripción")
    potencia = models.CharField(max_length=50, blank=True, verbose_name="Potencia (ej: 550W, 15kW)")
    atributos = models.JSONField(
        default=dict,
        blank=True,
        help_text="Atributos adicionales en formato JSON"
    )
    
    # Precio y stock
    precio_clp = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio CLP"
    )
    stock = models.IntegerField(default=0, verbose_name="Stock disponible")
    
    # Imagen
    imagen = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True,
        verbose_name="Foto del producto"
    )
    
    # Estado
    activo = models.BooleanField(default=True, verbose_name="Activo")
    destacado = models.BooleanField(default=False, verbose_name="Destacado")
    
    # Metadata
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto Solar"
        verbose_name_plural = "Productos Solares"
        ordering = ['-destacado', 'categoria', 'nombre']
    
    def __str__(self):
        return f"{self.sku} - {self.nombre}"
    
    @property
    def precio_formato(self):
        return f"${self.precio_clp:,.0f}"


class MetodoPago(models.Model):
    """Métodos de pago informativos - Administrable - PASO 4"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre del método")
    descripcion = models.TextField(verbose_name="Descripción")
    
    # Datos bancarios (para transferencias)
    datos_transferencia = models.JSONField(
        default=dict,
        blank=True,
        help_text="Ej: {banco: 'BancoEstado', titular: 'Empresa XYZ', rut: '12345678-9', cuenta: '123456789'}"
    )
    
    # Visualización
    icono = models.CharField(max_length=50, blank=True, help_text="Clase de icono FontAwesome")
    orden = models.IntegerField(default=0, help_text="Orden de visualización")
    visible = models.BooleanField(default=True, verbose_name="Visible en formulario")
    
    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class Cotizacion(models.Model):
    """Cotización completa - Generada al finalizar wizard"""
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADA', 'Enviada'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    # Identificación
    folio = models.CharField(max_length=20, unique=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Relaciones
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones')
    
    # Datos guardados (snapshot del momento)
    datos_tecnicos_snapshot = models.JSONField(help_text="Snapshot de datos técnicos")
    
    # Totales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Descuento manual aplicado"
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Comentarios finales - PASO 6
    comentarios = models.TextField(blank=True, verbose_name="Comentarios del cliente")
    notas_internas = models.TextField(blank=True, verbose_name="Notas internas")
    
    # PDF generado
    pdf_generado = models.FileField(
        upload_to='cotizaciones/pdf/%Y/%m/',
        blank=True,
        null=True
    )
    pdf_fecha_generacion = models.DateTimeField(blank=True, null=True)
    
    # Estado y fechas
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Metadata
    ip_cliente = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Cotización {self.folio} - {self.cliente.nombre_completo}"
    
    def save(self, *args, **kwargs):
        if not self.folio:
            # Generar folio único
            ultimo = Cotizacion.objects.order_by('-id').first()
            numero = (ultimo.id + 1) if ultimo else 1
            self.folio = f"COT-{numero:06d}"
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        """Calcula subtotal, IVA y total"""
        items = self.items.all()
        self.subtotal = sum(item.total_item for item in items)
        self.iva = self.subtotal * Decimal('0.19')  # IVA 19%
        self.total = self.subtotal + self.iva - self.descuento
        self.save()


class ItemCotizacion(models.Model):
    """Items de productos en la cotizacion - PASO 3"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(ProductoSolar, on_delete=models.PROTECT)
    
    # Datos snapshot (por si el producto cambia después)
    nombre_producto = models.CharField(max_length=200)
    sku_producto = models.CharField(max_length=50)
    descripcion_producto = models.TextField()
    
    # Cantidades y precios
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Descuento en porcentaje"
    )
    total_item = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Orden de visualización
    orden = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Item de Cotización"
        verbose_name_plural = "Items de Cotización"
        ordering = ['orden', 'id']
    
    def __str__(self):
        return f"{self.nombre_producto} x {self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Guardar snapshot del producto
        if self.producto_id and not self.nombre_producto:
            self.nombre_producto = self.producto.nombre
            self.sku_producto = self.producto.sku
            self.descripcion_producto = self.producto.descripcion
            if not self.precio_unitario:
                self.precio_unitario = self.producto.precio_clp
        
        # Calcular total con descuento
        precio_con_descuento = self.precio_unitario * (1 - self.descuento_porcentaje / 100)
        self.total_item = precio_con_descuento * self.cantidad
        
        super().save(*args, **kwargs)
        
        # Actualizar totales de la cotización
        if self.cotizacion_id:
            self.cotizacion.calcular_totales()


class EstadoWizard(models.Model):
    """Guardar estado del wizard para continuar después"""
    session_key = models.CharField(max_length=100, unique=True)
    paso_actual = models.IntegerField(default=1)
    datos = models.JSONField(default=dict, help_text="Datos del wizard en formato JSON")
    
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    expira_en = models.DateTimeField()
    
    class Meta:
        verbose_name = "Estado del Wizard"
        verbose_name_plural = "Estados del Wizard"
    
    def __str__(self):
        return f"Wizard paso {self.paso_actual} - {self.session_key[:10]}"