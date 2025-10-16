# apps/core/management/commands/setup_inicial.py
"""
Comando personalizado para configurar el sistema inicial
Uso: python manage.py setup_inicial
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.usuarios.models import Cliente
from apps.inventario.models import Categoria, Producto
from apps.core.models import ConfiguracionSistema
from decimal import Decimal

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Configura datos iniciales del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Carga datos de demostración',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando configuración...'))

        # 1. Crear superusuario si no existe
        if not Usuario.objects.filter(is_superuser=True).exists():
            self.stdout.write('👤 Creando superusuario...')
            Usuario.objects.create_superuser(
                username='admin',
                email='admin@cotizador.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            self.stdout.write(self.style.SUCCESS('✅ Superusuario creado'))

        # 2. Configuraciones del sistema
        self.stdout.write('⚙️  Configurando sistema...')
        configs = [
            ('nombre_empresa', 'Mi Empresa S.A.'),
            ('rut_empresa', '12.345.678-9'),
            ('direccion_empresa', 'Av. Principal 123, Santiago'),
            ('telefono_empresa', '+56 9 1234 5678'),
            ('email_empresa', 'contacto@miempresa.com'),
            ('tasa_iva', '19'),
            ('moneda', 'CLP'),
            ('dias_validez_cotizacion', '30'),
        ]
        
        for nombre, valor in configs:
            ConfiguracionSistema.objects.get_or_create(
                nombre=nombre,
                defaults={'valor': valor}
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Configuraciones creadas'))

        # 3. Datos demo (opcional)
        if options['demo']:
            self.stdout.write('📦 Cargando datos de demostración...')
            self.cargar_datos_demo()

        self.stdout.write(self.style.SUCCESS('\n✨ ¡Configuración completada exitosamente!'))
        self.stdout.write(self.style.WARNING('\n📝 Usuario: admin | Contraseña: admin123'))

    def cargar_datos_demo(self):
        # Clientes
        clientes_data = [
            {'nombre': 'Empresa ABC Ltda.', 'email': 'contacto@abc.cl'},
            {'nombre': 'Comercial XYZ S.A.', 'email': 'ventas@xyz.cl'},
            {'nombre': 'Industrias DEF', 'email': 'info@def.cl'},
        ]
        
        for data in clientes_data:
            Cliente.objects.get_or_create(nombre=data['nombre'], defaults=data)
        
        self.stdout.write('  ✓ Clientes creados')

        # Categorías
        categorias_data = [
            {'nombre': 'Electrónica', 'descripcion': 'Productos electrónicos'},
            {'nombre': 'Oficina', 'descripcion': 'Artículos de oficina'},
            {'nombre': 'Hardware', 'descripcion': 'Hardware computacional'},
            {'nombre': 'Software', 'descripcion': 'Licencias de software'},
        ]
        
        for data in categorias_data:
            Categoria.objects.get_or_create(nombre=data['nombre'], defaults=data)
        
        self.stdout.write('  ✓ Categorías creadas')

        # Productos
        productos_data = [
            {
                'nombre': 'Laptop HP 15"',
                'categoria': 'Hardware',
                'descripcion': 'Laptop HP 15 pulgadas, Intel Core i5, 8GB RAM',
                'precio': Decimal('549990'),
                'stock': 25,
                'stock_minimo': 5
            },
            {
                'nombre': 'Mouse Logitech MX Master',
                'categoria': 'Hardware',
                'descripcion': 'Mouse inalámbrico de alta precisión',
                'precio': Decimal('79990'),
                'stock': 50,
                'stock_minimo': 10
            },
            {
                'nombre': 'Teclado Mecánico RGB',
                'categoria': 'Hardware',
                'descripcion': 'Teclado mecánico retroiluminado RGB',
                'precio': Decimal('89990'),
                'stock': 30,
                'stock_minimo': 8
            },
            {
                'nombre': 'Monitor 27" Full HD',
                'categoria': 'Electrónica',
                'descripcion': 'Monitor LED 27 pulgadas Full HD',
                'precio': Decimal('199990'),
                'stock': 15,
                'stock_minimo': 3
            },
            {
                'nombre': 'Licencia Office 365',
                'categoria': 'Software',
                'descripcion': 'Licencia anual Office 365 Business',
                'precio': Decimal('89990'),
                'stock': 100,
                'stock_minimo': 20
            },
        ]
        
        for data in productos_data:
            categoria = Categoria.objects.get(nombre=data['categoria'])
            data_producto = data.copy()
            del data_producto['categoria']
            
            Producto.objects.get_or_create(
                nombre=data['nombre'],
                defaults={**data_producto, 'categoria': categoria}
            )
        
        self.stdout.write('  ✓ Productos creados')


# apps/core/management/commands/generar_reportes.py
"""
Comando para generar reportes programados
Uso: python manage.py generar_reportes --tipo mensual
"""

from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from apps.cotizaciones.models import Cotizacion
from datetime import timedelta
import openpyxl

class Command(BaseCommand):
    help = 'Genera y envía reportes automáticos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            default='semanal',
            choices=['diario', 'semanal', 'mensual'],
            help='Tipo de reporte a generar'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email de destino (opcional)'
        )

    def handle(self, *args, **options):
        tipo = options['tipo']
        self.stdout.write(f'📊 Generando reporte {tipo}...')

        # Calcular rango de fechas
        hoy = timezone.now().date()
        if tipo == 'diario':
            fecha_desde = hoy
        elif tipo == 'semanal':
            fecha_desde = hoy - timedelta(days=7)
        else:  # mensual
            fecha_desde = hoy - timedelta(days=30)

        # Obtener datos
        cotizaciones = Cotizacion.objects.filter(
            fecha_creacion__date__gte=fecha_desde
        )

        # Generar Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Reporte {tipo}"

        # Headers
        ws.append([
            'Número', 'Cliente', 'Fecha', 'Estado', 
            'Subtotal', 'IVA', 'Total'
        ])

        # Datos
        total_general = 0
        for cot in cotizaciones:
            ws.append([
                cot.numero_cotizacion,
                cot.cliente.nombre,
                cot.fecha_creacion.strftime('%Y-%m-%d'),
                cot.get_estado_display(),
                float(cot.subtotal),
                float(cot.impuesto),
                float(cot.total)
            ])
            if cot.estado == 'APROBADA':
                total_general += float(cot.total)

        # Guardar archivo
        filename = f'reporte_{tipo}_{hoy.strftime("%Y%m%d")}.xlsx'
        wb.save(f'/tmp/{filename}')

        # Enviar email
        email_destino = options.get('email') or 'admin@cotizador.com'
        
        mensaje = f"""
        Reporte {tipo} generado exitosamente
        
        Período: {fecha_desde} - {hoy}
        Total cotizaciones: {cotizaciones.count()}
        Total facturado: ${total_general:,.0f}
        """

        email = EmailMessage(
            f'Reporte {tipo} - Cotizaciones',
            mensaje,
            to=[email_destino]
        )
        email.attach_file(f'/tmp/{filename}')
        email.send()

        self.stdout.write(self.style.SUCCESS(f'✅ Reporte enviado a {email_destino}'))


# apps/core/management/commands/limpiar_datos.py
"""
Comando para limpieza de datos antiguos
Uso: python manage.py limpiar_datos --dias 90
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.cotizaciones.models import Cotizacion
from apps.core.models import Auditoria
from datetime import timedelta

