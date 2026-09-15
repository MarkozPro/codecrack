from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from .models import *
from .forms import *


# ==================== TESTS DE MODELOS ====================

class ModelosTest(TestCase):
    """Pruebas de los modelos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test12345'
        )
        self.perfil = Perfil.objects.create(
            usuario=self.user,
            grado='10mo',
            edad=16,
            nivel_programacion='nunca',
            intereses=['videojuegos']
        )

    def test_perfil_se_crea_correctamente(self):
        self.assertEqual(self.perfil.usuario.username, 'testuser')
        self.assertEqual(self.perfil.grado, '10mo')
        self.assertEqual(self.perfil.edad, 16)
        self.assertEqual(self.perfil.estado, 'activo')

    def test_perfil_nivel_nombre(self):
        self.perfil.xp_total = 150
        self.perfil.save()
        self.assertEqual(self.perfil.get_nivel_nombre(), 'Explorador')

    def test_perfil_puede_chatear_activo(self):
        self.assertTrue(self.perfil.puede_chatear())

    def test_perfil_no_puede_chatear_silenciado(self):
        self.perfil.estado = 'silenciado'
        self.perfil.save()
        self.assertFalse(self.perfil.puede_chatear())

    def test_perfil_no_puede_login_suspendido(self):
        self.perfil.estado = 'suspendido'
        self.perfil.save()
        self.assertFalse(self.perfil.puede_iniciar_sesion())

    def test_proyecto_se_crea(self):
        proyecto = Proyecto.objects.create(
            titulo='Test Proyecto',
            descripcion_corta='Test',
            descripcion_completa='Test completo',
            dificultad='facil',
            tiempo_estimado='30 min',
            herramientas_necesarias='PC',
            pasos='1. Hacer algo',
            categoria='juego',
            autor=self.user
        )
        self.assertEqual(proyecto.titulo, 'Test Proyecto')
        self.assertEqual(proyecto.vistas, 0)

    def test_desafio_se_crea(self):
        desafio = Desafio.objects.create(
            titulo='Test Desafío',
            descripcion='Test',
            categoria='programacion',
            xp_recompensa=50
        )
        self.assertEqual(desafio.titulo, 'Test Desafío')
        self.assertEqual(desafio.total_completados(), 0)

    def test_notificacion_se_crea(self):
        notif = Notificacion.objects.create(
            usuario=self.user,
            tipo='comentario',
            mensaje='Test notificación'
        )
        self.assertEqual(notif.usuario, self.user)
        self.assertFalse(notif.leida)


# ==================== TESTS DE AUTENTICACIÓN ====================

class AutenticacionTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_registro_crea_usuario_y_perfil(self):
        response = self.client.post(reverse('registro'), {
            'username': 'nuevo',
            'email': 'nuevo@test.com',
            'grado': '10mo',
            'edad': 16,
            'nivel_programacion': 'nunca',
            'intereses': ['videojuegos'],
            'password1': 'testpass123',
            'password2': 'testpass123',
        })
        self.assertTrue(User.objects.filter(username='nuevo').exists())
        self.assertTrue(Perfil.objects.filter(usuario__username='nuevo').exists())

    def test_login_correcto(self):
        User.objects.create_user(username='testuser', password='test12345')
        Perfil.objects.create(
            usuario=User.objects.get(username='testuser'),
            grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=['videojuegos']
        )
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'test12345'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_incorrecto(self):
        User.objects.create_user(username='testuser', password='test12345')
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_funciona(self):
        User.objects.create_user(username='testuser', password='test12345')
        self.client.login(username='testuser', password='test12345')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


# ==================== TESTS DE SANCIONES ====================

class SancionesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )

    def test_usuario_activo_puede_login(self):
        self.perfil.estado = 'activo'
        self.perfil.save()
        self.assertTrue(self.perfil.puede_iniciar_sesion())

    def test_usuario_suspendido_no_puede_login(self):
        self.perfil.estado = 'suspendido'
        self.perfil.save()
        self.assertFalse(self.perfil.puede_iniciar_sesion())

    def test_usuario_baneado_no_puede_login(self):
        self.perfil.estado = 'baneado'
        self.perfil.save()
        self.assertFalse(self.perfil.puede_iniciar_sesion())

    def test_usuario_silenciado_no_puede_comentar(self):
        self.perfil.estado = 'silenciado'
        self.perfil.save()
        self.assertFalse(self.perfil.puede_comentar())

    def test_usuario_advertido_puede_comentar(self):
        self.perfil.estado = 'advertido'
        self.perfil.save()
        self.assertTrue(self.perfil.puede_comentar())


# ==================== TESTS DE PERMISOS ====================

class PermisosTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_chat_requiere_login(self):
        response = self.client.get(reverse('chat'))
        self.assertEqual(response.status_code, 302)

    def test_foro_requiere_login(self):
        response = self.client.get(reverse('foro'))
        self.assertEqual(response.status_code, 302)

    def test_mensajes_requieren_login(self):
        response = self.client.get(reverse('bandeja_entrada'))
        self.assertEqual(response.status_code, 302)

    def test_notificaciones_requieren_login(self):
        response = self.client.get(reverse('notificaciones'))
        self.assertEqual(response.status_code, 302)

    def test_ranking_requiere_login(self):
        response = self.client.get(reverse('ranking'))
        self.assertEqual(response.status_code, 302)

    def test_home_es_publico(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_proyectos_es_publico(self):
        response = self.client.get(reverse('proyectos'))
        self.assertEqual(response.status_code, 200)


# ==================== TESTS DE PROYECTOS ====================

class ProyectosTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )
        self.client.login(username='test', password='test12345')
        self.proyecto = Proyecto.objects.create(
            titulo='Test Proyecto',
            descripcion_corta='Test',
            descripcion_completa='Test completo',
            dificultad='facil',
            tiempo_estimado='30 min',
            herramientas_necesarias='PC',
            pasos='1. Hacer algo',
            categoria='juego',
            autor=self.user
        )

    def test_lista_proyectos(self):
        response = self.client.get(reverse('proyectos'))
        self.assertEqual(response.status_code, 200)

    def test_detalle_proyecto(self):
        vistas_antes = self.proyecto.vistas
        response = self.client.get(reverse('proyecto_detalle', args=[self.proyecto.id]))
        self.assertEqual(response.status_code, 200)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.vistas, vistas_antes + 1)

    def test_completar_proyecto(self):
        xp_antes = self.perfil.xp_total
        self.client.get(reverse('completar_proyecto', args=[self.proyecto.id]))
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.xp_total, xp_antes + 50)

    def test_favorito(self):
        self.client.get(reverse('toggle_favorito', args=[self.proyecto.id]))
        self.assertIn(self.proyecto, self.user.proyectos_favoritos.all())

    def test_buscar_proyecto(self):
        response = self.client.get(reverse('proyectos') + '?buscar=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Proyecto')


# ==================== TESTS DE COMENTARIOS ====================

class ComentariosTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )
        self.client.login(username='test', password='test12345')
        self.proyecto = Proyecto.objects.create(
            titulo='Test', descripcion_corta='T', descripcion_completa='T',
            dificultad='facil', tiempo_estimado='30 min',
            herramientas_necesarias='PC', pasos='1',
            categoria='juego', autor=self.user
        )

    def test_comentar_proyecto(self):
        response = self.client.post(
            reverse('comentar_proyecto', args=[self.proyecto.id]),
            {'texto': 'Comentario test'}
        )
        self.assertEqual(Comentario.objects.count(), 1)

    def test_silenciado_no_puede_comentar(self):
        self.perfil.estado = 'silenciado'
        self.perfil.save()
        response = self.client.post(
            reverse('comentar_proyecto', args=[self.proyecto.id]),
            {'texto': 'Comentario test'}
        )
        self.assertEqual(Comentario.objects.count(), 0)


# ==================== TESTS DE CHAT ====================

class ChatTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )
        self.client.login(username='test', password='test12345')

    def test_enviar_mensaje_chat(self):
        response = self.client.post(reverse('chat'), {'mensaje': 'Hola mundo'})
        self.assertEqual(MensajeChat.objects.count(), 1)
        self.assertEqual(MensajeChat.objects.first().mensaje, 'Hola mundo')

    def test_silenciado_no_puede_chatear(self):
        self.perfil.estado = 'silenciado'
        self.perfil.save()
        response = self.client.get(reverse('chat'))
        self.assertEqual(response.status_code, 302)


# ==================== TESTS DE FORO ====================

class ForoTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )
        self.client.login(username='test', password='test12345')

    def test_crear_pregunta(self):
        response = self.client.post(reverse('nueva_pregunta'), {
            'titulo': '¿Cómo aprender Python?',
            'contenido': 'Quiero aprender Python desde cero'
        })
        self.assertEqual(Pregunta.objects.count(), 1)
        self.assertEqual(Pregunta.objects.first().autor, self.user)

    def test_responder_pregunta(self):
        pregunta = Pregunta.objects.create(
            titulo='Test', contenido='Test', autor=self.user
        )
        response = self.client.post(
            reverse('pregunta_detalle', args=[pregunta.id]),
            {'contenido': 'Mi respuesta'}
        )
        self.assertEqual(Respuesta.objects.count(), 1)

    def test_votar_respuesta(self):
        pregunta = Pregunta.objects.create(titulo='T', contenido='T', autor=self.user)
        respuesta = Respuesta.objects.create(
            pregunta=pregunta, autor=self.user, contenido='R'
        )
        votos_antes = respuesta.votos
        self.client.get(reverse('votar_respuesta', args=[respuesta.id]))
        respuesta.refresh_from_db()
        self.assertEqual(respuesta.votos, votos_antes + 1)


# ==================== TESTS DE MENSAJES PRIVADOS ====================

class MensajesPrivadosTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='test12345')
        self.user2 = User.objects.create_user(username='user2', password='test12345')
        Perfil.objects.create(usuario=self.user1, grado='10mo', edad=16, nivel_programacion='nunca', intereses=[])
        Perfil.objects.create(usuario=self.user2, grado='10mo', edad=16, nivel_programacion='nunca', intereses=[])
        self.client.login(username='user1', password='test12345')

    def test_enviar_mensaje_privado(self):
        response = self.client.post(
            reverse('conversacion', args=['user2']),
            {'mensaje': 'Hola user2'}
        )
        self.assertEqual(MensajePrivado.objects.count(), 1)

    def test_bandeja_entrada_carga(self):
        response = self.client.get(reverse('bandeja_entrada'))
        self.assertEqual(response.status_code, 200)


# ==================== TESTS DE NOTIFICACIONES ====================

class NotificacionesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test12345')
        Perfil.objects.create(
            usuario=self.user, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )
        self.client.login(username='test', password='test12345')

    def test_notificaciones_cargan(self):
        response = self.client.get(reverse('notificaciones'))
        self.assertEqual(response.status_code, 200)

    def test_marcar_notificacion_leida(self):
        notif = Notificacion.objects.create(
            usuario=self.user, tipo='comentario', mensaje='Test'
        )
        self.client.get(reverse('marcar_leida', args=[notif.id]))
        notif.refresh_from_db()
        self.assertTrue(notif.leida)


# ==================== TESTS DE SEGUIDORES ====================

class SeguidoresTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='test12345')
        self.user2 = User.objects.create_user(username='user2', password='test12345')
        Perfil.objects.create(usuario=self.user1, grado='10mo', edad=16, nivel_programacion='nunca', intereses=[])
        Perfil.objects.create(usuario=self.user2, grado='10mo', edad=16, nivel_programacion='nunca', intereses=[])
        self.client.login(username='user1', password='test12345')

    def test_seguir_usuario(self):
        self.client.get(reverse('seguir_usuario', args=['user2']))
        self.assertTrue(Seguidor.objects.filter(seguidor=self.user1, seguido=self.user2).exists())

    def test_dejar_de_seguir(self):
        Seguidor.objects.create(seguidor=self.user1, seguido=self.user2)
        self.client.get(reverse('seguir_usuario', args=['user2']))
        self.assertFalse(Seguidor.objects.filter(seguidor=self.user1, seguido=self.user2).exists())


# ==================== TESTS DE RANKING ====================

class RankingTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='test12345')
        self.user2 = User.objects.create_user(username='user2', password='test12345')
        Perfil.objects.create(usuario=self.user1, grado='10mo', edad=16, nivel_programacion='nunca', intereses=[], xp_total=500)
        Perfil.objects.create(usuario=self.user2, grado='10mo', edad=16, nivel_programacion='nunca', intereses=[], xp_total=100)
        self.client.login(username='user1', password='test12345')

    def test_ranking_carga(self):
        response = self.client.get(reverse('ranking'))
        self.assertEqual(response.status_code, 200)


# ==================== TESTS DE DESAFÍOS ====================

class DesafiosTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )
        self.client.login(username='test', password='test12345')
        self.desafio = Desafio.objects.create(
            titulo='Test', descripcion='Test',
            categoria='programacion', xp_recompensa=50
        )

    def test_completar_desafio_da_xp(self):
        """Completar un desafío da XP"""
        xp_antes = self.perfil.xp_total
        self.client.post(reverse('desafios'), {'desafio_id': self.desafio.id})
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.xp_total, xp_antes + 50)

    def test_no_se_puede_completar_dos_veces(self):
        """No se puede completar el mismo desafío dos veces"""
        # Primera vez
        self.client.post(reverse('desafios'), {'desafio_id': self.desafio.id})
        self.perfil.refresh_from_db()
        xp_despues_primera = self.perfil.xp_total

        # Segunda vez
        self.client.post(reverse('desafios'), {'desafio_id': self.desafio.id})
        self.perfil.refresh_from_db()

        # El XP no debe cambiar
        self.assertEqual(self.perfil.xp_total, xp_despues_primera)

        # Solo debe haber 1 registro
        self.assertEqual(DesafioCompletado.objects.filter(
            usuario=self.user, desafio=self.desafio
        ).count(), 1)


# ==================== TESTS DEL ADMIN ====================

class AdminTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='admin123', email='admin@test.com'
        )
        Perfil.objects.create(
            usuario=self.admin, grado='10mo', edad=16,
            nivel_programacion='nunca', intereses=[]
        )
        self.client.login(username='admin', password='admin123')

    def test_admin_accesible(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_admin_accesible(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_usuario_normal_no_accede_admin(self):
        user = User.objects.create_user(username='normal', password='test12345')
        Perfil.objects.create(usuario=user, grado='10mo', edad=16, nivel_programacion='nunca', intereses=[])
        self.client.login(username='normal', password='test12345')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)


# ==================== TESTS DE PÁGINAS PÚBLICAS ====================

class PaginasPublicasTest(TestCase):
    def test_home(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_acerca_de(self):
        response = self.client.get(reverse('acerca_de'))
        self.assertEqual(response.status_code, 200)

    def test_que_es_programar(self):
        response = self.client.get(reverse('que_es_programar'))
        self.assertEqual(response.status_code, 200)

    def test_contacto(self):
        response = self.client.get(reverse('contacto'))
        self.assertEqual(response.status_code, 200)

    def test_recursos(self):
        response = self.client.get(reverse('recursos'))
        self.assertEqual(response.status_code, 200)

    def test_historias(self):
        response = self.client.get(reverse('historias'))
        self.assertEqual(response.status_code, 200)

    def test_eventos(self):
        response = self.client.get(reverse('eventos'))
        self.assertEqual(response.status_code, 200)

    def test_galeria(self):
        response = self.client.get(reverse('galeria'))
        self.assertEqual(response.status_code, 200)