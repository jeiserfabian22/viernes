from django.http import HttpResponse
from django.shortcuts import redirect, render
from software.models.ProvinciaModel import Provincia
from software.models.RegionModel import Region
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def provincias(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        provincias_registros = Provincia.objects.filter(estado=1).select_related('id_region')
        regiones_registros = Region.objects.filter(estado=1)

        data = {
            'provincias_registros': provincias_registros,
            'regiones_registros': regiones_registros,
            'permisos': permisos
        }
        
        return render(request, 'provincias/provincias.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def provinciasEliminar(request, id):
    Provincia.objects.filter(id_provincia=id).update(estado=0)
    return redirect('provincias')

def agregarProvincias(request):
    nombre = request.POST.get('nameProvinciaAgregar')
    id_region = request.POST.get('idRegionAgregar')
    
    region = Region.objects.get(id_region=id_region)
    Provincia.objects.create(nombre_provincia=nombre, id_region=region, estado=1)
    return redirect('provincias')

def editarProvincias(request):
    id = request.POST.get('idProvincia')
    nombre = request.POST.get('nameProvincia')
    id_region = request.POST.get('idRegion')

    provincia = Provincia.objects.get(id_provincia=id)
    provincia.nombre_provincia = nombre
    provincia.id_region = Region.objects.get(id_region=id_region)
    provincia.save()
    return redirect('provincias')