class Command(BaseCommand):
    help = 'Limpia datos antiguos del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=90,
            help='Días de antigüedad para eliminar'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la ejecución sin eliminar'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']

        self.stdout.write(f'🧹 Limpiando datos con más de {dias} días...')

        fecha_limite = timezone.now() - timedelta(days=dias)

        # Cotizaciones rechazadas antiguas
        cotizaciones_antiguas = Cotizacion.objects.filter(
            estado='RECHAZADA',
            fecha_creacion__lt=fecha_limite
        )
        
        count_cot = cotizaciones_antiguas.count()

        # Logs de auditoría antiguos
        logs_antiguos = Auditoria.objects.filter(
            fecha__lt=fecha_limite
        )
        
        count_logs = logs_antiguos.count()

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO SIMULACIÓN:'))
            self.stdout.write(f'  - Se eliminarían {count_cot} cotizaciones')
            self.stdout.write(f'  - Se eliminarían {count_logs} logs')
        else:
            cotizaciones_antiguas.delete()
            logs_antiguos.delete()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Eliminadas {count_cot} cotizaciones'))
            self.stdout.write(self.style.SUCCESS(f'✅ Eliminados {count_logs} logs'))


# apps/core/management/commands/backup_db.py
"""
Comando para backup de base de datos
Uso: python manage.py backup_db
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Realiza backup de la base de datos PostgreSQL'

    def handle(self, *args, **options):
        self.stdout.write('💾 Iniciando backup de base de datos...')

        # Configuración
        db_config = settings.DATABASES['default']
        backup_dir = '/var/backups/cotizador'
        
        # Crear directorio si no existe
        os.makedirs(backup_dir, exist_ok=True)

        # Nombre del archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)

        # Comando pg_dump
        comando = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-p', db_config['PORT'],
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '-F', 'c',  # Formato custom
            '-f', filepath
        ]

        # Ejecutar backup
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            subprocess.run(comando, check=True, env=env)
            
            # Comprimir (opcional)
            subprocess.run(['gzip', filepath], check=True)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Backup creado: {filepath}.gz'))
            
            # Limpiar backups antiguos (mantener últimos 7)
            self.limpiar_backups_antiguos(backup_dir)
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Error en backup: {e}'))

    def limpiar_backups_antiguos(self, backup_dir):
        """Mantiene solo los últimos 7 backups"""
        archivos = sorted([
            os.path.join(backup_dir, f) 
            for f in os.listdir(backup_dir) 
            if f.startswith('backup_')
        ])
        
        # Eliminar los más antiguos
        for archivo in archivos[:-7]:
            os.remove(archivo)
            self.stdout.write(f'  🗑️  Eliminado: {os.path.basename(archivo)}')