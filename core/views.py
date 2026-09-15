from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, F
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
import os
from datetime import date, timedelta
import random

from .models import *
from .forms import *


# ==================== FUNCIONES AUXILIARES ====================

def crear_notificacion(usuario, tipo, mensaje, enlace=None):
    Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        mensaje=mensaje,
        enlace=enlace
    )


def enviar_codigo_confirmacion(user):
    """Envía el código de confirmación al usuario"""
    # Crear o actualizar código
    codigo_obj, created = CodigoConfirmacion.objects.get_or_create(usuario=user)
    # Generar nuevo código siempre
    codigo_obj.codigo = CodigoConfirmacion.generar_codigo()
    codigo_obj.usado = False
    codigo_obj.creado = timezone.now()
    codigo_obj.save()

    # Enviar email con el código
    asunto = '✅ Confirma tu cuenta en CodeCrack'
    mensaje = f"""
Hola {user.username},

¡Bienvenido a CodeCrack! 🚀

Tu código de confirmación es:

    {codigo_obj.codigo}

Ingresa este código en la página de CodeCrack para activar tu cuenta.

El código expira en 15 minutos.

Si no te registraste en CodeCrack, ignora este email.

Saludos,
El equipo de CodeCrack
    """

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False


def enviar_codigo_recuperacion(user):
    """Envía el código de recuperación al usuario"""
    # Crear nuevo código
    codigo_obj = CodigoRecuperacion.objects.create(
        usuario=user,
        codigo=CodigoRecuperacion.generar_codigo()
    )

    # Enviar email con el código
    asunto = '🔑 Recuperar contraseña - CodeCrack'
    mensaje = f"""
Hola {user.username},

Recibimos una solicitud para cambiar tu contraseña en CodeCrack.

Tu código de recuperación es:

    {codigo_obj.codigo}

Ingresa este código en la página de CodeCrack para poner una nueva contraseña.

El código expira en 15 minutos.

Si no solicitaste esto, ignora este email.

Saludos,
El equipo de CodeCrack
    """

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False


def verificar_insignias(usuario):
    try:
        perfil = usuario.perfil
    except Perfil.DoesNotExist:
        return

    insignias_disponibles = Insignia.objects.all()
    for insignia in insignias_disponibles:
        ya_tiene = InsigniaUsuario.objects.filter(usuario=usuario, insignia=insignia).exists()
        if ya_tiene:
            continue

        otorgar = False
        condicion = insignia.condicion.lower()

        if 'proyecto' in condicion and 'completar' in condicion:
            num = int(''.join(filter(str.isdigit, condicion)) or 1)
            if ProyectoCompletado.objects.filter(usuario=usuario).count() >= num:
                otorgar = True
        elif 'racha' in condicion:
            num = int(''.join(filter(str.isdigit, condicion)) or 7)
            if perfil.racha_dias >= num:
                otorgar = True
        elif 'comentario' in condicion:
            num = int(''.join(filter(str.isdigit, condicion)) or 5)
            if Comentario.objects.filter(usuario=usuario).count() >= num:
                otorgar = True
        elif 'xp' in condicion:
            num = int(''.join(filter(str.isdigit, condicion)) or 100)
            if perfil.xp_total >= num:
                otorgar = True

        if otorgar:
            InsigniaUsuario.objects.create(usuario=usuario, insignia=insignia)
            crear_notificacion(
                usuario=usuario,
                tipo='insignia',
                mensaje=f'🏅 ¡Has ganado la insignia "{insignia.nombre}"!',
                enlace='/progreso/'
            )


# ==================== VISTAS PÚBLICAS ====================

def home(request):
    frases = [
        ("La mejor manera de predecir el futuro es inventarlo.", "Alan Kay"),
        ("Cualquier tonto puede escribir código que una computadora pueda entender. Los buenos programadores escriben código que los humanos pueden entender.", "Martin Fowler"),
        ("Programar no es solo escribir código, es resolver problemas.", "Anónimo"),
        ("El primer paso para ser un gran programador es creer que puedes serlo.", "Anónimo"),
        ("Los errores son la mejor forma de aprender. ¡No les tengas miedo!", "Anónimo"),
    ]
    frase = random.choice(frases)

    proyectos_destacados = Proyecto.objects.all().order_by('-fecha_publicacion')[:3]
    eventos = Evento.objects.filter(fecha__gte=date.today()).order_by('fecha')[:3]
    total_estudiantes = User.objects.count()

    context = {
        'frase_texto': frase[0],
        'frase_autor': frase[1],
        'proyectos_destacados': proyectos_destacados,
        'eventos': eventos,
        'total_estudiantes': total_estudiantes,
    }

    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
            context['proyectos_completados_count'] = ProyectoCompletado.objects.filter(usuario=request.user).count()
            context['desafios_completados_count'] = DesafioCompletado.objects.filter(usuario=request.user).count()
        except Perfil.DoesNotExist:
            pass

        context['top_usuarios'] = User.objects.annotate(
            total_xp=F('perfil__xp_total')
        ).order_by('-total_xp')[:3]

    return render(request, 'home.html', context)


