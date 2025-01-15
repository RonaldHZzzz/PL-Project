from django import forms
from .models import Trabajo,Descuentos


class TrabajoForm(forms.ModelForm):
    class Meta:
            model=Trabajo
            fields=['trabajo','monto']
            widgets = {
                'trabajo': forms.TextInput(attrs={
                    'class': 'w-full max-w-xs rounded-lg border border-gray-300 p-3 shadow-sm mb-6',
                    'placeholder': 'Escribe aquí',
                }),
                'monto': forms.TextInput(attrs={
                    'class': 'w-24 ml-6 rounded-lg border border-gray-300 p-3 shadow-sm text-center',
                    'placeholder': '00.00',
                }),
            }
            labels = {
            'trabajo': 'Trabajo realizado',
            'monto': 'Monto',
            }   
            
class DescuentoForm(forms.ModelForm):
    class Meta:
        model = Descuentos
        fields = ['descripcion', 'descuento']  # Solo los campos que necesitas
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-pink-500 focus:ring-pink-500 sm:text-sm',
                'placeholder': 'Ingrese qué se descontó',
                'required': True,
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'block w-full rounded-l-md border-gray-300 shadow-sm focus:border-pink-500 focus:ring-pink-500 sm:text-sm',
                'step': '0.01',
                'placeholder': '0.00',
                'required': True,
            }),
        }

