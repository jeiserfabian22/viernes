
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from software.models.compradetalleModel import CompraDetalle
from software.models.VentaDetalleModel import VentaDetalle
from software.models.transferenciaModel import Transferencia
from software.models.detalleTransferenciaModel import DetalleTransferencia
from software.models.stockModel import Stock
from software.models.movimientoCajaModel import MovimientoCaja


# ============================================
# SIGNAL 1: Crear Stock al registrar Compra
# ============================================
@receiver(post_save, sender=CompraDetalle)
def crear_stock_compra(sender, instance, created, **kwargs):
    """
    Cuando se registra un detalle de compra, crea o actualiza el stock
    en el almacén de la sucursal principal
    """
    if created:
        # Obtener almacén de la sucursal principal (o de la compra si está definido)
        if instance.idcompra.id_sucursal:
            almacen = instance.idcompra.id_sucursal.almacenes.filter(estado=1).first()
        else:
            # Si no hay sucursal en la compra, usar la primera sucursal principal
            from software.models.sucursalesModel import Sucursales
            sucursal_principal = Sucursales.objects.filter(es_principal=True, estado=1).first()
            if sucursal_principal:
                almacen = sucursal_principal.almacenes.filter(estado=1).first()
            else:
                print("❌ ERROR: No se encontró sucursal principal")
                return
        
        if not almacen:
            print("❌ ERROR: No se encontró almacén para la sucursal")
            return
        
        # Determinar si es vehículo o repuesto
        if instance.id_vehiculo:
            # VEHÍCULO: Cantidad siempre es 1 (unidad individual)
            stock, created = Stock.objects.get_or_create(
                id_almacen=almacen,
                id_vehiculo=instance.id_vehiculo,
                defaults={'cantidad_disponible': 1, 'estado': 1}
            )
            if not created:
                stock.agregar_stock(1)
            
            print(f"✅ Stock creado/actualizado: Vehículo {instance.id_vehiculo.id_vehiculo} en {almacen.nombre_almacen}")
        
        elif instance.id_repuesto_comprado:
            # REPUESTO: Usar cantidad del detalle
            stock, created = Stock.objects.get_or_create(
                id_almacen=almacen,
                id_repuesto_comprado=instance.id_repuesto_comprado,
                defaults={'cantidad_disponible': instance.cantidad, 'estado': 1}
            )
            if not created:
                stock.agregar_stock(instance.cantidad)
            
            print(f"✅ Stock creado/actualizado: Repuesto {instance.id_repuesto_comprado.id_repuesto_comprado} - Cantidad: {instance.cantidad}")


# ============================================
# SIGNAL 2: Actualizar Stock en Transferencias
# ============================================
@receiver(post_save, sender=Transferencia)
def actualizar_stock_transferencia(sender, instance, created, **kwargs):
    """
    Cuando una transferencia es CONFIRMADA, actualiza el stock:
    - Descuenta del almacén origen
    - Aumenta en el almacén destino
    """
    # Solo ejecutar cuando la transferencia pasa a estado 'confirmada'
    if not created and instance.estado == 'confirmada' and instance.puede_confirmar():
        # Actualizar fecha de confirmación
        if not instance.fecha_confirmacion:
            instance.fecha_confirmacion = timezone.now()
            instance.save(update_fields=['fecha_confirmacion'])
        
        # Procesar cada detalle de la transferencia
        for detalle in instance.detalles.filter(estado=1):
            if detalle.id_vehiculo:
                # VEHÍCULO
                # Descontar del origen
                stock_origen = Stock.objects.filter(
                    id_almacen=instance.id_almacen_origen,
                    id_vehiculo=detalle.id_vehiculo,
                    estado=1
                ).first()
                
                if stock_origen and stock_origen.descontar_stock(detalle.cantidad):
                    # Agregar al destino
                    stock_destino, created = Stock.objects.get_or_create(
                        id_almacen=instance.id_almacen_destino,
                        id_vehiculo=detalle.id_vehiculo,
                        defaults={'cantidad_disponible': 0, 'estado': 1}
                    )
                    stock_destino.agregar_stock(detalle.cantidad)
                    
                    print(f"✅ Transferencia confirmada: Vehículo {detalle.id_vehiculo.id_vehiculo}")
                    print(f"   Origen: {instance.id_almacen_origen.nombre_almacen} ({stock_origen.cantidad_disponible})")
                    print(f"   Destino: {instance.id_almacen_destino.nombre_almacen} ({stock_destino.cantidad_disponible})")
                else:
                    print(f"❌ ERROR: Stock insuficiente en origen para vehículo {detalle.id_vehiculo.id_vehiculo}")
            
            elif detalle.id_repuesto_comprado:
                # REPUESTO
                stock_origen = Stock.objects.filter(
                    id_almacen=instance.id_almacen_origen,
                    id_repuesto_comprado=detalle.id_repuesto_comprado,
                    estado=1
                ).first()
                
                if stock_origen and stock_origen.descontar_stock(detalle.cantidad):
                    stock_destino, created = Stock.objects.get_or_create(
                        id_almacen=instance.id_almacen_destino,
                        id_repuesto_comprado=detalle.id_repuesto_comprado,
                        defaults={'cantidad_disponible': 0, 'estado': 1}
                    )
                    stock_destino.agregar_stock(detalle.cantidad)
                    
                    print(f"✅ Transferencia confirmada: Repuesto {detalle.id_repuesto_comprado.id_repuesto_comprado} - Cantidad: {detalle.cantidad}")
                else:
                    print(f"❌ ERROR: Stock insuficiente en origen para repuesto {detalle.id_repuesto_comprado.id_repuesto_comprado}")


