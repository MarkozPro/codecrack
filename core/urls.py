from django.urls import path
from . import views

urlpatterns = [
    # Públicas
    path('', views.home, name='home'),
    path('acerca-de/', views.acerca_de, name='acerca_de'),
    path('que-es-programar/', views.que_es_programar, name='que_es_programar'),
    path('historias/', views.historias, name='historias'),
    path('historias/<int:historia_id>/', views.historia_detalle, name='historia_detalle'),
    path('proyectos/', views.proyectos, name='proyectos'),
    path('proyectos/<int:proyecto_id>/', views.proyecto_detalle, name='proyecto_detalle'),
    path('recursos/', views.recursos, name='recursos'),
    path('galeria/', views.galeria, name='galeria'),
    path('galeria/<int:proyecto_id>/', views.proyecto_estudiante_detalle, name='proyecto_estudiante_detalle'),
    path('galeria/<int:proyecto_id>/descargar/', views.descargar_proyecto, name='descargar_proyecto'),
    path('eventos/', views.eventos, name='eventos'),
    path('contacto/', views.contacto, name='contacto'),

    # Autenticación
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ✅ Confirmación por código
    path('confirmar-codigo/', views.confirmar_codigo, name='confirmar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo, name='reenviar_codigo'),

    # ✅ Cambiar contraseña (recordando la actual)
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),

    # ✅ Recuperar contraseña (por código)
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('ingresar-codigo-recuperacion/', views.ingresar_codigo_recuperacion, name='ingresar_codigo_recuperacion'),
    path('nueva-password/', views.nueva_password, name='nueva_password'),

    # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('usuario/<str:username>/', views.perfil_publico, name='perfil_publico'),
    path('usuario/<str:username>/seguir/', views.seguir_usuario, name='seguir_usuario'),
    path('usuario/<str:username>/seguidores/', views.lista_seguidores, name='lista_seguidores'),
    path('usuario/<str:username>/siguiendo/', views.lista_siguiendo, name='lista_siguiendo'),
    path('progreso/', views.progreso, name='progreso'),

    # Test
    path('test-vocacional/', views.test_vocacional, name='test_vocacional'),

    # Proyectos
    path('subir-proyecto/', views.subir_proyecto, name='subir_proyecto'),
    path('like/<int:proyecto_id>/', views.like_proyecto, name='like_proyecto'),
    path('completar/<int:proyecto_id>/', views.completar_proyecto, name='completar_proyecto'),
    path('favorito/<int:proyecto_id>/', views.toggle_favorito, name='toggle_favorito'),
    path('comentar/proyecto/<int:proyecto_id>/', views.comentar, name='comentar_proyecto'),
    path('comentar/historia/<int:historia_id>/', views.comentar, name='comentar_historia'),
    path('evento/<int:evento_id>/inscribir/', views.inscribir_evento, name='inscribir_evento'),

    # Chat público
    path('chat/', views.chat, name='chat'),

    # Ranking
    path('ranking/', views.ranking, name='ranking'),

    # Desafíos
    path('desafios/', views.desafios, name='desafios'),

    # Notificaciones
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('notificaciones/<int:notif_id>/leer/', views.marcar_leida, name='marcar_leida'),

    # Mensajes privados
    path('mensajes/', views.bandeja_entrada, name='bandeja_entrada'),
    path('mensajes/<str:username>/', views.conversacion, name='conversacion'),

    # Foro
    path('foro/', views.foro, name='foro'),
    path('foro/nueva/', views.nueva_pregunta, name='nueva_pregunta'),
    path('foro/<int:pregunta_id>/', views.pregunta_detalle, name='pregunta_detalle'),
    path('foro/respuesta/<int:respuesta_id>/votar/', views.votar_respuesta, name='votar_respuesta'),
    path('foro/respuesta/<int:respuesta_id>/correcta/', views.marcar_correcta, name='marcar_correcta'),

    # Dashboard Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]