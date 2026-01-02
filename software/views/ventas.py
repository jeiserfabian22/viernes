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
from software.models.UsuarioModel import Usuario
from software.models.stockModel import Stock
from software.models.almacenesModel import Almacenes
from software.models.Tipo_entidadModel import TipoEntidad
from software.models.AuditoriaVentasModel import AuditoriaVentas
from software.models.CreditoModel import Credito
from software.models.movimientoCajaModel import MovimientoCaja
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


# Listado de ventas
def ventas(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    
    if not id2:
        return HttpResponse("<h1>No tiene acceso señor</h1>")
    
    # Validación de permisos
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    
    # ✅ FILTRAR VENTAS POR SUCURSAL
    idusuario = request.session.get('idusuario')
    id_sucursal = request.session.get('id_sucursal')
    es_admin = (id2 == 1)
    
    if es_admin and id_sucursal:
        # Admin ve ventas de la sucursal seleccionada
        ventas_registros = Ventas.objects.filter(
            estado=1,
            id_sucursal_id=id_sucursal
        ).select_related(
            'idcliente', 'idtipocomprobante', 'idusuario', 'id_forma_pago'
        ).order_by('-fecha_venta')
    elif not es_admin:
        # Usuario normal ve solo ventas de su sucursal
        try:
            usuario = Usuario.objects.get(idusuario=idusuario)
            ventas_registros = Ventas.objects.filter(
                estado=1,
                id_sucursal=usuario.id_sucursal
            ).select_related(
                'idcliente', 'idtipocomprobante', 'idusuario', 'id_forma_pago'
            ).order_by('-fecha_venta')
        except Usuario.DoesNotExist:
            ventas_registros = []
    else:
        # Admin sin sucursal seleccionada no ve nada
        ventas_registros = []
    
    # Catálogos relacionados
    clientes = Cliente.objects.filter(estado=1)
    tipo_comprobante = Tipocomprobante.objects.filter(estado=1)
    forma_pago = FormaPago.objects.filter(estado=1)
    tipo_pago = TipoPago.objects.filter(estado=1)
    tipo_igv = TipoIgv.objects.filter(estado=1)
    serie_comprobante = Seriecomprobante.objects.filter(estado=1)
    
    # ========================================
    # ✅ VEHÍCULOS - CORREGIDO
    # ========================================
    productos_stock = {}
    productos = Producto.objects.filter(estado=1)
    
    for producto in productos:
        vehiculos = Vehiculo.objects.filter(
            idproducto=producto,
            estado=1
        ).select_related('idestadoproducto')
        
        vehiculos_disponibles = []
        for vehiculo in vehiculos:
            # ✅ OBTENER STOCK DEL ALMACÉN EN SESIÓN
            id_almacen_session = request.session.get('id_almacen')
            
            if id_almacen_session:
                # ⭐ BUSCAR STOCK CON idcompradetalle
                stock_registros = Stock.objects.filter(
                    id_almacen_id=id_almacen_session,
                    id_vehiculo=vehiculo,
                    estado=1,
                    cantidad_disponible__gt=0  # ✅ SOLO CON STOCK
                ).select_related('idcompradetalle')
                
                # ⭐ PROCESAR CADA STOCK CON SU PRECIO ESPECÍFICO
                for stock_registro in stock_registros:
                    # ✅ USAR LA RELACIÓN DIRECTA CON COMPRADETALLE
                    if stock_registro.idcompradetalle:
                        detalle_compra = stock_registro.idcompradetalle
                    else:
                        # ⚠️ FALLBACK: Buscar por vehículo (para stocks antiguos)
                        detalle_compra = CompraDetalle.objects.filter(
                            id_vehiculo=vehiculo
                        ).order_by('-idcompradetalle').first()
                    
                    if detalle_compra:
                        vehiculos_disponibles.append({
                            'id_vehiculo': vehiculo.id_vehiculo,
                            'serie_motor': vehiculo.serie_motor,
                            'serie_chasis': vehiculo.serie_chasis,
                            'precio_venta': float(detalle_compra.precio_venta),
                            'precio_compra': float(detalle_compra.precio_compra),
                            'stock_disponible': stock_registro.cantidad_disponible,
                        })
        
        # Solo agregar productos que tengan vehículos disponibles
        if vehiculos_disponibles:
            if producto.nomproducto not in productos_stock:
                productos_stock[producto.nomproducto] = []
            productos_stock[producto.nomproducto].extend(vehiculos_disponibles)
    
    # ========================================
    # ✅ REPUESTOS - CORREGIDO
    # ========================================
    repuestos_stock = {}
    catalogo_repuestos = Repuesto.objects.filter(estado=1)
    
    for repuesto_catalogo in catalogo_repuestos:
        repuestos_comprados = RepuestoComp.objects.filter(
            id_repuesto=repuesto_catalogo,
            estado=1
        )
        
        repuestos_disponibles = []
        for repuesto_comp in repuestos_comprados:
            # ✅ OBTENER STOCK DEL ALMACÉN EN SESIÓN
            id_almacen_session = request.session.get('id_almacen')
            
            if id_almacen_session:
                # ⭐ BUSCAR STOCK CON idcompradetalle
                stock_registros = Stock.objects.filter(
                    id_almacen_id=id_almacen_session,
                    id_repuesto_comprado=repuesto_comp,
                    estado=1,
                    cantidad_disponible__gt=0  # ✅ SOLO CON STOCK
                ).select_related('idcompradetalle')
                
                # ⭐ PROCESAR CADA STOCK CON SU PRECIO ESPECÍFICO
                for stock_registro in stock_registros:
                    # ✅ USAR LA RELACIÓN DIRECTA CON COMPRADETALLE
                    if stock_registro.idcompradetalle:
                        detalle_compra = stock_registro.idcompradetalle
                    else:
                        # ⚠️ FALLBACK: Buscar por repuesto_comp (para stocks antiguos)
                        detalle_compra = CompraDetalle.objects.filter(
                            id_repuesto_comprado=repuesto_comp
                        ).order_by('-idcompradetalle').first()
                    
                    if detalle_compra:
                        repuestos_disponibles.append({
                            'id_repuesto_comprado': repuesto_comp.id_repuesto_comprado,
                            'codigo_barras': repuesto_comp.codigo_barras if repuesto_comp.codigo_barras else 'N/A',
                            'precio_venta': float(detalle_compra.precio_venta),
                            'precio_compra': float(detalle_compra.precio_compra),
                            'stock_disponible': stock_registro.cantidad_disponible,
                        })
        
        # Solo agregar repuestos que tengan items disponibles
        if repuestos_disponibles:
            if repuesto_catalogo.nombre not in repuestos_stock:
                repuestos_stock[repuesto_catalogo.nombre] = []
            repuestos_stock[repuesto_catalogo.nombre].extend(repuestos_disponibles)
    
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
        'es_admin': es_admin,
        'tipos_entidad': TipoEntidad.objects.filter(estado=1),
    }
    
    return render(request, 'ventas/ventas.html', data)