def que_es_programar(request):
    return render(request, 'que_es_programar.html')


def acerca_de(request):
    return render(request, 'acerca_de.html')


def historias(request):
    historias_list = HistoriaExito.objects.all().order_by('-fecha_creacion')
    return render(request, 'historias.html', {'historias': historias_list})


def historia_detalle(request, historia_id):
    historia = get_object_or_404(HistoriaExito, id=historia_id)
    comentarios = Comentario.objects.filter(historia=historia, aprobado=True)
    return render(request, 'historia_detalle.html', {
        'historia': historia,
        'comentarios': comentarios
    })


def proyectos(request):
    proyectos_list = Proyecto.objects.all().order_by('-fecha_publicacion')
    categorias = Proyecto.CATEGORIA_PROYECTO
    dificultades = Proyecto.DIFICULTAD_OPCIONES

    categoria_filtro = request.GET.get('categoria')
    dificultad_filtro = request.GET.get('dificultad')
    buscar = request.GET.get('buscar')

    if categoria_filtro:
        proyectos_list = proyectos_list.filter(categoria=categoria_filtro)
    if dificultad_filtro:
        proyectos_list = proyectos_list.filter(dificultad=dificultad_filtro)
    if buscar:
        proyectos_list = proyectos_list.filter(
            Q(titulo__icontains=buscar) |
            Q(descripcion_corta__icontains=buscar) |
            Q(descripcion_completa__icontains=buscar)
        )

    paginator = Paginator(proyectos_list, 6)
    page_number = request.GET.get('page')
    proyectos_paginados = paginator.get_page(page_number)

    context = {
        'proyectos': proyectos_paginados,
        'categorias': categorias,
        'dificultades': dificultades,
        'categoria_seleccionada': categoria_filtro,
        'dificultad_seleccionada': dificultad_filtro,
        'buscar': buscar,
    }
    return render(request, 'proyectos.html', context)


def proyecto_detalle(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    comentarios = Comentario.objects.filter(proyecto=proyecto, aprobado=True)

    proyecto.vistas += 1
    proyecto.save()

    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
            perfil.xp_total += 10
            perfil.save()
        except Perfil.DoesNotExist:
            pass

        proyectos_vistos = request.session.get('proyectos_vistos', [])
        if proyecto_id not in proyectos_vistos:
            proyectos_vistos.append(proyecto_id)
            request.session['proyectos_vistos'] = proyectos_vistos
            request.session.modified = True

    return render(request, 'proyecto_detalle.html', {
        'proyecto': proyecto,
        'comentarios': comentarios
    })


def recursos(request):
    recursos_list = Recurso.objects.all().order_by('-id')
    categorias = Recurso.CATEGORIA_RECURSO

    categoria_filtro = request.GET.get('categoria')
    buscar = request.GET.get('buscar')

    if categoria_filtro:
        recursos_list = recursos_list.filter(categoria=categoria_filtro)
    if buscar:
        recursos_list = recursos_list.filter(
            Q(titulo__icontains=buscar) | Q(descripcion__icontains=buscar)
        )

    paginator = Paginator(recursos_list, 9)
    page_number = request.GET.get('page')
    recursos_paginados = paginator.get_page(page_number)

    return render(request, 'recursos.html', {
        'recursos': recursos_paginados,
        'categorias': categorias,
        'categoria_seleccionada': categoria_filtro,
        'buscar': buscar,
    })


def galeria(request):
    proyectos_estudiantes = ProyectoEstudiante.objects.filter(aprobado=True).order_by('-fecha_subida')

    categoria_filtro = request.GET.get('categoria')
    buscar = request.GET.get('buscar')

    if categoria_filtro:
        proyectos_estudiantes = proyectos_estudiantes.filter(categoria=categoria_filtro)
    if buscar:
        proyectos_estudiantes = proyectos_estudiantes.filter(
            Q(titulo__icontains=buscar) | Q(descripcion__icontains=buscar)
        )

    paginator = Paginator(proyectos_estudiantes, 9)
    page_number = request.GET.get('page')
    proyectos_paginados = paginator.get_page(page_number)

    return render(request, 'galeria.html', {
        'proyectos': proyectos_paginados,
        'categorias': ProyectoEstudiante.CATEGORIA_PROYECTO_EST,
        'categoria_seleccionada': categoria_filtro,
        'buscar': buscar,
    })


def proyecto_estudiante_detalle(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoEstudiante, id=proyecto_id, aprobado=True)

    proyecto.vistas += 1
    proyecto.save()

    return render(request, 'proyecto_estudiante_detalle.html', {'proyecto': proyecto})


def descargar_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoEstudiante, id=proyecto_id, aprobado=True)

    if not proyecto.archivo:
        messages.error(request, '❌ Este proyecto no tiene archivo para descargar.')
        return redirect('proyecto_estudiante_detalle', proyecto_id=proyecto.id)

    proyecto.descargas += 1
    proyecto.save()

    if request.user.is_authenticated and request.user != proyecto.estudiante:
        crear_notificacion(
            usuario=proyecto.estudiante,
            tipo='descarga',
            mensaje=f'📥 {request.user.username} descargó tu proyecto "{proyecto.titulo}"',
            enlace=f'/galeria/{proyecto.id}/'
        )

    try:
        return FileResponse(
            proyecto.archivo.open('rb'),
            as_attachment=True,
            filename=os.path.basename(proyecto.archivo.name)
        )
    except FileNotFoundError:
        messages.error(request, '❌ El archivo no existe.')
        return redirect('proyecto_estudiante_detalle', proyecto_id=proyecto.id)


