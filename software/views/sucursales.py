from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from software.models.sucursalesModel import Sucursales
from software.models.empresaModel import Empresa
from software.models.DistritoModel import Distrito
from software.models.ProvinciaModel import Provincia
from software.models.RegionModel import Region
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def sucursales(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        sucursales_registros = Sucursales.objects.filter(estado=1).select_related(
            'idempresa', 
            'id_distrito__id_provincia__id_region'
        )
        empresas_registros = Empresa.objects.filter(activo=1)
        distritos_registros = Distrito.objects.filter(estado=1).select_related('id_provincia__id_region')
        provincias_registros = Provincia.objects.filter(estado=1).select_related('id_region')
        regiones_registros = Region.objects.filter(estado=1)

        data = {
            'sucursales_registros': sucursales_registros,
            'empresas_registros': empresas_registros,
            'distritos_registros': distritos_registros,
            'provincias_registros': provincias_registros,
            'regiones_registros': regiones_registros,
            'permisos': permisos
        }
        
        return render(request, 'sucursales/sucursales.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def sucursalesEliminar(request, id):
    Sucursales.objects.filter(id_sucursal=id).update(estado=0)
    return redirect('sucursales')

def agregarSucursales(request):
    idempresa = request.POST.get('idEmpresaAgregar')
    id_distrito = request.POST.get('idDistritoAgregar')
    nombre_sucursal = request.POST.get('nameSucursalAgregar')
    codigo_sucursal = request.POST.get('codigoSucursalAgregar')
    direccion = request.POST.get('direccionAgregar')
    telefono = request.POST.get('telefonoAgregar')
    fecha_apertura = request.POST.get('fechaAperturaAgregar')
    es_principal = request.POST.get('esPrincipalAgregar') == 'on'
    
    empresa = Empresa.objects.get(idempresa=idempresa)
    distrito = Distrito.objects.get(id_distrito=id_distrito)
    
    Sucursales.objects.create(
        idempresa=empresa,
        id_distrito=distrito,
        nombre_sucursal=nombre_sucursal,
        codigo_sucursal=codigo_sucursal,
        direccion=direccion,
        telefono=telefono,
        fecha_apertura=fecha_apertura,
        es_principal=es_principal,
        estado=1
    )
    return redirect('sucursales')

def editarSucursales(request):
    id_sucursal = request.POST.get('idSucursal')
    idempresa = request.POST.get('idEmpresa')
    id_distrito = request.POST.get('idDistrito')
    nombre_sucursal = request.POST.get('nameSucursal')
    codigo_sucursal = request.POST.get('codigoSucursal')
    direccion = request.POST.get('direccion')
    telefono = request.POST.get('telefono')
    fecha_apertura = request.POST.get('fechaApertura')
    es_principal = request.POST.get('esPrincipal') == 'on'

    sucursal = Sucursales.objects.get(id_sucursal=id_sucursal)
    sucursal.idempresa = Empresa.objects.get(idempresa=idempresa)
    sucursal.id_distrito = Distrito.objects.get(id_distrito=id_distrito)
    sucursal.nombre_sucursal = nombre_sucursal
    sucursal.codigo_sucursal = codigo_sucursal
    sucursal.direccion = direccion
    sucursal.telefono = telefono
    sucursal.fecha_apertura = fecha_apertura
    sucursal.es_principal = es_principal
    sucursal.save()
    return redirect('sucursales')

# Vista AJAX para obtener provincias por región
def obtenerProvinciasPorRegion(request):
    id_region = request.GET.get('id_region')
    provincias = Provincia.objects.filter(id_region=id_region, estado=1).values('id_provincia', 'nombre_provincia')
    return JsonResponse(list(provincias), safe=False)

# Vista AJAX para obtener distritos por provincia
def obtenerDistritosPorProvincia(request):
    id_provincia = request.GET.get('id_provincia')
    distritos = Distrito.objects.filter(id_provincia=id_provincia, estado=1).values('id_distrito', 'nombre_distrito')
    return JsonResponse(list(distritos), safe=False)