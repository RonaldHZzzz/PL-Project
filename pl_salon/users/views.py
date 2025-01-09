from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib import messages




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
            # Crear usuario
            user = User.objects.create_user(username=username, password=password)
            user.is_active = True
            user.save()

            # Autenticar al usuario recién creado
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)  # Aquí user es autenticado
                messages.success(request, 'Usuario registrado exitosamente.')
                return redirect('home')
            else:
                return render(request, 'register.html', {
                    'form': UserCreationForm(),
                    'error': 'Error al autenticar al usuario después del registro.'
                })

        except IntegrityError:
            return render(request, 'register.html', {
                'form': UserCreationForm(),
                'error': 'El nombre de usuario ya está en uso.'
            })

        except Exception as e:
            return render(request, 'register.html', {
                'form': UserCreationForm(),
                'error': f'Ocurrió un error inesperado: {e}'
            })


def home(request):
    return render(request, 'home.html')


def signout(request):
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('home')


def signin(request):
    return render(request,'login.html')