from django.shortcuts import render, redirect
from django.http import HttpResponse
from software.models.compradetalleModel import CompraDetalle
from software.models.VehiculosModel import Vehiculo
from software.models.ProductoModel import Producto
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.RepuestoModel import Repuesto
from software.models.RespuestoCompModel import RepuestoComp
from software.models.stockModel import Stock
from software.models.sucursalesModel import Sucursales


def stock(request):
    id2 = request.session.get('idtipousuario')
    
    if not id2:
        return HttpResponse("<h1>No tiene acceso señor</h1>")
    
    es_admin = (id2 == 1)
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    id_sucursal_activa = request.session.get('id_sucursal')
    
    print(f"🔍 STOCK DEBUG:")
    print(f"   id_sucursal en sesión: {id_sucursal_activa}")
    
    if not id_sucursal_activa:
        return HttpResponse("<h1>No hay sucursal seleccionada</h1>")
    
    try:
        sucursal_usuario = Sucursales.objects.get(id_sucursal=id_sucursal_activa)
        print(f"   Nombre de sucursal: {sucursal_usuario.nombre_sucursal}")
    except Sucursales.DoesNotExist:
        return HttpResponse("<h1>Sucursal no encontrada</h1>")
    
    # ==================== VEHÍCULOS ====================
    vehiculos_stock = []
    productos = Producto.objects.filter(estado=1)
    
    for producto in productos:
        stocks_vehiculos = Stock.objects.filter(
            id_vehiculo__idproducto=producto,
            id_vehiculo__estado=1,
            id_vehiculo__isnull=False,  # ✅ ASEGURAR QUE TENGA VEHÍCULO
            id_almacen__id_sucursal=sucursal_usuario,
            estado=1,
            cantidad_disponible__gt=0
        ).select_related(
            'id_vehiculo__idestadoproducto',
            'id_vehiculo__idproducto',
            'id_almacen',
            'idcompradetalle'  # ✅ USAR EL NOMBRE CORRECTO DEL CAMPO
        )
        
        if stocks_vehiculos.exists():
            print(f"   📦 Producto: {producto.nomproducto} - Stock encontrado: {stocks_vehiculos.count()}")
            detalles = []
            cantidad_total = 0
            
            for stock in stocks_vehiculos:
                vehiculo = stock.id_vehiculo
                
                # ✅ VALIDAR QUE VEHICULO NO SEA NONE
                if not vehiculo:
                    print(f"   ⚠️ Stock #{stock.id_stock} sin vehículo, saltando...")
                    continue
                
                # ✅ USAR LA RELACIÓN DIRECTA PRIMERO
                detalle_compra = stock.idcompradetalle  # ✅ NOMBRE CORRECTO
                
                # ⚠️ FALLBACK: Si el stock no tiene idcompradetalle (stocks antiguos)
                if not detalle_compra:
                    detalle_compra = CompraDetalle.objects.filter(
                        id_vehiculo=vehiculo
                    ).order_by('-idcompradetalle').first()
                    print(f"   ⚠️ Vehículo sin idcompradetalle, usando fallback")
                
                if detalle_compra:
                    detalles.append({
                        'serie_motor': vehiculo.serie_motor,
                        'serie_chasis': vehiculo.serie_chasis,
                        'estado': vehiculo.idestadoproducto.nombreestadoproducto if vehiculo.idestadoproducto else 'Sin estado',
                        'imperfecciones': vehiculo.imperfecciones if vehiculo.imperfecciones else 'Ninguna',
                        'precio_compra': detalle_compra.precio_compra,
                        'precio_venta': detalle_compra.precio_venta,
                        'cantidad': stock.cantidad_disponible,
                        'almacen': stock.id_almacen.nombre_almacen
                    })
                    cantidad_total += stock.cantidad_disponible
            
            if detalles:
                vehiculos_stock.append({
                    'nombre': producto.nomproducto,
                    'detalles': detalles,
                    'cantidad_total': cantidad_total
                })
    
    # ==================== REPUESTOS ====================
    repuestos_stock = []
    catalogo_repuestos = Repuesto.objects.filter(estado=1)
    
    for repuesto_catalogo in catalogo_repuestos:
        stocks_repuestos = Stock.objects.filter(
            id_repuesto_comprado__id_repuesto=repuesto_catalogo,
            id_repuesto_comprado__estado=1,
            id_repuesto_comprado__isnull=False,  # ✅ ASEGURAR QUE TENGA REPUESTO
            id_almacen__id_sucursal=sucursal_usuario,
            estado=1,
            cantidad_disponible__gt=0
        ).select_related(
            'id_repuesto_comprado__id_repuesto',
            'id_almacen',
            'idcompradetalle'  # ✅ USAR EL NOMBRE CORRECTO DEL CAMPO
        )
        
        if stocks_repuestos.exists():
            detalles = []
            cantidad_total = 0
            
            for stock in stocks_repuestos:
                repuesto_comp = stock.id_repuesto_comprado
                
                # ✅ VALIDAR QUE REPUESTO_COMP NO SEA NONE
                if not repuesto_comp:
                    print(f"   ⚠️ Stock #{stock.id_stock} sin repuesto_comprado, saltando...")
                    continue
                
                # ✅ USAR LA RELACIÓN DIRECTA PRIMERO
                detalle_compra = stock.idcompradetalle  # ✅ NOMBRE CORRECTO
                
                # ⚠️ FALLBACK: Si el stock no tiene idcompradetalle (stocks antiguos)
                if not detalle_compra:
                    detalle_compra = CompraDetalle.objects.filter(
                        id_repuesto_comprado=repuesto_comp
                    ).order_by('-idcompradetalle').first()
                    print(f"   ⚠️ Repuesto sin idcompradetalle, usando fallback")
                
                if detalle_compra:
                    detalles.append({
                        'codigo_barras': repuesto_comp.codigo_barras if repuesto_comp.codigo_barras else 'N/A',
                        'descripcion': repuesto_comp.descripcion if repuesto_comp.descripcion else 'Sin descripción',
                        'precio_compra': detalle_compra.precio_compra,
                        'precio_venta': detalle_compra.precio_venta,
                        'cantidad': stock.cantidad_disponible,
                        'almacen': stock.id_almacen.nombre_almacen
                    })
                    cantidad_total += stock.cantidad_disponible
            
            if detalles:
                repuestos_stock.append({
                    'nombre': repuesto_catalogo.nombre,
                    'detalles': detalles,
                    'cantidad_total': cantidad_total
                })
    
    print(f"   Total vehículos en stock: {len(vehiculos_stock)}")
    print(f"   Total repuestos en stock: {len(repuestos_stock)}")
    
    data = {
        'vehiculos_stock': vehiculos_stock,
        'repuestos_stock': repuestos_stock,
        'permisos': permisos,
        'sucursal': sucursal_usuario,
        'es_admin': es_admin,
    }
    
    print("=" * 60)
    print("🔍 CONTEXTO ENVIADO A TEMPLATE:")
    print(f"   sucursal en data: {data.get('sucursal')}")
    print(f"   sucursal en request: {request.session.get('id_sucursal')}")
    print("=" * 60)
    
    return render(request, 'stock/stock.html', data)