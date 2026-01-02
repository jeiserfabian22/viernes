from django.http import HttpResponse
from django.shortcuts import redirect, render
from software.models.RegionModel import Region
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def regiones(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        regiones_registros = Region.objects.filter(estado=1)

        data = {
            'regiones_registros': regiones_registros,
            'permisos': permisos
        }
        
        return render(request, 'regiones/regiones.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def regionesEliminar(request, id):
    Region.objects.filter(id_region=id).update(estado=0)
    return redirect('regiones')

def agregarRegiones(request):
    nombre = request.POST.get('nameRegionAgregar')
    Region.objects.create(nombre_region=nombre, estado=1)
    return redirect('regiones')

def editarRegiones(request):
    id = request.POST.get('idRegion')
    nombre = request.POST.get('nameRegion')

    region = Region.objects.get(id_region=id)
    region.nombre_region = nombre
    region.save()
    return redirect('regiones')