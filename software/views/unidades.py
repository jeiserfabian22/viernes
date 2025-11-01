
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from software.models.UnidadesModel import Unidades
from django.core.paginator import Paginator
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

# Create your views here.


def unidades(request):

    id2 = request.session.get('idtipousuario')
    if id2:

        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        unidades = Unidades.objects.all()
        
        data = {
            'unidades': unidades,
            'permisos': permisos
        }
        return render(request, 'unidades/unidades.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


def activo(request, id):
    # Obtiene la unidad o retorna un 404 si no se encuentra
    unidad = get_object_or_404(Unidades, idunidad=id)
    unidad.estado = 1  # Cambiar a activo
    unidad.save()
    return JsonResponse({'status': 'success', 'new_state': 'activo'})


def desactivo(request, id):
    # Obtiene la unidad o retorna un 404 si no se encuentra
    unidad = get_object_or_404(Unidades, idunidad=id)
    unidad.estado = 0  # Cambiar a desactivado
    unidad.save()
    return JsonResponse({'status': 'success', 'new_state': 'desactivado'})
