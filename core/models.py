from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid
import random

# Opciones para los campos
GRADO_OPCIONES = [
    ('10mo', '10mo Grado'),
    ('11ro', '11ro Grado'),
    ('12mo', '12mo Grado'),
]

NIVEL_OPCIONES = [
    ('nunca', 'Nunca he programado'),
    ('un_poco', 'He programado un poco'),
    ('ya_se', 'Ya sé algo de programación'),
]

INTERES_OPCIONES = [
    ('videojuegos', '🎮 Videojuegos'),
    ('diseno', '🎨 Diseño'),
    ('robots', '🤖 Robots'),
    ('apps', '📱 Apps'),
    ('ia', '🧠 Inteligencia Artificial'),
    ('no_se', '🤔 No sé, quiero descubrirlo'),
]

TIPO_PROGRAMADOR = [
    ('creativo', '🎨 Creativo'),
    ('logico', '🧠 Lógico'),
    ('visual', '👁️ Visual'),
    ('social', '🤝 Social'),
    ('explorador', '🌍 Explorador'),
]

ESTADO_SANCION = [
    ('activo', '✅ Activo'),
    ('advertido', '⚠️ Advertido'),
    ('silenciado', '🔇 Silenciado'),
    ('suspendido', '⏸️ Suspendido'),
    ('baneado', '🚫 Baneado'),
]


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    grado = models.CharField(max_length=10, choices=GRADO_OPCIONES)
    edad = models.IntegerField(validators=[MinValueValidator(14), MaxValueValidator(19)])
    nivel_programacion = models.CharField(max_length=20, choices=NIVEL_OPCIONES, default='nunca')
    intereses = models.JSONField(default=list)
    tipo_programador = models.CharField(max_length=20, choices=TIPO_PROGRAMADOR, null=True, blank=True)
    racha_dias = models.IntegerField(default=0)
    xp_total = models.IntegerField(default=0)
    nivel = models.IntegerField(default=1)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_visita = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=300, blank=True, null=True)

    # ✅ Email confirmado
    email_confirmado = models.BooleanField(default=False)

    # Sanciones
    estado = models.CharField(max_length=20, choices=ESTADO_SANCION, default='activo')
    motivo_sancion = models.TextField(blank=True, null=True)
    fecha_sancion = models.DateTimeField(null=True, blank=True)
    fecha_fin_sancion = models.DateTimeField(null=True, blank=True)
    sancionado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sanciones_aplicadas')

    # Seguidores
    seguidores = models.ManyToManyField(User, related_name='siguiendo', blank=True)

    def __str__(self):
        return f"{self.usuario.username} ({self.grado})"

    def get_nivel_nombre(self):
        niveles = [
            (0, 'Aprendiz'),
            (100, 'Explorador'),
            (300, 'Creador'),
            (600, 'Genio'),
            (1000, 'Leyenda'),
        ]
        for xp, nombre in reversed(niveles):
            if self.xp_total >= xp:
                return nombre
        return 'Aprendiz'

    def esta_sancionado(self):
        return self.estado != 'activo'

    def puede_chatear(self):
        return self.estado in ['activo', 'advertido']

    def puede_comentar(self):
        return self.estado in ['activo', 'advertido']

    def puede_iniciar_sesion(self):
        return self.estado not in ['suspendido', 'baneado']

    def total_seguidores(self):
        return self.seguidores.count()

    def total_siguiendo(self):
        return self.usuario.siguiendo.count()


