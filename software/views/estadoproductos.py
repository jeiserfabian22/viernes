
from django.http import HttpResponse
from django.shortcuts import redirect, render
from software.models.estadoproductoModel import EstadoProducto
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def estadoproductos(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        estadoproductos_registros = EstadoProducto.objects.filter(estado=1)

        data = {
            'estadoproductos_registros': estadoproductos_registros,
            'permisos': permisos
        }
        
        return render(request, 'estadoproductos/estadoproductos.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def eliminar(request, id):
    EstadoProducto.objects.filter(idestadoproducto=id).update(estado=0)
    return redirect('estadoproductos')

def agregar(request):
    nombre = request.POST.get('nameEstadoProductoAgregar')
    EstadoProducto.objects.create(nombreestadoproducto=nombre, estado=1)
    return redirect('estadoproductos')

def editar(request):
    id = request.POST.get('idEstadoProducto')
    nombre = request.POST.get('nameEstadoProducto')

    estadoproducto = EstadoProducto.objects.get(idestadoproducto=id)
    estadoproducto.nombreestadoproducto = nombre
    estadoproducto.save()
    return redirect('estadoproductos')