def eventos(request):
    eventos_futuros = Evento.objects.filter(fecha__gte=date.today()).order_by('fecha')
    eventos_pasados = Evento.objects.filter(fecha__lt=date.today()).order_by('-fecha')
    return render(request, 'eventos.html', {
        'eventos_futuros': eventos_futuros,
        'eventos_pasados': eventos_pasados,
    })


def contacto(request):
    if request.method == 'POST':
        form = MensajeContactoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Mensaje enviado! Te responderemos pronto. 📨')
            return redirect('contacto')
    else:
        form = MensajeContactoForm()
    return render(request, 'contacto.html', {'form': form})


# ==================== AUTENTICACIÓN ====================

def registro(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()

            # ✅ Enviar código de confirmación
            enviado = enviar_codigo_confirmacion(user)

            if enviado:
                messages.success(
                    request,
                    f'✅ ¡Cuenta creada! Te enviamos un código a {user.email}. '
                    'Debes confirmar tu correo para poder iniciar sesión.'
                )
            else:
                messages.warning(
                    request,
                    '⚠️ Cuenta creada, pero no pudimos enviar el código. '
                    'Contacta al administrador.'
                )

            # Guardar el username en la sesión para la página de código
            request.session['usuario_pendiente'] = user.username
            return redirect('confirmar_codigo')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})


