from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from software.models.DistritoModel import Distrito
from software.models.ProvinciaModel import Provincia
from software.models.RegionModel import Region
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def distritos(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        distritos_registros = Distrito.objects.filter(estado=1).select_related('id_provincia__id_region')
        provincias_registros = Provincia.objects.filter(estado=1).select_related('id_region')
        regiones_registros = Region.objects.filter(estado=1)

        data = {
            'distritos_registros': distritos_registros,
            'provincias_registros': provincias_registros,
            'regiones_registros': regiones_registros,
            'permisos': permisos
        }
        
        return render(request, 'distritos/distritos.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def distritosEliminar(request, id):
    Distrito.objects.filter(id_distrito=id).update(estado=0)
    return redirect('distritos')

def agregarDistritos(request):
    nombre = request.POST.get('nameDistritoAgregar')
    id_provincia = request.POST.get('idProvinciaAgregar')
    
    provincia = Provincia.objects.get(id_provincia=id_provincia)
    Distrito.objects.create(nombre_distrito=nombre, id_provincia=provincia, estado=1)
    return redirect('distritos')

def editarDistritos(request):
    id = request.POST.get('idDistrito')
    nombre = request.POST.get('nameDistrito')
    id_provincia = request.POST.get('idProvincia')

    distrito = Distrito.objects.get(id_distrito=id)
    distrito.nombre_distrito = nombre
    distrito.id_provincia = Provincia.objects.get(id_provincia=id_provincia)
    distrito.save()
    return redirect('distritos')

# Vista AJAX para obtener provincias por región
def obtenerProvinciasPorRegion(request):
    id_region = request.GET.get('id_region')
    provincias = Provincia.objects.filter(id_region=id_region, estado=1).values('id_provincia', 'nombre_provincia')
    return JsonResponse(list(provincias), safe=False)