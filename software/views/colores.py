
from django.http import HttpResponse
from django.shortcuts import redirect, render
from software.models.colorModel import Color
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def colores(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        colores_registros = Color.objects.filter(estado=1)

        data = {
            'colores_registros': colores_registros,
            'permisos': permisos
        }
        
        return render(request, 'colores/colores.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def eliminar(request, id):
    Color.objects.filter(idcolor=id).update(estado=0)
    return redirect('colores')

def agregar(request):
    nombre = request.POST.get('nameColorAgregar')
    Color.objects.create(nombrecolor=nombre, estado=1)
    return redirect('colores')

def editar(request):
    id = request.POST.get('idColor')
    nombre = request.POST.get('nameColor')

    color = Color.objects.get(idcolor=id)
    color.nombrecolor = nombre
    color.save()
    return redirect('colores')