def confirmar_codigo(request):
    """Vista para escribir el código de confirmación"""
    username = request.session.get('usuario_pendiente')
    if not username:
        messages.error(request, '❌ No hay usuario pendiente de confirmación.')
        return redirect('login')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, '❌ Usuario no encontrado.')
        return redirect('login')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()

        try:
            codigo_obj = CodigoConfirmacion.objects.get(usuario=user)
        except CodigoConfirmacion.DoesNotExist:
            messages.error(request, '❌ No hay código para este usuario.')
            return redirect('confirmar_codigo')

        if codigo_obj.usado:
            messages.error(request, '❌ Este código ya fue usado.')
            return redirect('confirmar_codigo')

        if not codigo_obj.es_valido():
            messages.error(request, '❌ El código ha expirado. Solicita uno nuevo.')
            return redirect('confirmar_codigo')

        if codigo_obj.codigo != codigo_ingresado:
            messages.error(request, '❌ El código es incorrecto.')
            return redirect('confirmar_codigo')

        # ✅ Código correcto
        codigo_obj.usado = True
        codigo_obj.save()

        try:
            perfil = user.perfil
            perfil.email_confirmado = True
            perfil.save()
        except Perfil.DoesNotExist:
            pass

        # Limpiar sesión
        if 'usuario_pendiente' in request.session:
            del request.session['usuario_pendiente']

        messages.success(request, '✅ ¡Email confirmado! Ya puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'confirmar_codigo.html', {'username': username})


def reenviar_codigo(request):
    """Reenviar código de confirmación"""
    username = request.session.get('usuario_pendiente')
    if not username:
        messages.error(request, '❌ No hay usuario pendiente.')
        return redirect('login')

    try:
        user = User.objects.get(username=username)
        enviado = enviar_codigo_confirmacion(user)
        if enviado:
            messages.success(request, f'✅ Código reenviado a {user.email}')
        else:
            messages.error(request, '❌ No pudimos enviar el código.')
    except User.DoesNotExist:
        messages.error(request, '❌ Usuario no encontrado.')

    return redirect('confirmar_codigo')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # ✅ Verificar si el email está confirmado
                try:
                    perfil = user.perfil
                    if not perfil.email_confirmado:
                        # Guardar en sesión para confirmar
                        request.session['usuario_pendiente'] = user.username
                        messages.error(
                            request,
                            '⚠️ Debes confirmar tu email antes de iniciar sesión. '
                            'Revisa tu correo (también la carpeta de spam).'
                        )
                        return redirect('confirmar_codigo')
                except Perfil.DoesNotExist:
                    pass

                # Verificar sanción
                try:
                    perfil = user.perfil
                    if perfil.estado in ['suspendido', 'baneado']:
                        messages.error(request, f'🚫 Tu cuenta está {perfil.get_estado_display()}. Motivo: {perfil.motivo_sancion or "No especificado"}')
                        return redirect('login')
                except Perfil.DoesNotExist:
                    pass

                login(request, user)

                try:
                    perfil = user.perfil
                    hoy = date.today()

                    if perfil.ultima_visita:
                        diferencia = (hoy - perfil.ultima_visita).days
                        if diferencia == 1:
                            perfil.racha_dias += 1
                            perfil.xp_total += 5
                            messages.success(request, f'🔥 ¡Llevas {perfil.racha_dias} días seguidos!')
                        elif diferencia > 1:
                            perfil.racha_dias = 0
                            messages.info(request, '¡Vuelve mañana para mantener tu racha! 💪')
                    else:
                        perfil.racha_dias = 1
                        messages.success(request, '¡Primer día! ¡Sigue así! 🌟')

                    perfil.ultima_visita = hoy
                    perfil.save()
                except Perfil.DoesNotExist:
                    pass

                return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. ❌')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, '¡Hasta luego! Vuelve pronto para seguir aprendiendo. 👋')
    return redirect('home')


# ==================== CAMBIO DE CONTRASEÑA (recordando la actual) ====================

@login_required
def cambiar_password(request):
    """Cambiar contraseña desde el perfil (requiere la actual)"""
    if request.method == 'POST':
        form = CambiarPasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ ¡Contraseña cambiada exitosamente!')
            return redirect('perfil')
    else:
        form = CambiarPasswordForm(user=request.user)
    return render(request, 'cambiar_password.html', {'form': form})


# ==================== RECUPERAR CONTRASEÑA (por código) ====================

def recuperar_password(request):
    """Solicitar recuperación de contraseña por código"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        usuarios = User.objects.filter(email=email)

        if usuarios.exists():
            for user in usuarios:
                enviar_codigo_recuperacion(user)
                # Guardar el último usuario en sesión
                request.session['usuario_recuperacion'] = user.username

            messages.success(
                request,
                f'✅ Si {email} está registrado, recibirás un código de recuperación.'
            )
            return redirect('ingresar_codigo_recuperacion')
        else:
            # Por seguridad, mostramos el mismo mensaje
            messages.success(
                request,
                f'✅ Si {email} está registrado, recibirás un código de recuperación.'
            )
            return redirect('recuperar_password')

    return render(request, 'recuperar_password.html')


def ingresar_codigo_recuperacion(request):
    """Ingresar el código de recuperación"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        codigo_ingresado = request.POST.get('codigo', '').strip()

        usuarios = User.objects.filter(email=email)

        if not usuarios.exists():
            messages.error(request, '❌ El código es incorrecto.')
            return redirect('ingresar_codigo_recuperacion')

        user = usuarios.first()

        # Buscar el código más reciente
        codigo_obj = CodigoRecuperacion.objects.filter(
            usuario=user, usado=False
        ).order_by('-creado').first()

        if not codigo_obj:
            messages.error(request, '❌ No hay código válido para este email.')
            return redirect('recuperar_password')

        if not codigo_obj.es_valido():
            messages.error(request, '❌ El código ha expirado. Solicita uno nuevo.')
            return redirect('recuperar_password')

        if codigo_obj.codigo != codigo_ingresado:
            messages.error(request, '❌ El código es incorrecto.')
            return redirect('ingresar_codigo_recuperacion')

        # ✅ Código correcto
        codigo_obj.usado = True
        codigo_obj.save()

        # Guardar en sesión para cambiar la contraseña
        request.session['usuario_recuperacion'] = user.username

        messages.success(request, '✅ Código verificado. Ahora pon tu nueva contraseña.')
        return redirect('nueva_password')

    return render(request, 'ingresar_codigo_recuperacion.html')


def nueva_password(request):
    """Poner nueva contraseña después de verificar el código"""
    username = request.session.get('usuario_recuperacion')

    if not username:
        messages.error(request, '❌ Debes verificar tu código primero.')
        return redirect('recuperar_password')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, '❌ Usuario no encontrado.')
        return redirect('recuperar_password')

    if request.method == 'POST':
        form = NuevaPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()

            # Limpiar sesión
            if 'usuario_recuperacion' in request.session:
                del request.session['usuario_recuperacion']

            messages.success(request, '✅ ¡Contraseña restablecida! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = NuevaPasswordForm(user)

    return render(request, 'nueva_password.html', {'form': form})


# ==================== PERFIL ====================

@login_required
def perfil(request):
    perfil = request.user.perfil
    insignias = InsigniaUsuario.objects.filter(usuario=request.user)
    proyectos_vistos = len(request.session.get('proyectos_vistos', []))
    proyectos_completados = ProyectoCompletado.objects.filter(usuario=request.user).count()
    comentarios = Comentario.objects.filter(usuario=request.user).count()
    proyectos_subidos = ProyectoEstudiante.objects.filter(estudiante=request.user).count()

    context = {
        'perfil': perfil,
        'insignias': insignias,
        'proyectos_vistos': proyectos_vistos,
        'proyectos_completados': proyectos_completados,
        'comentarios': comentarios,
        'proyectos_subidos': proyectos_subidos,
    }
    return render(request, 'perfil.html', context)


@login_required
def editar_perfil(request):
    perfil = request.user.perfil
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado! ✅')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=perfil)
    return render(request, 'editar_perfil.html', {'form': form})


def perfil_publico(request, username):
    usuario = get_object_or_404(User, username=username)
    try:
        perfil = usuario.perfil
    except Perfil.DoesNotExist:
        messages.error(request, 'Usuario sin perfil')
        return redirect('home')

    insignias = InsigniaUsuario.objects.filter(usuario=usuario)
    proyectos_completados = ProyectoCompletado.objects.filter(usuario=usuario)
    comentarios = Comentario.objects.filter(usuario=usuario, aprobado=True).order_by('-fecha_creacion')[:5]
    proyectos_subidos = ProyectoEstudiante.objects.filter(estudiante=usuario, aprobado=True)

    siguiendo = False
    if request.user.is_authenticated and request.user != usuario:
        siguiendo = Seguidor.objects.filter(seguidor=request.user, seguido=usuario).exists()

    context = {
        'perfil_usuario': usuario,
        'perfil': perfil,
        'insignias': insignias,
        'proyectos_completados': proyectos_completados,
        'comentarios': comentarios,
        'proyectos_subidos': proyectos_subidos,
        'siguiendo': siguiendo,
    }
    return render(request, 'perfil_publico.html', context)


@login_required
def seguir_usuario(request, username):
    usuario = get_object_or_404(User, username=username)

    if usuario == request.user:
        messages.error(request, 'No puedes seguirte a ti mismo.')
        return redirect('perfil_publico', username=username)

    seguidor, created = Seguidor.objects.get_or_create(seguidor=request.user, seguido=usuario)

    if not created:
        seguidor.delete()
        messages.info(request, f'Has dejado de seguir a {usuario.username}')
    else:
        messages.success(request, f'¡Ahora sigues a {usuario.username}!')
        crear_notificacion(
            usuario=usuario,
            tipo='seguidor',
            mensaje=f'👥 {request.user.username} te está siguiendo',
            enlace=f'/usuario/{request.user.username}/'
        )

    return redirect('perfil_publico', username=username)


@login_required
def lista_seguidores(request, username):
    usuario = get_object_or_404(User, username=username)
    try:
        perfil = usuario.perfil
    except Perfil.DoesNotExist:
        messages.error(request, 'Usuario sin perfil')
        return redirect('home')

    seguidores = Seguidor.objects.filter(seguido=usuario).select_related('seguidor')

    context = {
        'perfil_usuario': usuario,
        'perfil': perfil,
        'seguidores': seguidores,
        'tipo': 'seguidores',
    }
    return render(request, 'lista_seguidores.html', context)


@login_required
def lista_siguiendo(request, username):
    usuario = get_object_or_404(User, username=username)
    try:
        perfil = usuario.perfil
    except Perfil.DoesNotExist:
        messages.error(request, 'Usuario sin perfil')
        return redirect('home')

    siguiendo = Seguidor.objects.filter(seguidor=usuario).select_related('seguido')

    context = {
        'perfil_usuario': usuario,
        'perfil': perfil,
        'siguiendo': siguiendo,
        'tipo': 'siguiendo',
    }
    return render(request, 'lista_seguidores.html', context)


@login_required
def progreso(request):
    perfil = request.user.perfil
    proyectos_vistos = len(request.session.get('proyectos_vistos', []))
    total_proyectos = Proyecto.objects.count()
    porcentaje = int((proyectos_vistos / total_proyectos) * 100) if total_proyectos > 0 else 0

    insignias = InsigniaUsuario.objects.filter(usuario=request.user)
    proyectos_completados = ProyectoCompletado.objects.filter(usuario=request.user)
    favoritos = request.user.proyectos_favoritos.all()
    desafios_completados = DesafioCompletado.objects.filter(usuario=request.user).count()

    context = {
        'perfil': perfil,
        'proyectos_vistos': proyectos_vistos,
        'total_proyectos': total_proyectos,
        'porcentaje': porcentaje,
        'insignias': insignias,
        'proyectos_completados': proyectos_completados,
        'favoritos': favoritos,
        'desafios_completados': desafios_completados,
    }
    return render(request, 'progreso.html', context)


@login_required
def test_vocacional(request):
    perfil = request.user.perfil
    if perfil.tipo_programador:
        return render(request, 'test_resultado.html', {'tipo': perfil.tipo_programador})

    preguntas = [
        {'id': 1, 'texto': '¿Qué prefieres hacer en tu tiempo libre?', 'opciones': [
            ('creativo', 'Dibujar, diseñar o crear algo visual'),
            ('logico', 'Resolver acertijos o juegos de lógica'),
            ('social', 'Jugar con amigos o hablar con personas'),
            ('explorador', 'Descubrir cosas nuevas o explorar'),
        ]},
        {'id': 2, 'texto': '¿Cómo te sientes cuando ves un problema difícil?', 'opciones': [
            ('creativo', 'Busco una solución creativa'),
            ('logico', 'Analizo paso a paso'),
            ('social', 'Pido ayuda o investigo'),
            ('explorador', 'Pruebo cosas'),
        ]},
        {'id': 3, 'texto': '¿Qué proyecto te llamaría más la atención?', 'opciones': [
            ('creativo', 'Diseñar una página web'),
            ('logico', 'Crear un juego'),
            ('social', 'Hacer una app social'),
            ('explorador', 'Crear un robot'),
        ]},
        {'id': 4, 'texto': '¿Qué palabra te describe mejor?', 'opciones': [
            ('creativo', 'Imaginativo/a'),
            ('logico', 'Analítico/a'),
            ('social', 'Comunicativo/a'),
            ('explorador', 'Curioso/a'),
        ]},
        {'id': 5, 'texto': '¿Qué te motiva a aprender programación?', 'opciones': [
            ('creativo', 'Crear cosas bonitas'),
            ('logico', 'Entender cómo funcionan'),
            ('social', 'Compartir proyectos'),
            ('explorador', 'Descubrir tecnologías'),
        ]},
    ]

    if request.method == 'POST':
        respuestas = {i: request.POST.get(f'pregunta_{i}') for i in range(1, 6)}
        tipos = {'creativo': 0, 'logico': 0, 'social': 0, 'explorador': 0}
        for respuesta in respuestas.values():
            if respuesta in tipos:
                tipos[respuesta] += 1
        tipo_ganador = max(tipos, key=tipos.get)
        perfil.tipo_programador = tipo_ganador
        perfil.save()
        ResultadoTest.objects.create(usuario=request.user, tipo_programador=tipo_ganador)
        messages.success(request, f'¡Eres un programador {tipo_ganador}! 🎉')
        return redirect('test_vocacional')

    return render(request, 'test_vocacional.html', {'preguntas': preguntas})


@login_required
def subir_proyecto(request):
    if request.method == 'POST':
        form = ProyectoEstudianteForm(request.POST, request.FILES)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.estudiante = request.user
            proyecto.grado_estudiante = request.user.perfil.grado
            proyecto.save()

            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                crear_notificacion(
                    usuario=admin,
                    tipo='aprobacion',
                    mensaje=f'📦 Nuevo proyecto pendiente: "{proyecto.titulo}" por {request.user.username}',
                    enlace=f'/admin/core/proyectoestudiante/{proyecto.id}/change/'
                )

            messages.success(request, '✅ ¡Proyecto subido! Espera la aprobación del admin. 📤')
            return redirect('galeria')
    else:
        form = ProyectoEstudianteForm()
    return render(request, 'subir_proyecto.html', {'form': form})


@login_required
def like_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoEstudiante, id=proyecto_id)
    proyecto.likes += 1
    proyecto.save()

    if proyecto.estudiante != request.user:
        crear_notificacion(
            usuario=proyecto.estudiante,
            tipo='like',
            mensaje=f'❤️ A {request.user.username} le gustó tu proyecto "{proyecto.titulo}"',
            enlace=f'/galeria/{proyecto.id}/'
        )

    messages.success(request, '❤️ ¡Te gusta este proyecto!')
    return redirect('galeria')


