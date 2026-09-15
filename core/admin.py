from django.contrib import admin
from django.utils import timezone
from .models import *


class MediaMixin:
    class Media:
        js = ('admin/js/image_preview.js',)


# ==================== PERFIL ====================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin, MediaMixin):
    list_display = ('usuario', 'grado', 'edad', 'nivel_programacion', 'estado', 'racha_dias', 'xp_total')
    list_filter = ('grado', 'nivel_programacion', 'estado')
    search_fields = ('usuario__username', 'usuario__email')
    actions = ['advertir_usuario', 'silenciar_usuario', 'suspender_usuario', 'banear_usuario', 'reactivar_usuario']
    list_per_page = 20
    save_on_top = True

    fieldsets = (
        ('Información Personal', {
            'fields': ('usuario', 'grado', 'edad', 'nivel_programacion', 'intereses', 'foto_perfil', 'bio')
        }),
        ('Estadísticas', {
            'fields': ('racha_dias', 'xp_total', 'nivel', 'tipo_programador', 'ultima_visita')
        }),
        ('Sanción', {
            'fields': ('estado', 'motivo_sancion', 'fecha_sancion', 'fecha_fin_sancion', 'sancionado_por'),
            'description': 'Aquí puedes gestionar el estado del usuario'
        }),
    )

    def advertir_usuario(self, request, queryset):
        updated = queryset.update(estado='advertido', fecha_sancion=timezone.now(), sancionado_por=request.user)
        self.message_user(request, f'⚠️ {updated} usuario(s) advertido(s).')
    advertir_usuario.short_description = '⚠️ Advertir usuarios seleccionados'

    def silenciar_usuario(self, request, queryset):
        updated = queryset.update(estado='silenciado', fecha_sancion=timezone.now(), sancionado_por=request.user)
        self.message_user(request, f'🔇 {updated} usuario(s) silenciado(s).')
    silenciar_usuario.short_description = '🔇 Silenciar usuarios seleccionados'

    def suspender_usuario(self, request, queryset):
        updated = queryset.update(estado='suspendido', fecha_sancion=timezone.now(), sancionado_por=request.user)
        self.message_user(request, f'⏸️ {updated} usuario(s) suspendido(s).')
    suspender_usuario.short_description = '⏸️ Suspender usuarios seleccionados'

    def banear_usuario(self, request, queryset):
        updated = queryset.update(estado='baneado', fecha_sancion=timezone.now(), sancionado_por=request.user)
        self.message_user(request, f'🚫 {updated} usuario(s) baneado(s).')
    banear_usuario.short_description = '🚫 Banear usuarios seleccionados'

    def reactivar_usuario(self, request, queryset):
        updated = queryset.update(
            estado='activo', motivo_sancion='', fecha_sancion=None,
            fecha_fin_sancion=None, sancionado_por=None
        )
        self.message_user(request, f'✅ {updated} usuario(s) reactivado(s).')
    reactivar_usuario.short_description = '✅ Reactivar usuarios seleccionados'


# ==================== HISTORIA ====================
@admin.register(HistoriaExito)
class HistoriaExitoAdmin(admin.ModelAdmin, MediaMixin):
    list_display = ('nombre_persona', 'edad_cuando_empezo', 'proyecto_famoso')
    search_fields = ('nombre_persona', 'proyecto_famoso')
    list_per_page = 20


# ==================== PROYECTO ====================
@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin, MediaMixin):
    list_display = ('titulo', 'categoria', 'dificultad', 'autor', 'vistas', 'fecha_publicacion')
    list_filter = ('categoria', 'dificultad')
    search_fields = ('titulo', 'descripcion_corta')
    list_per_page = 20


# ==================== COMENTARIO ====================
@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'texto_corto', 'aprobado', 'fecha_creacion')
    list_filter = ('aprobado',)
    search_fields = ('texto', 'usuario__username')
    actions = ['aprobar_comentarios', 'rechazar_comentarios']
    list_per_page = 20

    def texto_corto(self, obj):
        return obj.texto[:50] + '...' if len(obj.texto) > 50 else obj.texto
    texto_corto.short_description = 'Comentario'

    def aprobar_comentarios(self, request, queryset):
        updated = queryset.update(aprobado=True)
        self.message_user(request, f'✅ {updated} comentario(s) aprobado(s).')
    aprobar_comentarios.short_description = '✅ Aprobar comentarios seleccionados'

    def rechazar_comentarios(self, request, queryset):
        updated = queryset.update(aprobado=False)
        self.message_user(request, f'❌ {updated} comentario(s) rechazado(s).')
    rechazar_comentarios.short_description = '❌ Rechazar comentarios seleccionados'