# ============================================
# SIGNAL 3: Descontar Stock y Crear Movimiento de Caja en Ventas
# ============================================
@receiver(post_save, sender=VentaDetalle)
def procesar_venta(sender, instance, created, **kwargs):
    """
    Cuando se registra un detalle de venta:
    1. Descuenta el stock del almacén de la sucursal
    2. Crea un movimiento de caja (ingreso) automático
    """
    if created:
        # Obtener almacén de la venta (desde la sesión o configuración)
        # En tu caso, deberás pasar el id_almacen desde la vista
        # Por ahora, usamos el primer almacén de la sucursal del usuario
        
        # IMPORTANTE: Necesitarás modificar la vista de ventas para pasar el almacén
        # Por ahora, esta lógica asume que hay un almacén asociado
        
        venta = instance.idventa
        
        # Obtener sucursal del usuario que vendió
        if venta.idusuario.id_sucursal:
            almacen = venta.idusuario.id_sucursal.almacenes.filter(estado=1).first()
        else:
            print("❌ ERROR: Usuario sin sucursal asignada")
            return
        
        if not almacen:
            print("❌ ERROR: No se encontró almacén para la sucursal")
            return
        
        # 1. DESCONTAR STOCK
        if instance.id_vehiculo:
            # VEHÍCULO
            stock = Stock.objects.filter(
                id_almacen=almacen,
                id_vehiculo=instance.id_vehiculo,
                estado=1
            ).first()
            
            if stock and stock.descontar_stock(instance.cantidad):
                print(f"✅ Stock descontado: Vehículo {instance.id_vehiculo.id_vehiculo} - Almacén: {almacen.nombre_almacen}")
            else:
                print(f"❌ ERROR: Stock insuficiente para vehículo {instance.id_vehiculo.id_vehiculo}")
        
        elif instance.id_repuesto_comprado:
            # REPUESTO
            stock = Stock.objects.filter(
                id_almacen=almacen,
                id_repuesto_comprado=instance.id_repuesto_comprado,
                estado=1
            ).first()
            
            if stock and stock.descontar_stock(instance.cantidad):
                print(f"✅ Stock descontado: Repuesto {instance.id_repuesto_comprado.id_repuesto_comprado} - Cantidad: {instance.cantidad}")
            else:
                print(f"❌ ERROR: Stock insuficiente para repuesto {instance.id_repuesto_comprado.id_repuesto_comprado}")


# ============================================
# SIGNAL 4: Crear Movimiento de Caja automático en Ventas
# ============================================
from software.models.VentasModel import Ventas

@receiver(post_save, sender=Ventas)
def crear_movimiento_caja_venta(sender, instance, created, **kwargs):
    """
    Cuando se completa una venta, crea automáticamente un movimiento de caja (ingreso)
    """
    if created:
        # Obtener la caja desde AperturaCierreCaja del usuario
        from software.models.AperturaCierreCajaModel import AperturaCierreCaja
        
        apertura_actual = AperturaCierreCaja.objects.filter(
            idusuario=instance.idusuario,
            estado='abierta'
        ).first()
        
        if not apertura_actual:
            print(f"❌ ERROR: No hay caja abierta para el usuario {instance.idusuario.nombrecompleto}")
            return
        
        # Crear movimiento de caja (ingreso por venta)
        movimiento = MovimientoCaja.objects.create(
            id_caja=apertura_actual.id_caja,
            idusuario=instance.idusuario,
            idventa=instance,
            tipo_movimiento='ingreso',
            monto=instance.total_venta,
            descripcion=f"Venta {instance.numero_comprobante} - Cliente: {instance.idcliente.razonsocial}",
            estado=1
        )
        
        print(f"✅ Movimiento de caja creado: Ingreso S/ {instance.total_venta} - Venta #{instance.idventa}")