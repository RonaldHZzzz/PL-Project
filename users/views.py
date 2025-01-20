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
from django.db.models.functions import ExtractWeekDay


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
        descuentos= Descuentos.objects.filter(
           fecha_registro_descuento__gte=from_date,
           fecha_registro_descuento__lte=to_date
            
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
    # Obtener la fecha actual y detalles de semana, mes y año
    hoy = datetime.date.today()
    semana_actual = hoy.isocalendar()[1]
    anio_actual = hoy.year
    mes_actual = hoy.month

    # Calcular ingresos semanales, agrupados por día de la semana
    trabajos_semanales = Trabajo.objects.filter(
        fecha_registro__year=anio_actual,
        fecha_registro__week=semana_actual
    ).annotate(
        dia_semana=ExtractWeekDay('fecha_registro')
    ).values('dia_semana').annotate(
        total=Sum('monto')
    )

    # Inicializar ingresos diarios a 0 (lunes a domingo)
    ingresos_por_dia = {i: 0 for i in range(1, 8)}
    for trabajo in trabajos_semanales:
        ingresos_por_dia[trabajo['dia_semana']] = trabajo['total']

    # Convertir los ingresos diarios a una lista (lunes a domingo)
    ingresos_por_dia_lista = [ingresos_por_dia[dia] for dia in range(1, 8)]

    # Calcular el total semanal de ingresos
    total_semanal = sum(ingresos_por_dia_lista)

    # Calcular descuentos semanales, agrupados por día de la semana
    descuentos_semanales = Descuentos.objects.filter(
        fecha_registro_descuento__year=anio_actual,
        fecha_registro_descuento__week=semana_actual
    ).annotate(
        dia_semana=ExtractWeekDay('fecha_registro_descuento')
    ).values('dia_semana').annotate(
        total=Sum('descuento')
    )

    # Inicializar descuentos diarios a 0 (lunes a domingo)
    descuentos_por_dia = {i: 0 for i in range(1, 8)}
    for descuento in descuentos_semanales:
        descuentos_por_dia[descuento['dia_semana']] = descuento['total']

    # Convertir los descuentos diarios a una lista (lunes a domingo)
    descuentos_por_dia_lista = [descuentos_por_dia[dia] for dia in range(1, 8)]

    # Calcular el total semanal de descuentos
    total_descuento_semanal = sum(descuentos_por_dia_lista)

    # Calcular el total mensual
    total_mensual = Trabajo.objects.filter(
        fecha_registro__year=anio_actual,
        fecha_registro__month=mes_actual
    ).aggregate(Sum('monto'))['monto__sum'] or 0

    # Obtener descuentos totales y calcular el total descontado
    total_descontado = Descuentos.objects.aggregate(Sum('descuento'))['descuento__sum'] or 0

    # Calcular el total final (evitar valores negativos)
    total_final = max(0, total_semanal - total_descuento_semanal)

    # Procesar el formulario de descuento
    if request.method == 'POST':
        descuento_form = DescuentoForm(request.POST)
        if descuento_form.is_valid():
            descuento = descuento_form.save(commit=False)
            descuento.usuario = request.user  # Asociar el descuento con el usuario actual
            descuento.save()
            # Redirigir para evitar duplicación del POST
            return redirect('total')
    else:
        descuento_form = DescuentoForm()

    # Contexto para pasar a la plantilla
    context = {
        'total_semanal': total_semanal,
        'total_descuento_semanal': total_descuento_semanal,
        'total_mensual': total_mensual,
        'total_descontado': total_descontado,
        'descuentos': Descuentos.objects.all(),
        'ingresos_por_dia_lista': ingresos_por_dia_lista,
        'descuentos_por_dia_lista': descuentos_por_dia_lista,
        'total_final': total_final,
        'descuento_form': descuento_form,
    }

    return render(request, 'total.html', context)




def eliminar_trabajo(request, trabajo_id):
    # Usamos get_object_or_404 para obtener el trabajo o devolver un error 404 si no se encuentra
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)

    # Verificamos si la solicitud es un POST, lo que indica que el usuario confirma la eliminación
    if request.method == 'POST':
        trabajo.delete()  # Eliminamos el trabajo
        messages.success(request, 'Trabajo eliminado correctamente')  # Mensaje de éxito
        return redirect('jobs')  # Redirigimos a la lista de trabajos

    # Si no es un POST, mostramos una página de confirmación
    return render(request, 'confirmar_eliminacion.html', {'trabajo': trabajo})

def eliminar_descuento(request, descuento_id):
    descuento = get_object_or_404(Descuentos, id=descuento_id)
    
    if request.method == 'POST':
        descuento.delete()
        messages.success(request, 'Descuento eliminado correctamente')
        return redirect('jobs')  # Redirigir a la lista de trabajos o página correspondiente
    
    # Si no es un POST, mostramos una página de confirmación
    return render(request, 'confirmar_eliminacion.html', {'descuento': descuento})
    
