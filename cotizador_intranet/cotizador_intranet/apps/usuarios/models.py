from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    rut = models.CharField(max_length=12, blank=True, default='')
    telefono = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return self.username

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
