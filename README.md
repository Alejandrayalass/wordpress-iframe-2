# wordpress-iframe-2
# 🚀 Sistema de Cotizaciones Intranet

Sistema completo de gestión de cotizaciones con integración de pagos, generación de PDF, y API REST para integración con sistemas PHP.

## 📋 Características Principales

### ✅ Gestión de Cotizaciones
- CRUD completo de cotizaciones
- Sistema de items con productos
- Cálculo automático de totales e IVA (19%)
- Estados: Pendiente, Aprobada, Rechazada, Enviada
- Duplicación de cotizaciones
- Búsqueda y filtros avanzados

### 📄 Generación de PDF
- PDFs profesionales con ReportLab
- Logo personalizado
- Tablas de items detalladas
- Totales y subtotales
- Descarga y almacenamiento automático

### 💳 Sistema de Pagos
- **One-Click Payment**: Pago con un clic usando tarjetas guardadas
- Tokenización segura (NO se guardan datos de tarjeta)
- Integración con Transbank (Chile)
- Webpay Plus
- Historial de transacciones
- Sistema de reembolsos

### 🔌 API REST para PHP
- Endpoints seguros con firma HMAC
- Crear cotizaciones desde PHP
- Consultar productos
- Actualizar stock
- Cliente PHP de ejemplo incluido

### 📊 Reportes y Estadísticas
- Dashboard con métricas
- Exportación a Excel
- Gráficos de ventas
- Top clientes
- Análisis por estado

### 🔐 Seguridad
- Autenticación robusta
- Tokens para API
- Firma HMAC para validación
- CSRF protection
- SQL injection protection

---

## 🛠️ Instalación

### 1. Requisitos Previos
```bash
# Python 3.10+
python --version

# PostgreSQL 13+
psql --version

# Redis (opcional, para Celery)
redis-cli --version
```

### 2. Clonar y Configurar Entorno
```bash
# Clonar repositorio
git clone <url-repositorio>
cd cotizador_intranet

# Crear entorno virtual
python -m venv venv

# Activar entorno
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Base de Datos
```bash
# Crear base de datos PostgreSQL
psql -U postgres
CREATE DATABASE cotizador_db;
CREATE USER cotizador_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE cotizador_db TO cotizador_user;
\q
```

### 4. Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
nano .env
```

### 5. Migraciones
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### 6. Archivos Estáticos
```bash
# Recolectar archivos estáticos
python manage.py collectstatic --no-input
```

### 7. Ejecutar Servidor
```bash
# Desarrollo
python manage.py runserver

# Producción con Gunicorn
gunicorn cotizador_intranet.wsgi:application --bind 0.0.0.0:8000
```

---

## 📁 Estructura del Proyecto

```
cotizador_intranet/
├── apps/
│   ├── core/              # Configuraciones y auditoría
│   ├── usuarios/          # Gestión de usuarios y clientes
│   ├── cotizaciones/      # Sistema de cotizaciones
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── services.py
│   │   ├── pdf_generator.py
│   │   └── urls.py
│   ├── inventario/        # Productos y categorías
│   ├── pagos/             # Sistema de pagos
│   │   ├── models.py      # Tarjetas y transacciones
│   │   ├── services.py    # OneClickPaymentService
│   │   ├── views.py
│   │   └── urls.py
│   └── api/               # API REST para PHP
│       ├── views.py       # Endpoints
│       └── urls.py
├── static/                # CSS, JS, imágenes
├── media/                 # Archivos subidos (PDFs, etc.)
├── templates/             # Templates HTML
├── cotizador_intranet/    # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Configuración de Pagos

### Transbank (Chile)

1. Obtener credenciales en [Transbank Developers](https://www.transbankdevelopers.cl/)

2. Configurar en `.env`:
```bash
TRANSBANK_ENVIRONMENT=desarrollo  # o produccion
TRANSBANK_COMMERCE_CODE=tu_codigo
TRANSBANK_API_KEY=tu_api_key
```

3. Implementación One-Click:
```python
from apps.pagos.services import OneClickPaymentService

service = OneClickPaymentService()

# Registrar tarjeta
resultado = service.registrar_tarjeta(cliente, {
    'numero': '4111111111111111',
    'nombre': 'Juan Pérez',
    'expiracion': '12/2025',
    'cvv': '123'
})

# Procesar pago
resultado = service.procesar_pago_oneclick(cotizacion, tarjeta)
```

---

## 🌐 Integración con PHP

### Configuración

1. Generar API Key y Secret en Django Admin

2. En tu sistema PHP:
```php
<?php
require_once 'DjangoAPIClient.php';