@login_required
def completar_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    completado, created = ProyectoCompletado.objects.get_or_create(usuario=request.user, proyecto=proyecto)
    if created:
        perfil = request.user.perfil
        perfil.xp_total += 50
        perfil.save()
        messages.success(request, f'🎉 ¡Completaste "{proyecto.titulo}"! +50 XP')
        verificar_insignias(request.user)
    else:
        messages.info(request, 'Ya habías completado este proyecto.')
    return redirect('proyecto_detalle', proyecto_id=proyecto_id)


@login_required
def toggle_favorito(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    if request.user in proyecto.favoritos.all():
        proyecto.favoritos.remove(request.user)
        messages.info(request, 'Quitado de favoritos ❌')
    else:
        proyecto.favoritos.add(request.user)
        messages.success(request, '¡Agregado a favoritos! ⭐')
    return redirect('proyecto_detalle', proyecto_id=proyecto_id)


@login_required
def comentar(request, proyecto_id=None, historia_id=None):
    try:
        perfil = request.user.perfil
        if not perfil.puede_comentar():
            messages.error(request, f'🔇 No puedes comentar. Estado: {perfil.get_estado_display()}')
            return redirect('home')
    except Perfil.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.usuario = request.user
            if proyecto_id:
                comentario.proyecto = get_object_or_404(Proyecto, id=proyecto_id)
                if comentario.proyecto.autor and comentario.proyecto.autor != request.user:
                    crear_notificacion(
                        usuario=comentario.proyecto.autor,
                        tipo='comentario',
                        mensaje=f'💬 {request.user.username} comentó en "{comentario.proyecto.titulo}"',
                        enlace=f'/proyectos/{proyecto_id}/'
                    )
            elif historia_id:
                comentario.historia = get_object_or_404(HistoriaExito, id=historia_id)

            comentario.aprobado = False
            comentario.save()

            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                crear_notificacion(
                    usuario=admin,
                    tipo='aprobacion',
                    mensaje=f'💬 Nuevo comentario pendiente de {request.user.username}',
                    enlace=f'/admin/core/comentario/{comentario.id}/change/'
                )

            messages.success(request, 'Comentario enviado. Espera aprobación. 💬')

            perfil = request.user.perfil
            perfil.xp_total += 5
            perfil.save()
            verificar_insignias(request.user)

            if proyecto_id:
                return redirect('proyecto_detalle', proyecto_id=proyecto_id)
            else:
                return redirect('historia_detalle', historia_id=historia_id)
    return redirect('home')


@login_required
def inscribir_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if evento.cupos_disponibles() <= 0:
        messages.error(request, '❌ ¡No hay cupos disponibles!')
        return redirect('eventos')

    if request.user in evento.inscritos.all():
        evento.inscritos.remove(request.user)
        messages.info(request, 'Te has desinscrito del evento.')
    else:
        evento.inscritos.add(request.user)
        messages.success(request, f'✅ ¡Te has inscrito a "{evento.titulo}"!')
    return redirect('eventos')


# ==================== CHAT PÚBLICO ====================

@login_required
def chat(request):
    try:
        perfil = request.user.perfil
        if not perfil.puede_chatear():
            messages.error(request, f'🔇 No puedes usar el chat. Estado: {perfil.get_estado_display()}')
            return redirect('home')
    except Perfil.DoesNotExist:
        pass

    mensajes = MensajeChat.objects.all().order_by('-fecha')[:50]

    if request.method == 'POST':
        form = MensajeChatForm(request.POST)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.usuario = request.user
            mensaje.save()
            return redirect('chat')
    else:
        form = MensajeChatForm()

    return render(request, 'chat.html', {'mensajes': mensajes[::-1], 'form': form})


# ==================== RANKING ====================

@login_required
def ranking(request):
    usuarios = User.objects.annotate(
        total_xp=F('perfil__xp_total'),
        total_proyectos=Count('proyectocompletado', distinct=True),
        total_comentarios=Count('comentario', distinct=True),
        total_desafios=Count('desafios_hechos', distinct=True),
        racha=F('perfil__racha_dias')
    ).order_by('-total_xp')[:20]

    return render(request, 'ranking.html', {'usuarios': usuarios})


# ==================== DESAFÍOS ====================

@login_required
def desafios(request):
    desafios_activos = Desafio.objects.filter(activo=True)
    desafios_completados = DesafioCompletado.objects.filter(usuario=request.user).values_list('desafio_id', flat=True)

    if request.method == 'POST':
        desafio_id = request.POST.get('desafio_id')
        desafio = get_object_or_404(Desafio, id=desafio_id)

        if DesafioCompletado.objects.filter(usuario=request.user, desafio=desafio).exists():
            messages.info(request, 'Ya habías completado este desafío.')
            return redirect('desafios')

        DesafioCompletado.objects.create(usuario=request.user, desafio=desafio)

        perfil = request.user.perfil
        perfil.xp_total += desafio.xp_recompensa
        perfil.save()

        messages.success(request, f'🎉 ¡Completaste "{desafio.titulo}"! +{desafio.xp_recompensa} XP')
        verificar_insignias(request.user)
        return redirect('desafios')

    for desafio in desafios_activos:
        desafio.completado = desafio.id in desafios_completados

    return render(request, 'desafios.html', {'desafios': desafios_activos})


# ==================== NOTIFICACIONES ====================

@login_required
def notificaciones(request):
    notifs = Notificacion.objects.filter(usuario=request.user)
    notifs.filter(leida=False).update(leida=True)
    return render(request, 'notificaciones.html', {'notificaciones': notifs})


@login_required
def marcar_leida(request, notif_id):
    notif = get_object_or_404(Notificacion, id=notif_id, usuario=request.user)
    notif.leida = True
    notif.save()
    if notif.enlace:
        return redirect(notif.enlace)
    return redirect('notificaciones')


# ==================== MENSAJES PRIVADOS ====================

@login_required
def bandeja_entrada(request):
    mensajes = MensajePrivado.objects.filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).order_by('-fecha')

    conversaciones = {}
    for msg in mensajes:
        otro = msg.destinatario if msg.remitente == request.user else msg.remitente
        if otro.id not in conversaciones:
            conversaciones[otro.id] = {
                'usuario': otro,
                'ultimo_mensaje': msg,
                'no_leidos': MensajePrivado.objects.filter(remitente=otro, destinatario=request.user, leido=False).count()
            }

    return render(request, 'bandeja_entrada.html', {'conversaciones': conversaciones.values()})


