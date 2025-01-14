from django import forms
from .models import Trabajo


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