# Obtener series por tipo de comprobante (AJAX)
def obtener_series(request):
    """Obtiene las series disponibles filtradas por tipo de comprobante (AJAX)"""
    if request.method == "GET":
        idtipocomprobante = request.GET.get('idtipocomprobante')
        
        if not idtipocomprobante:
            return JsonResponse({'error': 'Tipo de comprobante no especificado'}, status=400)
        
        try:
            # Filtrar series activas por tipo de comprobante
            series = Seriecomprobante.objects.filter(
                idtipocomprobante=idtipocomprobante,
                estado=1
            ).values(
                'idseriecomprobante',
                'serie',
                'numero_actual'
            ).order_by('serie')
            
            series_list = list(series)
            
            # Agregar información adicional del próximo número
            for s in series_list:
                siguiente_numero = s['numero_actual'] + 1
                s['proximo_numero'] = f"{s['serie']}-{str(siguiente_numero).zfill(8)}"
            
            return JsonResponse({
                'ok': True,
                'series': series_list
            })
        
        except Exception as e:
            return JsonResponse({
                'ok': False,
                'error': f'Error al obtener series: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=400)

# Nueva venta
@requiere_caja_aperturada
def nueva_venta(request):
    if request.method == "POST":
        try:
            print("=" * 60)
            print("🔍 VALORES EN SESIÓN:")
            print(f"   idusuario: {request.session.get('idusuario')}")
            print(f"   id_sucursal: {request.session.get('id_sucursal')}")
            print(f"   id_almacen: {request.session.get('id_almacen')}")
            print(f"   id_caja: {request.session.get('id_caja')}")
            print("=" * 60)
            print("======= DEBUG POST VENTA =======")
            for k, v in request.POST.items():
                print(f"{k}: {v}")
            print("================================")

            # ⭐ VALIDACIÓN 1: Obtener datos de sesión
            idusuario_session = request.session.get('idusuario')
            id_caja_session = request.session.get('id_caja')
            id_almacen_session = request.session.get('id_almacen')
            id_sucursal_session = request.session.get('id_sucursal')
            
            # Validar que tenga caja seleccionada
            if not id_caja_session:
                return JsonResponse({
                    'ok': False,
                    'error': 'Debe seleccionar una caja en el modal de configuración antes de vender.'
                }, status=400)
            
            # Validar que tenga almacén seleccionado
            if not id_almacen_session:
                return JsonResponse({
                    'ok': False,
                    'error': 'Debe seleccionar un almacén en el modal de configuración antes de vender.'
                }, status=400)
            
            # Validar que tenga sucursal seleccionada
            if not id_sucursal_session:
                return JsonResponse({
                    'ok': False,
                    'error': 'Debe seleccionar una sucursal en el modal de configuración antes de vender.'
                }, status=400)
            
            # ⭐ VALIDACIÓN 2: Verificar que la caja esté aperturada
            apertura = AperturaCierreCaja.objects.filter(
                idusuario_id=idusuario_session,
                id_caja_id=id_caja_session,
                estado__in=['abierta', 'reabierta']
            ).first()
            
            if not apertura:
                return JsonResponse({
                    'ok': False,
                    'error': 'La caja seleccionada no está aperturada. Por favor, aperture la caja antes de realizar ventas.',
                    'necesita_aperturar': True
                }, status=400)
            
            # ⭐ VALIDACIÓN 3: Verificar usuario
            usuario = Usuario.objects.get(idusuario=idusuario_session)
            
            if not usuario.id_sucursal:
                return JsonResponse({
                    'ok': False,
                    'error': 'Usuario sin sucursal asignada. Contacte al administrador.'
                }, status=400)
            
            # ⭐ VALIDACIÓN 4: Obtener almacén desde la SESIÓN
            try:
                almacen = Almacenes.objects.get(id_almacen=id_almacen_session, estado=1)
            except Almacenes.DoesNotExist:
                return JsonResponse({
                    'ok': False,
                    'error': 'El almacén seleccionado no existe o está inactivo.'
                }, status=400)
            
            # ⭐ VALIDACIÓN 5: Obtener caja desde la SESIÓN
            try:
                from software.models.cajaModel import Caja
                caja = Caja.objects.get(id_caja=id_caja_session, estado=1)
            except Caja.DoesNotExist:
                return JsonResponse({
                    'ok': False,
                    'error': 'La caja seleccionada no existe o está inactiva.'
                }, status=400)
            
            # ⭐ VALIDACIÓN 6: Validar datos obligatorios de la venta
            idcliente_str = request.POST.get("cliente", "").strip()
            if not idcliente_str:
                return JsonResponse({
                    'ok': False,
                    'error': 'Debe seleccionar un cliente para realizar la venta.'
                }, status=400)
            
            idtipocomprobante_str = request.POST.get("tipo_comprobante", "").strip()
            if not idtipocomprobante_str:
                return JsonResponse({
                    'ok': False,
                    'error': 'Debe seleccionar un tipo de comprobante.'
                }, status=400)
            
            # ⭐ VALIDACIÓN 7: Validar items
            items = int(request.POST.get("items_count") or 0)
            
            if items == 0:
                return JsonResponse({
                    'ok': False,
                    'error': 'Debe agregar al menos un producto a la venta.'
                }, status=400)
            
            # ⭐ VALIDACIÓN 8: Validar stock de cada ítem EN EL ALMACÉN CORRECTO
            for i in range(1, items + 1):
                tipo_item = request.POST.get(f"tipo_item_{i}")
                
                if not tipo_item:
                    continue
                
                cantidad = int(request.POST.get(f"cantidad_{i}") or 1)
                
                if tipo_item == "vehiculo":
                    id_vehiculo = request.POST.get(f"id_vehiculo_{i}", "").strip()
                    
                    if id_vehiculo:
                        stock = Stock.objects.filter(
                            id_almacen=almacen,
                            id_vehiculo_id=int(id_vehiculo),
                            estado=1
                        ).first()
                        
                        if not stock or stock.cantidad_disponible < cantidad:
                            vehiculo = Vehiculo.objects.get(id_vehiculo=id_vehiculo)
                            return JsonResponse({
                                'ok': False,
                                'error': f'Stock insuficiente para el vehículo {vehiculo.idproducto.nomproducto}. Disponible en {almacen.nombre_almacen}: {stock.cantidad_disponible if stock else 0}'
                            }, status=400)
                
                elif tipo_item == "repuesto":
                    id_repuesto = request.POST.get(f"id_repuesto_{i}", "").strip()
                    
                    if id_repuesto:
                        stock = Stock.objects.filter(
                            id_almacen=almacen,
                            id_repuesto_comprado_id=int(id_repuesto),
                            estado=1
                        ).first()
                        
                        if not stock or stock.cantidad_disponible < cantidad:
                            repuesto = RepuestoComp.objects.get(id_repuesto_comprado=id_repuesto)
                            return JsonResponse({
                                'ok': False,
                                'error': f'Stock insuficiente para el repuesto {repuesto.id_repuesto.nombre}. Disponible: {stock.cantidad_disponible if stock else 0}'
                            }, status=400)
            
            # ✅ Si llegó hasta aquí, todas las validaciones pasaron, continuar con la venta
            
            with transaction.atomic():
                # Obtener datos de cabecera
                idcliente = int(idcliente_str)
                idusuario = int(request.POST.get("idusuario"))
                idtipocomprobante = int(idtipocomprobante_str)
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
                
                tipo_igv = request.POST.get("tipo_igv")
                if tipo_igv and tipo_igv.strip():
                    id_tipo_igv = int(tipo_igv)
                else:
                    id_tipo_igv = None

                # ✅ Crear venta CON ALMACÉN, CAJA Y SUCURSAL
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
                    id_almacen_id=id_almacen_session,
                    id_caja_id=id_caja_session,
                    id_sucursal_id=id_sucursal_session,
                    estado=1,
                )

                total = Decimal('0')
                total_ganancia = Decimal('0')

                # Procesar items del detalle
                for i in range(1, items + 1):
                    tipo_item = request.POST.get(f"tipo_item_{i}")
                    if not tipo_item:
                        continue

                    cantidad = int(request.POST.get(f"cantidad_{i}") or 1)
                    precio_venta_contado = Decimal(request.POST.get(f"precio_venta_contado_{i}") or 0)
                    
                    # ✅ CORREGIDO: Buscar con el nombre correcto del campo
                    precio_credito_str = request.POST.get(f"precio_credito_{i}")
                    precio_venta_credito = Decimal(precio_credito_str) if precio_credito_str and precio_credito_str.strip() else None
                    
                    precio_compra = Decimal(request.POST.get(f"precio_compra_{i}") or 0)
                    
                    # ✅ Obtener precio de descuento (solo contado)
                    precio_descuento_str = request.POST.get(f"precio_descuento_{i}")
                    precio_descuento = Decimal(precio_descuento_str) if precio_descuento_str and precio_descuento_str.strip() else None
                    
                    # ✅ DETERMINAR PRECIO FINAL SEGÚN FORMA DE PAGO
                    if id_forma_pago == 2:  # CRÉDITO
                        if not precio_venta_credito:
                            raise ValueError(f"Debe ingresar el precio a crédito para el ítem {i}")
                        precio_final = precio_venta_credito
                    elif id_forma_pago == 1:  # CONTADO
                        if precio_descuento:
                            precio_final = precio_descuento
                        else:
                            precio_final = precio_venta_contado
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

                print(f"💰 TOTALES CALCULADOS:")
                print(f"   Forma de pago: {id_forma_pago} ({'CRÉDITO' if id_forma_pago == 2 else 'CONTADO'})")
                print(f"   Total venta: S/ {total}")
                print(f"   Total ganancia: S/ {total_ganancia}")

                # ========================================
                # ✅ GUARDAR CUOTAS Y CREAR CRÉDITO SI ES VENTA A CRÉDITO
                # ========================================
                if id_forma_pago == 2 and request.POST.get("tiene_cuotas") == "1":
                    cantidad_cuotas = int(request.POST.get("cantidad_cuotas") or 0)
                    
                    if cantidad_cuotas > 0:
                        # ✅ OBTENER DATOS DE CRÉDITO
                        monto_adelanto_str = request.POST.get("monto_adelanto")
                        monto_adelanto = Decimal(monto_adelanto_str) if monto_adelanto_str and monto_adelanto_str.strip() else Decimal('0')
                        
                        tasa_interes_str = request.POST.get("tasa_interes")
                        tasa_interes = Decimal(tasa_interes_str) if tasa_interes_str else Decimal('0')
                        
                        tipo_periodo = request.POST.get("tipo_periodo", "dias")
                        
                        # ✅ CALCULAR SALDO A FINANCIAR
                        saldo_financiar = total - monto_adelanto
                        
                        print(f"📊 DATOS DE CRÉDITO:")
                        print(f"   Total venta (con precio crédito): S/ {total}")
                        print(f"   Monto adelanto: S/ {monto_adelanto}")
                        print(f"   Saldo a financiar: S/ {saldo_financiar}")
                        print(f"   Cantidad cuotas: {cantidad_cuotas}")
                        print(f"   Tasa interés: {tasa_interes}%")
                        
                        # ✅ GENERAR CÓDIGO DE CRÉDITO ÚNICO
                        ultimo_credito = Credito.objects.all().order_by('-idcredito').first()
                        if ultimo_credito:
                            try:
                                ultimo_numero = int(ultimo_credito.codigo_credito.split('-')[1])
                                nuevo_numero = ultimo_numero + 1
                            except:
                                nuevo_numero = 1
                        else:
                            nuevo_numero = 1
                        
                        codigo_credito = f"CR-{str(nuevo_numero).zfill(3)}"
                        
                        # ✅ CREAR EL CRÉDITO
                        credito = Credito.objects.create(
                            codigo_credito=codigo_credito,
                            idventa=venta,
                            monto_total=total,  # ⭐ TOTAL CON PRECIO CRÉDITO
                            monto_adelanto=monto_adelanto,  # ⭐ ADELANTO
                            saldo_pendiente=saldo_financiar,  # ⭐ SALDO A FINANCIAR
                            cantidad_cuotas=cantidad_cuotas,
                            estado_credito='activo',
                            estado=1
                        )
                        
                        print(f"✅ CRÉDITO CREADO - ID: {credito.idcredito}, Código: {codigo_credito}")
                        
                        # ✅ GUARDAR CUOTAS EN CuotasVenta
                        print(f"📅 Guardando {cantidad_cuotas} cuotas en CuotasVenta...")
                        
                        suma_total_cuotas = Decimal('0')
                        suma_capital_cuotas = Decimal('0')
                        
                        for i in range(1, cantidad_cuotas + 1):
                            numero_cuota_str = request.POST.get(f"cuota_{i}_numero")
                            fecha_venc_str = request.POST.get(f"cuota_{i}_fecha")
                            monto_cuota_str = request.POST.get(f"cuota_{i}_monto")
                            interes_cuota_str = request.POST.get(f"cuota_{i}_interes")
                            total_cuota_str = request.POST.get(f"cuota_{i}_total")
                            tasa_cuota_str = request.POST.get(f"cuota_{i}_tasa")
                            
                            # Convertir a los tipos correctos
                            numero_cuota = int(numero_cuota_str) if numero_cuota_str else i
                            monto_cuota = Decimal(monto_cuota_str) if monto_cuota_str else Decimal('0')
                            interes_cuota = Decimal(interes_cuota_str) if interes_cuota_str else Decimal('0')
                            total_cuota = Decimal(total_cuota_str) if total_cuota_str else (monto_cuota + interes_cuota)
                            tasa_cuota = Decimal(tasa_cuota_str) if tasa_cuota_str else tasa_interes
                            
                            suma_capital_cuotas += monto_cuota
                            suma_total_cuotas += total_cuota
                            
                            # Parsear fecha
                            if fecha_venc_str:
                                fecha_vencimiento = datetime.strptime(fecha_venc_str, '%Y-%m-%d').date()
                            else:
                                fecha_base = datetime.strptime(fecha_venta, "%Y-%m-%d")
                                fecha_vencimiento = (fecha_base + timedelta(days=30 * i)).date()
                            
                            # ✅ CREAR CUOTA en CuotasVenta
                            cuota = CuotasVenta.objects.create(
                                idventa=venta,
                                numero_cuota=numero_cuota,
                                monto=monto_cuota,  # Capital de la cuota (sin interés)
                                tasa=tasa_cuota,
                                interes=interes_cuota,
                                total=total_cuota,  # Capital + interés
                                fecha_vencimiento=fecha_vencimiento,
                                monto_adelanto=monto_adelanto if i == 1 else Decimal('0'),  # Solo en primera cuota
                                monto_pagado=Decimal('0'),
                                saldo_cuota=total_cuota,  # Inicialmente, saldo = total
                                fecha_pago=None,
                                estado_pago='Pendiente',
                                estado=1
                            )
                            
                            print(f"  Cuota {numero_cuota}: capital=S/ {monto_cuota}, interés=S/ {interes_cuota}, total=S/ {total_cuota}, vence={fecha_vencimiento}")
                        
                        # ✅ VALIDAR QUE LA SUMA DE CUOTAS (CAPITAL) COINCIDA CON EL SALDO A FINANCIAR
                        diferencia_capital = abs(suma_capital_cuotas - saldo_financiar)
                        
                        print(f"\n📊 RESUMEN DE CUOTAS:")
                        print(f"   Suma capital cuotas: S/ {suma_capital_cuotas}")
                        print(f"   Saldo a financiar: S/ {saldo_financiar}")
                        print(f"   Diferencia: S/ {diferencia_capital}")
                        print(f"   Suma total con intereses: S/ {suma_total_cuotas}")
                        
                        if diferencia_capital > Decimal('0.02'):  # Tolerancia de 2 centavos
                            print(f"⚠️ ADVERTENCIA: Diferencia mayor a tolerancia")
                        else:
                            print(f"✅ Cuotas correctas (diferencia dentro de tolerancia)")
                        
                        print(f"\n✅ RESUMEN CRÉDITO COMPLETO:")
                        print(f"   Código: {codigo_credito}")
                        print(f"   Sucursal: {venta.id_sucursal.nombre_sucursal if venta.id_sucursal else 'N/A'}")
                        print(f"   Almacén: {almacen.nombre_almacen}")
                        print(f"   Caja: {caja.nombre_caja}")
                        print(f"   Total venta: S/ {total}")
                        print(f"   Adelanto: S/ {monto_adelanto}")
                        print(f"   Saldo a financiar: S/ {saldo_financiar}")
                        print(f"   Cantidad cuotas: {cantidad_cuotas}")
                        print(f"   Tasa interés: {tasa_interes}%")

                        return JsonResponse({
                            'ok': True,
                            'message': 'Venta a crédito registrada correctamente.',
                            'numero_comprobante': numero_comprobante,
                            'codigo_credito': codigo_credito,
                            'idventa': venta.idventa,
                            'total_venta': float(total),
                            'monto_adelanto': float(monto_adelanto),
                            'saldo_financiar': float(saldo_financiar),
                            'es_credito': True
                        })

                # ========================================
                # SI ES VENTA AL CONTADO
                # ========================================
                print(f"✅ VENTA AL CONTADO REGISTRADA - ID: {venta.idventa}")
                print(f"   Sucursal: {venta.id_sucursal.nombre_sucursal if venta.id_sucursal else 'N/A'}")
                print(f"   Almacén: {almacen.nombre_almacen}")
                print(f"   Caja: {caja.nombre_caja}")
                print(f"   Total: S/ {venta.total_venta}")
                
                descripcion_movimiento = f"Venta {numero_comprobante} - Cliente: {venta.idcliente.razonsocial}"
                
                movimiento_caja = MovimientoCaja.objects.create(
                    id_caja=caja,
                    id_movimiento=apertura,  # ✅ Asociar a la apertura actual
                    idusuario=usuario,
                    tipo_movimiento='ingreso',
                    monto=total,
                    descripcion=descripcion_movimiento,
                    idventa=venta,
                    estado=1
                )
                
                print(f"✅ MOVIMIENTO DE CAJA CREADO - ID: {movimiento_caja.id_movimiento_caja}")
                print(f"   Asociado a apertura: {apertura.id_movimiento}")
                print(f"   Monto ingreso: S/ {total}")

                return JsonResponse({
                    'ok': True,
                    'message': 'Venta registrada correctamente.',
                    'numero_comprobante': numero_comprobante,
                    'idventa': venta.idventa,
                    'es_credito': False
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


# ==================== OBTENER VENTA PARA EDICIÓN ====================
def obtener_venta(request, eid):
    """Obtiene los datos de una venta para edición (AJAX)"""
    try:
        from software.utils.url_encryptor import decrypt_id
        
        id = decrypt_id(eid)
        if not id:
            return JsonResponse({'success': False, 'error': 'URL inválida'}, status=400)
        
        venta = Ventas.objects.get(idventa=id, estado=1)
        
        # ✅ VALIDAR: Solo ventas al CONTADO son editables
        if venta.id_forma_pago and venta.id_forma_pago.id_forma_pago == 2:
            return JsonResponse({
                'success': False,
                'error': 'No se pueden editar ventas a crédito. Solo puede anularla y crear una nueva.',
                'codigo': 'VENTA_CREDITO_NO_EDITABLE'
            }, status=400)
        
        detalles = VentaDetalle.objects.filter(idventa=venta, estado=1).select_related(
            'id_vehiculo__idproducto',
            'id_vehiculo__idestadoproducto',
            'id_repuesto_comprado__id_repuesto'
        )
        
        # Formatear detalles
        detalles_list = []
        for d in detalles:
            if d.tipo_item == 'vehiculo' and d.id_vehiculo:
                detalles_list.append({
                    'tipo': 'vehiculo',
                    'id_vehiculo': d.id_vehiculo.id_vehiculo,
                    'nombre_producto': d.id_vehiculo.idproducto.nomproducto,
                    'serie_motor': d.id_vehiculo.serie_motor or '',
                    'serie_chasis': d.id_vehiculo.serie_chasis or '',
                    'cantidad': d.cantidad,
                    'precio_compra': float(d.precio_compra),
                    'precio_venta_contado': float(d.precio_venta_contado),
                    'precio_venta_credito': float(d.precio_venta_credito) if d.precio_venta_credito else 0,
                    'subtotal': float(d.subtotal),
                    'ganancia': float(d.ganancia)
                })
            elif d.tipo_item == 'repuesto' and d.id_repuesto_comprado:
                detalles_list.append({
                    'tipo': 'repuesto',
                    'id_repuesto_comprado': d.id_repuesto_comprado.id_repuesto_comprado,
                    'nombre_repuesto': d.id_repuesto_comprado.id_repuesto.nombre,
                    'codigo_barras': d.id_repuesto_comprado.codigo_barras or '',
                    'cantidad': d.cantidad,
                    'precio_compra': float(d.precio_compra),
                    'precio_venta_contado': float(d.precio_venta_contado),
                    'precio_venta_credito': float(d.precio_venta_credito) if d.precio_venta_credito else 0,
                    'subtotal': float(d.subtotal),
                    'ganancia': float(d.ganancia)
                })
        
        # ✅ CONSTRUIR RESPUESTA CON VALIDACIONES
        return JsonResponse({
            'success': True,
            'venta': {
                'idventa': venta.idventa,
                'idcliente': venta.idcliente.idcliente,
                'cliente_nombre': venta.idcliente.razonsocial,
                'numero_comprobante': venta.numero_comprobante,
                'fecha_venta': venta.fecha_venta.strftime('%Y-%m-%d'),
                'idtipocomprobante': venta.idtipocomprobante.idtipocomprobante if venta.idtipocomprobante else None,
                'idseriecomprobante': venta.idseriecomprobante.idseriecomprobante if venta.idseriecomprobante else None,
                'id_tipo_igv': venta.id_tipo_igv.id_tipo_igv if venta.id_tipo_igv else 1,  # ✅ VALIDACIÓN AGREGADA
                'id_forma_pago': venta.id_forma_pago.id_forma_pago if venta.id_forma_pago else 1,  # ✅ VALIDACIÓN
                'id_tipo_pago': venta.id_tipo_pago.id_tipo_pago if venta.id_tipo_pago else None,
                'importe_recibido': float(venta.importe_recibido) if venta.importe_recibido else 0,
                'vuelto': float(venta.vuelto) if venta.vuelto else 0,
                'observaciones': venta.observaciones or '',
                'total_venta': float(venta.total_venta),
                'total_ganancia': float(venta.total_ganancia)
            },
            'detalles': detalles_list
        })
        
    except Ventas.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Venta no encontrada'
        }, status=404)
    except Exception as e:
        print(f"ERROR obtener_venta: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== ACTUALIZAR VENTA (EDICIÓN) - CON AUDITORÍA ====================
@requiere_caja_aperturada
@transaction.atomic
def actualizar_venta(request, eid):
    """Actualiza una venta existente - SOLO CONTADO (crédito no se puede editar por cuotas)"""
    if request.method == "POST":
        try:
            print("======= DEBUG POST ACTUALIZAR VENTA =======")
            for k, v in request.POST.items():
                print(f"{k}: {v}")
            print("===========================================")
            from software.utils.url_encryptor import decrypt_id
            
            id = decrypt_id(eid)
            if not id:
                return JsonResponse({'ok': False, 'error': 'URL inválida'}, status=400)
            
            # Obtener la venta existente
            venta = Ventas.objects.get(idventa=id, estado=1)
            
            # VALIDAR: No se puede editar ventas a crédito (por las cuotas y créditos)
            if venta.id_forma_pago.id_forma_pago == 2:
                return JsonResponse({
                    'ok': False,
                    'error': 'No se pueden editar ventas a crédito. Debe anularla y crear una nueva.',
                    'codigo': 'VENTA_CREDITO_NO_EDITABLE'
                }, status=400)
            
            # ✅ GUARDAR DATOS ANTERIORES PARA AUDITORÍA
            datos_anteriores = {
                'numero_comprobante': venta.numero_comprobante,
                'cliente': venta.idcliente.razonsocial,
                'total': float(venta.total_venta),
                'fecha': str(venta.fecha_venta),
                'forma_pago': venta.id_forma_pago.nombre,
                'tipo_pago': venta.id_tipo_pago.nombre if venta.id_tipo_pago else 'N/A',
                'observaciones': venta.observaciones or ''
            }
            
            # Actualizar datos principales
            venta.idcliente_id = int(request.POST.get("cliente"))
            venta.idtipocomprobante_id = int(request.POST.get("tipo_comprobante"))
            venta.idseriecomprobante_id = int(request.POST.get("serie"))
            venta.id_tipo_igv_id = int(request.POST.get("tipo_igv"))
            venta.fecha_venta = request.POST.get("fecha_venta")
            venta.id_forma_pago_id = int(request.POST.get("forma_pago"))
            
            tipo_pago = request.POST.get("tipo_pago")
            venta.id_tipo_pago_id = int(tipo_pago) if tipo_pago else None
            
            importe_recibido = request.POST.get("importe_recibido")
            vuelto = request.POST.get("vuelto")
            venta.importe_recibido = Decimal(importe_recibido) if importe_recibido else None
            venta.vuelto = Decimal(vuelto) if vuelto else None
            venta.observaciones = request.POST.get("observaciones", "")
            
            # Eliminar detalles antiguos (soft delete)
            VentaDetalle.objects.filter(idventa=venta).update(estado=0)
            
            # Agregar nuevos detalles
            total = Decimal('0')
            total_ganancia = Decimal('0')
            items = int(request.POST.get("items_count") or 0)
            
            for i in range(1, items + 1):
                tipo_item = request.POST.get(f"tipo_item_{i}")
                if not tipo_item:
                    continue

                cantidad = int(request.POST.get(f"cantidad_{i}") or 1)
                precio_venta_contado = Decimal(request.POST.get(f"precio_venta_contado_{i}") or 0)
                precio_venta_credito = request.POST.get(f"precio_venta_credito_{i}")
                precio_venta_credito = Decimal(precio_venta_credito) if precio_venta_credito else None
                precio_compra = Decimal(request.POST.get(f"precio_compra_{i}") or 0)
                
                # ✅ NUEVO: Precio de descuento
                precio_descuento = request.POST.get(f"precio_descuento_{i}")
                precio_descuento = Decimal(precio_descuento) if precio_descuento else None
                
                # Para contado, usar precio con descuento si existe
                if precio_descuento:
                    precio_final = precio_descuento
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
            
            # Actualizar totales
            venta.subtotal = total
            venta.total_venta = total
            venta.total_ganancia = total_ganancia
            venta.save()
            
            # ✅ REGISTRAR EN AUDITORÍA
            AuditoriaVentas.objects.create(
                idventa=id,
                accion='EDICION',
                motivo='Venta actualizada',
                idusuario_id=request.session.get('idusuario'),
                datos_anteriores=datos_anteriores
            )
            
            print(f"✅ VENTA ACTUALIZADA - ID: {venta.idventa}")
            print(f"✅ AUDITORÍA REGISTRADA")
            
            return JsonResponse({
                'ok': True,
                'message': 'Venta actualizada correctamente'
            })
            
        except Ventas.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'La venta no existe o ya fue eliminada'
            }, status=404)
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
                'error': f'Error al actualizar la venta: {str(e)}'
            }, status=400)
    
    return redirect("ventas")