@login_required
def conversacion(request, username):
    otro_usuario = get_object_or_404(User, username=username)

    MensajePrivado.objects.filter(remitente=otro_usuario, destinatario=request.user, leido=False).update(leido=True)

    mensajes = MensajePrivado.objects.filter(
        Q(remitente=request.user, destinatario=otro_usuario) |
        Q(remitente=otro_usuario, destinatario=request.user)
    ).order_by('fecha')

    if request.method == 'POST':
        form = MensajePrivadoForm(request.POST)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.remitente = request.user
            mensaje.destinatario = otro_usuario
            mensaje.save()

            crear_notificacion(
                usuario=otro_usuario,
                tipo='mensaje',
                mensaje=f'✉️ Nuevo mensaje de {request.user.username}',
                enlace=f'/mensajes/{request.user.username}/'
            )

            return redirect('conversacion', username=username)
    else:
        form = MensajePrivadoForm()

    return render(request, 'conversacion.html', {
        'otro_usuario': otro_usuario,
        'mensajes': mensajes,
        'form': form
    })


# ==================== FORO ====================

@login_required
def foro(request):
    preguntas = Pregunta.objects.all().order_by('-fecha')

    paginator = Paginator(preguntas, 10)
    page_number = request.GET.get('page')
    preguntas_paginadas = paginator.get_page(page_number)

    return render(request, 'foro.html', {'preguntas': preguntas_paginadas})


