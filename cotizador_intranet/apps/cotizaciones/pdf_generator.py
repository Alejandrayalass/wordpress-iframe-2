# apps/cotizaciones/pdf_generator.py
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime

class CotizacionPDFGenerator:
    """Genera PDFs profesionales de cotizaciones"""
    
    def __init__(self, cotizacion):
        self.cotizacion = cotizacion
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Crea estilos personalizados"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='RightAlign',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT
        ))
    
    def generate(self):
        """Genera el PDF y retorna el buffer"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Logo (si existe)
        logo_path = settings.STATIC_ROOT / 'img' / 'logo.png'
        if logo_path.exists():
            logo = Image(str(logo_path), width=2*inch, height=1*inch)
            story.append(logo)
            story.append(Spacer(1, 0.3*inch))
        
        # Título
        title = Paragraph(
            f"COTIZACIÓN {self.cotizacion.numero_cotizacion}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Información de la empresa y cliente
        info_data = [
            ['Fecha:', self.cotizacion.fecha_creacion.strftime('%d/%m/%Y')],
            ['Válida hasta:', self.cotizacion.fecha_vencimiento.strftime('%d/%m/%Y')],
            ['Cliente:', self.cotizacion.cliente.nombre],
            ['Email:', self.cotizacion.cliente.email or 'N/A'],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Tabla de items
        items_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Descuento', 'Subtotal']]
        
        for item in self.cotizacion.items.all():
            items_data.append([
                item.producto.nombre,
                str(item.cantidad),
                f"${item.precio_unitario:,.0f}",
                f"{item.descuento}%",
                f"${item.subtotal:,.0f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Totales
        totales_data = [
            ['Subtotal:', f"${self.cotizacion.subtotal:,.0f}"],
            ['IVA (19%):', f"${self.cotizacion.impuesto:,.0f}"],
            ['TOTAL:', f"${self.cotizacion.total:,.0f}"]
        ]
        
        totales_table = Table(totales_data, colWidths=[4.5*inch, 2*inch])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a237e')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1a237e')),
            ('TOPPADDING', (0, -1), (-1, -1), 10),
        ]))
        story.append(totales_table)
        
        # Notas
        if self.cotizacion.notas:
            story.append(Spacer(1, 0.4*inch))
            story.append(Paragraph('<b>Notas:</b>', self.styles['Heading3']))
            story.append(Paragraph(self.cotizacion.notas, self.styles['Normal']))
        
        # Pie de página
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        story.append(Paragraph(footer_text, self.styles['RightAlign']))
        
        # Build PDF
        doc.build(story)
        self.buffer.seek(0)
        return self.buffer
    
    def save_to_model(self):
        """Genera el PDF y lo guarda en el modelo"""
        pdf_buffer = self.generate()
        filename = f"cotizacion_{self.cotizacion.numero_cotizacion}.pdf"
        
        self.cotizacion.pdf_generado.save(
            filename,
            ContentFile(pdf_buffer.read()),
            save=True
        )
        self.cotizacion.pdf_fecha_generacion = datetime.now()
        self.cotizacion.save()
        
        return self.cotizacion.pdf_generado.url


# Vista para generar PDF
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from apps.cotizaciones.models import Cotizacion

def generar_pdf_cotizacion(request, cotizacion_id):
    """Vista para generar y descargar PDF de cotización"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    
    generator = CotizacionPDFGenerator(cotizacion)
    pdf_buffer = generator.generate()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cotizacion_{cotizacion.numero_cotizacion}.pdf"'
    
    return response