# ==================== ELIMINAR VENTA CON MOTIVO Y AUDITORÍA (SOLO ADMIN) ====================
def eliminar_venta(request, eid):
    """Eliminación lógica de una venta (cambia estado a 0) - SOLO ADMIN con motivo obligatorio"""
    if request.method == "POST":
        try:
            from software.utils.url_encryptor import decrypt_id
            
            id = decrypt_id(eid)
            if not id:
                return JsonResponse({'success': False, 'error': 'URL inválida'}, status=400)
            # ✅ VALIDAR PERMISOS: Solo admin puede eliminar
            id_tipo_usuario = request.session.get('idtipousuario')
            
            if id_tipo_usuario != 1:  # 1 = Admin
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'No tiene permisos para eliminar ventas. Solo administradores pueden realizar esta acción.',
                        'codigo': 'SIN_PERMISOS'
                    }, status=403)
                return redirect('ventas')
            
            # ✅ VALIDAR MOTIVO
            motivo = request.POST.get('motivo', '').strip()
            
            if not motivo or len(motivo) < 10:
                return JsonResponse({
                    'success': False,
                    'error': 'Debe proporcionar un motivo válido (mínimo 10 caracteres)'
                }, status=400)
            
            idusuario = request.session.get('idusuario')
            
            # Obtener la venta
            venta = Ventas.objects.get(idventa=id, estado=1)
            
            # ✅ GUARDAR DATOS PARA AUDITORÍA
            datos_venta = {
                'numero_comprobante': venta.numero_comprobante,
                'cliente': venta.idcliente.razonsocial,
                'total': float(venta.total_venta),
                'fecha': str(venta.fecha_venta),
                'forma_pago': venta.id_forma_pago.nombre
            }
            
            # Cambiar estado (soft delete)
            venta.estado = 0
            venta.save()
            
            # ✅ REGISTRAR EN AUDITORÍA
            AuditoriaVentas.objects.create(
                idventa=id,
                accion='ELIMINACION',
                motivo=motivo,
                idusuario_id=idusuario,
                datos_anteriores=datos_venta
            )
            
            print(f"✅ VENTA ELIMINADA - ID: {id}")
            print(f"✅ AUDITORÍA REGISTRADA - Motivo: {motivo}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Venta eliminada correctamente'
                })
            
            return redirect('ventas')
            
        except Ventas.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'La venta no existe'
                }, status=404)
            return redirect('ventas')
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            return redirect('ventas')
    
    return redirect("ventas")
    

