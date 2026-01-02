from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

from software.models.ImposicionPlacaModel import ImposicionPlaca
from software.models.HistorialImposicionModel import HistorialImposicion
from software.models.VentasModel import Ventas
from software.models.VentaDetalleModel import VentaDetalle
from software.models.VehiculosModel import Vehiculo
from software.models.ClienteModel import Cliente
from software.models.UsuarioModel import Usuario
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def imposicion_placas(request):
    """Vista principal - Listado de imposiciones de placas"""
    id2 = request.session.get('idtipousuario')
    
    if not id2:
        return HttpResponse("<h1>No tiene acceso</h1>")
    
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    idusuario = request.session.get('idusuario')
    id_sucursal = request.session.get('id_sucursal')
    es_admin = (id2 == 1)
    
    # Filtrar imposiciones por sucursal
    if es_admin and id_sucursal:
        imposiciones = ImposicionPlaca.objects.filter(
            estado=1, id_sucursal_id=id_sucursal
        ).select_related(
            'idventa', 'id_vehiculo', 'idcliente', 'idusuario', 'id_vehiculo__idproducto'
        ).order_by('-fecha_solicitud')
    elif not es_admin:
        try:
            usuario = Usuario.objects.get(idusuario=idusuario)
            imposiciones = ImposicionPlaca.objects.filter(
                estado=1, id_sucursal=usuario.id_sucursal
            ).select_related(
                'idventa', 'id_vehiculo', 'idcliente', 'idusuario', 'id_vehiculo__idproducto'
            ).order_by('-fecha_solicitud')
        except Usuario.DoesNotExist:
            imposiciones = []
    else:
        imposiciones = []
    
    # Vehículos vendidos sin imposición
    ventas_con_vehiculos = obtener_ventas_sin_imposicion(id_sucursal, es_admin, idusuario)
    
    # Estadísticas
    estadisticas = {
        'total': ImposicionPlaca.objects.filter(estado=1).count(),
        'pendientes': ImposicionPlaca.objects.filter(estado=1, estado_tramite='pendiente').count(),
        'en_tramite': ImposicionPlaca.objects.filter(estado=1, estado_tramite='en_tramite').count(),
        'completados': ImposicionPlaca.objects.filter(estado=1, estado_tramite='completado').count(),
    }
    
    data = {
        'imposiciones': imposiciones,
        'ventas_con_vehiculos': ventas_con_vehiculos,
        'estadisticas': estadisticas,
        'permisos': permisos,
        'es_admin': es_admin,
        'idusuario': idusuario,
    }
    
    return render(request, 'imposicion_placas/imposicion_placas.html', data)


def obtener_ventas_sin_imposicion(id_sucursal, es_admin, idusuario):
    """Obtiene ventas con vehículos sin imposición de placa - AGRUPADAS"""
    vehiculos_con_imposicion = ImposicionPlaca.objects.filter(
        estado=1
    ).values_list('id_vehiculo_id', flat=True)
    
    if es_admin and id_sucursal:
        detalles = VentaDetalle.objects.filter(
            idventa__estado=1,
            idventa__id_sucursal_id=id_sucursal,
            tipo_item='vehiculo',
            estado=1
        ).exclude(
            id_vehiculo_id__in=vehiculos_con_imposicion
        ).select_related(
            'idventa',
            'idventa__idcliente',
            'id_vehiculo',
            'id_vehiculo__idproducto'
        ).order_by('idventa__idventa')  # ⭐ ORDENAR por venta
        
    elif not es_admin:
        try:
            usuario = Usuario.objects.get(idusuario=idusuario)
            detalles = VentaDetalle.objects.filter(
                idventa__estado=1,
                idventa__id_sucursal=usuario.id_sucursal,
                tipo_item='vehiculo',
                estado=1
            ).exclude(
                id_vehiculo_id__in=vehiculos_con_imposicion
            ).select_related(
                'idventa',
                'idventa__idcliente',
                'id_vehiculo',
                'id_vehiculo__idproducto'
            ).order_by('idventa__idventa')  # ⭐ ORDENAR por venta
        except Usuario.DoesNotExist:
            detalles = []
    else:
        detalles = []
    
    return detalles


