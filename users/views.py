from datetime import datetime, timedelta,date
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
from django.db.models.functions import ExtractIsoWeekDay, TruncWeek
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models.functions import ExtractWeek
import difflib
from collections import defaultdict, Counter
from django.db.models import Count






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
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = TrabajoForm(request.POST)
        if form.is_valid():
            trabajo = form.save(commit=False)
            trabajo.usuario = request.user
            trabajo.save()
            data = {
                'id': trabajo.id,
                'trabajo': trabajo.trabajo,
                'monto': float(trabajo.monto),
                'fecha_registro': trabajo.fecha_registro.strftime('%Y-%m-%d %H:%M'),
                'usuario': request.user.username,
            }
            return JsonResponse({'success': True, 'trabajo': data})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    trabajos = Trabajo.objects.filter(usuario=request.user).order_by('-fecha_registro')[:20]
    return render(request, 'home.html', {'trabajos': trabajos})

@login_required
def signout(request):
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('home')


def signin(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {
                'form': form,
                'errorlogin': 'Usuario y Contraseña incorrectos.'
            })
    else:
        return render(request, 'login.html', {
            'form': AuthenticationForm()
        })
    
@login_required       
def jobs(request):
    # Obtener las fechas desde el formulario
    from_date = request.GET.get('from-date')
    to_date = request.GET.get('to-date')
    hoy = timezone.localtime().date()
    semana_actual = hoy.isocalendar()[1]
    anio_actual = hoy.year

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
        trabajos = Trabajo.objects.filter(
        fecha_registro__year=anio_actual,
        fecha_registro__week=semana_actual
        )
          # Obtener todos los descuentos del usuario actual
        descuentos = Descuentos.objects.filter(
        fecha_registro_descuento__year=anio_actual,
        fecha_registro_descuento__week=semana_actual
        )

    
    context={
            'trabajos':trabajos,
            'descuentos':descuentos
        }
    
    return render(request, 'jobs.html',context)

