from datetime import datetime, timedelta,date,time
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
from django.db.models.functions import ExtractWeek,ExtractYear
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
    from_date = request.GET.get('from-date')
    to_date = request.GET.get('to-date')
    hoy = timezone.localtime().date()

    # Calcular el próximo martes
    dias_hasta_proximo_martes = (1 - hoy.weekday()) % 7  # martes = 1
    if dias_hasta_proximo_martes == 0:
        dias_hasta_proximo_martes = 7  # si hoy es martes, se toma el próximo martes

    martes_siguiente = hoy + timedelta(days=dias_hasta_proximo_martes)
    martes_anterior = martes_siguiente - timedelta(days=7)

    # Rango con hora
    inicio_rango = datetime.combine(martes_anterior, time.min)  # martes anterior 00:00:00
    fin_rango = datetime.combine(martes_siguiente, time.max)    # martes actual 23:59:59

    # Si el usuario ingresó un filtro de fechas
    if from_date and to_date:
        trabajos = Trabajo.objects.filter(
            fecha_registro__gte=from_date,
            fecha_registro__lte=to_date
        )
        descuentos = Descuentos.objects.filter(
            fecha_registro_descuento__gte=from_date,
            fecha_registro_descuento__lte=to_date
        )
    else:
        trabajos = Trabajo.objects.filter(
            fecha_registro__gte=inicio_rango,
            fecha_registro__lte=fin_rango
        )
        descuentos = Descuentos.objects.filter(
            fecha_registro_descuento__gte=inicio_rango,
            fecha_registro_descuento__lte=fin_rango
        )
 

    context = {
        'trabajos': trabajos,
        'descuentos': descuentos,
        'desde': inicio_rango,
        'hasta': fin_rango
    }
    
    return render(request, 'jobs.html', context)


