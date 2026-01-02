from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from software.models.almacenesModel import Almacenes
from software.models.sucursalesModel import Sucursales
from software.models.empresaModel import Empresa
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def almacenes(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        almacenes_registros = Almacenes.objects.filter(estado=1).select_related(
            'id_sucursal__idempresa'
        )
        sucursales_registros = Sucursales.objects.filter(estado=1).select_related('idempresa')
        empresas_registros = Empresa.objects.filter(activo=1)

        data = {
            'almacenes_registros': almacenes_registros,
            'sucursales_registros': sucursales_registros,
            'empresas_registros': empresas_registros,
            'permisos': permisos
        }
        
        return render(request, 'almacenes/almacenes.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def almacenesEliminar(request, id):
    Almacenes.objects.filter(id_almacen=id).update(estado=0)
    return redirect('almacenes')

def agregarAlmacenes(request):
    id_sucursal = request.POST.get('idSucursalAgregar')
    nombre_almacen = request.POST.get('nameAlmacenAgregar')
    codigo_almacen = request.POST.get('codigoAlmacenAgregar')
    descripcion = request.POST.get('descripcionAgregar')
    capacidad_maxima = request.POST.get('capacidadMaximaAgregar')
    
    sucursal = Sucursales.objects.get(id_sucursal=id_sucursal)
    
    Almacenes.objects.create(
        id_sucursal=sucursal,
        nombre_almacen=nombre_almacen,
        codigo_almacen=codigo_almacen,
        descripcion=descripcion if descripcion else None,
        capacidad_maxima=int(capacidad_maxima) if capacidad_maxima else None,
        estado=1
    )
    return redirect('almacenes')

def editarAlmacenes(request):
    id_almacen = request.POST.get('idAlmacen')
    id_sucursal = request.POST.get('idSucursal')
    nombre_almacen = request.POST.get('nameAlmacen')
    codigo_almacen = request.POST.get('codigoAlmacen')
    descripcion = request.POST.get('descripcion')
    capacidad_maxima = request.POST.get('capacidadMaxima')

    almacen = Almacenes.objects.get(id_almacen=id_almacen)
    almacen.id_sucursal = Sucursales.objects.get(id_sucursal=id_sucursal)
    almacen.nombre_almacen = nombre_almacen
    almacen.codigo_almacen = codigo_almacen
    almacen.descripcion = descripcion if descripcion else None
    almacen.capacidad_maxima = int(capacidad_maxima) if capacidad_maxima else None
    almacen.save()
    return redirect('almacenes')

# Vista AJAX para obtener sucursales por empresa
def obtenerSucursalesPorEmpresa(request):
    id_empresa = request.GET.get('id_empresa')
    sucursales = Sucursales.objects.filter(idempresa=id_empresa, estado=1).values('id_sucursal', 'nombre_sucursal')
    return JsonResponse(list(sucursales), safe=False)