def nueva_imposicion(request):
    """Crear nueva imposición de placa"""
    if request.method == "POST":
        try:
            with transaction.atomic():
                idusuario = request.session.get('idusuario')
                id_sucursal = request.session.get('id_sucursal')
                
                idventa = int(request.POST.get('idventa'))
                id_vehiculo = int(request.POST.get('id_vehiculo'))
                tipo_placa = request.POST.get('tipo_placa', 'nueva')
                numero_placa = request.POST.get('numero_placa', '').strip().upper()
                
                costo_tramite = Decimal(request.POST.get('costo_tramite') or '0')
                costo_placa = Decimal(request.POST.get('costo_placa') or '0')
                otros_costos = Decimal(request.POST.get('otros_costos') or '0')
                
                fecha_tramite = request.POST.get('fecha_tramite') or None
                fecha_vencimiento = request.POST.get('fecha_vencimiento_tramite') or None
                
                tiene_tarjeta = request.POST.get('tiene_tarjeta_propiedad') == 'on'
                tiene_soat = request.POST.get('tiene_soat') == 'on'
                tiene_revision = request.POST.get('tiene_revision_tecnica') == 'on'
                numero_expediente = request.POST.get('numero_expediente', '').strip()
                observaciones = request.POST.get('observaciones', '')
                
                venta = Ventas.objects.get(idventa=idventa)
                vehiculo = Vehiculo.objects.get(id_vehiculo=id_vehiculo)
                
                # Verificar duplicado
                if ImposicionPlaca.objects.filter(id_vehiculo=vehiculo, estado=1).exists():
                    return JsonResponse({
                        'ok': False,
                        'error': 'Este vehículo ya tiene una imposición de placa registrada.'
                    }, status=400)
                
                imposicion = ImposicionPlaca.objects.create(
                    idventa=venta,
                    id_vehiculo=vehiculo,
                    idcliente=venta.idcliente,
                    idusuario_id=idusuario,
                    tipo_placa=tipo_placa,
                    numero_placa=numero_placa if numero_placa else None,
                    costo_tramite=costo_tramite,
                    costo_placa=costo_placa,
                    otros_costos=otros_costos,
                    fecha_tramite=fecha_tramite,
                    fecha_vencimiento_tramite=fecha_vencimiento,
                    tiene_tarjeta_propiedad=tiene_tarjeta,
                    tiene_soat=tiene_soat,
                    tiene_revision_tecnica=tiene_revision,
                    numero_expediente=numero_expediente if numero_expediente else None,
                    observaciones=observaciones,
                    estado_tramite='pendiente',
                    id_sucursal_id=id_sucursal or venta.id_sucursal_id,
                    estado=1
                )
                
                HistorialImposicion.objects.create(
                    id_imposicion=imposicion,
                    idusuario_id=idusuario,
                    estado_anterior='nuevo',
                    estado_nuevo='pendiente',
                    comentario='Imposición de placa creada'
                )
                
                return JsonResponse({
                    'ok': True,
                    'message': 'Imposición de placa registrada correctamente.',
                    'id_imposicion': imposicion.id_imposicion
                })
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'ok': False, 'error': f'Error al registrar: {str(e)}'}, status=400)
    
    return redirect('imposicion_placas')