@login_required
def total(request):
    # Obtener la fecha actual ajustada a la zona horaria de Django
    hoy = timezone.localtime().date()
    semana_actual = hoy.isocalendar()[1]  # Semana ISO actual
    anio_actual = hoy.year
    mes_actual = hoy.month

    # Calcular ingresos semanales, agrupados por día de la semana (lunes=1, domingo=7)
    trabajos_semanales = Trabajo.objects.annotate(
        semana=TruncWeek('fecha_registro'),  # Redondear a la semana (lunes a domingo)
        dia_semana=ExtractIsoWeekDay('fecha_registro')
    ).filter(
        fecha_registro__year=anio_actual,
        semana__week=semana_actual
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

    # Calcular descuentos semanales, agrupados por día de la semana (lunes=1, domingo=7)
    descuentos_semanales = Descuentos.objects.annotate(
        semana=TruncWeek('fecha_registro_descuento'),
        dia_semana=ExtractIsoWeekDay('fecha_registro_descuento')
    ).filter(
        fecha_registro_descuento__year=anio_actual,
        semana__week=semana_actual
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
    
    # Descuentos de la semana actual
    descuento_semana_actual = Descuentos.objects.filter(
        fecha_registro_descuento__year=anio_actual,
        fecha_registro_descuento__week=semana_actual
    )

    # Obtener descuentos totales y calcular el total descontado
    total_descontado = Descuentos.objects.aggregate(Sum('descuento'))['descuento__sum'] or 0

    # Calcular el total final (evitar valores negativos)
    total_final = max(0, total_semanal - total_descuento_semanal)

    # Procesar el formulario de descuento
    if request.method == 'POST':
        descuento_form = DescuentoForm(request.POST)
        if descuento_form.is_valid():
            descuento = descuento_form.save(commit=False)
            descuento.usuario = request.user
            descuento.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                 return JsonResponse({
                    'success': True,
                    'descuento': {
                        'id': descuento.id,
                        'descripcion': descuento.descripcion,
                        'fecha_registro_descuento': descuento.fecha_registro_descuento.strftime('%Y-%m-%d'),
                        'descuento': float(descuento.descuento),
                    }
                })
            else:
                return redirect('total')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': descuento_form.errors}, status=400)
    else:
        descuento_form = DescuentoForm()

    # Contexto para la plantilla
    context = {
        'total_semanal': total_semanal,
        'total_mensual': total_mensual,
        'ingresos_por_dia_lista': ingresos_por_dia_lista,
        'total_descuento_semanal': total_descuento_semanal,
        'total_descontado': total_descontado,
        'descuentos': Descuentos.objects.all(),
        'descuentos_por_dia_lista': descuentos_por_dia_lista,
        'descuento_semana_actual': descuento_semana_actual,
        'descuento_form': descuento_form,
        'total_final': total_final,
    }
    
    

    return render(request, 'total.html', context)

@login_required
def Report(request):
    hoy = timezone.localtime().date()
    anio_actual = hoy.year
    semana_actual = hoy.isocalendar()[1]

    # Obtener totales de trabajos agrupados por semana (en año actual y semanas válidas)
    ingresos_por_semana = Trabajo.objects.filter(
        fecha_registro__year=anio_actual,
        fecha_registro__week__lte=semana_actual
    ).values('fecha_registro__week').annotate(total_ingresos=Sum('monto'))

    # Diccionario para acceso rápido: {semana: total_ingresos}
    ingresos_dict = {item['fecha_registro__week']: item['total_ingresos'] for item in ingresos_por_semana}

    # Obtener totales de descuentos agrupados por semana
    descuentos_por_semana = Descuentos.objects.filter(
        fecha_registro_descuento__year=anio_actual,
        fecha_registro_descuento__week__lte=semana_actual
    ).values('fecha_registro_descuento__week').annotate(total_descuentos=Sum('descuento'))

    descuentos_dict = {item['fecha_registro_descuento__week']: item['total_descuentos'] for item in descuentos_por_semana}

    semanas = []
    for semana in reversed(range(1, semana_actual + 1)):
        total_ingresos = ingresos_dict.get(semana, 0)
        total_descuentos = descuentos_dict.get(semana, 0)

        fecha_inicio_semana = date.fromisocalendar(anio_actual, semana, 1)
        fecha_fin_semana = date.fromisocalendar(anio_actual, semana, 7)

        semanas.append({
            'anio': anio_actual,
            'semana': semana,
            'inicio': fecha_inicio_semana.strftime('%d %b'),
            'fin': fecha_fin_semana.strftime('%d %b'),
            'ingresos': total_ingresos,
            'descuentos': total_descuentos,
            'total': max(0, total_ingresos - total_descuentos),
        })

    # Paginador - 4 semanas por página
    paginator = Paginator(semanas, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reportes.html', {'page_obj': page_obj})


@login_required
def eliminar_trabajo(request, trabajo_id):
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)

    if request.method == 'POST':
        trabajo.delete()
        messages.success(request, 'Trabajo eliminado correctamente')
        return redirect('jobs')  # Redirigir a la lista de trabajos actualizada

    # Mostramos una página de confirmación
    return render(request, 'confirmar_eliminacion.html', {'trabajo': trabajo})

@login_required
def eliminar_descuento(request, descuento_id):
    descuento = get_object_or_404(Descuentos, id=descuento_id)
    
    if request.method == 'POST':
        descuento.delete()
        messages.success(request, 'Descuento eliminado correctamente')
        return redirect('jobs')  # Redirigir a la lista de trabajos actualizada
    
    # Mostramos una página de confirmación
    return render(request, 'confirmar_eliminacion.html', {'descuento': descuento})
    
@login_required
def semana_detalle(request, anio, semana):
    # Obtener fecha de inicio (lunes) y fin (domingo) de la semana ISO
    fecha_inicio = date.fromisocalendar(anio, semana, 1)
    fecha_fin = fecha_inicio + timedelta(days=6)

    # ✅ Eliminar filtro por usuario
    trabajos = Trabajo.objects.filter(
        fecha_registro__range=(fecha_inicio, fecha_fin)
    ).order_by('fecha_registro')

    descuentos = Descuentos.objects.filter(
        fecha_registro_descuento__range=(fecha_inicio, fecha_fin)
    ).order_by('fecha_registro_descuento')

    total_ingresos = trabajos.aggregate(total=Sum('monto'))['total'] or 0
    total_descuentos = descuentos.aggregate(total=Sum('descuento'))['total'] or 0
    total_final = max(0, total_ingresos - total_descuentos)

    context = {
        'anio': anio,
        'semana': semana,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'trabajos': trabajos,
        'descuentos': descuentos,
        'total_ingresos': total_ingresos,
        'total_descuentos': total_descuentos,
        'total_final': total_final,
    }

    return render(request, 'semana_detalle.html', context)


@login_required
def analizar(request):
    trabajos = Trabajo.objects.all()

    # Recolectar todos los nombres de trabajos
    nombres_raw = [t.trabajo.strip().title() for t in trabajos]
    nombres_unicos = list(set(nombres_raw))

    # Agrupar trabajos similares
    grupos_similares = []
    usados = set()

    for nombre in nombres_unicos:
        if nombre in usados:
            continue
        grupo = [n for n in nombres_unicos if difflib.SequenceMatcher(None, nombre, n).ratio() > 0.75]
        usados.update(grupo)
        grupos_similares.append(grupo)

    # Contar ocurrencias reales de cada grupo
    conteo_grupos = []
    for grupo in grupos_similares:
        total = sum(nombres_raw.count(nombre) for nombre in grupo)
        nombre_representativo = grupo[0]
        conteo_grupos.append((nombre_representativo, total))

    # Ordenar los trabajos
    conteo_ordenado = sorted(conteo_grupos, key=lambda x: x[1], reverse=True)

    # Top 5 más y menos realizados
    top_mas = conteo_ordenado[:5]
    top_menos = conteo_ordenado[-5:] if len(conteo_ordenado) >= 5 else conteo_ordenado[::-1]

    context = {
        'top_mas': top_mas,
        'top_menos': top_menos,
    }

    return render(request, "analize.html", context)