$api = new DjangoAPIClient(
    'https://tu-servidor.com',
    'tu_api_key',
    'tu_secret_key'
);

// Crear cotización
$resultado = $api->crearCotizacion(
    1, // cliente_id
    '2025-12-31',
    [
        ['producto_id' => 1, 'cantidad' => 2, 'precio_unitario' => 10000],
        ['producto_id' => 2, 'cantidad' => 1, 'precio_unitario' => 25000]
    ],
    'Cotización desde PHP'
);

echo $resultado['data']['numero_cotizacion'];
?>
```

### Endpoints Disponibles

```
POST   /api/php/cotizacion/crear/           # Crear cotización
GET    /api/php/cotizacion/{id}/            # Obtener cotización
GET    /api/php/productos/                  # Listar productos
POST   /api/php/stock/actualizar/           # Actualizar stock
```

---

## 📊 Uso del Sistema

### Crear Cotización

1. Navegar a **Cotizaciones > Crear Nueva**
2. Seleccionar cliente y fecha de vencimiento
3. Agregar productos con cantidades y precios
4. Sistema calcula automáticamente subtotal, IVA y total
5. Guardar cotización

### Generar PDF

```python
from apps.cotizaciones.pdf_generator import CotizacionPDFGenerator

# Generar y guardar PDF
cotizacion = Cotizacion.objects.get(id=1)
generator = CotizacionPDFGenerator(cotizacion)
url_pdf = generator.save_to_model()

# O descargar directamente
pdf_buffer = generator.generate()
```

### Procesar Pago One-Click

1. Cliente guarda su tarjeta (tokenización segura)
2. En futuras compras, selecciona tarjeta guardada
3. Pago se procesa con un solo clic
4. Transacción se registra automáticamente

### Enviar Cotización por Email

```python
# Desde la vista de detalle
# Click en "Enviar Email"
# Sistema genera PDF y lo adjunta
# Email se envía al cliente automáticamente
```

---

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test apps.cotizaciones

# Con coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Genera reporte HTML
```

### Crear Tests
```python
# apps/cotizaciones/tests.py
from django.test import TestCase
from .models import Cotizacion

class CotizacionTestCase(TestCase):
    def test_crear_cotizacion(self):
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            fecha_vencimiento='2025-12-31'
        )
        self.assertIsNotNone(cotizacion.numero_cotizacion)
```

---

## 📦 Despliegue en Producción

### 1. Preparar Entorno

```bash
# Instalar dependencias de producción
pip install -r requirements.txt

# Variables de entorno
export DEBUG=False
export SECRET_KEY=tu-secret-key-segura
export ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# Base de datos
export DB_HOST=tu-servidor-db
export DB_PASSWORD=password-seguro
```

### 2. Recolectar Estáticos
```bash
python manage.py collectstatic --no-input
```

### 3. Migraciones
```bash
python manage.py migrate
```

