from django.contrib import admin
from .models import Trabajo, Descuentos


# Configuración para mostrar detalles adicionales en la interfaz de administrador
@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ('trabajo', 'usuario', 'monto', 'fecha_registro')  # Campos que se mostrarán en la lista
    search_fields = ('trabajo', 'usuario__username')  # Campos para habilitar búsquedas
    list_filter = ('fecha_registro',)  # Filtro por fechas

@admin.register(Descuentos)
class DescuentosAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'usuario', 'descuento', 'fecha_registro_descuento')
    search_fields = ('descripcion', 'usuario__username')
    list_filter = ('fecha_registro_descuento',)