@login_required
def total(request):
    # Obtener fecha actual y calcular el rango de martes a martes
    hoy = timezone.localtime().date()

    dias_hasta_proximo_martes = (1 - hoy.weekday()) % 7  # martes = 1
    if dias_hasta_proximo_martes == 0:
        dias_hasta_proximo_martes = 7  # si hoy es martes, usar el martes siguiente

    martes_siguiente = hoy + timedelta(days=dias_hasta_proximo_martes)
    martes_anterior = martes_siguiente - timedelta(days=7)

    # Rango exacto con tiempo incluido
    inicio_rango = datetime.combine(martes_anterior, time.min)
    fin_rango = datetime.combine(martes_siguiente, time.max)

    # --- Ingresos semanales (martes a martes) ---
    trabajos_semanales = Trabajo.objects.filter(
        fecha_registro__gte=inicio_rango,
        fecha_registro__lte=fin_rango
    ).annotate(
        dia_semana=ExtractIsoWeekDay('fecha_registro')
    ).values('dia_semana').annotate(
        total=Sum('monto')
    )

    ingresos_por_dia = {i: 0 for i in range(1, 8)}
    for trabajo in trabajos_semanales:
        ingresos_por_dia[trabajo['dia_semana']] = trabajo['total'] or 0

    ingresos_por_dia_lista = [ingresos_por_dia[dia] for dia in range(1, 8)]
    total_semanal = sum(ingresos_por_dia_lista)

    # --- Descuentos semanales (martes a martes) ---
    descuentos_semanales = Descuentos.objects.filter(
        fecha_registro_descuento__gte=inicio_rango,
        fecha_registro_descuento__lte=fin_rango
    ).annotate(
        dia_semana=ExtractIsoWeekDay('fecha_registro_descuento')
    ).values('dia_semana').annotate(
        total=Sum('descuento')
    )

    descuentos_por_dia = {i: 0 for i in range(1, 8)}
    for d in descuentos_semanales:
        descuentos_por_dia[d['dia_semana']] = d['total'] or 0

    descuentos_por_dia_lista = [descuentos_por_dia[dia] for dia in range(1, 8)]
    total_descuento_semanal = sum(descuentos_por_dia_lista)

    # --- Totales generales ---
    hoy_datetime = timezone.localtime()
    anio_actual = hoy_datetime.year
    mes_actual = hoy_datetime.month

    total_mensual = Trabajo.objects.filter(
        fecha_registro__year=anio_actual,
        fecha_registro__month=mes_actual
    ).aggregate(Sum('monto'))['monto__sum'] or 0

    total_descontado = Descuentos.objects.aggregate(Sum('descuento'))['descuento__sum'] or 0

    total_final = max(0, total_semanal - total_descuento_semanal)

    # --- Descuentos dentro del rango actual ---
    descuento_semana_actual = Descuentos.objects.filter(
        fecha_registro_descuento__gte=inicio_rango,
        fecha_registro_descuento__lte=fin_rango
    )

    # --- Procesar formulario ---
    if request.method == 'POST':
        descuento_form = DescuentoForm(request.POST)
        if descuento_form.is_valid():
            descuento = descuento_form.save(commit=False)
            descuento.usuario = request.user
            descuento.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Recalcular los descuentos
                descuentos_actualizados = Descuentos.objects.filter(
                    fecha_registro_descuento__gte=inicio_rango,
                    fecha_registro_descuento__lte=fin_rango
                ).annotate(
                    dia_semana=ExtractIsoWeekDay('fecha_registro_descuento')
                ).values('dia_semana').annotate(
                    total=Sum('descuento')
                )

                descuentos_por_dia_actual = {i: 0 for i in range(1, 8)}
                for d in descuentos_actualizados:
                    descuentos_por_dia_actual[d['dia_semana']] = d['total'] or 0

                total_descuento_actual = sum([descuentos_por_dia_actual[d] for d in range(1, 8)])
                total_final_actualizado = max(0, total_semanal - total_descuento_actual)

                return JsonResponse({
                    'success': True,
                    'descuento': {
                        'id': descuento.id,
                        'descripcion': descuento.descripcion,
                        'fecha_registro_descuento': descuento.fecha_registro_descuento.strftime('%Y-%m-%d'),
                        'descuento': float(descuento.descuento),
                    },
                    'total_descuento_semanal': float(total_descuento_actual),
                    'total_final': float(total_final_actualizado)
                })

            return redirect('total')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': descuento_form.errors}, status=400)
    else:
        descuento_form = DescuentoForm()

    # --- Contexto ---
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
        'desde': inicio_rango,
        'hasta': fin_rango,
    }

    return render(request, 'total.html', context)

