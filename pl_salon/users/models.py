from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Trabajo(models.Model):
    usuario= models.ForeignKey(User, on_delete=models.CASCADE) #relacion con el usario
    trabajo=models.CharField(max_length=255)#campo de trabajo
    monto=models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro= models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.trabajo} - {self.usuario.username}"