def editar_imposicion(request, id):
    "Editar una imposición de placa existente"
    if request.method == "POST":
        try:
            with transaction.atomic():
                idusuario = request.session.get('idusuario')
                imposicion = get_object_or_404(ImposicionPlaca, id_imposicion=id, estado=1)
                estado_anterior = imposicion.estado_tramite
                
                # Guardar valores anteriores para detectar cambios
                datos_anteriores = {
                    'tipo_placa': imposicion.tipo_placa,
                    'numero_placa': imposicion.numero_placa,
                    'costo_tramite': imposicion.costo_tramite,
                    'costo_placa': imposicion.costo_placa,
                    'otros_costos': imposicion.otros_costos,
                    'fecha_tramite': imposicion.fecha_tramite,
                    'fecha_entrega': imposicion.fecha_entrega,
                    'fecha_vencimiento_tramite': imposicion.fecha_vencimiento_tramite,
                    'tiene_tarjeta_propiedad': imposicion.tiene_tarjeta_propiedad,
                    'tiene_soat': imposicion.tiene_soat,
                    'tiene_revision_tecnica': imposicion.tiene_revision_tecnica,
                    'numero_expediente': imposicion.numero_expediente,
                    'observaciones': imposicion.observaciones,
                }
                
                # Actualizar todos los campos
                imposicion.tipo_placa = request.POST.get('tipo_placa', imposicion.tipo_placa)
                numero_placa = request.POST.get('numero_placa', '').strip().upper()
                imposicion.numero_placa = numero_placa if numero_placa else None
                
                imposicion.costo_tramite = Decimal(request.POST.get('costo_tramite') or '0')
                imposicion.costo_placa = Decimal(request.POST.get('costo_placa') or '0')
                imposicion.otros_costos = Decimal(request.POST.get('otros_costos') or '0')
                
                fecha_tramite = request.POST.get('fecha_tramite')
                imposicion.fecha_tramite = fecha_tramite if fecha_tramite else None
                
                fecha_entrega = request.POST.get('fecha_entrega')
                imposicion.fecha_entrega = fecha_entrega if fecha_entrega else None
                
                fecha_vencimiento = request.POST.get('fecha_vencimiento_tramite')
                imposicion.fecha_vencimiento_tramite = fecha_vencimiento if fecha_vencimiento else None
                
                imposicion.tiene_tarjeta_propiedad = request.POST.get('tiene_tarjeta_propiedad') == 'on'
                imposicion.tiene_soat = request.POST.get('tiene_soat') == 'on'
                imposicion.tiene_revision_tecnica = request.POST.get('tiene_revision_tecnica') == 'on'
                
                numero_expediente = request.POST.get('numero_expediente', '').strip()
                imposicion.numero_expediente = numero_expediente if numero_expediente else None
                imposicion.observaciones = request.POST.get('observaciones', '')
                
                nuevo_estado = request.POST.get('estado_tramite', imposicion.estado_tramite)
                imposicion.estado_tramite = nuevo_estado
                
                # Guardar cambios
                imposicion.save()
                
                # OBTENER COMENTARIO DEL USUARIO
                comentario_usuario = request.POST.get('comentario_cambio', '').strip()
                
                # DETECTAR QUÉ CAMBIÓ
                cambios_detectados = []
                
                if estado_anterior != nuevo_estado:
                    cambios_detectados.append(f'Estado: {estado_anterior} → {nuevo_estado}')
                
                if datos_anteriores['numero_placa'] != imposicion.numero_placa:
                    cambios_detectados.append(f'Placa: {datos_anteriores["numero_placa"] or "Sin placa"} → {imposicion.numero_placa or "Sin placa"}')
                
                if datos_anteriores['costo_tramite'] != imposicion.costo_tramite:
                    cambios_detectados.append(f'Costo trámite: S/ {datos_anteriores["costo_tramite"]} → S/ {imposicion.costo_tramite}')
                
                if datos_anteriores['costo_placa'] != imposicion.costo_placa:
                    cambios_detectados.append(f'Costo placa: S/ {datos_anteriores["costo_placa"]} → S/ {imposicion.costo_placa}')
                
                if datos_anteriores['otros_costos'] != imposicion.otros_costos:
                    cambios_detectados.append(f'Otros costos: S/ {datos_anteriores["otros_costos"]} → S/ {imposicion.otros_costos}')
                
                if datos_anteriores['fecha_tramite'] != imposicion.fecha_tramite:
                    cambios_detectados.append('Fecha de trámite actualizada')
                
                if datos_anteriores['fecha_entrega'] != imposicion.fecha_entrega:
                    cambios_detectados.append('Fecha de entrega actualizada')
                
                if datos_anteriores['fecha_vencimiento_tramite'] != imposicion.fecha_vencimiento_tramite:
                    cambios_detectados.append('Fecha de vencimiento actualizada')
                
                if datos_anteriores['tiene_tarjeta_propiedad'] != imposicion.tiene_tarjeta_propiedad:
                    cambios_detectados.append(f'Tarjeta propiedad: {"Sí" if imposicion.tiene_tarjeta_propiedad else "No"}')
                
                if datos_anteriores['tiene_soat'] != imposicion.tiene_soat:
                    cambios_detectados.append(f'SOAT: {"Sí" if imposicion.tiene_soat else "No"}')
                
                if datos_anteriores['tiene_revision_tecnica'] != imposicion.tiene_revision_tecnica:
                    cambios_detectados.append(f'Revisión técnica: {"Sí" if imposicion.tiene_revision_tecnica else "No"}')
                
                if datos_anteriores['numero_expediente'] != imposicion.numero_expediente:
                    cambios_detectados.append('Número de expediente actualizado')
                
                if datos_anteriores['observaciones'] != imposicion.observaciones:
                    cambios_detectados.append('Observaciones actualizadas')
                
                # CONSTRUIR COMENTARIO FINAL
                if comentario_usuario:
                    # Si el usuario escribió algo, usarlo como comentario principal
                    comentario_final = comentario_usuario
                    if cambios_detectados:
                        comentario_final += f" | Cambios: {', '.join(cambios_detectados[:3])}"  # Máximo 3 cambios
                else:
                    # Si no escribió nada, usar los cambios detectados
                    if cambios_detectados:
                        comentario_final = 'Edición: ' + ', '.join(cambios_detectados[:5])  # Máximo 5 cambios
                    else:
                        comentario_final = 'Datos revisados sin cambios significativos'
                
                # SIEMPRE GUARDAR EN HISTORIAL (incluso si no cambió el estado)
                HistorialImposicion.objects.create(
                    id_imposicion=imposicion,
                    idusuario_id=idusuario,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    comentario=comentario_final
                )
                
                return JsonResponse({'ok': True, 'message': 'Imposición actualizada correctamente.'})
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'ok': False, 'error': f'Error al actualizar: {str(e)}'}, status=400)
    
    return redirect('imposicion_placas')


