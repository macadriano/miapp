from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import Rol, Perfil, PermisoEntidad, SesionUsuario, PerfilUsuario
from .serializers import (
    UsuarioSerializer, UsuarioCreateSerializer, LoginSerializer,
    RolSerializer, PerfilSerializer, PermisoEntidadSerializer,
    CambiarPasswordSerializer, PermisosUsuarioSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Vista de login
    POST /api/auth/login/
    Body: { "username": "user@example.com", "password": "password123" }
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        usuario = serializer.validated_data['usuario']
        
        # Asegurar que el usuario tenga PerfilUsuario
        from .models import PerfilUsuario
        if not hasattr(usuario, 'perfil_usuario'):
            PerfilUsuario.objects.create(user=usuario)
        
        # Resetear intentos fallidos
        if hasattr(usuario, 'perfil_usuario'):
            usuario.perfil_usuario.resetear_intentos_fallidos()
            usuario.perfil_usuario.ultima_ip = get_client_ip(request)
            usuario.perfil_usuario.save()
        
        # Crear o obtener token
        token, created = Token.objects.get_or_create(user=usuario)
        
        # Crear o actualizar sesión (evita error de duplicado)
        sesion, sesion_created = SesionUsuario.objects.update_or_create(
            token=token.key,
            defaults={
                'user': usuario,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'activa': True,
                'fecha_fin': None,
            }
        )
        
        # Si no es nueva, actualizar fecha_ultimo_acceso
        if not sesion_created:
            sesion.save()  # Esto actualizará fecha_ultimo_acceso (auto_now=True)
        
        # Login de Django (para sesiones web)
        login(request, usuario)
        
        # Obtener perfiles y permisos
        permisos_serializer = PermisosUsuarioSerializer(usuario)
        
        # Preparar respuesta
        response_data = {
            'token': token.key,
            'usuario': UsuarioSerializer(usuario).data,
            'perfiles': permisos_serializer.data.get('perfiles', []),
            'permisos': permisos_serializer.data.get('permisos', {}),
            'mensaje': 'Login exitoso'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Vista de logout
    POST /api/auth/logout/
    Headers: Authorization: Token <token>
    """
    try:
        # Cerrar sesión activa
        if hasattr(request.user, 'auth_token'):
            sesiones = SesionUsuario.objects.filter(
                user=request.user,
                token=request.user.auth_token.key,
                activa=True
            )
            sesiones.update(activa=False, fecha_fin=timezone.now())
            
            # Eliminar token
            request.user.auth_token.delete()
        
        # Logout de Django
        logout(request)
        
        return Response({'mensaje': 'Logout exitoso'}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_actual(request):
    """
    Obtiene el perfil del usuario actual
    GET /api/auth/me/
    """
    serializer = UsuarioSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permisos_usuario(request):
    """
    Obtiene los permisos completos del usuario actual
    GET /api/auth/permisos/
    """
    serializer = PermisosUsuarioSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    """
    Cambia la contraseña del usuario actual
    POST /api/auth/cambiar-password/
    Body: { 
        "password_actual": "old_password",
        "password_nueva": "new_password",
        "password_nueva_confirm": "new_password"
    }
    """
    serializer = CambiarPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        usuario = request.user
        
        # Verificar password actual
        if not usuario.check_password(serializer.validated_data['password_actual']):
            return Response(
                {'error': 'La contraseña actual es incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Establecer nueva contraseña
        usuario.set_password(serializer.validated_data['password_nueva'])
        usuario.save()
        
        # Invalidar todas las sesiones anteriores
        SesionUsuario.objects.filter(user=usuario, activa=True).update(
            activa=False,
            fecha_fin=timezone.now()
        )
        
        # Crear nuevo token
        Token.objects.filter(user=usuario).delete()
        nuevo_token = Token.objects.create(user=usuario)
        
        return Response({
            'mensaje': 'Contraseña cambiada exitosamente',
            'token': nuevo_token.key
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ViewSets para administración
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        return UsuarioSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Superusuario ve todos
        if user.is_superuser:
            return User.objects.all()
        
        # Usuarios con rol de superusuario ven todos
        if hasattr(user, 'perfil_usuario') and user.perfil_usuario.rol and user.perfil_usuario.rol.es_superusuario:
            return User.objects.all()
        
        # Otros usuarios solo ven su propio perfil
        return User.objects.filter(id=user.id)


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]


class PerfilViewSet(viewsets.ModelViewSet):
    queryset = Perfil.objects.filter(activo=True)
    serializer_class = PerfilSerializer
    permission_classes = [IsAuthenticated]


class PermisoEntidadViewSet(viewsets.ModelViewSet):
    queryset = PermisoEntidad.objects.all()
    serializer_class = PermisoEntidadSerializer
    permission_classes = [IsAuthenticated]


# Vista para servir el frontend de login
def login_frontend(request):
    """Renderiza la página de login.

    - Si viene ?logout=1, fuerza el cierre de sesión de Django y muestra siempre
      el formulario de login (sin redirigir al dashboard).
    - Si el usuario ya está autenticado y NO viene logout, redirige al dashboard
      o a la URL indicada en ?next=.
    """
    next_url = request.GET.get('next')

    # Forzar logout explícito desde el frontend
    if request.GET.get('logout') == '1':
        logout(request)
        return render(request, 'authentication/login.html', {'next': next_url})

    # Usuario ya autenticado: redirigir a destino
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        if next_url:
            return redirect(next_url)
        return redirect('moviles_dashboard')

    # Usuario anónimo: mostrar formulario de login
    return render(request, 'authentication/login.html', {'next': next_url})


# Función helper para obtener IP del cliente
def get_client_ip(request):
    """Obtiene la IP real del cliente considerando proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
