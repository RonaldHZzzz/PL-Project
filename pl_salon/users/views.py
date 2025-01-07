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
                return HttpResponse('usuario creado')
            except:
                return HttpResponse('usurio no existe')
        return HttpResponse('conctraseña no e igual')
    
    
        
    