#Para Imprimir_comprobante
def imprimir_comprobante(request, eid):
    """
    Genera un PDF del comprobante de venta en formato TICKET con logo y QR
    Optimizado para impresoras térmicas de 80mm - ALTURA AUTOMÁTICA
    SOLO para ventas al CONTADO
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
        from software.models.empresaModel import Empresa
        from software.utils.url_encryptor import decrypt_id
        
        idventa = decrypt_id(eid)
        if not idventa:
            return HttpResponse("URL inválida", status=400)
        
        # Obtener la venta
        venta = get_object_or_404(Ventas, idventa=idventa)
        
        # ✅ VALIDAR: Si es crédito, NO imprimir ticket
        if venta.id_forma_pago.id_forma_pago == 2:  # Es crédito
            return HttpResponse("""
                <html>
                <head>
                    <title>Venta a Crédito</title>
                    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
                </head>
                <body>
                    <script>
                        Swal.fire({
                            icon: 'info',
                            title: 'Venta a Crédito',
                            html: '<p>Las ventas a crédito no generan ticket de venta.</p>' +
                                  '<p>Debe imprimir el <strong>Cronograma de Cuotas</strong> desde el módulo de Créditos.</p>',
                            confirmButtonText: 'Ir a Créditos',
                            showCancelButton: true,
                            cancelButtonText: 'Cerrar',
                            confirmButtonColor: '#3085d6',
                            cancelButtonColor: '#6c757d'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                window.location.href = '/creditos/';
                            } else {
                                window.close();
                            }
                        });
                    </script>
                </body>
                </html>
            """, content_type='text/html')
        
        # Obtener detalles de la venta
        detalles = VentaDetalle.objects.filter(idventa=venta, estado=1)

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
        # ENCABEZADO - DATOS DE LA EMPRESA
        # ==========================================
        nombre_empresa = empresa.razonsocial if empresa.razonsocial else empresa.nombrecomercial
        elements.append(Paragraph(nombre_empresa.upper(), style_company))
        elements.append(Paragraph(f"RUC: {empresa.ruc}", style_normal_center))
        elements.append(Paragraph(empresa.direccion.upper(), style_normal_center))
        elements.append(Paragraph(f"Telf: {empresa.telefono}", style_normal_center))
        if empresa.pagina:
            elements.append(Paragraph(f"Pagina: {empresa.pagina}", style_small))
         
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
            # ✅ VALIDAR tipo de item y que los datos existan
            if detalle.tipo_item == 'vehiculo' and detalle.id_vehiculo:
                vehiculo = detalle.id_vehiculo
                
                # Validar que el vehículo tenga producto asociado
                if not vehiculo or not vehiculo.idproducto:
                    print(f"⚠️ Detalle {detalle.id} tiene vehículo sin producto")
                    continue
                
                nombre_producto = vehiculo.idproducto.nomproducto
                if len(nombre_producto) > 25:
                    nombre_producto = nombre_producto[:22] + '...'
                
                serie_motor = vehiculo.serie_motor[:15] if vehiculo.serie_motor else 'N/A'
                serie_chasis = vehiculo.serie_chasis[:15] if vehiculo.serie_chasis else 'N/A'
                descripcion = f"{nombre_producto}\n{serie_motor}\n{serie_chasis}"
                
            elif detalle.tipo_item == 'repuesto' and detalle.id_repuesto_comprado:
                repuesto = detalle.id_repuesto_comprado
                
                # ✅ VALIDAR que repuesto y su relación existan
                if not repuesto or not repuesto.id_repuesto:
                    print(f"⚠️ Detalle {detalle.id} tiene repuesto sin relación id_repuesto")
                    continue
                
                nombre_repuesto = repuesto.id_repuesto.nombre
                if len(nombre_repuesto) > 25:
                    nombre_repuesto = nombre_repuesto[:22] + '...'
                codigo = repuesto.codigo_barras or 'S/N'
                descripcion = f"{nombre_repuesto}\n{codigo[:12]}"
                
            else:
                # ✅ Si el detalle no tiene datos válidos, saltar
                print(f"⚠️ Detalle sin datos válidos - ID: {detalle.id if hasattr(detalle, 'id') else 'N/A'}, Tipo: {detalle.tipo_item}")
                continue
            
            # Precio unitario (siempre contado porque ya validamos que no es crédito)
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
        
        # Importe recibido y vuelto (solo para contado)
        if venta.importe_recibido:
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





