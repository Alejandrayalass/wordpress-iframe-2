from django.db import models
from django.core.validators import MinValueValidator

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, default='')
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, blank=True)
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    descripcion = models.TextField(blank=True, default='')
    precio = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    
    # Metadata
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generar código único
            ultimo = Producto.objects.order_by('-id').first()
            numero = (ultimo.id + 1) if ultimo else 1
            self.codigo = f"PROD-{numero:05d}"
        super().save(*args, **kwargs)
    
    @property
    def stock_bajo(self):
        """Retorna True si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo
    
    @property
    def disponible(self):
        """Retorna True si está activo y tiene stock"""
        return self.activo and self.stock > 0