# ==================== PROYECTO ESTUDIANTE ====================
@admin.register(ProyectoEstudiante)
class ProyectoEstudianteAdmin(admin.ModelAdmin, MediaMixin):
    list_display = ('titulo', 'estudiante', 'grado_estudiante', 'categoria', 'aprobado', 'likes', 'descargas')
    list_filter = ('aprobado', 'grado_estudiante', 'categoria')
    search_fields = ('titulo', 'descripcion', 'estudiante__username')
    actions = ['aprobar_proyectos', 'rechazar_proyectos']
    list_per_page = 20
    readonly_fields = ('vistas', 'descargas', 'likes')

    fieldsets = (
        ('Información', {
            'fields': ('titulo', 'descripcion', 'descripcion_larga', 'categoria', 'herramientas')
        }),
        ('Archivos', {
            'fields': ('imagen', 'archivo', 'enlace_externo')
        }),
        ('Autor', {
            'fields': ('estudiante', 'grado_estudiante')
        }),
        ('Estado', {
            'fields': ('aprobado', 'fecha_aprobacion', 'likes', 'vistas', 'descargas')
        }),
    )

    def aprobar_proyectos(self, request, queryset):
        updated = queryset.update(aprobado=True, fecha_aprobacion=timezone.now())
        self.message_user(request, f'✅ {updated} proyecto(s) aprobado(s).')
    aprobar_proyectos.short_description = '✅ Aprobar proyectos seleccionados'

    def rechazar_proyectos(self, request, queryset):
        updated = queryset.update(aprobado=False)
        self.message_user(request, f'❌ {updated} proyecto(s) rechazado(s).')
    rechazar_proyectos.short_description = '❌ Rechazar proyectos seleccionados'


# ==================== EVENTO ====================
@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha', 'hora', 'lugar', 'cupos', 'cupos_disponibles')
    list_filter = ('fecha', 'grado_requerido')
    list_per_page = 20

    def cupos_disponibles(self, obj):
        return obj.cupos_disponibles()
    cupos_disponibles.short_description = 'Cupos disponibles'


# ==================== RECURSO ====================
@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin, MediaMixin):
    list_display = ('titulo', 'categoria', 'recomendado_para')
    list_filter = ('categoria', 'recomendado_para')
    list_per_page = 20


# ==================== INSIGNIA ====================
@admin.register(Insignia)
class InsigniaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'icono', 'condicion')
    list_per_page = 20


@admin.register(InsigniaUsuario)
class InsigniaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'insignia', 'fecha_desbloqueo')
    list_per_page = 20


# ==================== CONTACTO ====================
@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'fecha', 'respondido')
    list_filter = ('respondido',)
    list_per_page = 20


@admin.register(ResultadoTest)
class ResultadoTestAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_programador', 'fecha_realizado')
    list_per_page = 20


# ==================== CHAT ====================
@admin.register(MensajeChat)
class MensajeChatAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mensaje_corto', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('usuario__username', 'mensaje')
    list_per_page = 20

    def mensaje_corto(self, obj):
        return obj.mensaje[:50] + '...' if len(obj.mensaje) > 50 else obj.mensaje
    mensaje_corto.short_description = 'Mensaje'


# ==================== DESAFÍOS ====================
@admin.register(Desafio)
class DesafioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'xp_recompensa', 'activo', 'total_completados')
    list_filter = ('categoria', 'activo')
    search_fields = ('titulo', 'descripcion')
    list_per_page = 20


@admin.register(DesafioCompletado)
class DesafioCompletadoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'desafio', 'fecha_completado')
    list_filter = ('fecha_completado',)
    list_per_page = 20


# ==================== NOTIFICACIONES ====================
@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'mensaje_corto', 'leida', 'fecha')
    list_filter = ('tipo', 'leida')
    list_per_page = 20

    def mensaje_corto(self, obj):
        return obj.mensaje[:50]
    mensaje_corto.short_description = 'Mensaje'


# ==================== SEGUIDORES ====================
@admin.register(Seguidor)
class SeguidorAdmin(admin.ModelAdmin):
    list_display = ('seguidor', 'seguido', 'fecha')
    list_per_page = 20


# ==================== MENSAJES PRIVADOS ====================
@admin.register(MensajePrivado)
class MensajePrivadoAdmin(admin.ModelAdmin):
    list_display = ('remitente', 'destinatario', 'mensaje_corto', 'leido', 'fecha')
    list_filter = ('leido',)
    list_per_page = 20

    def mensaje_corto(self, obj):
        return obj.mensaje[:40]
    mensaje_corto.short_description = 'Mensaje'


# ==================== FORO ====================
@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'total_respuestas', 'resuelta', 'vistas', 'fecha')
    list_filter = ('resuelta',)
    list_per_page = 20


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ('pregunta', 'autor', 'votos', 'es_correcta', 'fecha')
    list_filter = ('es_correcta',)
    list_per_page = 20