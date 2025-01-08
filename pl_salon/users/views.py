from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db import IntegrityError  # Para capturar errores de unicidad
from django.contrib import messages

def login_view(request):
    return render(request, 'login.html')

def register(request):
    if request.method == 'GET':
        return render(request, 'register.html', {
            'form': UserCreationForm()
        })
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        if password != confirm_password:
            return render(request, 'register.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden.'
            })

        try:
            # Verificar si el usuario ya existe (opcional, User.objects.create_user también lo hace)
            if User.objects.filter(username=username).exists():
                return render(request, 'register.html', {
                    'form': UserCreationForm(),
                    'error': 'El nombre de usuario ya está en uso.'
                })

            # Registrar usuario
            user = User.objects.create_user(username=username, password=password)
            user.save()

            # Iniciar sesión automáticamente después de registrarse
            login(request, user)
            messages.success(request, 'Usuario registrado exitosamente.')
            return redirect('home')

        except IntegrityError:
            # Captura errores de unicidad en la base de datos
            return render(request, 'register.html', {
                'form': UserCreationForm(),
                'error': 'El nombre de usuario ya está en uso.'
            })

        except Exception as e:
            # Captura cualquier otro error inesperado
            return render(request, 'register.html', {
                'form': UserCreationForm(),
                'error': f'Ocurrió un error: {e}'
            })

def home(request):
    return render(request, 'home.html')
