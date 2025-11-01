from django.http import HttpResponse
from django.shortcuts import redirect, render
from software.models.marcaModel import Marca
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def marcas(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        marcas_registros = Marca.objects.filter(estado=1)

        data = {
            'marcas_registros': marcas_registros,
            'permisos': permisos
        }
        
        return render(request, 'marcas/marcas.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def eliminar(request, id):
    Marca.objects.filter(idmarca=id).update(estado=0)
    return redirect('marcas')

def agregar(request):
    nombre = request.POST.get('nameMarcaAgregar')
    Marca.objects.create(nombremarca=nombre, estado=1)
    return redirect('marcas')

def editar(request):
    id = request.POST.get('idMarca')
    nombre = request.POST.get('nameMarca')

    marca = Marca.objects.get(idmarca=id)
    marca.nombremarca = nombre
    marca.save()
    return redirect('marcas')
