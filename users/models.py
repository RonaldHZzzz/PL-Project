from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Trabajo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Relación con el usuario
    trabajo = models.CharField(max_length=255)  # Descripción del trabajo
    monto = models.DecimalField(max_digits=10, decimal_places=2)  # Monto del trabajo
    # Guardar la fecha local, evitando desfaces de UTC
    fecha_registro = models.DateField(
        default=timezone.localdate
    )

    def __str__(self):
        return f"{self.trabajo} - {self.usuario.username}"  


class Descuentos(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Relación con el usuario
    descripcion = models.CharField(max_length=255)  # Descripción del descuento
    descuento = models.DecimalField(max_digits=10, decimal_places=2)  # Monto del descuento
    # Guardar la fecha local, evitando desfaces de UTC
    fecha_registro_descuento = models.DateField(
        default=timezone.localdate
    )

    def __str__(self):
        return f"Descuento de {self.descripcion} para {self.usuario.username}"
