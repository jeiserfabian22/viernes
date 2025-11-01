from django.shortcuts import render, redirect
from django.http import HttpResponse
from software.models.compradetalleModel import CompraDetalle
from software.models.VehiculosModel import Vehiculo
from software.models.ProductoModel import Producto
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.RepuestoModel import Repuesto
from software.models.RespuestoCompModel import RepuestoComp


def stock(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    
    if not id2:
        return HttpResponse("<h1>No tiene acceso señor</h1>")
    
    # Validación de permisos
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    
    # Stock de Vehículos agrupado por nombre de producto
    vehiculos_stock = []
    productos = Producto.objects.filter(estado=1)
    
    for producto in productos:
        vehiculos = Vehiculo.objects.filter(
            idproducto=producto,
            estado=1
        ).select_related('idestadoproducto')
        
        if vehiculos.exists():
            detalles = []
            cantidad_total = 0
            
            for vehiculo in vehiculos:
                # Obtener detalles de compras para este vehículo
                detalle_compra = CompraDetalle.objects.filter(
                    id_vehiculo=vehiculo
                ).first()
                
                if detalle_compra:
                    detalles.append({
                        'serie_motor': vehiculo.serie_motor,
                        'serie_chasis': vehiculo.serie_chasis,
                        'estado': vehiculo.idestadoproducto.nombreestadoproducto if vehiculo.idestadoproducto else 'Sin estado',
                        'imperfecciones': vehiculo.imperfecciones if vehiculo.imperfecciones else 'Ninguna',
                        'precio_compra': detalle_compra.precio_compra,
                        'precio_venta': detalle_compra.precio_venta,
                        'cantidad': detalle_compra.cantidad
                    })
                    cantidad_total += detalle_compra.cantidad
            
            if detalles:
                vehiculos_stock.append({
                    'nombre': producto.nomproducto,
                    'detalles': detalles,
                    'cantidad_total': cantidad_total
                })
    
    # Stock de Repuestos agrupado por nombre de repuesto
    repuestos_stock = []
    catalogo_repuestos = Repuesto.objects.filter(estado=1)
    
    for repuesto_catalogo in catalogo_repuestos:
        repuestos_comprados = RepuestoComp.objects.filter(
            id_repuesto=repuesto_catalogo,
            estado=1
        )
        
        if repuestos_comprados.exists():
            detalles = []
            cantidad_total = 0
            
            for repuesto_comp in repuestos_comprados:
                # Obtener detalles de compras para este repuesto
                detalle_compra = CompraDetalle.objects.filter(
                    id_repuesto_comprado=repuesto_comp
                ).first()
                
                if detalle_compra:
                    detalles.append({
                        'codigo_barras': repuesto_comp.codigo_barras if repuesto_comp.codigo_barras else 'N/A',
                        'descripcion': repuesto_comp.descripcion if repuesto_comp.descripcion else 'Sin descripción',
                        'precio_compra': detalle_compra.precio_compra,
                        'precio_venta': detalle_compra.precio_venta,
                        'cantidad': detalle_compra.cantidad
                    })
                    cantidad_total += detalle_compra.cantidad
            
            if detalles:
                repuestos_stock.append({
                    'nombre': repuesto_catalogo.nombre,
                    'detalles': detalles,
                    'cantidad_total': cantidad_total
                })
    
    # Contexto para el template
    data = {
        'vehiculos_stock': vehiculos_stock,
        'repuestos_stock': repuestos_stock,
        'permisos': permisos
    }
    
    return render(request, 'stock/stock.html', data)