### 4. Con Gunicorn
```bash
# Instalar
pip install gunicorn

# Ejecutar
gunicorn cotizador_intranet.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

### 5. Con Nginx (Recomendado)

```nginx
# /etc/nginx/sites-available/cotizador
server {
    listen 80;
    server_name tudominio.com;

    location /static/ {
        alias /ruta/al/proyecto/staticfiles/;
    }

    location /media/ {
        alias /ruta/al/proyecto/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. Systemd Service

```ini
# /etc/systemd/system/cotizador.service
[Unit]
Description=Cotizador Intranet
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/ruta/al/proyecto
Environment="PATH=/ruta/al/venv/bin"
ExecStart=/ruta/al/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/tmp/cotizador.sock \
    cotizador_intranet.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Activar servicio
sudo systemctl enable cotizador
sudo systemctl start cotizador
sudo systemctl status cotizador
```

---

## 🔄 Tareas Asíncronas con Celery (Opcional)

### Configurar Celery

```python
# cotizador_intranet/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizador_intranet.settings')

app = Celery('cotizador_intranet')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### Crear Tarea
```python
# apps/cotizaciones/tasks.py
from celery import shared_task
from .models import Cotizacion
from .pdf_generator import CotizacionPDFGenerator

@shared_task
def generar_pdf_async(cotizacion_id):
    """Genera PDF de forma asíncrona"""
    cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    generator = CotizacionPDFGenerator(cotizacion)
    generator.save_to_model()
    return f"PDF generado para {cotizacion.numero_cotizacion}"

@shared_task
def enviar_recordatorios_vencimiento():
    """Envía recordatorios de cotizaciones próximas a vencer"""
    from datetime import datetime, timedelta
    
    manana = datetime.now().date() + timedelta(days=1)
    cotizaciones = Cotizacion.objects.filter(
        fecha_vencimiento=manana,
        estado='PENDIENTE'
    )
    
    for cot in cotizaciones:
        # Enviar email de recordatorio
        pass
```

### Ejecutar Celery
```bash
# Worker
celery -A cotizador_intranet worker -l info

# Beat (tareas programadas)
celery -A cotizador_intranet beat -l info

# Flower (monitoreo)
celery -A cotizador_intranet flower
```

---

## 📊 Monitoreo y Logs

### Configurar Sentry

```python
# settings.py ya tiene la configuración

# En .env
SENTRY_DSN=https://tu-sentry-dsn@sentry.io/proyecto
```

### Ver Logs
```bash
# Logs de Django
tail -f logs/django.log

# Logs de Gunicorn
journalctl -u cotizador -f
```

---

## 🐛 Solución de Problemas Comunes

### Error de Conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar credenciales en .env
psql -U cotizador_user -d cotizador_db -h 127.0.0.1
```

### Error al generar PDF
```bash
# Instalar dependencias de sistema para ReportLab
sudo apt-get install python3-dev libfreetype6-dev

# Reinstalar ReportLab
pip uninstall reportlab
pip install reportlab
```

### Error 502 Bad Gateway (Nginx)
```bash
# Verificar que Gunicorn esté corriendo
sudo systemctl status cotizador

# Verificar logs
sudo journalctl -u cotizador -n 50
```

### Archivos estáticos no se cargan
```bash
# Recolectar estáticos nuevamente
python manage.py collectstatic --clear --no-input

# Verificar permisos
sudo chown -R www-data:www-data staticfiles/
```

---

## 🔐 Seguridad

### Checklist de Seguridad

- [ ] `DEBUG=False` en producción
- [ ] `SECRET_KEY` única y segura
- [ ] HTTPS habilitado (Let's Encrypt)
- [ ] Firewall configurado
- [ ] PostgreSQL con contraseña fuerte
- [ ] Backups automáticos configurados
- [ ] Rate limiting en API
- [ ] CORS configurado correctamente
- [ ] Headers de seguridad (HSTS, etc.)
- [ ] Dependencias actualizadas

### Actualizar Dependencias
```bash
# Verificar vulnerabilidades
pip-audit

# Actualizar paquetes
pip install --upgrade -r requirements.txt
```

---

## 📚 Comandos Útiles

```bash
# Crear app nueva
python manage.py startapp nombre_app

# Shell interactivo
python manage.py shell

# Crear migración vacía
python manage.py makemigrations --empty nombre_app

# Ver SQL de migración
python manage.py sqlmigrate nombre_app 0001

# Cargar fixtures
python manage.py loaddata fixtures/usuarios.json

# Crear fixtures
python manage.py dumpdata nombre_app --indent 2 > fixtures/data.json

# Limpiar sesiones expiradas
python manage.py clearsessions

# Crear superusuario sin interacción
python manage.py createsuperuser --noinput --username admin --email admin@example.com
```

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## 📝 Changelog

### v1.0.0 (2025-10-15)
- ✅ Sistema completo de cotizaciones
- ✅ Generación de PDF profesionales
- ✅ Sistema de pagos One-Click
- ✅ API REST para integración PHP
- ✅ Reportes y estadísticas
- ✅ Exportación a Excel
- ✅ Sistema de emails automáticos

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 👥 Equipo

- **Desarrollo**: Tu Nombre
- **Email**: tu@email.com
- **Website**: https://tudominio.com

---

## 🆘 Soporte

- 📧 Email: soporte@tudominio.com
- 📞 Teléfono: +56 9 XXXX XXXX
- 💬 Discord: [Link al servidor]
- 📖 Docs: https://docs.tudominio.com

---

## 🎯 Roadmap

### Próximas Características

- [ ] Dashboard con gráficos interactivos (Chart.js)
- [ ] Sistema de permisos por roles
- [ ] Multi-idioma (i18n)
- [ ] App móvil (React Native)
- [ ] Integración con ERP externos
- [ ] Firma digital de documentos
- [ ] WhatsApp Business API
- [ ] OCR para facturas
- [ ] Machine Learning para predicciones

---

## 📸 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Cotización PDF
![PDF](docs/screenshots/pdf_ejemplo.png)

### Pago One-Click
![Pago](docs/screenshots/oneclick.png)

---

**¡Gracias por usar el Sistema de Cotizaciones Intranet! 🚀**