from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from software.models.transferenciaModel import Transferencia
from software.models.detalleTransferenciaModel import DetalleTransferencia
from software.models.stockModel import Stock
from software.models.almacenesModel import Almacenes
from software.models.sucursalesModel import Sucursales
from software.models.VehiculosModel import Vehiculo
from software.models.RespuestoCompModel import RepuestoComp
from software.models.UsuarioModel import Usuario
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def transferencias(request):
    """
    Listado de transferencias
    """
    id_tipo_usuario = request.session.get('idtipousuario')
    idusuario = request.session.get('idusuario')
    
    if not id_tipo_usuario or not idusuario:
        return HttpResponse("<h1>No tiene acceso</h1>")
    
    # Verificar permisos
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id_tipo_usuario)
    es_admin = id_tipo_usuario == 1
    
    # Obtener usuario actual
    usuario = Usuario.objects.get(idusuario=idusuario)
    
    # Obtener transferencias
    if es_admin:
        # Admin ve todas las transferencias
        transferencias_list = Transferencia.objects.all().select_related(
            'id_almacen_origen', 'id_almacen_destino', 
            'idusuario_solicita', 'idusuario_confirma'
        ).prefetch_related('detalles').order_by('-fecha_transferencia')
    else:
        # Usuario normal solo ve transferencias de su sucursal
        if usuario.id_sucursal:
            almacenes_sucursal = Almacenes.objects.filter(
                id_sucursal=usuario.id_sucursal,
                estado=1
            )
            transferencias_list = Transferencia.objects.filter(
                id_almacen_destino__in=almacenes_sucursal
            ).select_related(
                'id_almacen_origen', 'id_almacen_destino',
                'idusuario_solicita', 'idusuario_confirma'
            ).prefetch_related('detalles').order_by('-fecha_transferencia')
        else:
            transferencias_list = []
    
    # Obtener sucursales y almacenes para el formulario
    if es_admin:
        sucursales = Sucursales.objects.filter(estado=1)
        almacenes = Almacenes.objects.filter(estado=1)
    else:
        sucursales = Sucursales.objects.filter(id_sucursal=usuario.id_sucursal.id_sucursal)
        almacenes = Almacenes.objects.filter(id_sucursal=usuario.id_sucursal, estado=1)
    
    # Obtener sucursal principal para transferencias
    sucursal_principal = Sucursales.objects.filter(es_principal=True, estado=1).first()
    almacenes_principal = Almacenes.objects.filter(
        id_sucursal=sucursal_principal,
        estado=1
    ) if sucursal_principal else []
    
    data = {
        'transferencias': transferencias_list,
        'sucursales': sucursales,
        'almacenes': almacenes,
        'almacenes_principal': almacenes_principal,
        'sucursal_principal': sucursal_principal,
        'es_admin': es_admin,
        'permisos': permisos,
    }
    
    return render(request, 'transferencias/transferencias.html', data)


