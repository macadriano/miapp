from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import Perfil, Rol, PermisoEntidad, PerfilUsuario


class Command(BaseCommand):
    help = 'Inicializa los datos básicos del sistema de autenticación (perfiles, roles, superusuario)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando configuración de autenticación...'))
        
        # 1. Crear Perfiles
        self.stdout.write('\n1. Creando Perfiles del Sistema...')
        perfiles_data = [
            {'nombre': 'Dashboard', 'codigo': 'dashboard', 'icono': 'bi-speedometer2', 'orden': 1},
            {'nombre': 'Móviles', 'codigo': 'moviles', 'icono': 'bi-truck', 'orden': 2},
            {'nombre': 'Equipos GPS', 'codigo': 'equipos', 'icono': 'bi-cpu', 'orden': 3},
            {'nombre': 'Personas/Conductores', 'codigo': 'personas', 'icono': 'bi-people', 'orden': 4},
            {'nombre': 'Zonas/Geocercas', 'codigo': 'zonas', 'icono': 'bi-geo-alt', 'orden': 5},
            {'nombre': 'Viajes', 'codigo': 'viajes', 'icono': 'bi-signpost', 'orden': 6},
            {'nombre': 'Reportes', 'codigo': 'reportes', 'icono': 'bi-graph-up', 'orden': 7},
            {'nombre': 'Usuarios', 'codigo': 'usuarios', 'icono': 'bi-person-gear', 'orden': 8},
            {'nombre': 'Empresas', 'codigo': 'empresas', 'icono': 'bi-building', 'orden': 9},
            {'nombre': 'Configuración', 'codigo': 'configuracion', 'icono': 'bi-gear', 'orden': 10},
        ]
        
        perfiles_creados = []
        for perfil_data in perfiles_data:
            perfil, created = Perfil.objects.get_or_create(
                codigo=perfil_data['codigo'],
                defaults=perfil_data
            )
            perfiles_creados.append(perfil)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  [OK] Perfil creado: {perfil.nombre}'))
            else:
                self.stdout.write(f'  - Perfil ya existe: {perfil.nombre}')
        
        # 2. Crear Rol de Superadministrador
        self.stdout.write('\n2. Creando Rol de Superadministrador...')
        rol_admin, created = Rol.objects.get_or_create(
            codigo='superadmin',
            defaults={
                'nombre': 'Super Administrador',
                'descripcion': 'Acceso total a todas las funcionalidades del sistema',
                'tipo_empresa': 'INTERNO',
                'es_superusuario': True,
                'puede_crear': True,
                'puede_editar': True,
                'puede_eliminar': True,
                'puede_ver_todo': True,
                'activo': True,
            }
        )
        
        if created:
            # Asignar todos los perfiles
            rol_admin.perfiles.set(perfiles_creados)
            self.stdout.write(self.style.SUCCESS(f'  [OK] Rol creado: {rol_admin.nombre}'))
        else:
            self.stdout.write(f'  - Rol ya existe: {rol_admin.nombre}')
        
        # 3. Crear permisos de entidad para Superadministrador
        self.stdout.write('\n3. Creando Permisos de Entidad...')
        entidades = ['moviles', 'equipos', 'personas', 'zonas', 'viajes', 'reportes', 'usuarios', 'empresas']
        
        for entidad in entidades:
            permiso, created = PermisoEntidad.objects.get_or_create(
                rol=rol_admin,
                entidad=entidad,
                defaults={
                    'puede_ver': True,
                    'puede_crear': True,
                    'puede_editar': True,
                    'puede_eliminar': True,
                    'puede_exportar': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  [OK] Permiso creado para: {entidad}'))
            else:
                self.stdout.write(f'  - Permiso ya existe para: {entidad}')
        
        # 4. Crear roles adicionales
        self.stdout.write('\n4. Creando Roles Adicionales...')
        
        # Rol Supervisor
        rol_supervisor, created = Rol.objects.get_or_create(
            codigo='supervisor',
            defaults={
                'nombre': 'Supervisor de Flota',
                'descripcion': 'Puede ver y gestionar móviles, viajes y reportes',
                'tipo_empresa': 'INTERNO',
                'es_superusuario': False,
                'puede_crear': True,
                'puede_editar': True,
                'puede_eliminar': False,
                'puede_ver_todo': True,
                'activo': True,
            }
        )
        
        if created:
            # Asignar perfiles específicos
            perfiles_supervisor = Perfil.objects.filter(codigo__in=['dashboard', 'moviles', 'viajes', 'reportes'])
            rol_supervisor.perfiles.set(perfiles_supervisor)
            
            # Crear permisos de entidad
            for entidad in ['moviles', 'viajes', 'reportes']:
                PermisoEntidad.objects.get_or_create(
                    rol=rol_supervisor,
                    entidad=entidad,
                    defaults={
                        'puede_ver': True,
                        'puede_crear': True,
                        'puede_editar': True,
                        'puede_eliminar': False,
                        'puede_exportar': True,
                    }
                )
            
            self.stdout.write(self.style.SUCCESS(f'  [OK] Rol creado: {rol_supervisor.nombre}'))
        else:
            self.stdout.write(f'  - Rol ya existe: {rol_supervisor.nombre}')
        
        # Rol Operador
        rol_operador, created = Rol.objects.get_or_create(
            codigo='operador',
            defaults={
                'nombre': 'Operador',
                'descripcion': 'Puede ver móviles y crear reportes básicos',
                'tipo_empresa': 'INTERNO',
                'es_superusuario': False,
                'puede_crear': False,
                'puede_editar': False,
                'puede_eliminar': False,
                'puede_ver_todo': True,
                'activo': True,
            }
        )
        
        if created:
            # Asignar perfiles específicos
            perfiles_operador = Perfil.objects.filter(codigo__in=['dashboard', 'moviles', 'reportes'])
            rol_operador.perfiles.set(perfiles_operador)
            
            # Crear permisos de entidad
            for entidad in ['moviles', 'reportes']:
                PermisoEntidad.objects.get_or_create(
                    rol=rol_operador,
                    entidad=entidad,
                    defaults={
                        'puede_ver': True,
                        'puede_crear': False,
                        'puede_editar': False,
                        'puede_eliminar': False,
                        'puede_exportar': False,
                    }
                )
            
            self.stdout.write(self.style.SUCCESS(f'  [OK] Rol creado: {rol_operador.nombre}'))
        else:
            self.stdout.write(f'  - Rol ya existe: {rol_operador.nombre}')
        
        # 5. Crear superusuario si no existe
        self.stdout.write('\n5. Verificando Superusuario...')
        
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('  No existe ningún superusuario.'))
            self.stdout.write('\n  Creando superusuario por defecto...')
            
            # Crear superusuario
            superuser = User.objects.create_superuser(
                username='admin',
                email='admin@waygps.com',
                password='admin123',  # Cambiar en producción
                first_name='Super',
                last_name='Administrador'
            )
            
            # Asignar rol de superadmin
            if hasattr(superuser, 'perfil_usuario'):
                superuser.perfil_usuario.rol = rol_admin
                superuser.perfil_usuario.save()
            
            self.stdout.write(self.style.SUCCESS('\n  [OK] Superusuario creado exitosamente!'))
            self.stdout.write(self.style.WARNING('\n  CREDENCIALES DEL SUPERUSUARIO:'))
            self.stdout.write(self.style.WARNING('  ==============================='))
            self.stdout.write(self.style.WARNING(f'  Username: admin'))
            self.stdout.write(self.style.WARNING(f'  Email:    admin@waygps.com'))
            self.stdout.write(self.style.WARNING(f'  Password: admin123'))
            self.stdout.write(self.style.WARNING('  ==============================='))
            self.stdout.write(self.style.WARNING('  [!] IMPORTANTE: Cambiar password en produccion!'))
        else:
            superusers = User.objects.filter(is_superuser=True)
            self.stdout.write(self.style.SUCCESS(f'  [OK] Ya existen {superusers.count()} superusuario(s):'))
            for su in superusers:
                self.stdout.write(f'     - {su.username} ({su.email})')
        
        # Resumen final
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('\n[OK] Inicializacion completada exitosamente!\n'))
        self.stdout.write('Resumen:')
        self.stdout.write(f'  - Perfiles creados: {Perfil.objects.count()}')
        self.stdout.write(f'  - Roles creados: {Rol.objects.count()}')
        self.stdout.write(f'  - Permisos de entidad: {PermisoEntidad.objects.count()}')
        self.stdout.write(f'  - Usuarios totales: {User.objects.count()}')
        self.stdout.write(f'  - Superusuarios: {User.objects.filter(is_superuser=True).count()}')
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('\n[OK] Sistema de autenticacion listo para usar!\n'))

