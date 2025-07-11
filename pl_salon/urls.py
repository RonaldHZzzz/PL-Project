"""
URL configuration for pl_salon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.signin, name='login'),
    path('register/',views.register, name='register'),
    path('home/',views.home, name='home'),
    path('logout/',views.signout,name='logout'),
    path('jobs/',views.jobs,name='jobs'),
    path('total/',views.total,name='total'),
    path('eliminar_trabajo/<int:trabajo_id>/',views.eliminar_trabajo, name='eliminar_trabajo'),
    path('eliminar_descuento/<int:descuento_id>/',views.eliminar_descuento, name='eliminar_descuento'),
    path('reportes/',views.Report,name='reportes'),
    path('semana/<int:anio>/<int:semana>/', views.semana_detalle, name='semana_detalle'),
    path('analizar/', views.analizar, name='analizar'),


]  
