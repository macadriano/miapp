from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Rol, Perfil, PermisoEntidad, SesionUsuario, PerfilUsuario


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'icono', 'orden', 'activo']


class PermisoEntidadSerializer(serializers.ModelSerializer):
    entidad_display = serializers.CharField(source='get_entidad_display', read_only=True)
    
    class Meta:
        model = PermisoEntidad
        fields = [
            'id', 'entidad', 'entidad_display', 
            'puede_ver', 'puede_crear', 'puede_editar', 'puede_eliminar', 'puede_exportar'
        ]


class RolSerializer(serializers.ModelSerializer):
    perfiles = PerfilSerializer(many=True, read_only=True)
    permisos_entidad = PermisoEntidadSerializer(many=True, read_only=True)
    tipo_empresa_display = serializers.CharField(source='get_tipo_empresa_display', read_only=True)
    
    class Meta:
        model = Rol
        fields = [
            'id', 'nombre', 'codigo', 'descripcion', 'tipo_empresa', 'tipo_empresa_display',
            'perfiles', 'permisos_entidad', 'es_superusuario',
            'puede_crear', 'puede_editar', 'puede_eliminar', 'puede_ver_todo',
            'activo', 'created_at', 'updated_at'
        ]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    rol_info = RolSerializer(source='rol', read_only=True)
    perfiles = PerfilSerializer(source='perfiles_personalizados', many=True, read_only=True)
    
    class Meta:
        model = PerfilUsuario
        fields = [
            'id', 'telefono', 'documento', 'rol', 'rol_info', 'perfiles',
            'empresa', 'two_factor_enabled', 'created_at', 'updated_at'
        ]


class UsuarioSerializer(serializers.ModelSerializer):
    perfil_info = PerfilUsuarioSerializer(source='perfil_usuario', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'nombre_completo',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login',
            'perfil_info'
        ]
        read_only_fields = ['date_joined', 'last_login']
    
    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios con password"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    rol_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'rol_id', 'is_active'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        rol_id = validated_data.pop('rol_id', None)
        
        user = User.objects.create_user(password=password, **validated_data)
        
        # Asignar rol si se proporcionó
        if rol_id:
            try:
                rol = Rol.objects.get(id=rol_id)
                user.perfil_usuario.rol = rol
                user.perfil_usuario.save()
            except Rol.DoesNotExist:
                pass
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField()  # Puede ser username o email
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Intentar autenticar por username o email
            usuario = None
            
            # Intentar primero como username
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            # Si no funciona, intentar como email
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(
                        request=self.context.get('request'),
                        username=user_obj.username,
                        password=password
                    )
                except User.DoesNotExist:
                    pass
            
            if not user:
                # Registrar intento fallido si el usuario existe
                try:
                    user_check = User.objects.get(username=username)
                    if hasattr(user_check, 'perfil_usuario'):
                        user_check.perfil_usuario.registrar_intento_fallido()
                except User.DoesNotExist:
                    try:
                        user_check = User.objects.get(email=username)
                        if hasattr(user_check, 'perfil_usuario'):
                            user_check.perfil_usuario.registrar_intento_fallido()
                    except User.DoesNotExist:
                        pass
                
                raise serializers.ValidationError('Credenciales inválidas')
            
            # Verificar si está bloqueado
            if hasattr(user, 'perfil_usuario') and user.perfil_usuario.esta_bloqueado():
                raise serializers.ValidationError(
                    'Usuario bloqueado temporalmente por múltiples intentos fallidos. '
                    'Intente nuevamente más tarde.'
                )
            
            # Verificar si está activo
            if not user.is_active:
                raise serializers.ValidationError('Esta cuenta está desactivada')
            
            attrs['usuario'] = user
        else:
            raise serializers.ValidationError('Debe proporcionar username/email y contraseña')
        
        return attrs


class CambiarPasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña"""
    password_actual = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_nueva = serializers.CharField(write_only=True, style={'input_type': 'password'}, min_length=8)
    password_nueva_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['password_nueva'] != attrs['password_nueva_confirm']:
            raise serializers.ValidationError({"password_nueva": "Las contraseñas no coinciden"})
        
        return attrs


class PermisosUsuarioSerializer(serializers.Serializer):
    """Serializer para obtener perfiles y permisos del usuario actual"""
    perfiles = serializers.SerializerMethodField()
    rol = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()
    
    def get_perfiles(self, user):
        if hasattr(user, 'perfil_usuario') and user.perfil_usuario.rol:
            perfiles = user.perfil_usuario.rol.perfiles.filter(activo=True)
            perfiles_personalizados = user.perfil_usuario.perfiles_personalizados.filter(activo=True)
            todos_perfiles = list(perfiles) + list(perfiles_personalizados)
            return PerfilSerializer(todos_perfiles, many=True).data
        return []
    
    def get_rol(self, user):
        if hasattr(user, 'perfil_usuario') and user.perfil_usuario.rol:
            return RolSerializer(user.perfil_usuario.rol).data
        return None
    
    def get_permisos(self, user):
        """Retorna un diccionario con todos los permisos del usuario"""
        if user.is_superuser or (hasattr(user, 'perfil_usuario') and user.perfil_usuario.rol and user.perfil_usuario.rol.es_superusuario):
            # Superusuario tiene todos los permisos
            return {
                'es_superusuario': True,
                'entidades': {
                    'moviles': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                    'equipos': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                    'personas': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                    'zonas': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                    'viajes': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                    'reportes': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                    'usuarios': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                    'empresas': {'ver': True, 'crear': True, 'editar': True, 'eliminar': True, 'exportar': True},
                }
            }
        
        permisos = {
            'es_superusuario': False,
            'entidades': {}
        }
        
        if hasattr(user, 'perfil_usuario') and user.perfil_usuario.rol:
            for permiso in user.perfil_usuario.rol.permisos_entidad.all():
                permisos['entidades'][permiso.entidad] = {
                    'ver': permiso.puede_ver,
                    'crear': permiso.puede_crear,
                    'editar': permiso.puede_editar,
                    'eliminar': permiso.puede_eliminar,
                    'exportar': permiso.puede_exportar,
                }
        
        return permisos
