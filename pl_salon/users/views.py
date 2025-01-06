from django.shortcuts import render

# Create your views here.
def hell(request):
    return render(request,'login.html')