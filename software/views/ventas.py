from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from software.decorators import requiere_caja_aperturada

from software.models.VentasModel import Ventas
from software.models.VentaDetalleModel import VentaDetalle
from software.models.CuotasVentaModel import CuotasVenta
from software.models.ClienteModel import Cliente
from software.models.TipoIgvModel import TipoIgv
from software.models.SeriecomprobanteModel import Seriecomprobante
from software.models.TipocomprobanteModel import Tipocomprobante
from software.models.FormaPagoModel import FormaPago
from software.models.TipoPagoModel import TipoPago
from software.models.VehiculosModel import Vehiculo
from software.models.ProductoModel import Producto
from software.models.RespuestoCompModel import RepuestoComp
from software.models.RepuestoModel import Repuesto
from software.models.compradetalleModel import CompraDetalle
from software.models.AperturaCierreCajaModel import AperturaCierreCaja
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


# Listado de ventas
def ventas(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    
    if not id2:
        return HttpResponse("<h1>No tiene acceso señor</h1>")
    
    # Verificar si tiene caja abierta
    idusuario = request.session.get('idusuario')
    apertura_actual = AperturaCierreCaja.objects.filter(
        idusuario_id=idusuario,
        estado='abierta'
    ).first()
    
    # Validación de permisos
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    
    # Ventas activas, ordenadas de más recientes a más antiguas
    ventas_registros = Ventas.objects.filter(estado=1).select_related(
        'idcliente', 'idtipocomprobante', 'idusuario', 'id_forma_pago'
    ).order_by('-fecha_venta')
    
    # Catálogos relacionados
    clientes = Cliente.objects.filter(estado=1)
    tipo_comprobante = Tipocomprobante.objects.filter(estado=1)
    forma_pago = FormaPago.objects.filter(estado=1)
    tipo_pago = TipoPago.objects.filter(estado=1)
    tipo_igv = TipoIgv.objects.filter(estado=1)
    serie_comprobante = Seriecomprobante.objects.filter(estado=1)
    
    # CORREGIDO: Agrupar vehículos por nombre de producto
    productos_stock = {}
    productos = Producto.objects.filter(estado=1)
    
    for producto in productos:
        vehiculos = Vehiculo.objects.filter(
            idproducto=producto,
            estado=1
        ).select_related('idestadoproducto')
        
        vehiculos_disponibles = []
        for vehiculo in vehiculos:
            detalle_compra = CompraDetalle.objects.filter(
                id_vehiculo=vehiculo
            ).first()
            
            if detalle_compra:
                vehiculos_disponibles.append({
                    'id_vehiculo': vehiculo.id_vehiculo,
                    'serie_motor': vehiculo.serie_motor,
                    'serie_chasis': vehiculo.serie_chasis,
                    'precio_venta': float(detalle_compra.precio_venta),
                    'precio_compra': float(detalle_compra.precio_compra),
                })
        
        # Solo agregar productos que tengan vehículos disponibles
        if vehiculos_disponibles:
            if producto.nomproducto not in productos_stock:
                productos_stock[producto.nomproducto] = []
            productos_stock[producto.nomproducto].extend(vehiculos_disponibles)
    
    # CORREGIDO: Agrupar repuestos por nombre
    repuestos_stock = {}
    catalogo_repuestos = Repuesto.objects.filter(estado=1)
    
    for repuesto_catalogo in catalogo_repuestos:
        repuestos_comprados = RepuestoComp.objects.filter(
            id_repuesto=repuesto_catalogo,
            estado=1
        )
        
        repuestos_disponibles = []
        for repuesto_comp in repuestos_comprados:
            detalle_compra = CompraDetalle.objects.filter(
                id_repuesto_comprado=repuesto_comp
            ).first()
            
            if detalle_compra:
                repuestos_disponibles.append({
                    'id_repuesto_comprado': repuesto_comp.id_repuesto_comprado,
                    'codigo_barras': repuesto_comp.codigo_barras if repuesto_comp.codigo_barras else 'N/A',
                    'precio_venta': float(detalle_compra.precio_venta),
                    'precio_compra': float(detalle_compra.precio_compra),
                })
        
        # Solo agregar repuestos que tengan items disponibles
        if repuestos_disponibles:
            if repuesto_catalogo.nombre not in repuestos_stock:
                repuestos_stock[repuesto_catalogo.nombre] = []
            repuestos_stock[repuesto_catalogo.nombre].extend(repuestos_disponibles)
    
    # Obtener usuario actual
    idusuario = request.session.get('idusuario')
    
    # Convertir a JSON para JavaScript
    import json
    productos_stock_json = json.dumps(productos_stock)
    repuestos_stock_json = json.dumps(repuestos_stock)
    
    # Contexto para el template
    data = {
        'ventas_registros': ventas_registros,
        'clientes': clientes,
        'tipo_comprobante': tipo_comprobante,
        'tipo_igv': tipo_igv,
        'serie_comprobante': serie_comprobante, 
        'forma_pago': forma_pago,
        'tipo_pago': tipo_pago,
        'productos_stock': productos_stock_json,
        'repuestos_stock': repuestos_stock_json,
        'idusuario': idusuario,
        'permisos': permisos,
        'apertura_actual': apertura_actual, 
        'tiene_caja_abierta': bool(apertura_actual)
    }
    
    return render(request, 'ventas/ventas.html', data)


# Obtener series por tipo de comprobante (AJAX)
def obtener_series(request):
    if request.method == "GET":
        idtipocomprobante = request.GET.get('idtipocomprobante')
        series = Seriecomprobante.objects.filter(
            idtipocomprobante=idtipocomprobante,
            estado=1
        ).values('idseriecomprobante', 'serie', 'numero_actual')
        
        return JsonResponse(list(series), safe=False)
    
    return JsonResponse({'error': 'Método no permitido'}, status=400)


# Nueva venta
@requiere_caja_aperturada
def nueva_venta(request):
    if request.method == "POST":
        try:
            print("======= DEBUG POST VENTA =======")
            for k, v in request.POST.items():
                print(f"{k}: {v}")
            print("================================")

            with transaction.atomic():
                # ⭐ NUEVO: Obtener y validar caja aperturada
                idusuario_session = request.session.get('idusuario')
                apertura = AperturaCierreCaja.objects.filter(
                    idusuario_id=idusuario_session,
                    estado='abierta'
                ).first()
                
                if not apertura:
                    return JsonResponse({
                        'ok': False,
                        'error': 'No tiene una caja aperturada. Por favor, aperture una caja antes de realizar ventas.',
                        'necesita_aperturar': True
                    }, status=400)
                
                # Obtener datos de cabecera
                idcliente = int(request.POST.get("cliente"))
                idusuario = int(request.POST.get("idusuario"))
                idtipocomprobante = int(request.POST.get("tipo_comprobante"))
                idseriecomprobante = int(request.POST.get("serie"))
                fecha_venta = request.POST.get("fecha_venta")
                id_forma_pago = int(request.POST.get("forma_pago"))
                id_tipo_pago = request.POST.get("tipo_pago")
                id_tipo_pago_id = int(id_tipo_pago) if id_tipo_pago else None
                importe_recibido = request.POST.get("importe_recibido")
                vuelto = request.POST.get("vuelto")
                observaciones = request.POST.get("observaciones", "")
                
                # Validación para Contado
                if id_forma_pago == 1:  # Contado
                    if not importe_recibido or not vuelto:
                        raise ValueError("Para ventas al contado, debe ingresar el importe recibido y el vuelto.")
                    importe_recibido = Decimal(importe_recibido)
                    vuelto = Decimal(vuelto)
                    if importe_recibido < 0 or vuelto < 0:
                        raise ValueError("El importe recibido y el vuelto no pueden ser negativos.")
                else:
                    importe_recibido = None
                    vuelto = None

                # Obtener serie y generar número de comprobante
                serie = Seriecomprobante.objects.get(idseriecomprobante=idseriecomprobante)
                serie.numero_actual += 1
                numero_comprobante = f"{serie.serie}-{str(serie.numero_actual).zfill(8)}"
                serie.save()
                
                id_tipo_igv = int(request.POST.get("tipo_igv"))

                # Crear venta
                venta = Ventas.objects.create(
                    idcliente_id=idcliente,
                    idusuario_id=idusuario,
                    idtipocomprobante_id=idtipocomprobante,
                    idseriecomprobante_id=idseriecomprobante,
                    id_tipo_igv_id=id_tipo_igv,
                    numero_comprobante=numero_comprobante,
                    fecha_venta=fecha_venta,
                    id_forma_pago_id=id_forma_pago,
                    id_tipo_pago_id=id_tipo_pago_id,
                    importe_recibido=importe_recibido,
                    vuelto=vuelto,
                    subtotal=0,
                    total_venta=0,
                    total_ganancia=0,
                    observaciones=observaciones,
                    estado=1,
                )

                total = Decimal('0')
                total_ganancia = Decimal('0')
                items = int(request.POST.get("items_count") or 0)

                # Procesar items del detalle
                for i in range(1, items + 1):
                    tipo_item = request.POST.get(f"tipo_item_{i}")
                    if not tipo_item:
                        continue

                    cantidad = int(request.POST.get(f"cantidad_{i}") or 1)
                    precio_venta_contado = Decimal(request.POST.get(f"precio_venta_contado_{i}") or 0)
                    precio_venta_credito = request.POST.get(f"precio_venta_credito_{i}")
                    precio_venta_credito = Decimal(precio_venta_credito) if precio_venta_credito else None
                    precio_compra = Decimal(request.POST.get(f"precio_compra_{i}") or 0)
                    
                    if id_forma_pago == 2 and precio_venta_credito:
                        precio_final = precio_venta_credito
                    else:
                        precio_final = precio_venta_contado
                    
                    subtotal = cantidad * precio_final
                    ganancia = (precio_final - precio_compra) * cantidad

                    if tipo_item == "vehiculo":
                        id_vehiculo = request.POST.get(f"id_vehiculo_{i}", "").strip()
                        
                        if not id_vehiculo:
                            raise ValueError(f"Debe seleccionar un vehículo para el ítem {i}")
                        
                        VentaDetalle.objects.create(
                            idventa=venta,
                            tipo_item='vehiculo',
                            id_vehiculo_id=int(id_vehiculo),
                            id_repuesto_comprado=None,
                            cantidad=cantidad,
                            precio_venta_contado=precio_venta_contado,
                            precio_venta_credito=precio_venta_credito,
                            precio_compra=precio_compra,
                            subtotal=subtotal,
                            ganancia=ganancia,
                            estado=1
                        )

                    elif tipo_item == "repuesto":
                        id_repuesto = request.POST.get(f"id_repuesto_{i}", "").strip()
                        
                        if not id_repuesto:
                            raise ValueError(f"Debe seleccionar un repuesto para el ítem {i}")
                        
                        VentaDetalle.objects.create(
                            idventa=venta,
                            tipo_item='repuesto',
                            id_vehiculo=None,
                            id_repuesto_comprado_id=int(id_repuesto),
                            cantidad=cantidad,
                            precio_venta_contado=precio_venta_contado,
                            precio_venta_credito=precio_venta_credito,
                            precio_compra=precio_compra,
                            subtotal=subtotal,
                            ganancia=ganancia,
                            estado=1
                        )

                    total += subtotal
                    total_ganancia += ganancia

                # Actualizar totales de la venta
                venta.subtotal = total
                venta.total_venta = total
                venta.total_ganancia = total_ganancia
                venta.save()

                # Guardar cuotas si aplica
                if id_forma_pago == 2 and request.POST.get("tiene_cuotas") == "1":
                    cantidad_cuotas = int(request.POST.get("cantidad_cuotas") or 0)
                    
                    if cantidad_cuotas > 0:
                        monto_adelanto_total = request.POST.get("monto_adelanto_total")
                        monto_adelanto_total = Decimal(monto_adelanto_total) if monto_adelanto_total else Decimal('0')
                        
                        saldo_financiar = total - monto_adelanto_total
                        monto_por_cuota = saldo_financiar / cantidad_cuotas
                        fecha_base = datetime.strptime(fecha_venta, "%Y-%m-%d")
                        
                        for i in range(1, cantidad_cuotas + 1):
                            numero_cuota = request.POST.get(f"numero_cuota_{i}")
                            monto_cuota = request.POST.get(f"monto_{i}")
                            tasa_cuota = request.POST.get(f"tasa_{i}")
                            interes_cuota = request.POST.get(f"interes_{i}")
                            total_cuota = request.POST.get(f"total_{i}")
                            fecha_venc = request.POST.get(f"fecha_vencimiento_{i}")
                            monto_adelanto_cuota = request.POST.get(f"monto_adelanto_{i}")
                            
                            if not monto_cuota:
                                monto_cuota = monto_por_cuota
                            else:
                                monto_cuota = Decimal(monto_cuota)
                            
                            if not tasa_cuota:
                                tasa_cuota = Decimal('0')
                            else:
                                tasa_cuota = Decimal(tasa_cuota)
                            
                            if not interes_cuota:
                                interes_cuota = Decimal('0')
                            else:
                                interes_cuota = Decimal(interes_cuota)
                            
                            if not total_cuota:
                                total_cuota = monto_cuota + interes_cuota
                            else:
                                total_cuota = Decimal(total_cuota)
                            
                            if not fecha_venc:
                                fecha_vencimiento = fecha_base + timedelta(days=30 * i)
                                fecha_venc = fecha_vencimiento.strftime("%Y-%m-%d")
                            
                            if not monto_adelanto_cuota:
                                monto_adelanto_cuota = monto_adelanto_total if i == 1 else Decimal('0')
                            else:
                                monto_adelanto_cuota = Decimal(monto_adelanto_cuota)
                            
                            CuotasVenta.objects.create(
                                idventa=venta,
                                numero_cuota=int(numero_cuota) if numero_cuota else i,
                                monto=monto_cuota,
                                tasa=tasa_cuota,
                                interes=interes_cuota,
                                total=total_cuota,
                                fecha_vencimiento=fecha_venc,
                                monto_adelanto=monto_adelanto_cuota,
                                estado_pago='Pendiente',
                                estado=1
                            )

                print(f"✅ VENTA REGISTRADA - ID: {venta.idventa}, Caja: {apertura.id_caja.nombre_caja}")

            return JsonResponse({
                'ok': True,
                'message': 'Venta registrada correctamente.',
                'numero_comprobante': numero_comprobante,
                'idventa': venta.idventa
            })

        except ValueError as ve:
            print(f"ERROR DE VALIDACIÓN: {str(ve)}")
            return JsonResponse({
                'ok': False,
                'error': str(ve)
            })
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'ok': False,
                'error': f'Error al procesar la venta: {str(e)}'
            })

    return redirect("ventas")