def obtener_stock_almacen(request):
    """
    API: Obtener stock disponible de un almacén
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    id_almacen = request.GET.get('id_almacen')
    
    if not id_almacen:
        return JsonResponse({'error': 'Almacén no especificado'}, status=400)
    
    try:
        almacen = Almacenes.objects.get(id_almacen=id_almacen)
        
        # Obtener stock disponible
        stocks = Stock.objects.filter(
            id_almacen=almacen,
            cantidad_disponible__gt=0,
            estado=1
        ).select_related('id_vehiculo', 'id_repuesto_comprado')
        
        # Agrupar por tipo
        vehiculos_stock = []
        repuestos_stock = []
        
        for stock in stocks:
            if stock.id_vehiculo:
                vehiculos_stock.append({
                    'id_vehiculo': stock.id_vehiculo.id_vehiculo,
                    'nombre': stock.id_vehiculo.idproducto.nomproducto,
                    'serie_motor': stock.id_vehiculo.serie_motor,
                    'serie_chasis': stock.id_vehiculo.serie_chasis,
                    'cantidad_disponible': stock.cantidad_disponible,
                })
            elif stock.id_repuesto_comprado:
                repuestos_stock.append({
                    'id_repuesto_comprado': stock.id_repuesto_comprado.id_repuesto_comprado,
                    'nombre': stock.id_repuesto_comprado.id_repuesto.nombre,
                    'codigo_barras': stock.id_repuesto_comprado.codigo_barras or 'S/N',
                    'cantidad_disponible': stock.cantidad_disponible,
                })
        
        return JsonResponse({
            'vehiculos': vehiculos_stock,
            'repuestos': repuestos_stock,
        })
        
    except Almacenes.DoesNotExist:
        return JsonResponse({'error': 'Almacén no encontrado'}, status=404)
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({'error': 'Error al obtener stock'}, status=500)


def nueva_transferencia(request):
    """
    Crear nueva transferencia
    """
    if request.method != 'POST':
        return redirect('transferencias')
    
    try:
        with transaction.atomic():
            # Obtener datos del formulario
            id_almacen_origen = int(request.POST.get('id_almacen_origen'))
            id_almacen_destino = int(request.POST.get('id_almacen_destino'))
            fecha_transferencia = request.POST.get('fecha_transferencia')
            numero_guia = request.POST.get('numero_guia', '').strip()
            observaciones = request.POST.get('observaciones', '').strip()
            idusuario = request.session.get('idusuario')
            
            # Validaciones
            if id_almacen_origen == id_almacen_destino:
                return JsonResponse({
                    'ok': False,
                    'error': 'El almacén origen y destino no pueden ser iguales'
                }, status=400)
            
            # Verificar que origen sea de sucursal principal
            almacen_origen = Almacenes.objects.get(id_almacen=id_almacen_origen)
            if not almacen_origen.id_sucursal.es_principal:
                return JsonResponse({
                    'ok': False,
                    'error': 'Solo se pueden realizar transferencias desde la sucursal principal'
                }, status=400)
            
            # Crear transferencia
            transferencia = Transferencia.objects.create(
                id_almacen_origen_id=id_almacen_origen,
                id_almacen_destino_id=id_almacen_destino,
                idusuario_solicita_id=idusuario,
                fecha_transferencia=fecha_transferencia,
                numero_guia=numero_guia,
                observaciones=observaciones,
                estado='pendiente'
            )
            
            # Procesar items (vehículos y repuestos)
            items_count = int(request.POST.get('items_count', 0))
            
            if items_count == 0:
                raise ValueError("Debe agregar al menos un producto a la transferencia")
            
            for i in range(1, items_count + 1):
                tipo_item = request.POST.get(f'tipo_item_{i}')
                
                if not tipo_item:
                    continue
                
                cantidad = int(request.POST.get(f'cantidad_{i}', 1))
                
                if tipo_item == 'vehiculo':
                    id_vehiculo = request.POST.get(f'id_vehiculo_{i}')
                    
                    if not id_vehiculo:
                        raise ValueError(f"Debe seleccionar un vehículo para el ítem {i}")
                    
                    # Verificar stock disponible
                    stock = Stock.objects.filter(
                        id_almacen_id=id_almacen_origen,
                        id_vehiculo_id=id_vehiculo,
                        estado=1
                    ).first()
                    
                    if not stock or stock.cantidad_disponible < cantidad:
                        vehiculo = Vehiculo.objects.get(id_vehiculo=id_vehiculo)
                        raise ValueError(f"Stock insuficiente para el vehículo {vehiculo.idproducto.nomproducto}")
                    
                    # Crear detalle
                    DetalleTransferencia.objects.create(
                        id_transferencia=transferencia,
                        id_vehiculo_id=id_vehiculo,
                        cantidad=cantidad,
                        estado=1
                    )
                
                elif tipo_item == 'repuesto':
                    id_repuesto_comprado = request.POST.get(f'id_repuesto_{i}')
                    
                    if not id_repuesto_comprado:
                        raise ValueError(f"Debe seleccionar un repuesto para el ítem {i}")
                    
                    # Verificar stock disponible
                    stock = Stock.objects.filter(
                        id_almacen_id=id_almacen_origen,
                        id_repuesto_comprado_id=id_repuesto_comprado,
                        estado=1
                    ).first()
                    
                    if not stock or stock.cantidad_disponible < cantidad:
                        repuesto = RepuestoComp.objects.get(id_repuesto_comprado=id_repuesto_comprado)
                        raise ValueError(f"Stock insuficiente para el repuesto {repuesto.id_repuesto.nombre}")
                    
                    # Crear detalle
                    DetalleTransferencia.objects.create(
                        id_transferencia=transferencia,
                        id_repuesto_comprado_id=id_repuesto_comprado,
                        cantidad=cantidad,
                        estado=1
                    )
            
            print(f"✅ Transferencia creada: #{transferencia.id_transferencia}")
            
            return JsonResponse({
                'ok': True,
                'message': 'Transferencia registrada correctamente',
                'id_transferencia': transferencia.id_transferencia
            })
    
    except ValueError as ve:
        print(f"Error de validación: {str(ve)}")
        return JsonResponse({
            'ok': False,
            'error': str(ve)
        }, status=400)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al procesar la transferencia: {str(e)}'
        }, status=500)


@transaction.atomic
def confirmar_transferencia(request, id):
    """
    Confirmar una transferencia y actualizar stock
    """
    if request.method != 'POST':
        return redirect('transferencias')
    
    try:
        transferencia = get_object_or_404(Transferencia, id_transferencia=id)
        
        # Validar que esté pendiente
        if transferencia.estado != 'pendiente':
            return JsonResponse({
                'ok': False,
                'error': 'La transferencia ya fue procesada'
            }, status=400)
        
        print(f"🔄 Confirmando transferencia #{transferencia.id_transferencia}")
        print(f"   Origen: {transferencia.id_almacen_origen.nombre_almacen}")
        print(f"   Destino: {transferencia.id_almacen_destino.nombre_almacen}")
        
        # Procesar cada detalle de la transferencia
        for detalle in transferencia.detalles.filter(estado=1):
            print(f"   📦 Procesando detalle - Cantidad: {detalle.cantidad}")
            
            # VEHÍCULOS
            if detalle.id_vehiculo:
                vehiculo = detalle.id_vehiculo
                print(f"      Vehículo: {vehiculo.serie_motor}")
                
                # 1️⃣ RESTAR del almacén ORIGEN
                stock_origen = Stock.objects.filter(
                    id_almacen=transferencia.id_almacen_origen,
                    id_vehiculo=vehiculo,
                    estado=1
                ).first()
                
                if not stock_origen:
                    raise ValueError(f'No existe stock en origen para vehículo {vehiculo.serie_motor}')
                
                if stock_origen.cantidad_disponible < detalle.cantidad:
                    raise ValueError(f'Stock insuficiente en origen para vehículo {vehiculo.serie_motor}. Disponible: {stock_origen.cantidad_disponible}, Requerido: {detalle.cantidad}')
                
                print(f"      Stock origen ANTES: {stock_origen.cantidad_disponible}")
                stock_origen.cantidad_disponible -= detalle.cantidad
                stock_origen.save()
                print(f"      Stock origen DESPUÉS: {stock_origen.cantidad_disponible}")
                
                # 2️⃣ SUMAR al almacén DESTINO
                stock_destino, created = Stock.objects.get_or_create(
                    id_almacen=transferencia.id_almacen_destino,
                    id_vehiculo=vehiculo,
                    defaults={
                        'cantidad_disponible': 0,
                        'estado': 1
                    }
                )
                
                print(f"      Stock destino ANTES: {stock_destino.cantidad_disponible} (creado: {created})")
                stock_destino.cantidad_disponible += detalle.cantidad
                stock_destino.save()
                print(f"      Stock destino DESPUÉS: {stock_destino.cantidad_disponible}")
            
            # REPUESTOS
            elif detalle.id_repuesto_comprado:
                repuesto = detalle.id_repuesto_comprado
                print(f"      Repuesto: {repuesto.id_repuesto.nombre}")
                
                # 1️⃣ RESTAR del almacén ORIGEN
                stock_origen = Stock.objects.filter(
                    id_almacen=transferencia.id_almacen_origen,
                    id_repuesto_comprado=repuesto,
                    estado=1
                ).first()
                
                if not stock_origen:
                    raise ValueError(f'No existe stock en origen para repuesto {repuesto.id_repuesto.nombre}')
                
                if stock_origen.cantidad_disponible < detalle.cantidad:
                    raise ValueError(f'Stock insuficiente en origen para repuesto {repuesto.id_repuesto.nombre}')
                
                print(f"      Stock origen ANTES: {stock_origen.cantidad_disponible}")
                stock_origen.cantidad_disponible -= detalle.cantidad
                stock_origen.save()
                print(f"      Stock origen DESPUÉS: {stock_origen.cantidad_disponible}")
                
                # 2️⃣ SUMAR al almacén DESTINO
                stock_destino, created = Stock.objects.get_or_create(
                    id_almacen=transferencia.id_almacen_destino,
                    id_repuesto_comprado=repuesto,
                    defaults={
                        'cantidad_disponible': 0,
                        'estado': 1
                    }
                )
                
                print(f"      Stock destino ANTES: {stock_destino.cantidad_disponible} (creado: {created})")
                stock_destino.cantidad_disponible += detalle.cantidad
                stock_destino.save()
                print(f"      Stock destino DESPUÉS: {stock_destino.cantidad_disponible}")
        
        # 3️⃣ MARCAR transferencia como confirmada
        idusuario = request.session.get('idusuario')
        transferencia.estado = 'confirmada'
        transferencia.idusuario_confirma_id = idusuario
        transferencia.fecha_confirmacion = timezone.now()
        transferencia.save()
        
        print(f"✅ Transferencia confirmada: #{transferencia.id_transferencia}")
        
        return JsonResponse({
            'ok': True,
            'message': 'Transferencia confirmada correctamente'
        })
    
    except ValueError as ve:
        print(f"❌ Error de validación: {str(ve)}")
        return JsonResponse({
            'ok': False,
            'error': str(ve)
        }, status=400)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al confirmar transferencia: {str(e)}'
        }, status=500)



def rechazar_transferencia(request, id):
    """
    Rechazar una transferencia
    """
    if request.method != 'POST':
        return redirect('transferencias')
    
    try:
        transferencia = get_object_or_404(Transferencia, id_transferencia=id)
        
        if transferencia.estado != 'pendiente':
            return JsonResponse({
                'ok': False,
                'error': 'La transferencia ya fue procesada'
            }, status=400)
        
        transferencia.estado = 'rechazada'
        transferencia.save()
        
        print(f"❌ Transferencia rechazada: #{transferencia.id_transferencia}")
        
        return JsonResponse({
            'ok': True,
            'message': 'Transferencia rechazada'
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Error al rechazar transferencia: {str(e)}'
        }, status=500)