from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
# Create your views here.
def login(request):
    return render(request,'login.html',{
        
    })

    
def register(request):
    return render(request,'register.html',{
        
    })