@login_required
def nueva_pregunta(request):
    if request.method == 'POST':
        form = PreguntaForm(request.POST)
        if form.is_valid():
            pregunta = form.save(commit=False)
            pregunta.autor = request.user
            pregunta.save()
            messages.success(request, '¡Pregunta publicada! ❓')
            return redirect('pregunta_detalle', pregunta_id=pregunta.id)
    else:
        form = PreguntaForm()
    return render(request, 'nueva_pregunta.html', {'form': form})


@login_required
def pregunta_detalle(request, pregunta_id):
    pregunta = get_object_or_404(Pregunta, id=pregunta_id)
    pregunta.vistas += 1
    pregunta.save()

    respuestas = pregunta.respuestas.all()

    if request.method == 'POST':
        form = RespuestaForm(request.POST)
        if form.is_valid():
            respuesta = form.save(commit=False)
            respuesta.pregunta = pregunta
            respuesta.autor = request.user
            respuesta.save()

            if pregunta.autor != request.user:
                crear_notificacion(
                    usuario=pregunta.autor,
                    tipo='comentario',
                    mensaje=f'💬 {request.user.username} respondió tu pregunta "{pregunta.titulo}"',
                    enlace=f'/foro/{pregunta.id}/'
                )

            messages.success(request, '¡Respuesta publicada! 💬')
            return redirect('pregunta_detalle', pregunta_id=pregunta.id)
    else:
        form = RespuestaForm()

    return render(request, 'pregunta_detalle.html', {
        'pregunta': pregunta,
        'respuestas': respuestas,
        'form': form
    })


