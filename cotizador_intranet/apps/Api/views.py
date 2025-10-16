# apps/api/views.py
"""
API REST para integración con sistemas PHP externos
Permite que aplicaciones PHP consulten y envíen datos al sistema Django
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import hashlib
import hmac
import json
from apps.cotizaciones.models import Cotizacion, ItemCotizacion
from apps.inventario.models import Producto
from apps.usuarios.models import Cliente


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================
# AUTENTICACIÓN PARA PHP
# ============================================

def verificar_firma_php(request):
    """
    Verifica que la petición venga de un sistema PHP autorizado
    usando firma HMAC
    """
    try:
        api_key = request.headers.get('X-API-Key')
        firma_recibida = request.headers.get('X-Signature')
        timestamp = request.headers.get('X-Timestamp')
        
        # Clave secreta compartida (en settings.py)
        from django.conf import settings
        secret = settings.PHP_API_SECRET
        
        # Generar firma esperada
        mensaje = f"{api_key}{timestamp}{request.body.decode()}"
        firma_esperada = hmac.new(
            secret.encode(),
            mensaje.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return firma_recibida == firma_esperada
    except:
        return False


# ============================================
# ENDPOINTS PARA PHP
# ============================================

@csrf_exempt
@api_view(['POST'])
def php_crear_cotizacion(request):
    """
    Endpoint para que sistemas PHP creen cotizaciones
    
    POST /api/php/cotizacion/crear/
    Headers:
        X-API-Key: tu_api_key
        X-Signature: firma_hmac
        X-Timestamp: unix_timestamp
    Body:
    {
        "cliente_id": 1,
        "fecha_vencimiento": "2025-12-31",
        "items": [
            {"producto_id": 1, "cantidad": 2, "precio_unitario": 10000},
            {"producto_id": 2, "cantidad": 1, "precio_unitario": 25000}
        ],
        "notas": "Cotización desde PHP"
    }
    """
    
    if not verificar_firma_php(request):
        return Response(
            {'error': 'Firma inválida o no autorizado'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        data = request.data
        
        # Validar cliente
        cliente = Cliente.objects.get(id=data['cliente_id'])
        
        # Crear cotización
        cotizacion = Cotizacion.objects.create(
            cliente=cliente,
            fecha_vencimiento=data['fecha_vencimiento'],
            notas=data.get('notas', '')
        )
        
        # Crear items
        for item_data in data['items']:
            producto = Producto.objects.get(id=item_data['producto_id'])
            ItemCotizacion.objects.create(
                cotizacion=cotizacion,
                producto=producto,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario'],
                descuento=item_data.get('descuento', 0)
            )
        
        # Calcular totales
        cotizacion.calcular_total()
        
        return Response({
            'success': True,
            'cotizacion_id': cotizacion.id,
            'numero_cotizacion': cotizacion.numero_cotizacion,
            'total': float(cotizacion.total),
            'mensaje': 'Cotización creada exitosamente'
        }, status=status.HTTP_201_CREATED)
        
    except Cliente.DoesNotExist:
        return Response(
            {'error': 'Cliente no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Producto.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@csrf_exempt
@api_view(['GET'])
def php_obtener_productos(request):
    """
    Endpoint para que PHP obtenga listado de productos
    
    GET /api/php/productos/?categoria=1&activos=true
    """
    
    if not verificar_firma_php(request):
        return Response(
            {'error': 'No autorizado'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    productos = Producto.objects.select_related('categoria')
    
    # Filtros
    if request.GET.get('activos') == 'true':
        productos = productos.filter(activo=True)
    
    if request.GET.get('categoria'):
        productos = productos.filter(categoria_id=request.GET.get('categoria'))
    
    if request.GET.get('search'):
        productos = productos.filter(nombre__icontains=request.GET.get('search'))
    
    data = [{
        'id': p.id,
        'codigo': p.codigo,
        'nombre': p.nombre,
        'categoria': p.categoria.nombre,
        'precio': float(p.precio),
        'stock': p.stock,
        'disponible': p.disponible
    } for p in productos[:100]]  # Limitar a 100
    
    return Response({'productos': data, 'total': len(data)})


@csrf_exempt
@api_view(['GET'])
def php_obtener_cotizacion(request, cotizacion_id):
    """
    Endpoint para obtener detalles de una cotización
    
    GET /api/php/cotizacion/123/
    """
    
    if not verificar_firma_php(request):
        return Response(
            {'error': 'No autorizado'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        cotizacion = Cotizacion.objects.select_related('cliente').get(id=cotizacion_id)
        
        items = [{
            'producto': item.producto.nombre,
            'cantidad': item.cantidad,
            'precio_unitario': float(item.precio_unitario),
            'descuento': float(item.descuento),
            'subtotal': float(item.subtotal)
        } for item in cotizacion.items.all()]
        
        data = {
            'id': cotizacion.id,
            'numero': cotizacion.numero_cotizacion,
            'cliente': {
                'id': cotizacion.cliente.id,
                'nombre': cotizacion.cliente.nombre,
                'email': cotizacion.cliente.email
            },
            'fecha_creacion': cotizacion.fecha_creacion.isoformat(),
            'fecha_vencimiento': cotizacion.fecha_vencimiento.isoformat(),
            'estado': cotizacion.estado,
            'items': items,
            'subtotal': float(cotizacion.subtotal),
            'impuesto': float(cotizacion.impuesto),
            'total': float(cotizacion.total),
            'notas': cotizacion.notas
        }
        
        return Response(data)
        
    except Cotizacion.DoesNotExist:
        return Response(
            {'error': 'Cotización no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )


@csrf_exempt
@api_view(['POST'])
def php_actualizar_stock(request):
    """
    Endpoint para actualizar stock desde PHP
    
    POST /api/php/stock/actualizar/
    Body:
    {
        "actualizaciones": [
            {"producto_id": 1, "cantidad": 50},
            {"producto_id": 2, "cantidad": -10}
        ]
    }
    """
    
    if not verificar_firma_php(request):
        return Response(
            {'error': 'No autorizado'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        actualizaciones = request.data.get('actualizaciones', [])
        resultados = []
        
        for item in actualizaciones:
            producto = Producto.objects.get(id=item['producto_id'])
            stock_anterior = producto.stock
            producto.stock += item['cantidad']
            
            if producto.stock < 0:
                producto.stock = 0
            
            producto.save()
            
            resultados.append({
                'producto_id': producto.id,
                'nombre': producto.nombre,
                'stock_anterior': stock_anterior,
                'stock_nuevo': producto.stock
            })
        
        return Response({
            'success': True,
            'actualizaciones': resultados
        })
        
    except Producto.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================
# CLIENTE PHP EJEMPLO
# ============================================

"""
<?php
// ejemplo_cliente_php.php
// Cliente PHP para consumir la API Django

