# apps/wizard/views.py
"""
Vistas del formulario wizard multi-step embebible
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
import uuid
from datetime import datetime, timedelta

from .models import (
    Cliente, DatosTecnicos, ArchivoBoleta, ProductoSolar, 
    MetodoPago, Cotizacion, ItemCotizacion, EstadoWizard
)
from .forms import (
    ClienteForm, DatosTecnicosForm, ProductoSeleccionForm, ComentariosForm
)
from .pdf_generator import CotizacionSolarPDFGenerator


# ============================================
# WIZARD PRINCIPAL - Embebible en WordPress
# ============================================

@xframe_options_exempt  # Permitir iframe
def wizard_embed(request):
    """Vista principal del wizard embebible"""
    # Obtener o crear sesión del wizard
    session_key = request.session.session_key or request.session.create()
    
    # Obtener paso actual
    paso = int(request.GET.get('paso', 1))
    
    # Temas (light/dark)
    theme = request.GET.get('theme', 'light')
    
    context = {
        'paso_actual': paso,
        'total_pasos': 6,
        'theme': theme,
        'session_key': session_key,
    }
    
    # Cargar datos guardados si existen
    try:
        estado = EstadoWizard.objects.get(session_key=session_key)
        context['datos_guardados'] = estado.datos
    except EstadoWizard.DoesNotExist:
        context['datos_guardados'] = {}
    
    return render(request, 'wizard/embed.html', context)


# ============================================
# PASO 1: DATOS PERSONALES
# ============================================

@csrf_exempt
def wizard_paso1(request):
    """Paso 1: Datos personales del cliente"""
    session_key = request.session.session_key
    
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        
        if form.is_valid():
            # Guardar en sesión
            datos_paso1 = form.cleaned_data
            
            # Guardar estado del wizard
            estado, created = EstadoWizard.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'expira_en': datetime.now() + timedelta(days=7)
                }
            )
            
            if 'paso1' not in estado.datos:
                estado.datos['paso1'] = {}
            
            estado.datos['paso1'] = {
                'nombre': datos_paso1['nombre'],
                'apellido': datos_paso1['apellido'],
                'rut': datos_paso1['rut'],
                'email': datos_paso1['email'],
                'telefono': datos_paso1['telefono'],
                'region': datos_paso1['region'],
                'direccion': datos_paso1['direccion'],
            }
            estado.paso_actual = 2
            estado.save()
            
            return JsonResponse({
                'success': True,
                'siguiente_paso': 2,
                'mensaje': 'Datos personales guardados'
            })
        else:
            return JsonResponse({
                'success': False,
                'errores': form.errors
            }, status=400)
    
    # GET: Mostrar formulario
    # Cargar datos previos si existen
    try:
        estado = EstadoWizard.objects.get(session_key=session_key)
        initial_data = estado.datos.get('paso1', {})
        form = ClienteForm(initial=initial_data)
    except EstadoWizard.DoesNotExist:
        form = ClienteForm()
    
    return render(request, 'wizard/paso1.html', {'form': form})


# ============================================
# PASO 2: DATOS TÉCNICOS
# ============================================

@csrf_exempt
def wizard_paso2(request):
    """Paso 2: Datos técnicos y boleta de luz"""
    session_key = request.session.session_key
    
    if request.method == 'POST':
        form = DatosTecnicosForm(request.POST)
        archivos = request.FILES.getlist('boleta_luz')
        
        if form.is_valid():
            # Validar archivos
            for archivo in archivos:
                # Validar tamaño (máx 10MB)
                if archivo.size > 10 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'errores': {'boleta_luz': ['Archivo muy grande. Máximo 10MB']}
                    }, status=400)
                
                # Validar extensión
                ext = archivo.name.split('.')[-1].lower()
                if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
                    return JsonResponse({
                        'success': False,
                        'errores': {'boleta_luz': ['Formato no permitido. Use PDF, JPG o PNG']}
                    }, status=400)
            
            # Guardar en sesión
            estado = EstadoWizard.objects.get(session_key=session_key)
            
            estado.datos['paso2'] = {
                'tipo_techo': form.cleaned_data['tipo_techo'],
                'orientacion': form.cleaned_data['orientacion'],
                'superficie_aproximada': str(form.cleaned_data['superficie_aproximada']),
                'potencia_objetivo': str(form.cleaned_data.get('potencia_objetivo') or 0),
                'consumo_promedio': str(form.cleaned_data.get('consumo_promedio') or 0),
                'observaciones': form.cleaned_data.get('observaciones', ''),
            }
            
            # Guardar archivos temporalmente en sesión
            estado.datos['archivos_boleta'] = []
            for archivo in archivos:
                # Aquí guardarías en sistema de archivos temporal
                estado.datos['archivos_boleta'].append({
                    'nombre': archivo.name,
                    'tamanio': archivo.size,
                    'tipo': archivo.content_type
                })
            
            estado.paso_actual = 3
            estado.save()
            
            return JsonResponse({
                'success': True,
                'siguiente_paso': 3,
                'mensaje': 'Datos técnicos guardados'
            })
        else:
            return JsonResponse({
                'success': False,
                'errores': form.errors
            }, status=400)
    
    # GET
    try:
        estado = EstadoWizard.objects.get(session_key=session_key)
        initial_data = estado.datos.get('paso2', {})
        form = DatosTecnicosForm(initial=initial_data)
    except EstadoWizard.DoesNotExist:
        form = DatosTecnicosForm()
    
    return render(request, 'wizard/paso2.html', {'form': form})


# ============================================
# PASO 3: SELECCIÓN DE PRODUCTOS
# ============================================

@csrf_exempt
def wizard_paso3(request):
    """Paso 3: Selector de productos"""
    session_key = request.session.session_key
    
    if request.method == 'GET':
        # Obtener productos activos
        productos = ProductoSolar.objects.filter(activo=True).order_by('-destacado', 'categoria')
        
        # Filtrar por categoría si se especifica
        categoria = request.GET.get('categoria')
        if categoria:
            productos = productos.filter(categoria=categoria)
        
        # Serializar para JSON
        productos_data = [{
            'id': p.id,
            'sku': p.sku,
            'nombre': p.nombre,
            'categoria': p.get_categoria_display(),
            'descripcion': p.descripcion,
            'potencia': p.potencia,
            'precio': float(p.precio_clp),
            'precio_formato': p.precio_formato,
            'imagen_url': p.imagen.url if p.imagen else None,
            'stock': p.stock,
            'destacado': p.destacado,
        } for p in productos]
        
        return JsonResponse({
            'productos': productos_data,
            'categorias': dict(ProductoSolar.CATEGORIA_CHOICES)
        })
    
    elif request.method == 'POST':
        # Guardar productos seleccionados
        data = json.loads(request.body)
        productos_seleccionados = data.get('productos', [])
        
        if not productos_seleccionados:
            return JsonResponse({
                'success': False,
                'errores': {'productos': ['Debe seleccionar al menos un producto']}
            }, status=400)
        
        estado = EstadoWizard.objects.get(session_key=session_key)
        estado.datos['paso3'] = {
            'productos': productos_seleccionados
        }
        estado.paso_actual = 4
        estado.save()
        
        return JsonResponse({
            'success': True,
            'siguiente_paso': 4,
            'mensaje': 'Productos guardados'
        })


# ============================================
# PASO 4: MÉTODOS DE PAGO (INFORMATIVOS)
# ============================================

@csrf_exempt
def wizard_paso4(request):
    """Paso 4: Métodos de pago informativos"""
    
    if request.method == 'GET':
        # Obtener métodos de pago visibles
        metodos = MetodoPago.objects.filter(visible=True).order_by('orden')
        
        metodos_data = [{
            'id': m.id,
            'nombre': m.nombre,
            'descripcion': m.descripcion,
            'datos_transferencia': m.datos_transferencia,
            'icono': m.icono,
        } for m in metodos]
        
        return JsonResponse({'metodos': metodos_data})
    
    elif request.method == 'POST':
        # Solo pasar al siguiente paso (los métodos son informativos)
        session_key = request.session.session_key
        estado = EstadoWizard.objects.get(session_key=session_key)
        estado.paso_actual = 5
        estado.save()
        
        return JsonResponse({
            'success': True,
            'siguiente_paso': 5
        })


# ============================================
# PASO 5: REVISIÓN Y TOTALES
# ============================================

@csrf_exempt
def wizard_paso5(request):
    """Paso 5: Resumen y cálculo de totales"""
    session_key = request.session.session_key
    
    try:
        estado = EstadoWizard.objects.get(session_key=session_key)
        
        # Calcular totales
        productos_seleccionados = estado.datos.get('paso3', {}).get('productos', [])
        
        subtotal = Decimal('0')
        items_resumen = []
        
        for item in productos_seleccionados:
            producto = ProductoSolar.objects.get(id=item['producto_id'])
            cantidad = item['cantidad']
            precio_unitario = producto.precio_clp
            total_item = precio_unitario * cantidad
            
            subtotal += total_item
            
            items_resumen.append({
                'nombre': producto.nombre,
                'cantidad': cantidad,
                'precio_unitario': float(precio_unitario),
                'total': float(total_item)
            })
        
        iva = subtotal * Decimal('0.19')
        total = subtotal + iva
        
        # Aplicar descuento si se proporciona
        descuento = Decimal(request.GET.get('descuento', 0))
        if descuento > 0:
            total -= descuento
        
        resumen = {
            'paso1': estado.datos.get('paso1', {}),
            'paso2': estado.datos.get('paso2', {}),
            'items': items_resumen,
            'subtotal': float(subtotal),
            'iva': float(iva),
            'descuento': float(descuento),
            'total': float(total),
        }
        
        if request.method == 'POST':
            # Guardar descuento aplicado
            estado.datos['descuento'] = float(descuento)
            estado.paso_actual = 6
            estado.save()
            
            return JsonResponse({
                'success': True,
                'siguiente_paso': 6
            })
        
        return JsonResponse({'resumen': resumen})
        
    except EstadoWizard.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Sesión no encontrada'
        }, status=404)


# ============================================
# PASO 6: COMENTARIOS Y ENVÍO FINAL
# ============================================

@csrf_exempt
def wizard_paso6(request):
    """Paso 6: Comentarios finales y envío"""
    session_key = request.session.session_key
    
    if request.method == 'POST':
        data = json.loads(request.body)
        comentarios = data.get('comentarios', '')
        
        try:
            estado = EstadoWizard.objects.get(session_key=session_key)
            
            # CREAR CLIENTE
            datos_cliente = estado.datos['paso1']
            cliente, created = Cliente.objects.get_or_create(
                rut=datos_cliente['rut'],
                defaults=datos_cliente
            )
            
            # CREAR DATOS TÉCNICOS
            datos_tecnicos_data = estado.datos['paso2']
            datos_tecnicos, _ = DatosTecnicos.objects.get_or_create(
                cliente=cliente,
                defaults=datos_tecnicos_data
            )
            
            # CREAR COTIZACIÓN
            cotizacion = Cotizacion.objects.create(
                cliente=cliente,
                datos_tecnicos_snapshot=datos_tecn