@login_required
def votar_respuesta(request, respuesta_id):
    respuesta = get_object_or_404(Respuesta, id=respuesta_id)
    respuesta.votos += 1
    respuesta.save()
    messages.success(request, '👍 ¡Voto registrado!')
    return redirect('pregunta_detalle', pregunta_id=respuesta.pregunta.id)


@login_required
def marcar_correcta(request, respuesta_id):
    respuesta = get_object_or_404(Respuesta, id=respuesta_id)
    if respuesta.pregunta.autor != request.user:
        messages.error(request, 'Solo el autor de la pregunta puede marcar la respuesta correcta.')
        return redirect('pregunta_detalle', pregunta_id=respuesta.pregunta.id)

    Respuesta.objects.filter(pregunta=respuesta.pregunta).update(es_correcta=False)
    respuesta.es_correcta = True
    respuesta.save()

    respuesta.pregunta.resuelta = True
    respuesta.pregunta.save()

    messages.success(request, '✅ Respuesta marcada como correcta')
    return redirect('pregunta_detalle', pregunta_id=respuesta.pregunta.id)


# ==================== DASHBOARD ADMIN ====================

@staff_member_required
def admin_dashboard(request):
    proyectos_pendientes = ProyectoEstudiante.objects.filter(aprobado=False)
    comentarios_pendientes = Comentario.objects.filter(aprobado=False)

    total_pendientes = proyectos_pendientes.count() + comentarios_pendientes.count()

    context = {
        'total_proyectos': Proyecto.objects.count(),
        'total_usuarios': User.objects.count(),
        'total_comentarios': Comentario.objects.count(),
        'total_historias': HistoriaExito.objects.count(),
        'total_eventos': Evento.objects.count(),
        'total_recursos': Recurso.objects.count(),
        'total_proyectos_estudiantes': ProyectoEstudiante.objects.count(),
        'total_preguntas': Pregunta.objects.count(),

        'proyectos_pendientes': proyectos_pendientes.count(),
        'comentarios_pendientes': comentarios_pendientes.count(),
        'total_pendientes': total_pendientes,
        'proyectos_pendientes_lista': proyectos_pendientes[:5],
        'comentarios_pendientes_lista': comentarios_pendientes[:5],

        'ultimos_usuarios': User.objects.order_by('-date_joined')[:5],
        'ultimos_proyectos': Proyecto.objects.order_by('-fecha_publicacion')[:5],
        'ultimos_comentarios': Comentario.objects.order_by('-fecha_creacion')[:5],

        'title': 'Dashboard Admin',
    }
    return render(request, 'dashboard_admin.html', context)