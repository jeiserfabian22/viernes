from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from software.models.comprasModel import Compras
from software.models.ProveedoresModel import Proveedores
from software.models.FormaPagoModel import FormaPago
from software.models.TipoPagoModel import TipoPago
from software.models.compradetalleModel import CompraDetalle
from software.models.RespuestoCompModel import RepuestoComp
from software.models.VehiculosModel import Vehiculo
from software.models.ProductoModel import Producto
from software.models.RepuestoModel import Repuesto
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.estadoproductoModel import EstadoProducto
from django.db import transaction
from software.models.cuotaModel import Cuota
from software.models.TipoclienteModel import Tipocliente
from software.models.AperturaCierreCajaModel import AperturaCierreCaja
from software.decorators import requiere_caja_aperturada


# Listado de compras optimizado
def compras(request):
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
    
    # Compras activas, ordenadas de más recientes a más antiguas
    Compras_registros = Compras.objects.filter(estado=1).order_by('-fechacompra')
    
    # Catálogos relacionados
    proveedor = Proveedores.objects.filter(estado=1)
    tipocliente = Tipocliente.objects.filter(estado=1)
    formapago = FormaPago.objects.filter(estado=1)
    tipopago = TipoPago.objects.filter(estado=1)
    repuestocomprado = RepuestoComp.objects.filter(estado=1)
    vehiculo = Vehiculo.objects.filter(estado=1)
    producto = Producto.objects.filter(estado=1)
    repuesto = Repuesto.objects.filter(estado=1)
    estadoproducto = EstadoProducto.objects.filter(estado=1)

    # Contexto para el template
    data = {
        'compras_registros': Compras_registros,
        'proveedor': proveedor,
        'tipo_cliente': tipocliente,
        'forma_pago': formapago,
        'tipo_pago': tipopago,
        'repuestos_comprados': repuestocomprado,
        'vehiculo': vehiculo,
        'producto': producto,
        'catalogo_repuestos': repuesto,
        'estado_producto': estadoproducto,
        'permisos': permisos,
        'apertura_actual': apertura_actual,
        'tiene_caja_abierta': bool(apertura_actual)
    }
    
    return render(request, 'compras/compras.html', data)


