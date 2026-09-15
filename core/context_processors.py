from .models import Perfil, Notificacion, MensajePrivado, ProyectoEstudiante, Comentario


def user_stats(request):
    """Context processor con estadísticas del usuario"""
    context = {}
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
            context['user_nivel'] = perfil.get_nivel_nombre()
            context['user_racha'] = perfil.racha_dias
            context['user_xp'] = perfil.xp_total
            context['user_tipo'] = perfil.tipo_programador
        except Perfil.DoesNotExist:
            pass

        # ✅ Notificaciones no leídas
        context['notificaciones_no_leidas'] = Notificacion.objects.filter(
            usuario=request.user, leida=False
        ).count()

        # ✅ Últimas 10 notificaciones (leídas o no)
        context['notificaciones_recientes'] = Notificacion.objects.filter(
            usuario=request.user
        ).order_by('-fecha')[:10]

        # ✅ Mensajes no leídos
        context['mensajes_no_leidos'] = MensajePrivado.objects.filter(
            destinatario=request.user, leido=False
        ).count()

        # ✅ Últimos 10 mensajes recibidos
        context['mensajes_recientes'] = MensajePrivado.objects.filter(
            destinatario=request.user
        ).order_by('-fecha')[:10]

        # ✅ Si es admin, contar pendientes
        if request.user.is_staff:
            context['admin_pendientes'] = (
                ProyectoEstudiante.objects.filter(aprobado=False).count() +
                Comentario.objects.filter(aprobado=False).count()
            )

    return context