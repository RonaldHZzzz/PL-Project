from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 
from django.http import HttpResponse
# Create your views here.
def login(request):
    return render(request,'login.html',{
        
    })

    
def register(request):
    
    if request.method=='GET':
        return render(request,'register.html',{
        'form':UserCreationForm
        })
    else:
        if request.POST['password']== request.POST['confirm-password']:
            #register user
            try:
                User.objects.create_user(username=request.POST['username'],password=request.POST['password'])
                User.save
                return render(request,'register.html',{
                'form':UserCreationForm,
                'success': 'Usuario creado'
                })
            except:
                return render(request,'register.html',{
                    'form':UserCreationForm,
                    'error': 'Usuario ya existe'
                    })
        return render(request,'register.html',{
                'form':UserCreationForm,
                'error': 'Contraseñas no coinciden'
                })
    
    
        
    