def cambiar_estado_imposicion(request, id):
    """Cambiar el estado de una imposición (AJAX)"""
    if request.method == "POST":
        try:
            idusuario = request.session.get('idusuario')
            imposicion = get_object_or_404(ImposicionPlaca, id_imposicion=id, estado=1)
            
            nuevo_estado = request.POST.get('nuevo_estado')
            comentario = request.POST.get('comentario', '')
            
            if nuevo_estado not in ['pendiente', 'en_tramite', 'completado', 'cancelado']:
                return JsonResponse({'ok': False, 'error': 'Estado no válido'}, status=400)
            
            estado_anterior = imposicion.estado_tramite
            imposicion.estado_tramite = nuevo_estado
            
            if nuevo_estado == 'completado' and not imposicion.fecha_entrega:
                imposicion.fecha_entrega = timezone.now().date()
            
            if nuevo_estado == 'cancelado':
                imposicion.motivo_cancelacion = comentario
            
            imposicion.save()
            
            HistorialImposicion.objects.create(
                id_imposicion=imposicion,
                idusuario_id=idusuario,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                comentario=comentario
            )
            
            return JsonResponse({'ok': True, 'message': f'Estado cambiado a {nuevo_estado}'})
            
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


def eliminar_imposicion(request, id):
    """Eliminar (desactivar) una imposición"""
    try:
        imposicion = get_object_or_404(ImposicionPlaca, id_imposicion=id)
        imposicion.estado = 0
        imposicion.save()
        
        idusuario = request.session.get('idusuario')
        HistorialImposicion.objects.create(
            id_imposicion=imposicion,
            idusuario_id=idusuario,
            estado_anterior=imposicion.estado_tramite,
            estado_nuevo='eliminado',
            comentario='Registro eliminado'
        )
        return redirect('imposicion_placas')
    except Exception as e:
        return HttpResponse(f"<h1>Error: {str(e)}</h1>")


