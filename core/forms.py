from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import (
    Perfil, ProyectoEstudiante, MensajeContacto, Comentario,
    GRADO_OPCIONES, NIVEL_OPCIONES, INTERES_OPCIONES, TIPO_PROGRAMADOR,
    MensajeChat, MensajePrivado, Pregunta, Respuesta
)


class RegistroForm(UserCreationForm):
    username = forms.CharField(
        label='Usuario',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Elige un nombre de usuario'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu-email@ejemplo.com'})
    )
    grado = forms.ChoiceField(
        label='Grado',
        choices=GRADO_OPCIONES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    edad = forms.IntegerField(
        label='Edad',
        min_value=14,
        max_value=19,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '14-19 años'})
    )
    nivel_programacion = forms.ChoiceField(
        label='Nivel de programación',
        choices=NIVEL_OPCIONES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    intereses = forms.MultipleChoiceField(
        label='¿Qué te interesa?',
        choices=INTERES_OPCIONES,
        widget=forms.CheckboxSelectMultiple()
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la contraseña'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'grado', 'edad', 'nivel_programacion', 'intereses', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ya está registrado.')
        return email

    def clean_grado(self):
        grado = self.cleaned_data.get('grado')
        if grado not in ['10mo', '11ro', '12mo']:
            raise forms.ValidationError('Este sitio es solo para estudiantes de 10mo a 12mo grado.')
        return grado

    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if edad < 14 or edad > 19:
            raise forms.ValidationError('La edad debe estar entre 14 y 19 años.')
        return edad

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = True  # El usuario puede existir pero el perfil no estará confirmado
        if commit:
            user.save()
            perfil = Perfil(
                usuario=user,
                grado=self.cleaned_data['grado'],
                edad=self.cleaned_data['edad'],
                nivel_programacion=self.cleaned_data['nivel_programacion'],
                intereses=self.cleaned_data['intereses'],
                email_confirmado=False  # ✅ No confirmado por defecto
            )
            perfil.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu usuario'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Tu contraseña'})
    )


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['grado', 'edad', 'nivel_programacion', 'foto_perfil', 'bio']
        widgets = {
            'grado': forms.Select(attrs={'class': 'form-control'}),
            'edad': forms.NumberInput(attrs={'class': 'form-control'}),
            'nivel_programacion': forms.Select(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Cuéntanos sobre ti...', 'maxlength': 300}),
        }


class ProyectoEstudianteForm(forms.ModelForm):
    class Meta:
        model = ProyectoEstudiante
        fields = [
            'titulo',
            'descripcion',
            'descripcion_larga',
            'imagen',
            'archivo',
            'enlace_externo',
            'categoria',
            'herramientas'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Mi primer juego en Scratch'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe brevemente tu proyecto...'
            }),
            'descripcion_larga': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Explica cómo lo hiciste, qué aprendiste, etc. (opcional)'
            }),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'enlace_externo': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/tu-usuario/tu-proyecto (opcional)'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'herramientas': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Scratch, Python, HTML/CSS'
            }),
        }
        labels = {
            'titulo': 'Título del proyecto',
            'descripcion': 'Descripción corta',
            'descripcion_larga': 'Descripción detallada (opcional)',
            'imagen': 'Imagen de portada',
            'archivo': 'Archivo del proyecto (ZIP, PDF, código, etc.)',
            'enlace_externo': 'Enlace externo (GitHub, YouTube, etc.)',
            'categoria': 'Categoría',
            'herramientas': 'Herramientas usadas',
        }


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe tu comentario...', 'class': 'form-control'})
        }


class MensajeContactoForm(forms.ModelForm):
    class Meta:
        model = MensajeContacto
        fields = ['nombre', 'email', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class MensajeChatForm(forms.ModelForm):
    class Meta:
        model = MensajeChat
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Escribe tu mensaje...', 'maxlength': 500})
        }


class MensajePrivadoForm(forms.ModelForm):
    class Meta:
        model = MensajePrivado
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Escribe un mensaje privado...', 'maxlength': 1000})
        }


class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ['titulo', 'contenido']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '¿Cuál es tu pregunta?'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe tu pregunta con detalle...'}),
        }


class RespuestaForm(forms.ModelForm):
    class Meta:
        model = Respuesta
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe tu respuesta...'}),
        }


# ==================== CAMBIO DE CONTRASEÑA (recordando la actual) ====================
class CambiarPasswordForm(PasswordChangeForm):
    """Formulario para cambiar contraseña desde el perfil (requiere contraseña actual)"""
    old_password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Tu contraseña actual'})
    )
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'})
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la nueva contraseña'})
    )


# ==================== RECUPERAR CONTRASEÑA (olvidó la actual) ====================
class RecuperarPasswordForm(PasswordResetForm):
    """Formulario para enviar email de recuperación"""
    email = forms.EmailField(
        label='Correo electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu-email@ejemplo.com',
            'autocomplete': 'email'
        })
    )


# ==================== NUEVA CONTRASEÑA (desde el enlace del email) ====================
class NuevaPasswordForm(SetPasswordForm):
    """Formulario para poner nueva contraseña desde el enlace del email"""
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'})
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la nueva contraseña'})
    )