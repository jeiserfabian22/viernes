from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

from software.models.CreditoModel import Credito
from software.models.VentasModel import Ventas
from software.models.CuotasVentaModel import CuotasVenta
from software.models.PagoCuotaModel import PagoCuota

from software.models.ClienteModel import Cliente
from software.models.UsuarioModel import Usuario
from software.models.TipoPagoModel import TipoPago
from software.decorators import requiere_caja_aperturada
from software.models.movimientoCajaModel import MovimientoCaja
from software.models.AperturaCierreCajaModel import AperturaCierreCaja


def creditos(request):
    """
    Vista principal del módulo de créditos
    Muestra el listado de todos los créditos con filtros
    """
    # Validación de sesión
    id_tipo_usuario = request.session.get('idtipousuario')
    if not id_tipo_usuario:
        return redirect('login')
    
    # Obtener parámetros de filtro
    estado_filtro = request.GET.get('estado', 'todos')
    busqueda = request.GET.get('busqueda', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Query base
    creditos_list = Credito.objects.filter(estado=1).select_related(
        'idventa__idcliente',
        'idventa__idusuario'
    )
    
    # Filtrar por estado
    if estado_filtro != 'todos':
        creditos_list = creditos_list.filter(estado_credito=estado_filtro)
    
    # Filtrar por búsqueda (código, cliente, comprobante)
    if busqueda:
        creditos_list = creditos_list.filter(
            Q(codigo_credito__icontains=busqueda) |
            Q(idventa__idcliente__razonsocial__icontains=busqueda) |
            Q(idventa__idcliente__numdoc__icontains=busqueda) |
            Q(idventa__numero_comprobante__icontains=busqueda)
        )
    
    # Filtrar por rango de fechas
    if fecha_desde:
        creditos_list = creditos_list.filter(fecha_credito__gte=fecha_desde)
    if fecha_hasta:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
        creditos_list = creditos_list.filter(fecha_credito__lte=fecha_hasta_dt)
    
    # Ordenar por fecha más reciente
    creditos_list = creditos_list.order_by('-fecha_credito')
    
    # Calcular estadísticas
    total_creditos = creditos_list.count()
    total_activos = creditos_list.filter(estado_credito='activo').count()
    total_mora = creditos_list.filter(estado_credito='mora').count()
    total_pagados = creditos_list.filter(estado_credito='pagado').count()
    
    monto_total_creditos = creditos_list.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    saldo_total_pendiente = creditos_list.aggregate(Sum('saldo_pendiente'))['saldo_pendiente__sum'] or 0
    
    # Contexto
    data = {
        'creditos': creditos_list,
        'total_creditos': total_creditos,
        'total_activos': total_activos,
        'total_mora': total_mora,
        'total_pagados': total_pagados,
        'monto_total_creditos': monto_total_creditos,
        'saldo_total_pendiente': saldo_total_pendiente,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'creditos/creditos.html', data)


def detalle_credito(request, idcredito):
    """
    Vista de detalle de un crédito específico
    Muestra todas las cuotas y el historial de pagos
    """
    credito = get_object_or_404(Credito, idcredito=idcredito)
    
    # Obtener cuotas del crédito
    cuotas = CuotasVenta.objects.filter(
        idventa=credito.idventa,
        estado=1
    ).order_by('numero_cuota')
    
    # Para cada cuota, obtener su historial de pagos
    cuotas_con_pagos = []
    for cuota in cuotas:
        pagos = PagoCuota.objects.filter(
            idcuotaventa=cuota,
            estado=1
        ).select_related('idusuario', 'id_tipo_pago').order_by('-fecha_pago')
        
        cuotas_con_pagos.append({
            'cuota': cuota,
            'pagos': pagos
        })
    
    # Calcular totales
    total_pagado = sum(cuota.monto_pagado for cuota in cuotas)
    total_pendiente = sum(cuota.saldo_cuota for cuota in cuotas)
    
    # Verificar cuotas vencidas
    hoy = timezone.now().date()
    cuotas_vencidas = cuotas.filter(
        estado_pago__in=['Pendiente', 'Parcial'],
        fecha_vencimiento__lt=hoy
    ).count()
    
    data = {
        'credito': credito,
        'cuotas_con_pagos': cuotas_con_pagos,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'cuotas_vencidas': cuotas_vencidas,
    }
    
    return render(request, 'creditos/detalle_credito.html', data)


@requiere_caja_aperturada
def pagar_cuota(request, idcuotaventa):
    cuota = get_object_or_404(CuotasVenta, idcuotaventa=idcuotaventa)
    credito = get_object_or_404(Credito, idventa=cuota.idventa)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                monto_pago = Decimal(request.POST.get('monto_pago', 0))
                id_tipo_pago = int(request.POST.get('id_tipo_pago'))
                numero_operacion = request.POST.get('numero_operacion', '').strip()
                observaciones = request.POST.get('observaciones', '').strip()
                idusuario = request.session.get('idusuario')
                
                # Validaciones...
                if monto_pago <= 0:
                    return JsonResponse({
                        'ok': False,
                        'error': 'El monto del pago debe ser mayor a 0'
                    }, status=400)
                
                if monto_pago > cuota.saldo_cuota:
                    return JsonResponse({
                        'ok': False,
                        'error': f'El monto no puede ser mayor al saldo de la cuota (S/ {cuota.saldo_cuota})'
                    }, status=400)
                
                # Verificar caja abierta
                apertura_actual = AperturaCierreCaja.objects.filter(
                    idusuario_id=idusuario,
                    estado__in=['abierta', 'reabierta']
                ).first()
                
                if not apertura_actual:
                    return JsonResponse({
                        'ok': False,
                        'error': 'No tiene una caja abierta. Debe aperturar una caja primero.'
                    }, status=400)
                
                # Registrar el pago
                pago = PagoCuota.objects.create(
                    idcuotaventa=cuota,
                    idusuario_id=idusuario,
                    id_tipo_pago_id=id_tipo_pago,
                    monto_pago=monto_pago,
                    numero_operacion=numero_operacion,
                    observaciones=observaciones,
                    estado=1
                )
                
                # ✅ Registrar ingreso en movimientos de caja CON id_apertura
                descripcion_movimiento = f"Pago cuota #{cuota.numero_cuota} - Crédito {credito.codigo_credito} - Cliente: {credito.idventa.idcliente.razonsocial}"
                
                movimiento_caja = MovimientoCaja.objects.create(
                    id_caja=apertura_actual.id_caja,
                    id_movimiento=apertura_actual,  # ✅ AGREGAR ESTO
                    idusuario_id=idusuario,
                    tipo_movimiento='ingreso',
                    monto=monto_pago,
                    descripcion=descripcion_movimiento,
                    idventa=None,
                    estado=1
                )
                
                print(f"✅ MOVIMIENTO DE CAJA CREADO - ID: {movimiento_caja.id_movimiento_caja}")
                print(f"   Asociado a apertura: {apertura_actual.id_movimiento}")
                
                # Actualizar la cuota
                cuota.monto_pagado += monto_pago
                cuota.saldo_cuota -= monto_pago
                
                if cuota.saldo_cuota == 0:
                    cuota.estado_pago = 'Pagado'
                    cuota.fecha_pago = timezone.now()
                elif cuota.monto_pagado > 0:
                    cuota.estado_pago = 'Parcial'
                
                cuota.save()
                
                # Actualizar el crédito
                credito.actualizar_estado()
                
                return JsonResponse({
                    'ok': True,
                    'message': 'Pago registrado correctamente',
                    'nuevo_saldo': float(cuota.saldo_cuota),
                    'estado_cuota': cuota.estado_pago,
                    'idpago': pago.idpagocuota
                })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'ok': False,
                'error': f'Error al procesar el pago: {str(e)}'
            }, status=500)
    
    # GET: Mostrar formulario
    tipos_pago = TipoPago.objects.filter(estado=1)
    
    data = {
        'cuota': cuota,
        'credito': credito,
        'tipos_pago': tipos_pago,
    }
    
    return render(request, 'creditos/pagar_cuota.html', data)