def detalle_imposicion(request, id):
    """Obtener detalle de una imposición (AJAX)"""
    try:
        imposicion = get_object_or_404(ImposicionPlaca, id_imposicion=id, estado=1)
        
        historial = HistorialImposicion.objects.filter(
            id_imposicion=imposicion
        ).select_related('idusuario').order_by('-fecha_cambio')[:10]
        
        historial_data = [{
            'fecha': h.fecha_cambio.strftime('%d/%m/%Y %H:%M'),
            'usuario': h.idusuario.nombrecompleto,
            'estado_anterior': h.estado_anterior,
            'estado_nuevo': h.estado_nuevo,
            'comentario': h.comentario or ''
        } for h in historial]
        
        data = {
            'id_imposicion': imposicion.id_imposicion,
            'numero_placa': imposicion.numero_placa or '',
            'tipo_placa': imposicion.tipo_placa,
            'estado_tramite': imposicion.estado_tramite,
            'fecha_solicitud': imposicion.fecha_solicitud.strftime('%d/%m/%Y'),
            'fecha_tramite': imposicion.fecha_tramite.strftime('%Y-%m-%d') if imposicion.fecha_tramite else '',
            'fecha_entrega': imposicion.fecha_entrega.strftime('%Y-%m-%d') if imposicion.fecha_entrega else '',
            'fecha_vencimiento_tramite': imposicion.fecha_vencimiento_tramite.strftime('%Y-%m-%d') if imposicion.fecha_vencimiento_tramite else '',
            'costo_tramite': float(imposicion.costo_tramite),
            'costo_placa': float(imposicion.costo_placa),
            'otros_costos': float(imposicion.otros_costos),
            'total_costo': float(imposicion.total_costo),
            'tiene_tarjeta_propiedad': imposicion.tiene_tarjeta_propiedad,
            'tiene_soat': imposicion.tiene_soat,
            'tiene_revision_tecnica': imposicion.tiene_revision_tecnica,
            'numero_expediente': imposicion.numero_expediente or '',
            'observaciones': imposicion.observaciones or '',
            'dias_en_tramite': imposicion.dias_en_tramite,
            'esta_vencido': imposicion.esta_vencido,
            'cliente': imposicion.idcliente.razonsocial,
            'vehiculo': imposicion.id_vehiculo.idproducto.nomproducto,
            'serie_motor': imposicion.id_vehiculo.serie_motor,
            'serie_chasis': imposicion.id_vehiculo.serie_chasis,
            'comprobante': imposicion.idventa.numero_comprobante,
            'historial': historial_data
        }
        
        return JsonResponse({'ok': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def obtener_vehiculos_venta(request):
    """Obtener vehículos de una venta específica (AJAX)"""
    idventa = request.GET.get('idventa')
    
    if not idventa:
        return JsonResponse({'ok': False, 'error': 'ID de venta requerido'}, status=400)
    
    try:
        vehiculos_con_imposicion = ImposicionPlaca.objects.filter(
            estado=1
        ).values_list('id_vehiculo_id', flat=True)
        
        detalles = VentaDetalle.objects.filter(
            idventa_id=idventa, tipo_item='vehiculo', estado=1
        ).exclude(
            id_vehiculo_id__in=vehiculos_con_imposicion
        ).select_related('id_vehiculo', 'id_vehiculo__idproducto')
        
        vehiculos = [{
            'id_vehiculo': d.id_vehiculo.id_vehiculo,
            'producto': d.id_vehiculo.idproducto.nomproducto,
            'serie_motor': d.id_vehiculo.serie_motor,
            'serie_chasis': d.id_vehiculo.serie_chasis,
        } for d in detalles]
        
        return JsonResponse({'ok': True, 'vehiculos': vehiculos})
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def imprimir_constancia(request, id):
    """Generar PDF de constancia de imposición de placa"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    imposicion = get_object_or_404(ImposicionPlaca, id_imposicion=id, estado=1)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=20)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=10)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, spaceAfter=5)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
    
    # Encabezado
    elements.append(Paragraph("CONSTANCIA DE IMPOSICIÓN DE PLACA", title_style))
    elements.append(Paragraph(f"N° {str(imposicion.id_imposicion).zfill(6)}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Datos del cliente
    elements.append(Paragraph("<b>DATOS DEL CLIENTE</b>", bold_style))
    elements.append(Spacer(1, 5))
    
    data_cliente = [
        ['Cliente:', imposicion.idcliente.razonsocial],
        ['Documento:', imposicion.idcliente.numdoc or 'N/A'],
        ['Teléfono:', imposicion.idcliente.telefono or 'N/A'],
        ['Dirección:', imposicion.idcliente.direccion or 'N/A'],
    ]
    
    t = Table(data_cliente, colWidths=[4*cm, 12*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))
    
    # Datos del vehículo
    elements.append(Paragraph("<b>DATOS DEL VEHÍCULO</b>", bold_style))
    elements.append(Spacer(1, 5))
    
    data_vehiculo = [
        ['Vehículo:', imposicion.id_vehiculo.idproducto.nomproducto],
        ['Serie Motor:', imposicion.id_vehiculo.serie_motor],
        ['Serie Chasis:', imposicion.id_vehiculo.serie_chasis],
        ['N° Placa:', imposicion.numero_placa or 'Pendiente de asignación'],
    ]
    
    t2 = Table(data_vehiculo, colWidths=[4*cm, 12*cm])
    t2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 15))
    
    # Datos del trámite
    elements.append(Paragraph("<b>DATOS DEL TRÁMITE</b>", bold_style))
    elements.append(Spacer(1, 5))
    
    tipo_placa_display = dict(ImposicionPlaca.TIPO_PLACA_CHOICES).get(imposicion.tipo_placa, imposicion.tipo_placa)
    estado_display = dict(ImposicionPlaca.ESTADO_CHOICES).get(imposicion.estado_tramite, imposicion.estado_tramite)
    
    data_tramite = [
        ['Tipo de Placa:', tipo_placa_display],
        ['Estado:', estado_display],
        ['Fecha Solicitud:', imposicion.fecha_solicitud.strftime('%d/%m/%Y')],
        ['N° Expediente:', imposicion.numero_expediente or 'N/A'],
    ]
    
    t3 = Table(data_tramite, colWidths=[4*cm, 12*cm])
    t3.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t3)
    elements.append(Spacer(1, 15))
    
    # Costos
    elements.append(Paragraph("<b>DETALLE DE COSTOS</b>", bold_style))
    elements.append(Spacer(1, 5))
    
    data_costos = [
        ['Concepto', 'Monto'],
        ['Costo de Trámite', f'S/ {imposicion.costo_tramite:.2f}'],
        ['Costo de Placa', f'S/ {imposicion.costo_placa:.2f}'],
        ['Otros Costos', f'S/ {imposicion.otros_costos:.2f}'],
        ['TOTAL', f'S/ {imposicion.total_costo:.2f}'],
    ]
    
    t4 = Table(data_costos, colWidths=[8*cm, 4*cm])
    t4.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t4)
    
    # Observaciones
    if imposicion.observaciones:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>OBSERVACIONES</b>", bold_style))
        elements.append(Paragraph(imposicion.observaciones, normal_style))
    
    # Firma
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("_" * 40, ParagraphStyle('Center', alignment=TA_CENTER)))
    elements.append(Paragraph("Firma y Sello", ParagraphStyle('Center', alignment=TA_CENTER, fontSize=10)))
    
    # Pie de página
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Documento generado el {timezone.now().strftime('%d/%m/%Y %H:%M')}", 
                              ParagraphStyle('Footer', alignment=TA_CENTER, fontSize=8, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = FileResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="constancia_placa_{imposicion.id_imposicion}.pdf"'
    
    return response