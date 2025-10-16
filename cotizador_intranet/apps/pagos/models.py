# apps/pagos/models.py
from django.db import models
from apps.cotizaciones.models import Cotizacion
from apps.usuarios.models import Cliente
from django.utils import timezone

class TarjetaGuardada(models.Model):
    """Modelo para guardar tarjetas con tokenización"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='tarjetas')
    token_tarjeta = models.CharField(max_length=255, unique=True)  # Token del gateway
    ultimos_4_digitos = models.CharField(max_length=4)
    marca = models.CharField(max_length=20)  # Visa, Mastercard, etc.
    nombre_titular = models.CharField(max_length=100)
    fecha_expiracion = models.CharField(max_length=7)  # MM/YYYY
    predeterminada = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tarjeta Guardada'
        verbose_name_plural = 'Tarjetas Guardadas'
        ordering = ['-predeterminada', '-creada']
    
    def __str__(self):
        return f"{self.marca} ****{self.ultimos_4_digitos}"
    
    def save(self, *args, **kwargs):
        # Si es predeterminada, quitar la marca de otras tarjetas
        if self.predeterminada:
            TarjetaGuardada.objects.filter(
                cliente=self.cliente, 
                predeterminada=True
            ).exclude(id=self.id).update(predeterminada=False)
        super().save(*args, **kwargs)


class Transaccion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('CANCELADA', 'Cancelada'),
        ('REEMBOLSADA', 'Reembolsada'),
    ]
    
    METODOS = [
        ('ONECLICK', 'One Click'),
        ('WEBPAY', 'Webpay'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('EFECTIVO', 'Efectivo'),
    ]
    
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.PROTECT, related_name='transacciones')
    tarjeta = models.ForeignKey(TarjetaGuardada, on_delete=models.SET_NULL, null=True, blank=True)
    
    numero_transaccion = models.CharField(max_length=50, unique=True, blank=True)
    metodo_pago = models.CharField(max_length=20, choices=METODOS)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    
    # Datos del gateway de pago
    codigo_autorizacion = models.CharField(max_length=100, blank=True)
    id_gateway = models.CharField(max_length=100, blank=True)
    respuesta_gateway = models.JSONField(blank=True, null=True)
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    ip_cliente = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Transacción {self.numero_transaccion} - {self.estado}"
    
    def save(self, *args, **kwargs):
        if not self.numero_transaccion:
            # Generar número único
            ultimo = Transaccion.objects.order_by('-id').first()
            numero = (ultimo.id + 1) if ultimo else 1
            self.numero_transaccion = f"TRX-{numero:08d}"
        super().save(*args, **kwargs)


# apps/pagos/services.py
import hashlib
import hmac
import json
import requests
from django.conf import settings
from decimal import Decimal

class OneClickPaymentService:
    """Servicio para procesamiento de pagos One-Click"""
    
    def __init__(self):
        self.api_url = settings.PAYMENT_GATEWAY_URL
        self.merchant_id = settings.PAYMENT_MERCHANT_ID
        self.api_key = settings.PAYMENT_API_KEY
        self.secret_key = settings.PAYMENT_SECRET_KEY
    
    def _generar_firma(self, datos):
        """Genera firma HMAC para seguridad"""
        mensaje = json.dumps(datos, sort_keys=True)
        return hmac.new(
            self.secret_key.encode(),
            mensaje.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def registrar_tarjeta(self, cliente, datos_tarjeta):
        """
        Registra una tarjeta para uso futuro (tokenización)
        NO guarda datos sensibles, solo el token del gateway
        """
        payload = {
            'merchant_id': self.merchant_id,
            'cliente_id': cliente.id,
            'numero_tarjeta': datos_tarjeta['numero'],  # Solo para tokenizar
            'nombre_titular': datos_tarjeta['nombre'],
            'fecha_exp': datos_tarjeta['expiracion'],
            'cvv': datos_tarjeta['cvv']  # Solo para validación inicial
        }
        
        payload['firma'] = self._generar_firma(payload)
        
        try:
            response = requests.post(
                f"{self.api_url}/tokenizar",
                json=payload,
                timeout=30,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Guardar solo el token, NO los datos de la tarjeta
                tarjeta = TarjetaGuardada.objects.create(
                    cliente=cliente,
                    token_tarjeta=data['token'],
                    ultimos_4_digitos=data['ultimos_4'],
                    marca=data['marca'],
                    nombre_titular=datos_tarjeta['nombre'],
                    fecha_expiracion=datos_tarjeta['expiracion'],
                    predeterminada=not cliente.tarjetas.exists()
                )
                
                return {'success': True, 'tarjeta': tarjeta}
            
            return {'success': False, 'error': 'Error al tokenizar tarjeta'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def procesar_pago_oneclick(self, cotizacion, tarjeta, ip_cliente=None):
        """
        Procesa un pago usando una tarjeta guardada (One-Click)
        """
        # Crear transacción
        transaccion = Transaccion.objects.create(
            cotizacion=cotizacion,
            tarjeta=tarjeta,
            metodo_pago='ONECLICK',
            monto=cotizacion.total,
            estado='PROCESANDO',
            ip_cliente=ip_cliente
        )
        
        payload = {
            'merchant_id': self.merchant_id,
            'transaccion_id': transaccion.numero_transaccion,
            'token_tarjeta': tarjeta.token_tarjeta,
            'monto': float(cotizacion.total),
            'moneda': 'CLP',
            'descripcion': f"Cotización {cotizacion.numero_cotizacion}"
        }
        
        payload['firma'] = self._generar_firma(payload)
        
        try:
            response = requests.post(
                f"{self.api_url}/cobrar",
                json=payload,
                timeout=30,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            
            data = response.json()
            transaccion.respuesta_gateway = data
            
            if response.status_code == 200 and data.get('estado') == 'aprobado':
                transaccion.estado = 'APROBADA'
                transaccion.codigo_autorizacion = data.get('codigo_autorizacion')
                transaccion.id_gateway = data.get('id_transaccion')
                transaccion.fecha_procesamiento = timezone.now()
                
                # Actualizar cotización
                cotizacion.pago_procesado = True
                cotizacion.metodo_pago = 'ONECLICK'
                cotizacion.estado = 'APROBADA'
                cotizacion.save()
                
                return {'success': True, 'transaccion': transaccion}
            else:
                transaccion.estado = 'RECHAZADA'
                return {'success': False, 'error': data.get('mensaje', 'Pago rechazado')}
            
        except Exception as e:
            transaccion.estado = 'RECHAZADA'
            return {'success': False, 'error': str(e)}
        
        finally:
            transaccion.save()
    
    def eliminar_tarjeta(self, tarjeta_id):
        """Elimina una tarjeta guardada"""
        try:
            tarjeta = TarjetaGuardada.objects.get(id=tarjeta_id)
            
            # Notificar al gateway para eliminar el token
            payload = {
                'merchant_id': self.merchant_id,
                'token': tarjeta.token_tarjeta
            }
            payload['firma'] = self._generar_firma(payload)
            
            requests.post(
                f"{self.api_url}/eliminar-token",
                json=payload,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            
            tarjeta.delete()
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# apps/pagos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def pagar_oneclick(request, cotizacion_id):
    """Vista para procesar pago con One-Click"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    cliente = cotizacion.cliente
    
    if request.method == 'POST':
        tarjeta_id = request.POST.get('tarjeta_id')
        
        if tarjeta_id:
            tarjeta = get_object_or_404(TarjetaGuardada, id=tarjeta_id, cliente=cliente)
            service = OneClickPaymentService()
            
            resultado = service.procesar_pago_oneclick(
                cotizacion, 
                tarjeta,
                ip_cliente=request.META.get('REMOTE_ADDR')
            )
            
            if resultado['success']:
                messages.success(request, '¡Pago procesado exitosamente!')
                return redirect('cotizaciones:detalle', pk=cotizacion.id)
            else:
                messages.error(request, f"Error: {resultado['error']}")
        else:
            messages.error(request, 'Debe seleccionar una tarjeta')
    
    # GET: mostrar tarjetas guardadas
    tarjetas = cliente.tarjetas.filter(activa=True)
    
    return render(request, 'pagos/oneclick_payment.html', {
        'cotizacion': cotizacion,
        'tarjetas': tarjetas
    })