# Anular venta
def anular_venta(request, id):
    try:
        venta = Ventas.objects.get(idventa=id)
        venta.estado = 0
        venta.save()
        return redirect('ventas')
    except Ventas.DoesNotExist:
        return HttpResponse("<h1>Venta no encontrada</h1>")
    

#Para Imprimir_comprobante
def imprimir_comprobante(request, idventa):
    """
    Genera un PDF del comprobante de venta en formato TICKET con logo y QR
    Optimizado para impresoras térmicas de 80mm - ALTURA AUTOMÁTICA
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from io import BytesIO
        import qrcode
        import os
        from django.conf import settings
        
        # Obtener la venta
        venta = get_object_or_404(Ventas, idventa=idventa)
        
        # Obtener detalles de la venta
        detalles = VentaDetalle.objects.filter(idventa=venta, estado=1)
        
        # Obtener cuotas si existen
        cuotas = CuotasVenta.objects.filter(idventa=venta, estado=1).order_by('numero_cuota')
        
        # Crear el PDF en memoria con tamaño de TICKET (80mm de ancho)
        buffer = BytesIO()
        
        # Tamaño de ticket: 80mm de ancho, altura MUY GRANDE para permitir crecimiento automático
        ticket_width = 80 * mm
        ticket_height = 800 * mm  # Altura muy grande, se ajustará automáticamente
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=(ticket_width, ticket_height),
            rightMargin=3*mm,
            leftMargin=3*mm,
            topMargin=3*mm, 
            bottomMargin=3*mm
        )
        
        # Ancho útil para el contenido (80mm - 6mm de márgenes)
        ancho_util = 74 * mm
        
        # Contenedor para los elementos del PDF
        elements = []
        
        # Estilos personalizados para ticket
        styles = getSampleStyleSheet()
        
        style_company = ParagraphStyle(
            'CompanyName',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=1,
            leading=11
        )
        
        style_header = ParagraphStyle(
            'TicketHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=2,
            leading=10
        )
        
        style_normal_center = ParagraphStyle(
            'NormalCenter',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            spaceAfter=1,
            leading=8
        )
        
        style_normal = ParagraphStyle(
            'TicketNormal',
            parent=styles['Normal'],
            fontSize=7,
            spaceAfter=1,
            leading=8
        )
        
        style_bold = ParagraphStyle(
            'TicketBold',
            parent=styles['Normal'],
            fontSize=7,
            fontName='Helvetica-Bold',
            spaceAfter=1,
            alignment=TA_CENTER,
            leading=8
        )
        
        style_small = ParagraphStyle(
            'SmallText',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_CENTER,
            spaceAfter=0.5,
            leading=7
        )
        
        # ==========================================
        # LOGO DE LA EMPRESA
        # ==========================================
        try:
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'img','empresa', 'logo.png')
            
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=30*mm, height=20*mm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 2*mm))
        except Exception as e:
            print(f"No se pudo cargar el logo: {str(e)}")
        
        # ==========================================
        # ENCABEZADO - DATOS DE LA EMPRESA
        # ==========================================
        elements.append(Paragraph("TU EMPRESA S.A.C.", style_company))
        elements.append(Paragraph("RUC: 12345678901", style_normal_center))
        elements.append(Paragraph("Av. Principal 123, Lima", style_normal_center))
        elements.append(Paragraph("Telf: (01) 123-4567", style_normal_center))
        elements.append(Paragraph("www.tuempresa.com", style_small))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("=" * 48, style_normal_center))
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # TIPO DE COMPROBANTE Y NÚMERO
        # ==========================================
        elements.append(Paragraph(f"<b>{venta.idtipocomprobante.nombre.upper()}</b>", style_header))
        elements.append(Paragraph(f"<b>{venta.numero_comprobante}</b>", style_header))
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # DATOS DEL CLIENTE
        # ==========================================
        cliente_nombre = venta.idcliente.razonsocial
        if len(cliente_nombre) > 35:
            cliente_nombre = cliente_nombre[:32] + '...'
        
        elements.append(Paragraph(f"<b>CLIENTE:</b>", style_bold))
        elements.append(Paragraph(f"{cliente_nombre}", style_normal_center))
        elements.append(Paragraph(f"<b>DNI/RUC:</b> {venta.idcliente.numdoc or '---'}", style_normal_center))
        
        if venta.idcliente.telefono:
            elements.append(Paragraph(f"<b>Tel:</b> {venta.idcliente.telefono}", style_small))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("-" * 50, style_normal_center))
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # FECHA Y HORA
        # ==========================================
        fecha_str = venta.fecha_venta.strftime('%d/%m/%Y')
        try:
            hora_str = venta.fecha_venta.strftime('%I:%M %p')
        except:
            hora_str = '---'
        
        elements.append(Paragraph(f"<b>FECHA:</b> {fecha_str}  <b>HORA:</b> {hora_str}", style_normal_center))
        
        # Acortar nombre de vendedor si es muy largo
        vendedor = venta.idusuario.nombrecompleto
        if len(vendedor) > 30:
            vendedor = vendedor[:27] + '...'
        elements.append(Paragraph(f"<b>VENDEDOR:</b> {vendedor}", style_small))
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # DETALLE DE PRODUCTOS/SERVICIOS
        # ==========================================
        elements.append(Paragraph("-" * 50, style_normal_center))
        elements.append(Spacer(1, 1*mm))
        
        # Encabezado de la tabla
        data_detalle = [['CN', 'DESCRIPCIÓN', 'P.U', 'TOTAL']]
        
        for detalle in detalles:
            if detalle.tipo_item == 'vehiculo':
                vehiculo = detalle.id_vehiculo
                nombre_producto = vehiculo.idproducto.nomproducto
                if len(nombre_producto) > 25:
                    nombre_producto = nombre_producto[:22] + '...'
                descripcion = f"{nombre_producto}\n{vehiculo.serie_motor[:15]}\n{vehiculo.serie_chasis[:15]}"
            else:
                repuesto = detalle.id_repuesto_comprado
                nombre_repuesto = repuesto.id_repuesto.nombre
                if len(nombre_repuesto) > 25:
                    nombre_repuesto = nombre_repuesto[:22] + '...'
                codigo = repuesto.codigo_barras or 'S/N'
                descripcion = f"{nombre_repuesto}\n{codigo[:12]}"
            
            # Determinar el precio según la forma de pago
            if venta.id_forma_pago.id_forma_pago == 2 and detalle.precio_venta_credito:
                precio_unitario = detalle.precio_venta_credito
            else:
                precio_unitario = detalle.precio_venta_contado
            
            data_detalle.append([
                str(detalle.cantidad),
                descripcion,
                f"{precio_unitario:.2f}",
                f"{detalle.subtotal:.2f}"
            ])
        
        # Anchos de columna para 74mm útiles
        col_widths = [7*mm, 40*mm, 13*mm, 14*mm]
        
        table_detalle = Table(data_detalle, colWidths=col_widths)
        table_detalle.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 6),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(table_detalle)
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("-" * 50, style_normal_center))
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # TOTALES
        # ==========================================
        data_totales = [
            ['SUBTOTAL:', f"S/ {venta.subtotal:.2f}"],
            ['IGV (0%):', f"S/ 0.00"],
        ]
        
        table_totales = Table(data_totales, colWidths=[50*mm, 24*mm])
        table_totales.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        elements.append(table_totales)
        
        # TOTAL
        data_total = [[f"TOTAL:    S/ {venta.total_venta:.2f}"]]
        table_total = Table(data_total, colWidths=[ancho_util])
        table_total.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(table_total)
        
        # Importe recibido y vuelto
        if venta.id_forma_pago.id_forma_pago == 1 and venta.importe_recibido:
            elements.append(Spacer(1, 2*mm))
            data_pago = [
                ['RECIBIDO:', f"S/ {venta.importe_recibido:.2f}"],
                ['VUELTO:', f"S/ {venta.vuelto:.2f}"],
            ]
            table_pago = Table(data_pago, colWidths=[50*mm, 24*mm])
            table_pago.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ]))
            elements.append(table_pago)
        
        elements.append(Spacer(1, 2*mm))
        
        # ==========================================
        # FORMA DE PAGO Y TIPO
        # ==========================================
        forma_pago_nombre = venta.id_forma_pago.nombre
        tipo_pago_nombre = venta.id_tipo_pago.nombre if venta.id_tipo_pago else 'N/A'
        
        elements.append(Paragraph(f"<b>FORMA DE PAGO:</b> {forma_pago_nombre}", style_normal_center))
        elements.append(Paragraph(f"<b>TIPO:</b> {tipo_pago_nombre}", style_small))
        
        # ==========================================
        # CRONOGRAMA DE CUOTAS (si aplica)
        # ==========================================
        if cuotas.exists():
            elements.append(Spacer(1, 2*mm))
            elements.append(Paragraph("-" * 50, style_normal_center))
            elements.append(Paragraph("<b>CRONOGRAMA DE PAGOS</b>", style_bold))
            elements.append(Spacer(1, 1*mm))
            
            data_cuotas = [['N°', 'VENC.', 'MONTO', 'TOTAL']]
            
            for cuota in cuotas:
                data_cuotas.append([
                    str(cuota.numero_cuota),
                    cuota.fecha_vencimiento.strftime('%d/%m/%y'),
                    f"{cuota.monto:.2f}",
                    f"{cuota.total:.2f}"
                ])
            
            table_cuotas = Table(data_cuotas, colWidths=[8*mm, 20*mm, 23*mm, 23*mm])
            table_cuotas.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 6),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(table_cuotas)
        
        # ==========================================
        # OBSERVACIONES
        # ==========================================
        if venta.observaciones:
            elements.append(Spacer(1, 2*mm))
            obs_text = venta.observaciones[:60] + '...' if len(venta.observaciones) > 60 else venta.observaciones
            elements.append(Paragraph(f"<b>Obs:</b> {obs_text}", style_small))
        
        # ==========================================
        # CÓDIGO QR
        # ==========================================
        try:
            elements.append(Spacer(1, 2*mm))
            
            qr_data = f"Comprobante: {venta.numero_comprobante}\n"
            qr_data += f"Cliente: {venta.idcliente.razonsocial[:30]}\n"
            qr_data += f"RUC/DNI: {venta.idcliente.numdoc or 'N/A'}\n"
            qr_data += f"Total: S/ {venta.total_venta:.2f}\n"
            qr_data += f"Fecha: {venta.fecha_venta.strftime('%d/%m/%Y')}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=1,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            qr_image = Image(qr_buffer, width=28*mm, height=28*mm)
            qr_image.hAlign = 'CENTER'
            elements.append(qr_image)
            
        except Exception as e:
            print(f"No se pudo generar el código QR: {str(e)}")
        
        # ==========================================
        # PIE DE PÁGINA
        # ==========================================
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("=" * 48, style_normal_center))
        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph("¡Gracias por su compra!", style_normal_center))
        elements.append(Paragraph("Vuelva pronto", style_small))
        
        # Construir el PDF - ReportLab ajustará automáticamente la altura
        doc.build(elements)
        
        buffer.seek(0)
        
        response = FileResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="ticket_{venta.numero_comprobante}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"ERROR al generar comprobante: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error al generar el comprobante: {str(e)}", status=500)