@login_required
def Report(request):
    # Configuración inicial
    anio_actual = date.today().year
    semana_corte = 27  # Semana de corte para reportes anteriores
    
    # Determinar el tipo de reporte a mostrar
    tab = request.GET.get('tab', 'nuevos')
    page_nuevos = request.GET.get('page_nuevos', 1)
    page_anteriores = request.GET.get('page_anteriores', 1)

    context = {
        'tab': tab,
    }

    # Solo cargamos los datos necesarios según la pestaña seleccionada
    if tab == 'anteriores':
        # --- REPORTES ANTERIORES (Lunes-Domingo) ---
        semanas_anteriores = []
        for semana in reversed(range(1, semana_corte + 1)):
            fecha_inicio = date.fromisocalendar(anio_actual, semana, 1)  # Lunes
            fecha_fin = date.fromisocalendar(anio_actual, semana, 7)     # Domingo
            
            ingresos_query = Trabajo.objects.filter(
                fecha_registro__gte=fecha_inicio,
                fecha_registro__lte=fecha_fin
            ).aggregate(total=Sum('monto'))
            
            descuentos_query = Descuentos.objects.filter(
                fecha_registro_descuento__gte=fecha_inicio,
                fecha_registro_descuento__lte=fecha_fin
            ).aggregate(total=Sum('descuento'))

            semanas_anteriores.append({
                'anio': anio_actual,
                'semana': semana,
                'inicio': fecha_inicio.strftime('%d %b'),
                'fin': fecha_fin.strftime('%d %b'),
                'ingresos': ingresos_query['total'] or 0,
                'descuentos': descuentos_query['total'] or 0,
                'total': max(0, (ingresos_query['total'] or 0) - (descuentos_query['total'] or 0)),
                'tipo_semana': 'iso'
            })

        paginator_anteriores = Paginator(semanas_anteriores, 6)
        context['page_obj_anteriores'] = paginator_anteriores.get_page(page_anteriores)
    
    else:
        # --- REPORTES NUEVOS (Martes-Martes) ---
        semanas_nuevos = []
        
        # Identificamos semanas distintas con registros
        trabajos_semanas = Trabajo.objects.annotate(
            semana=ExtractWeek('fecha_registro'),
            anio=ExtractYear('fecha_registro')
        ).values('anio', 'semana').distinct()
        
        descuentos_semanas = Descuentos.objects.annotate(
            semana=ExtractWeek('fecha_registro_descuento'),
            anio=ExtractYear('fecha_registro_descuento')
        ).values('anio', 'semana').distinct()
        
        # Combinamos y obtenemos semanas únicas
        todas_semanas = set()
        for item in trabajos_semanas:
            todas_semanas.add((item['anio'], item['semana']))
        for item in descuentos_semanas:
            todas_semanas.add((item['anio'], item['semana']))
        
        # Procesamos solo semanas posteriores a la semana de corte
        for anio, semana in todas_semanas:
            if anio == anio_actual and semana <= semana_corte:
                continue
                
            fecha_inicio = date.fromisocalendar(anio, semana, 2)  # Martes
            fecha_fin = fecha_inicio + timedelta(days=6)           # Lunes siguiente
            
            ingresos = Trabajo.objects.filter(
                fecha_registro__gte=fecha_inicio,
                fecha_registro__lte=fecha_fin
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            descuentos = Descuentos.objects.filter(
                fecha_registro_descuento__gte=fecha_inicio,
                fecha_registro_descuento__lte=fecha_fin
            ).aggregate(total=Sum('descuento'))['total'] or 0

            semanas_nuevos.append({
                'anio': anio,
                'semana': semana,
                'inicio': fecha_inicio.strftime('%d %b'),
                'fin': fecha_fin.strftime('%d %b'),
                'ingresos': ingresos,
                'descuentos': descuentos,
                'total': max(0, ingresos - descuentos),
                'tipo_semana': 'martes',
                'fecha_inicio_real': fecha_inicio,
                'fecha_fin_real': fecha_fin
            })
        
        # Ordenamos por fecha descendente
        semanas_nuevos.sort(key=lambda x: x['fecha_inicio_real'], reverse=True)
        
        paginator_nuevos = Paginator(semanas_nuevos, 6)
        context['page_obj_nuevos'] = paginator_nuevos.get_page(page_nuevos)
    
    return render(request, 'reportes.html', context)

@login_required
def semana_detalle(request, anio, semana):
    
    tipo_semana = request.GET.get('tipo', 'iso')
    
    if tipo_semana == 'martes':
        fecha_inicio = date.fromisocalendar(anio, semana, 2)  # Martes
        fecha_fin = fecha_inicio + timedelta(days=6)          # Lunes
    else:
        fecha_inicio = date.fromisocalendar(anio, semana, 1)  # Lunes
        fecha_fin = date.fromisocalendar(anio, semana, 7)     # Domingo
    
    trabajos = Trabajo.objects.filter(
        fecha_registro__gte=fecha_inicio,
        fecha_registro__lte=fecha_fin
    ).order_by('fecha_registro')

    descuentos = Descuentos.objects.filter(
        fecha_registro_descuento__gte=fecha_inicio,
        fecha_registro_descuento__lte=fecha_fin
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
        'tipo_semana': tipo_semana,
    }

    return render(request, 'semana_detalle.html', context)



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