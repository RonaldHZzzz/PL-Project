import datetime
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Trabajo, Descuentos
from .forms import TrabajoForm, DescuentoForm
from django.db.models import Sum





def register(request):
    if request.user.is_authenticated:  # Verifica si el usuario ya está autenticado
        return redirect('home')  # Redirige a 'home'
    
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
            user = User.objects.create_user(username=username, password=password)
            user.is_active = True
            user.save()
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
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
            
@login_required
def home(request):
    if request.method == 'POST':
        form = TrabajoForm(request.POST)
        if form.is_valid():
            trabajo = form.save(commit=False)
            trabajo.usuario = request.user  # Asociar el trabajo con el usuario actual
            trabajo.save()
            messages.success(request, 'Trabajo registrado exitosamente.')
            return redirect('home')  # Redirigir a la misma página después de guardar
        else:
            messages.error(request, 'Hubo un error al registrar el trabajo.')
    else:
        form = TrabajoForm()
    
    # Obtener los trabajos del usuario actual
        trabajos = Trabajo.objects.filter(usuario=request.user).order_by('-fecha_registro')#esto solo en caso de filtrar
    
    return render(request, 'home.html', {'form': form, 'trabajos': trabajos})

@login_required
def signout(request):
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('home')


def signin(request):
    if request.user.is_authenticated:  # Verifica si el usuario ya está autenticado
        return redirect('home')  # Redirige a 'home'
    
    if request.method == 'GET':
        return render(request, 'login.html', {
            'form': AuthenticationForm
        })
    else: 
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'login.html', {
                'form': AuthenticationForm,
                'errorlogin': 'Usuario y Contraseña incorrectos.'
            })
        else:
            login(request, user)
            return redirect('home')
        
@login_required
def jobs(request):
    # Obtener las fechas desde el formulario
    from_date = request.GET.get('from-date')
    to_date = request.GET.get('to-date')

    # Filtrar los trabajos si las fechas están presentes
    if from_date and to_date:
        trabajos = Trabajo.objects.filter(
            fecha_registro__gte=from_date,  # fecha mayor o igual a 'Desde'
            fecha_registro__lte=to_date     # fecha menor o igual a 'Hasta'
        )
    else:
        # Si no se proporciona ningún filtro, obtener todos los trabajos
        trabajos = Trabajo.objects.all()
          # Obtener todos los descuentos del usuario actual
    descuentos = Descuentos.objects.all()

    
    context={
            'trabajos':trabajos,
            'descuentos':descuentos
        }
    return render(request, 'jobs.html',context)



@login_required
def total(request):
    # Obtener la fecha actual
    hoy = datetime.date.today()
    semana_actual = hoy.isocalendar()[1]  # Número de semana actual
    anio_actual = hoy.year  # Año actual
    mes_actual = hoy.month  # Mes actual

    # Filtrar los trabajos de la semana actual y agrupar por día de la semana
    trabajos_semanales = Trabajo.objects.filter(
        fecha_registro__year=anio_actual, 
        fecha_registro__week=semana_actual
    ).annotate(dia_semana=ExtractWeekDay('fecha_registro')).values('dia_semana').annotate(total=Sum('monto'))

    # Crear un diccionario para las ganancias diarias
    ingresos_por_dia = {i: 0 for i in range(1, 8)}  # Días de la semana (1=Lunes, 7=Domingo)
    for trabajo in trabajos_semanales:
        ingresos_por_dia[trabajo['dia_semana']] = trabajo['total']

    # Convertir a lista en orden (lunes a domingo)
    ingresos_por_dia_lista = [ingresos_por_dia[dia] for dia in range(1, 8)]

    # Filtrar y calcular totales mensuales, descuentos, etc., como antes
    total_mensual = Trabajo.objects.filter(
        fecha_registro__year=anio_actual, 
        fecha_registro__month=mes_actual
    ).aggregate(Sum('monto'))['monto__sum'] or 0

    descuentos = Descuentos.objects.filter(usuario=request.user).order_by('-fecha_registro_descuento')
    total_descontado = descuentos.aggregate(Sum('descuento'))['descuento__sum'] or 0
    total_final = sum(ingresos_por_dia_lista) - total_descontado

    # Contexto para la plantilla
    context = {
        'total_semanal': sum(ingresos_por_dia_lista),
        'total_mensual': total_mensual,
        'total_descontado': total_descontado,
        'descuentos': descuentos,
        'ingresos_por_dia_lista': ingresos_por_dia_lista,
        'total_final': total_final
    }

    return render(request, 'total.html', context)



def eliminar_trabajo(request, trabajo_id):
    # Usamos get_object_or_404 para obtener el trabajo o devolver un error 404 si no se encuentra
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)

    # Verificamos si la solicitud es un POST, lo que indica que el usuario confirma la eliminación
    if request.method == 'POST':
        trabajo.delete()  # Eliminamos el trabajo
        return redirect('jobs')  # Redirigimos a la lista de trabajos

    return redirect('jobs')  # Si no es un POST, simplemente redirigimos sin eliminar

def eliminar_descuento(request,descuento_id):
    descuento=get_object_or_404(Descuentos,id=descuento_id)
    if request.method=='POST':
        descuento.delete()
        return redirect('jobs')
    
    return redirect('jobs')
    
    
    