# ==================== CÓDIGO DE CONFIRMACIÓN ====================
class CodigoConfirmacion(models.Model):
    """Código de 4 dígitos para confirmar el email del usuario"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='codigo_confirmacion')
    codigo = models.CharField(max_length=4)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    def __str__(self):
        return f"Código de {self.usuario.username}"

    def es_valido(self):
        """El código es válido por 15 minutos"""
        if self.usado:
            return False
        expiracion = self.creado + timedelta(minutes=15)
        return timezone.now() < expiracion

    @staticmethod
    def generar_codigo():
        """Genera un código aleatorio de 4 dígitos"""
        return str(random.randint(1000, 9999))


# ==================== CÓDIGO DE RECUPERACIÓN ====================
class CodigoRecuperacion(models.Model):
    """Código de 4 dígitos para recuperar contraseña"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='codigos_recuperacion')
    codigo = models.CharField(max_length=4)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f"Código de {self.usuario.username}"

    def es_valido(self):
        """El código es válido por 15 minutos"""
        if self.usado:
            return False
        expiracion = self.creado + timedelta(minutes=15)
        return timezone.now() < expiracion

    @staticmethod
    def generar_codigo():
        """Genera un código aleatorio de 4 dígitos"""
        return str(random.randint(1000, 9999))


class HistoriaExito(models.Model):
    nombre_persona = models.CharField(max_length=100)
    edad_cuando_empezo = models.IntegerField()
    foto = models.ImageField(upload_to='historias/', null=True, blank=True)
    historia_corta = models.TextField(max_length=300)
    historia_completa = models.TextField()
    proyecto_famoso = models.CharField(max_length=200)
    frase_celebre = models.TextField(max_length=200)
    enlace = models.URLField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_persona


class Proyecto(models.Model):
    CATEGORIA_PROYECTO = [
        ('juego', '🎮 Juego'),
        ('web', '🌐 Web'),
        ('robot', '🤖 Robot'),
        ('app', '📱 App'),
        ('arte', '🎨 Arte'),
    ]

    DIFICULTAD_OPCIONES = [
        ('facil', '⭐ Fácil'),
        ('medio', '⭐⭐ Medio'),
        ('dificil', '⭐⭐⭐ Difícil'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion_corta = models.TextField(max_length=300)
    descripcion_completa = models.TextField()
    dificultad = models.CharField(max_length=10, choices=DIFICULTAD_OPCIONES)
    tiempo_estimado = models.CharField(max_length=50)
    herramientas_necesarias = models.TextField()
    pasos = models.TextField()
    imagen_resultado = models.ImageField(upload_to='proyectos/', null=True, blank=True)
    video_enlace = models.URLField(blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_PROYECTO)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='proyectos_creados')
    completado_por = models.ManyToManyField(User, through='ProyectoCompletado', related_name='proyectos_completados')
    favoritos = models.ManyToManyField(User, related_name='proyectos_favoritos', blank=True)
    vistas = models.IntegerField(default=0)

    def __str__(self):
        return self.titulo


class ProyectoCompletado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    fecha_completado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'proyecto')


class Comentario(models.Model):
    texto = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, null=True, blank=True)
    historia = models.ForeignKey(HistoriaExito, on_delete=models.CASCADE, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=False)

    def __str__(self):
        return f"Comentario de {self.usuario.username}"


class ProyectoEstudiante(models.Model):
    CATEGORIA_PROYECTO_EST = [
        ('juego', '🎮 Juego'),
        ('web', '🌐 Web'),
        ('robot', '🤖 Robot'),
        ('app', '📱 App'),
        ('arte', '🎨 Arte'),
        ('otro', '📦 Otro'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    descripcion_larga = models.TextField(blank=True, null=True, help_text='Explica cómo lo hiciste')
    imagen = models.ImageField(upload_to='proyectos_estudiantes/', help_text='Imagen de portada')
    archivo = models.FileField(upload_to='proyectos_archivos/', null=True, blank=True, help_text='Sube tu proyecto terminado')
    enlace_externo = models.URLField(blank=True, null=True, help_text='Enlace a GitHub, YouTube, etc.')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_PROYECTO_EST, default='otro')
    herramientas = models.CharField(max_length=200, blank=True, null=True, help_text='Ej: Scratch, Python, HTML/CSS')

    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proyectos_subidos')
    grado_estudiante = models.CharField(max_length=10, choices=GRADO_OPCIONES)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    aprobado = models.BooleanField(default=False)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    descargas = models.IntegerField(default=0)
    vistas = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.titulo} - {self.estudiante.username}"