class DjangoAPIClient {
    private $baseUrl;
    private $apiKey;
    private $secretKey;
    
    public function __construct($baseUrl, $apiKey, $secretKey) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->apiKey = $apiKey;
        $this->secretKey = $secretKey;
    }
    
    private function generarFirma($body) {
        $timestamp = time();
        $mensaje = $this->apiKey . $timestamp . $body;
        $firma = hash_hmac('sha256', $mensaje, $this->secretKey);
        
        return [
            'timestamp' => $timestamp,
            'firma' => $firma
        ];
    }
    
    private function request($endpoint, $method = 'GET', $data = null) {
        $url = $this->baseUrl . $endpoint;
        $body = $data ? json_encode($data) : '';
        
        $auth = $this->generarFirma($body);
        
        $headers = [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->apiKey,
            'X-Signature: ' . $auth['firma'],
            'X-Timestamp: ' . $auth['timestamp']
        ];
        
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        
        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        return [
            'code' => $httpCode,
            'data' => json_decode($response, true)
        ];
    }
    
    // Crear cotización desde PHP
    public function crearCotizacion($clienteId, $fechaVencimiento, $items, $notas = '') {
        return $this->request('/api/php/cotizacion/crear/', 'POST', [
            'cliente_id' => $clienteId,
            'fecha_vencimiento' => $fechaVencimiento,
            'items' => $items,
            'notas' => $notas
        ]);
    }
    
    // Obtener productos
    public function obtenerProductos($filtros = []) {
        $query = http_build_query($filtros);
        $endpoint = '/api/php/productos/' . ($query ? '?' . $query : '');
        return $this->request($endpoint, 'GET');
    }
    
    // Obtener cotización
    public function obtenerCotizacion($cotizacionId) {
        return $this->request("/api/php/cotizacion/{$cotizacionId}/", 'GET');
    }
    
    // Actualizar stock
    public function actualizarStock($actualizaciones) {
        return $this->request('/api/php/stock/actualizar/', 'POST', [
            'actualizaciones' => $actualizaciones
        ]);
    }
}

// Ejemplo de uso
$api = new DjangoAPIClient(
    'http://localhost:8000',
    'tu_api_key_aqui',
    'tu_secret_key_aqui'
);

// Crear cotización
$resultado = $api->crearCotizacion(
    1, // cliente_id
    '2025-12-31',
    [
        ['producto_id' => 1, 'cantidad' => 2, 'precio_unitario' => 10000],
        ['producto_id' => 2, 'cantidad' => 1, 'precio_unitario' => 25000]
    ],
    'Cotización desde sistema PHP'
);

if ($resultado['code'] === 201) {
    echo "Cotización creada: " . $resultado['data']['numero_cotizacion'];
} else {
    echo "Error: " . $resultado['data']['error'];
}

// Obtener productos activos
$productos = $api->obtenerProductos(['activos' => 'true']);
print_r($productos['data']);

?>
"""