def anular_pago(request, idpagocuota):
    """
    Anular un pago de cuota (cambia estado a 0)
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                pago = get_object_or_404(PagoCuota, idpagocuota=idpagocuota)
                cuota = pago.idcuotaventa
                credito = Credito.objects.get(idventa=cuota.idventa)
                
                # Revertir el monto en la cuota
                cuota.monto_pagado -= pago.monto_pago
                cuota.saldo_cuota += pago.monto_pago
                
                if cuota.monto_pagado == 0:
                    cuota.estado_pago = 'Pendiente'
                    cuota.fecha_pago = None
                elif cuota.saldo_cuota > 0:
                    cuota.estado_pago = 'Parcial'
                
                cuota.save()
                
                # ⭐ MEJORADO: Buscar el movimiento usando filtros más precisos
                movimiento = MovimientoCaja.objects.filter(
                    idusuario=pago.idusuario,
                    tipo_movimiento='ingreso',
                    monto=pago.monto_pago,
                    fecha_movimiento__date=pago.fecha_pago.date(),
                    descripcion__icontains=credito.codigo_credito,  # ✅ Más preciso
                    estado=1
                ).first()
                
                if movimiento:
                    movimiento.estado = 0
                    movimiento.save()
                    print(f"✅ Movimiento de caja anulado: ID {movimiento.id_movimiento_caja}")
                
                # Anular el pago
                pago.estado = 0
                pago.save()
                
                # Actualizar el crédito
                credito.actualizar_estado()
                
                return JsonResponse({
                    'ok': True,
                    'message': 'Pago anulado correctamente'
                })
            
        except Exception as e:
            return JsonResponse({
                'ok': False,
                'error': f'Error al anular el pago: {str(e)}'
            }, status=500)
    
    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=400)


def reportes_creditos(request):
    """
    Vista de reportes y estadísticas de créditos
    """
    # Obtener fechas del filtro o usar mes actual
    hoy = timezone.now()
    fecha_desde = request.GET.get('fecha_desde', hoy.replace(day=1).strftime('%Y-%m-%d'))
    fecha_hasta = request.GET.get('fecha_hasta', hoy.strftime('%Y-%m-%d'))
    
    # Convertir a datetime
    fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
    fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    
    # Créditos en el periodo
    creditos_periodo = Credito.objects.filter(
        estado=1,
        fecha_credito__range=[fecha_desde_dt, fecha_hasta_dt]
    )
    
    # Estadísticas generales
    total_creditos_periodo = creditos_periodo.count()
    monto_total_financiado = creditos_periodo.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    
    # Créditos por estado
    creditos_activos = creditos_periodo.filter(estado_credito='activo').count()
    creditos_mora = creditos_periodo.filter(estado_credito='mora').count()
    creditos_pagados = creditos_periodo.filter(estado_credito='pagado').count()
    
    # Cuotas vencidas en el sistema (todas, no solo del periodo)
    cuotas_vencidas = CuotasVenta.objects.filter(
        estado=1,
        estado_pago__in=['Pendiente', 'Parcial'],
        fecha_vencimiento__lt=hoy.date()
    ).select_related('idventa__idcliente')
    
    monto_vencido = sum(cuota.saldo_cuota for cuota in cuotas_vencidas)
    
    # Cuotas por vencer en los próximos 30 días
    fecha_limite = hoy.date() + timedelta(days=30)
    cuotas_por_vencer = CuotasVenta.objects.filter(
        estado=1,
        estado_pago__in=['Pendiente', 'Parcial'],
        fecha_vencimiento__range=[hoy.date(), fecha_limite]
    ).select_related('idventa__idcliente').order_by('fecha_vencimiento')
    
    monto_por_vencer = sum(cuota.saldo_cuota for cuota in cuotas_por_vencer)
    
    # Top 10 clientes con mayor deuda
    clientes_deuda = {}
    creditos_activos_todos = Credito.objects.filter(
        estado=1,
        estado_credito__in=['activo', 'mora']
    )
    
    for credito in creditos_activos_todos:
        cliente = credito.idventa.idcliente
        if cliente.idcliente not in clientes_deuda:
            clientes_deuda[cliente.idcliente] = {
                'cliente': cliente,
                'total_deuda': Decimal('0'),
                'creditos': 0
            }
        clientes_deuda[cliente.idcliente]['total_deuda'] += credito.saldo_pendiente
        clientes_deuda[cliente.idcliente]['creditos'] += 1
    
    top_clientes = sorted(
        clientes_deuda.values(),
        key=lambda x: x['total_deuda'],
        reverse=True
    )[:10]
    
    # Pagos recibidos en el periodo
    pagos_periodo = PagoCuota.objects.filter(
        estado=1,
        fecha_pago__range=[fecha_desde_dt, fecha_hasta_dt]
    )
    
    total_pagos_recibidos = pagos_periodo.aggregate(Sum('monto_pago'))['monto_pago__sum'] or 0
    cantidad_pagos = pagos_periodo.count()
    
    # Datos para gráficos - Créditos por mes (últimos 12 meses)
    hace_12_meses = hoy - timedelta(days=365)
    creditos_por_mes = []
    
    for i in range(12):
        mes_inicio = (hoy - timedelta(days=30*i)).replace(day=1)
        if i == 0:
            mes_fin = hoy
        else:
            mes_fin = mes_inicio.replace(day=28) + timedelta(days=4)
            mes_fin = mes_fin.replace(day=1) - timedelta(days=1)
        
        count = Credito.objects.filter(
            estado=1,
            fecha_credito__range=[mes_inicio, mes_fin]
        ).count()
        
        creditos_por_mes.insert(0, {
            'mes': mes_inicio.strftime('%b %Y'),
            'cantidad': count
        })
    
    data = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_creditos_periodo': total_creditos_periodo,
        'monto_total_financiado': monto_total_financiado,
        'creditos_activos': creditos_activos,
        'creditos_mora': creditos_mora,
        'creditos_pagados': creditos_pagados,
        'cuotas_vencidas': cuotas_vencidas,
        'monto_vencido': monto_vencido,
        'cuotas_por_vencer': cuotas_por_vencer,
        'monto_por_vencer': monto_por_vencer,
        'top_clientes': top_clientes,
        'total_pagos_recibidos': total_pagos_recibidos,
        'cantidad_pagos': cantidad_pagos,
        'creditos_por_mes': creditos_por_mes,
    }
    
    return render(request, 'creditos/reportes.html', data)


def imprimir_cronograma_credito(request, eid):
    """
    Genera un PDF con el cronograma de cuotas del crédito
    Formato A4 con diseño uniforme - Encabezados integrados en las tablas
    """
    try:
        import os
        from django.conf import settings
        from software.models.VentaDetalleModel import VentaDetalle
        from software.models.empresaModel import Empresa
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        idventa = decrypt_id(eid)
        if not idventa:
            return HttpResponse("URL inválida", status=400)
        
        # Obtener la venta y el crédito
        venta = get_object_or_404(Ventas, idventa=idventa)
        
        try:
            credito = Credito.objects.get(idventa=venta)
        except Credito.DoesNotExist:
            return HttpResponse("Esta venta no tiene un crédito asociado.", status=400)
        

        # OBTENER LA EMPRESA DE LA VENTA
        try:
            if venta.idempresa:
                empresa = Empresa.objects.get(idempresa=venta.idempresa, activo=True)
            else:
                # Si no tiene empresa asignada, usar la primera activa
                empresa = Empresa.objects.filter(activo=True).first()
            
            if not empresa:
                return HttpResponse("No se encontró información de la empresa. Configure los datos en el sistema.", status=400)
        except Empresa.DoesNotExist:
            return HttpResponse(f"La empresa con ID {venta.idempresa} no existe en el sistema.", status=400)   
        
        # Obtener las cuotas
        cuotas = CuotasVenta.objects.filter(idventa=venta, estado=1).order_by('numero_cuota')
        
        if not cuotas.exists():
            return HttpResponse("No hay cuotas para este crédito.", status=400)
        
        # OBTENER DETALLE DE VEHICULOS/REPUESTOS
        detalles = VentaDetalle.objects.filter(idventa=venta, estado=1).select_related(
            'id_vehiculo__idproducto',
            'id_repuesto_comprado__id_repuesto'
        )
        
        # Crear el PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=6*mm,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        style_subtitle = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#424242'),
            spaceAfter=3*mm,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        style_normal = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=2*mm,
            alignment=TA_LEFT
        )
        
        style_bold = ParagraphStyle(
            'CustomBold',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=2*mm
        )
        
        style_small = ParagraphStyle(
            'SmallText',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            spaceAfter=0.5*mm,
            leading=9
        )
        
        # ==========================================
        # LOGO (si existe)
        # ==========================================
        if empresa.logo:
            try:
                # Intentar cargar desde MEDIA_ROOT
                logo_path = os.path.join(settings.MEDIA_ROOT, empresa.logo)
                
                # Si no existe en media, intentar en static
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(settings.BASE_DIR, 'static', empresa.logo)
                
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=40*mm, height=25*mm)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 3*mm))
                else:
                    print(f"⚠️ Logo no encontrado en: {logo_path}")
            except Exception as e:
                print(f"❌ Error al cargar el logo: {str(e)}")
        # ==========================================
        # ENCABEZADO
        # ==========================================
        nombre_empresa = empresa.razonsocial if empresa.razonsocial else empresa.nombrecomercial
        elements.append(Paragraph(nombre_empresa.upper(), style_title))
        elements.append(Paragraph(f"RUC: {empresa.ruc}", style_normal))
        elements.append(Paragraph(empresa.direccion.upper(), style_normal))
        elements.append(Paragraph(f"Telf: {empresa.telefono}", style_normal))
        if empresa.pagina:
            elements.append(Paragraph(f"Pagina: {empresa.pagina}", style_normal))
        if empresa.slogan:
            elements.append(Paragraph(f"Slogan: {empresa.slogan}", style_normal))

        
        elements.append(Spacer(1, 8*mm))
        
        # ==========================================
        # TÍTULO DEL DOCUMENTO
        # ==========================================
        elements.append(Paragraph("CRONOGRAMA DE PAGOS - CRÉDITO", style_subtitle))
        elements.append(Paragraph(f"Solicitud de Crédito: {credito.codigo_credito}", style_bold))
        
        elements.append(Spacer(1, 5*mm))
        
        # INFORMACIÓN DEL CRÉDITO
        fecha_credito = credito.fecha_credito.strftime('%d/%m/%Y')
        
        data_credito = [
            # PRIMERA FILA: Encabezado azul (con SPAN para ocupar ambas columnas)
            ['DATOS DEL CRÉDITO', ''],
            # Contenido normal
            ['Cliente:', venta.idcliente.razonsocial],
            ['DNI/RUC:', venta.idcliente.numdoc or '---'],
            ['Teléfono:', venta.idcliente.telefono or '---'],
            ['Comprobante:', venta.numero_comprobante],
            ['Fecha de Venta:', fecha_credito],
        ]
        
        table_credito = Table(data_credito, colWidths=[45*mm, 145*mm])
        table_credito.setStyle(TableStyle([
            # ENCABEZADO (primera fila)
            ('SPAN', (0, 0), (1, 0)),  # Combinar ambas columnas en fila 0
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('ALIGN', (0, 0), (1, 0), 'LEFT'),
            ('TOPPADDING', (0, 0), (1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (1, 0), 4),
            ('LEFTPADDING', (0, 0), (1, 0), 5),
            
            # CONTENIDO (resto de filas)
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#424242')),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 1), (-1, -1), 5),
            ('RIGHTPADDING', (0, 1), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table_credito)
        
        elements.append(Spacer(1, 6*mm))
        
      
        # DETALLE DE VEHÍCULOS/REPUESTOS FINANCIADOS
        #Primera fila: Encabezado azul
        data_productos = [
            ['VEHÍCULOS/REPUESTOS FINANCIADOS', '', '', '', '', ''],  # Encabezado azul
            ['N°', 'DESCRIPCIÓN', 'SERIE/CODIGO', 'CANT.', 'P. UNIT.', 'SUBTOTAL']  # Títulos de columnas
        ]
        
        item_num = 1
        for detalle in detalles:
            if detalle.tipo_item == 'vehiculo' and detalle.id_vehiculo:
                vehiculo = detalle.id_vehiculo
                nombre = vehiculo.idproducto.nomproducto
                serie_info = f"Motor: {vehiculo.serie_motor}\nChasis: {vehiculo.serie_chasis}"
                precio = detalle.precio_venta_credito if detalle.precio_venta_credito else detalle.precio_venta_contado
                
            elif detalle.tipo_item == 'repuesto' and detalle.id_repuesto_comprado:
                repuesto = detalle.id_repuesto_comprado
                nombre = repuesto.id_repuesto.nombre
                codigo = repuesto.codigo_barras or 'S/N'
                serie_info = f"Código: {codigo}"
                precio = detalle.precio_venta_credito if detalle.precio_venta_credito else detalle.precio_venta_contado
            else:
                continue
            
            data_productos.append([
                str(item_num),
                nombre,
                serie_info,
                str(detalle.cantidad),
                f"S/ {precio:,.2f}",
                f"S/ {detalle.subtotal:,.2f}"
            ])
            item_num += 1
        
        col_widths_productos = [12*mm, 70*mm, 55*mm, 15*mm, 19*mm, 19*mm]
        
        table_productos = Table(data_productos, colWidths=col_widths_productos)
        table_productos.setStyle(TableStyle([
            # ENCABEZADO AZUL (primera fila)
            ('SPAN', (0, 0), (5, 0)),  # Combinar todas las columnas en fila 0
            ('BACKGROUND', (0, 0), (5, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (5, 0), colors.white),
            ('FONTNAME', (0, 0), (5, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (5, 0), 11),
            ('ALIGN', (0, 0), (5, 0), 'LEFT'),
            ('TOPPADDING', (0, 0), (5, 0), 4),
            ('BOTTOMPADDING', (0, 0), (5, 0), 4),
            ('LEFTPADDING', (0, 0), (5, 0), 5),
            
            # TÍTULOS DE COLUMNAS (segunda fila)
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 8),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, 1), 'MIDDLE'),
            
            # CONTENIDO (resto de filas)
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, -1), 8),
            ('ALIGN', (0, 2), (0, -1), 'CENTER'),
            ('ALIGN', (1, 2), (2, -1), 'LEFT'),
            ('ALIGN', (3, 2), (3, -1), 'CENTER'),
            ('ALIGN', (4, 2), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 2), (-1, -1), 'TOP'),
            
            # Bordes y padding
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_productos)
        
        elements.append(Spacer(1, 6*mm))
        
        # RESUMEN FINANCIERO
        total_interes = sum(cuota.interes for cuota in cuotas)
        total_con_interes = sum(cuota.total for cuota in cuotas)
        
        data_resumen = [
            # PRIMERA FILA: Encabezado azul
            ['RESUMEN FINANCIERO', ''],
            # Contenido
            ['Monto Total (precio crédito):', f"S/ {venta.total_venta:,.2f}"],
            ['Adelanto:', f"S/ {credito.monto_adelanto:,.2f}"],
            ['Saldo a Financiar:', f"S/ {credito.saldo_pendiente:,.2f}"],
            ['Cantidad de Cuotas:', f"{credito.cantidad_cuotas}"],
            ['Total Intereses:', f"S/ {total_interes:,.2f}"],
            ['Total a Pagar (con intereses):', f"S/ {total_con_interes:,.2f}"],
            ['Estado del Crédito:', credito.estado_credito.upper()],
        ]
        
        table_resumen = Table(data_resumen, colWidths=[95*mm, 95*mm])
        table_resumen.setStyle(TableStyle([
            # ENCABEZADO (primera fila)
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('ALIGN', (0, 0), (1, 0), 'LEFT'),
            ('TOPPADDING', (0, 0), (1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (1, 0), 4),
            ('LEFTPADDING', (0, 0), (1, 0), 5),
            
            # CONTENIDO
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Resaltar "Total a Pagar"
            ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#fff9c4')),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 1), (-1, -1), 5),
            ('RIGHTPADDING', (0, 1), (-1, -1), 5),
        ]))
        elements.append(table_resumen)
        
        elements.append(Spacer(1, 6*mm))
        
        # TABLA DE CUOTAS
        data_cuotas = [
            #PRIMERA FILA: Encabezado azul
            ['DETALLE DE CUOTAS', '', '', '', '', '', '', ''],
            # Segunda fila: Títulos de columnas
            ['N°', 'F. Vencimiento', 'Monto', 'Interés', 'Total', 'Pagado', 'Saldo', 'Estado']
        ]
        
        # Datos de cada cuota
        for cuota in cuotas:
            fecha_venc = cuota.fecha_vencimiento.strftime('%d/%m/%Y')
            
            data_cuotas.append([
                str(cuota.numero_cuota),
                fecha_venc,
                f"S/ {cuota.monto:,.2f}",
                f"S/ {cuota.interes:,.2f}",
                f"S/ {cuota.total:,.2f}",
                f"S/ {cuota.monto_pagado:,.2f}",
                f"S/ {cuota.saldo_cuota:,.2f}",
                cuota.estado_pago
            ])
        
        # Fila de totales
        total_monto = sum(c.monto for c in cuotas)
        total_interes_cuotas = sum(c.interes for c in cuotas)
        total_total = sum(c.total for c in cuotas)
        total_pagado = sum(c.monto_pagado for c in cuotas)
        total_saldo = sum(c.saldo_cuota for c in cuotas)
        
        data_cuotas.append([
            '',
            'TOTALES:',
            f"S/ {total_monto:,.2f}",
            f"S/ {total_interes_cuotas:,.2f}",
            f"S/ {total_total:,.2f}",
            f"S/ {total_pagado:,.2f}",
            f"S/ {total_saldo:,.2f}",
            ''
        ])
        
        table_cuotas = Table(data_cuotas, colWidths=[12*mm, 28*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 22*mm])
        table_cuotas.setStyle(TableStyle([
            # ENCABEZADO AZUL (primera fila)
            ('SPAN', (0, 0), (7, 0)),
            ('BACKGROUND', (0, 0), (7, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (7, 0), colors.white),
            ('FONTNAME', (0, 0), (7, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (7, 0), 11),
            ('ALIGN', (0, 0), (7, 0), 'LEFT'),
            ('TOPPADDING', (0, 0), (7, 0), 4),
            ('BOTTOMPADDING', (0, 0), (7, 0), 4),
            ('LEFTPADDING', (0, 0), (7, 0), 5),
            
            # TÍTULOS DE COLUMNAS (segunda fila)
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 8),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            
            # CONTENIDO
            ('FONTNAME', (0, 2), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, -2), 8),
            ('ALIGN', (0, 2), (0, -2), 'CENTER'),
            ('ALIGN', (1, 2), (1, -2), 'CENTER'),
            ('ALIGN', (2, 2), (-2, -2), 'RIGHT'),
            ('ALIGN', (-1, 2), (-1, -2), 'CENTER'),
            
            # FILA DE TOTALES
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 8),
            ('ALIGN', (1, -1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, -1), (-2, -1), 'RIGHT'),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(table_cuotas)
        
        elements.append(Spacer(1, 10*mm))
        
        # PIE DE PÁGINA / NOTAS
        style_note = ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_JUSTIFY,
            spaceAfter=2*mm
        )
        
        elements.append(Paragraph("NOTAS IMPORTANTES:", style_bold))
        elements.append(Paragraph(
            "• Las cuotas vencidas generan intereses moratorios según lo acordado.",
            style_note
        ))
        elements.append(Paragraph(
            "• Los pagos deben realizarse en las oficinas de la empresa o a través de los canales autorizados.",
            style_note
        ))
        elements.append(Paragraph(
            "• Conserve este cronograma para su control de pagos.",
            style_note
        ))
        elements.append(Paragraph(
            f"• Fecha de emisión: {timezone.now().strftime('%d/%m/%Y %I:%M %p')}",
            style_note
        ))
        
        elements.append(Spacer(1, 15*mm))
        
        # Firma
        data_firma = [
            ['_________________________', '_________________________'],
            ['Firma del Cliente', 'Firma del Vendedor'],
        ]
        table_firma = Table(data_firma, colWidths=[95*mm, 95*mm])
        table_firma.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, 1), 5),
        ]))
        elements.append(table_firma)
        
        # Construir el PDF
        doc.build(elements)
        
        buffer.seek(0)
        
        response = FileResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="cronograma_{credito.codigo_credito}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"ERROR al generar cronograma: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error al generar el cronograma: {str(e)}", status=500)


def buscar_cuotas_cliente(request):
    """
    AJAX: Buscar cuotas pendientes de un cliente específico
    """
    if request.method == 'GET':
        idcliente = request.GET.get('idcliente')
        
        if not idcliente:
            return JsonResponse({'error': 'Cliente no especificado'}, status=400)
        
        # Obtener créditos activos del cliente
        creditos = Credito.objects.filter(
            idventa__idcliente_id=idcliente,
            estado=1,
            estado_credito__in=['activo', 'mora']
        )
        
        resultado = []
        for credito in creditos:
            cuotas = CuotasVenta.objects.filter(
                idventa=credito.idventa,
                estado=1,
                estado_pago__in=['Pendiente', 'Parcial']
            ).order_by('numero_cuota')
            
            for cuota in cuotas:
                resultado.append({
                    'idcuotaventa': cuota.idcuotaventa,
                    'codigo_credito': credito.codigo_credito,
                    'numero_cuota': cuota.numero_cuota,
                    'fecha_vencimiento': cuota.fecha_vencimiento.strftime('%d/%m/%Y'),
                    'total': float(cuota.total),
                    'monto_pagado': float(cuota.monto_pagado),
                    'saldo_cuota': float(cuota.saldo_cuota),
                    'estado_pago': cuota.estado_pago,
                    'vencida': cuota.esta_vencida()
                })
        
        return JsonResponse(resultado, safe=False)
    
    return JsonResponse({'error': 'Método no permitido'}, status=400)

def imprimir_recibo_pago(request, idpagocuota):
    """
    Genera un PDF del recibo de pago de cuota en formato TICKET 80mm
    Estructura exacta del recibo físico de D CREDITOS E.I.R.L
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from io import BytesIO
        import os
        from django.conf import settings
        from software.models.empresaModel import Empresa
        from django.utils import timezone
        
        # Obtener el pago
        pago = get_object_or_404(PagoCuota, idpagocuota=idpagocuota)
        cuota = pago.idcuotaventa
        credito = Credito.objects.get(idventa=cuota.idventa)
        venta = cuota.idventa
        cliente = venta.idcliente
        
        # ✅ OBTENER LA EMPRESA
        try:
            if venta.idempresa:
                empresa = Empresa.objects.get(idempresa=venta.idempresa, activo=True)
            else:
                empresa = Empresa.objects.filter(activo=True).first()
            
            if not empresa:
                return HttpResponse("No se encontró información de la empresa.", status=400)
        except Empresa.DoesNotExist:
            return HttpResponse(f"La empresa no existe en el sistema.", status=400)
        
        # ✅ OBTENER VEHÍCULO Y PLACA
        from software.models.VentaDetalleModel import VentaDetalle
        detalles = VentaDetalle.objects.filter(idventa=venta, estado=1, tipo_item='vehiculo').select_related(
            'id_vehiculo__idproducto'
        )
        
        placa_vehiculo = "SIN PLACA"
        nombre_vehiculo = "Vehículo"
        
        if detalles.exists():
            primer_vehiculo = detalles.first().id_vehiculo
            if primer_vehiculo:
                nombre_vehiculo = primer_vehiculo.idproducto.nomproducto
                # ✅ OBTENER PLACA
                if primer_vehiculo.placas and primer_vehiculo.placas.strip():
                    placa_vehiculo = primer_vehiculo.placas.strip()
                else:
                    placa_vehiculo = "PENDIENTE"
        
        # Generar número de recibo
        numero_recibo = f"RI{str(venta.id_sucursal.id_sucursal).zfill(2)}-{str(idpagocuota).zfill(6)}"
        
        # ✅ CALCULAR CUOTAS PENDIENTES Y ATRASADAS
        cuotas_totales = CuotasVenta.objects.filter(idventa=venta, estado=1).count()
        cuotas_pagadas = CuotasVenta.objects.filter(idventa=venta, estado=1, estado_pago='Pagado').count()
        cuotas_pendientes = cuotas_totales - cuotas_pagadas
        
        # Cuotas atrasadas (vencidas y no pagadas)
        hoy = timezone.now().date()
        cuotas_atrasadas = CuotasVenta.objects.filter(
            idventa=venta,
            estado=1,
            estado_pago__in=['Pendiente', 'Parcial'],
            fecha_vencimiento__lt=hoy
        ).count()
        
        # Crear el PDF en memoria
        buffer = BytesIO()
        ticket_width = 80 * mm
        ticket_height = 800 * mm
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(ticket_width, ticket_height),
            rightMargin=3*mm,
            leftMargin=3*mm,
            topMargin=3*mm,
            bottomMargin=3*mm
        )
        
        ancho_util = 74 * mm
        elements = []
        styles = getSampleStyleSheet()
        
        # ==========================================
        # ESTILOS
        # ==========================================
        style_company = ParagraphStyle(
            'CompanyName',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=0.5*mm,
            leading=10
        )
        
        style_normal_center = ParagraphStyle(
            'NormalCenter',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            spaceAfter=0.5*mm,
            leading=8
        )
        
        style_label = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_LEFT,
            spaceAfter=0.5*mm,
            leading=8
        )
        
        style_title = ParagraphStyle(
            'Title',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=1*mm,
            leading=10
        )
        
        style_importe = ParagraphStyle(
            'Importe',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=1*mm,
            leading=14
        )
        
        style_small = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_CENTER,
            spaceAfter=0.5*mm,
            leading=7
        )
        
        style_small_left = ParagraphStyle(
            'SmallLeft',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_LEFT,
            spaceAfter=0.5*mm,
            leading=7
        )
        
        # ==========================================
        # LOGO
        # ==========================================
        if empresa.logo:
            try:
                logo_path = os.path.join(settings.MEDIA_ROOT, empresa.logo)
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(settings.BASE_DIR, 'static', empresa.logo)
                
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=35*mm, height=20*mm)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 2*mm))
            except Exception as e:
                print(f"No se pudo cargar el logo: {str(e)}")
        
        # ==========================================
        # DATOS DE LA EMPRESA
        # ==========================================
        nombre_empresa = empresa.razonsocial if empresa.razonsocial else empresa.nombrecomercial
        elements.append(Paragraph(nombre_empresa.upper(), style_company))
        
        # Dirección (ajustar formato según imagen)
        direccion_local = empresa.direccion.upper() if empresa.direccion else "TARAPOTO"
        elements.append(Paragraph(f"Local: {direccion_local}", style_small))
        
        elements.append(Paragraph(f"TELEFONOS: {empresa.telefono}", style_small))
        elements.append(Paragraph(f"<b>RUC: {empresa.ruc}</b>", style_normal_center))
        elements.append(Paragraph(f"<b>RECIBO {numero_recibo}</b>", style_title))
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # DATOS DEL CLIENTE
        # ==========================================
        elements.append(Paragraph("<b>CLIENTE</b>", style_label))
        elements.append(Paragraph(f"DNI: {cliente.numdoc or '---'}", style_label))
        elements.append(Paragraph(cliente.razonsocial.upper(), style_small_left))
        
        direccion = cliente.direccion or 'JR MPSM'
        elements.append(Paragraph(direccion.upper(), style_small_left))

        elements.append(Paragraph(f'CONTRATO N° : {credito.codigo_credito}', style_label))
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # DETALLE DE PRODUCTOS/VEHÍCULOS
        # ==========================================
        elements.append(Paragraph("<b>DESCRIPCIÓN</b>", style_label))
        elements.append(Spacer(1, 1*mm))
        
        # Obtener todos los detalles de la venta
        detalles_venta = VentaDetalle.objects.filter(idventa=venta, estado=1).select_related(
            'id_vehiculo__idproducto',
            'id_repuesto_comprado__id_repuesto'
        )
        
        # Construir lista de productos
        for detalle in detalles_venta:
            if detalle.tipo_item == 'vehiculo' and detalle.id_vehiculo:
                vehiculo = detalle.id_vehiculo
                nombre_producto = vehiculo.idproducto.nomproducto
                
                # Agregar nombre del producto
                elements.append(Paragraph(nombre_producto.upper(), style_small_left))
                
                # Agregar serie motor si existe
                if vehiculo.serie_motor:
                    elements.append(Paragraph(f"Motor: {vehiculo.serie_motor}", style_small_left))
                
                # Agregar serie chasis si existe
                if vehiculo.serie_chasis:
                    elements.append(Paragraph(f"Chasis: {vehiculo.serie_chasis}", style_small_left))
                
                # ✅ AGREGAR PLACA DEBAJO DEL CHASIS
                if vehiculo.placas and vehiculo.placas.strip():
                    elements.append(Paragraph(f"Placa: {vehiculo.placas.strip()}", style_small_left))
                else:
                    elements.append(Paragraph("Placa: PENDIENTE", style_small_left))
                
            elif detalle.tipo_item == 'repuesto' and detalle.id_repuesto_comprado:
                repuesto = detalle.id_repuesto_comprado
                nombre_repuesto = repuesto.id_repuesto.nombre
                
                # Agregar nombre del repuesto
                elements.append(Paragraph(nombre_repuesto.upper(), style_small_left))
                
                # Agregar código de barras si existe
                if repuesto.codigo_barras:
                    elements.append(Paragraph(f"Código: {repuesto.codigo_barras}", style_small_left))
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # FECHA Y HORA
        # ==========================================
        fecha_str = pago.fecha_pago.strftime('%d/%m/%Y')
        hora_str = pago.fecha_pago.strftime('%H:%M')
        
        elements.append(Paragraph(f"<b>FECHA EMISION:</b> {fecha_str}", style_label))
        elements.append(Paragraph(f"<b>HORA:</b> {hora_str}", style_small_left))
        
        elements.append(Spacer(1, 1*mm))
        
        # ==========================================
        # MONEDA Y FORMA DE PAGO
        # ==========================================
        elements.append(Paragraph("<b>MONEDA: SOLES</b>", style_small_left))
        
        tipo_pago_nombre = pago.id_tipo_pago.nombre if pago.id_tipo_pago else 'EFECTIVO'
        elements.append(Paragraph(f"<b>FORMA DE PAGO: {tipo_pago_nombre.upper()}</b>", style_small_left))
        
        # Cajero
        cajero = pago.idusuario.nombrecompleto.split()[0].upper()
        elements.append(Paragraph(f"<b>CAJERO(A): {cajero}</b>", style_small_left))
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # CONCEPTO Y TOTAL (en la misma línea)
        # ==========================================
        data_concepto = [
            ['CONCEPTO', 'TOTAL'],
            [f'Cuota N° {cuota.numero_cuota}', f'{cuota.total:.2f}']
        ]
        
        table_concepto = Table(data_concepto, colWidths=[50*mm, 24*mm])
        table_concepto.setStyle(TableStyle([
            # Primera fila (encabezados) - en negrita
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            
            # Segunda fila (monto) - en negrita
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 7),
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),
            ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
            
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        elements.append(table_concepto)
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # PAGO LETRA
        # ==========================================
        elements.append(Paragraph("<b>PAGO CUOTA</b>", style_normal_center))
        
        # ✅ DETERMINAR SI ES PAGO COMPLETO O AMORTIZADO
        if cuota.saldo_cuota == 0:
            tipo_pago_letra = "CUOTA PAGADA"
        else:
            tipo_pago_letra = "AMORTIZADO"
        
        # ✅ LETRA PAGADA = NÚMERO DE CUOTA + TIPO DE PAGO
        elements.append(Paragraph(
            f"<b>CUOTA PAGADA: ({cuota.numero_cuota}) {tipo_pago_letra}</b>", 
            style_label
        ))
        
        # Fecha de vencimiento
        fecha_venc = cuota.fecha_vencimiento.strftime('%d/%m/%Y')
        elements.append(Paragraph(fecha_venc, style_small_left))
        
        # ✅ PENDIENTES Y ATRASADAS
        elements.append(Paragraph(
            f"<b>PENDIENTES {cuotas_pendientes} / ATRAZADAS {cuotas_atrasadas}</b>", 
            style_small_left
        ))
        
        elements.append(Spacer(1, 3*mm))
        
        # ==========================================
        # IMPORTE TOTAL
        # ==========================================
        elements.append(Paragraph(
            f"<b>Importe Total {pago.monto_pago:.2f}</b>", 
            style_importe
        ))
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # MONTO EN LETRAS
        # ==========================================
        try:
            from software.utils.numero_a_letras import numero_a_letras
            monto_letras = numero_a_letras(pago.monto_pago)
        except:
            parte_entera = int(pago.monto_pago)
            parte_decimal = int((pago.monto_pago - parte_entera) * 100)
            monto_letras = f"CON {parte_decimal:02d}/100"
        
        elements.append(Paragraph(
            f"<b>SON: {monto_letras.upper()} SOLES</b>", 
            style_normal_center
        ))
        
        elements.append(Spacer(1, 3*mm))
        
        # ==========================================
        # MENSAJE DE RETENCIÓN (SIEMPRE APARECE)
        # ==========================================
        elements.append(Paragraph(
            "<b>Vehículo Sujeto Hacer Retenido</b>", 
            style_small
        ))
        elements.append(Paragraph(
            "<b>Póngase al día en sus pagos.</b>", 
            style_small
        ))
        elements.append(Paragraph(
            "<b>Plazo: 5 días.</b>", 
            style_small
        ))
        
        elements.append(Spacer(1, 3*mm))
        
        # ==========================================
        # LÍNEA DE CORTE
        # ==========================================
        elements.append(Paragraph(
            "- - - - - - - - - - - - - - - - - - - - - - - -", 
            style_normal_center
        ))
        
        # Construir el PDF
        doc.build(elements)
        
        buffer.seek(0)
        
        response = FileResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="recibo_{numero_recibo}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"ERROR al generar recibo: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error al generar el recibo: {str(e)}", status=500)

    