class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha = models.DateField()
    hora = models.TimeField()
    lugar = models.CharField(max_length=200)
    cupos = models.IntegerField()
    inscritos = models.ManyToManyField(User, related_name='eventos_inscritos', blank=True)
    grado_requerido = models.CharField(max_length=10, choices=GRADO_OPCIONES, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def cupos_disponibles(self):
        return self.cupos - self.inscritos.count()

    def __str__(self):
        return self.titulo


class Recurso(models.Model):
    CATEGORIA_RECURSO = [
        ('principiante', '🌟 Principiante'),
        ('juegos', '🎮 Juegos'),
        ('webs', '🌐 Webs'),
        ('apps', '📱 Apps'),
        ('robots', '🤖 Robots'),
    ]
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_RECURSO)
    enlace = models.URLField()
    imagen = models.ImageField(upload_to='recursos/', null=True, blank=True)
    recomendado_para = models.CharField(max_length=20, choices=TIPO_PROGRAMADOR, null=True, blank=True)

    def __str__(self):
        return self.titulo


class Insignia(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50)
    condicion = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class InsigniaUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insignias')
    insignia = models.ForeignKey(Insignia, on_delete=models.CASCADE)
    fecha_desbloqueo = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'insignia')


class MensajeContacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    respondido = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje de {self.nombre}"


class ResultadoTest(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resultados_test')
    tipo_programador = models.CharField(max_length=20, choices=TIPO_PROGRAMADOR)
    fecha_realizado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'tipo_programador')


class MensajeChat(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_chat')
    mensaje = models.TextField(max_length=500)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario.username}: {self.mensaje[:30]}"


class Desafio(models.Model):
    CATEGORIA_DESAFIO = [
        ('programacion', '💻 Programación'),
        ('creatividad', '🎨 Creatividad'),
        ('logica', '🧠 Lógica'),
        ('social', '🤝 Social'),
    ]
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_DESAFIO)
    xp_recompensa = models.IntegerField(default=50)
    icono = models.CharField(max_length=50, default='🏆')
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_fin = models.DateField(null=True, blank=True)
    completado_por = models.ManyToManyField(User, through='DesafioCompletado', related_name='desafios_completados')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

    def total_completados(self):
        return self.desafio_completados.count()


class DesafioCompletado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='desafios_hechos')
    desafio = models.ForeignKey(Desafio, on_delete=models.CASCADE, related_name='desafio_completados')
    fecha_completado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'desafio')

    def __str__(self):
        return f"{self.usuario.username} completó {self.desafio.titulo}"


class Notificacion(models.Model):
    TIPO_NOTIFICACION = [
        ('comentario', '💬 Nuevo comentario'),
        ('aprobacion', '✅ Aprobación'),
        ('insignia', '🏅 Nueva insignia'),
        ('seguidor', '👥 Nuevo seguidor'),
        ('desafio', '🎯 Desafío completado'),
        ('sancion', '⚠️ Sanción'),
        ('mensaje', '✉️ Mensaje privado'),
        ('like', '❤️ Nuevo like'),
        ('descarga', '📥 Nueva descarga'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_NOTIFICACION)
    mensaje = models.TextField(max_length=300)
    enlace = models.CharField(max_length=200, blank=True, null=True)
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario.username}: {self.mensaje[:30]}"


class Seguidor(models.Model):
    seguidor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='siguiendo_a')
    seguido = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seguidores_de')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('seguidor', 'seguido')

    def __str__(self):
        return f"{self.seguidor.username} sigue a {self.seguido.username}"


class MensajePrivado(models.Model):
    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_recibidos')
    mensaje = models.TextField(max_length=1000)
    leido = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"{self.remitente.username} → {self.destinatario.username}"


class Pregunta(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preguntas_foro')
    fecha = models.DateTimeField(auto_now_add=True)
    vistas = models.IntegerField(default=0)
    resuelta = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return self.titulo

    def total_respuestas(self):
        return self.respuestas.count()


class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='respuestas_foro')
    contenido = models.TextField()
    votos = models.IntegerField(default=0)
    es_correcta = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-votos', 'fecha']

    def __str__(self):
        return f"Respuesta de {self.autor.username}"