# Nueva compra
@requiere_caja_aperturada
def nueva_compra(request):
    if request.method == "POST":
        try:
            print("======= DEBUG POST COMPRA =======")
            for k, v in request.POST.items():
                print(f"{k}: {v}")
            print("=================================")

            with transaction.atomic():
                # ⭐ NUEVO: Validar caja aperturada
                idusuario_session = request.session.get('idusuario')
                apertura = AperturaCierreCaja.objects.filter(
                    idusuario_id=idusuario_session,
                    estado='abierta'
                ).first()
                
                if not apertura:
                    return JsonResponse({
                        'ok': False,
                        'error': 'No tiene una caja aperturada. Por favor, aperture una caja antes de realizar compras.',
                        'necesita_aperturar': True
                    }, status=400)
                
                # Manejar tipo_pago cuando es crédito
                tipo_pago = request.POST.get("tipo_pago")
                tipo_pago_id = int(tipo_pago) if tipo_pago else None
                
                compra = Compras.objects.create(
                    idproveedor_id=int(request.POST.get("proveedor")),
                    idtipocliente_id=int(request.POST.get("tipo_cliente")),
                    id_forma_pago_id=int(request.POST.get("forma_pago")),
                    id_tipo_pago_id=tipo_pago_id,
                    numcorrelativo=request.POST.get("numcorrelativo"),
                    fechacompra=request.POST.get("fechacompra"),
                    estado=1,
                )

                total = 0
                items = int(request.POST.get("items_count") or 0)
                print(f"DEBUG items_count: {items}")

                for i in range(1, items + 1):
                    tipo_item = request.POST.get(f"tipo_item_{i}")
                    if not tipo_item:
                        continue

                    cantidad = int(request.POST.get(f"cantidad_{i}") or 0)
                    precio_compra = float(request.POST.get(f"precio_compra_{i}") or 0)
                    precio_venta = float(request.POST.get(f"precio_venta_{i}") or 0)

                    if tipo_item == "vehiculo":
                        idproducto = request.POST.get(f"idproducto_{i}", "").strip()
                        idestadoproducto = request.POST.get(f"idestadoproducto_{i}", "").strip()
                        
                        if not idproducto:
                            raise ValueError(f"Debe seleccionar un producto para el ítem {i}")
                        
                        if not idestadoproducto:
                            raise ValueError(f"Debe seleccionar el estado del producto para el ítem {i}")
                        
                        vehiculo = Vehiculo.objects.create(
                            idproducto_id=int(idproducto),
                            serie_motor=request.POST.get(f"serie_motor_{i}", "").strip(),
                            serie_chasis=request.POST.get(f"serie_chasis_{i}", "").strip(),
                            idestadoproducto_id=int(idestadoproducto),
                            imperfecciones=request.POST.get(f"imperfecciones_{i}", "").strip(),
                            estado=1
                        )
                        CompraDetalle.objects.create(
                            idcompra=compra,
                            id_vehiculo=vehiculo,
                            id_repuesto_comprado=None,
                            cantidad=cantidad,
                            precio_compra=precio_compra,
                            precio_venta=precio_venta,
                            subtotal=cantidad * precio_compra
                        )

                    elif tipo_item == "repuesto":
                        id_repuesto = request.POST.get(f"id_repuesto_{i}", "").strip()
                        
                        if not id_repuesto:
                            raise ValueError(f"Debe seleccionar un repuesto para el ítem {i}")
                        
                        repuesto = RepuestoComp.objects.create(
                            id_repuesto_id=int(id_repuesto),
                            descripcion=request.POST.get(f"descripcion_{i}", "").strip(),
                            codigo_barras=request.POST.get(f"codigo_barras_{i}", "").strip(),
                            estado=1
                        )
                        CompraDetalle.objects.create(
                            idcompra=compra,
                            id_repuesto_comprado=repuesto,
                            id_vehiculo=None,
                            cantidad=cantidad,
                            precio_compra=precio_compra,
                            precio_venta=precio_venta,
                            subtotal=cantidad * precio_compra
                        )

                    total += cantidad * precio_compra

                compra.total_compra = total
                compra.save()

                # Guardar cuotas si aplica
                if request.POST.get("forma_pago") == "2" and request.POST.get("tiene_cuotas") == "1":
                    cuotas = int(request.POST.get("credito_cuotas") or 0)
                    for i in range(1, cuotas + 1):
                        monto_adelanto_cuota = float(request.POST.get(f"monto_adelanto_{i}", 0) or 0)
                        
                        Cuota.objects.create(
                            idcompra=compra,
                            numero_cuota=int(request.POST.get(f"numero_cuota_{i}")),
                            monto=float(request.POST.get(f"monto_{i}")),
                            tasa=float(request.POST.get(f"tasa_{i}")),
                            interes=float(request.POST.get(f"interes_{i}")),
                            total=float(request.POST.get(f"total_{i}")),
                            fecha_vencimiento=request.POST.get(f"fecha_vencimiento_{i}"),
                            monto_adelanto=monto_adelanto_cuota,
                            estado=1
                        )

                print(f"✅ COMPRA REGISTRADA - ID: {compra.idcompra}, Caja: {apertura.id_caja.nombre_caja}")

            return JsonResponse({
                'ok': True,
                'message': 'Compra registrada correctamente.'
            })

        except ValueError as ve:
            print(f"ERROR DE VALIDACIÓN: {str(ve)}")
            return JsonResponse({
                'ok': False,
                'error': str(ve)
            })
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return JsonResponse({
                'ok': False,
                'error': 'Error al procesar la compra. Verifica que todos los campos estén completos.'
            })

    return redirect("compras")


