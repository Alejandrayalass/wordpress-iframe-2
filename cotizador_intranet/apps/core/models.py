from django.db import models

class ConfiguracionSistema(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    valor = models.CharField(max_length=255, blank=True, default='')
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} = {self.valor}"

class Auditoria(models.Model):
    accion = models.CharField(max_length=100)
    usuario = models.CharField(max_length=150, blank=True, default='')
    detalle = models.TextField(blank=True, default='')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} @ {self.fecha:%Y-%m-%d %H:%M}"
