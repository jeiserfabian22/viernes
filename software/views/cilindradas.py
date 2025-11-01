from django.http import HttpResponse
from django.shortcuts import redirect, render
from software.models.cilindradaModel import Cilindrada
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

def cilindradas(request):
    # Obtención del id del tipo de usuario desde la sesión
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        cilindradas_registros = Cilindrada.objects.filter(estado=1)

        data = {
            'cilindradas_registros': cilindradas_registros,
            'permisos': permisos
        }
        
        return render(request, 'cilindradas/cilindradas.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def eliminar(request, id):
    Cilindrada.objects.filter(idcilindrada=id).update(estado=0)
    return redirect('cilindradas')

def agregar(request):
    nombre = request.POST.get('nameCilindradaAgregar')
    Cilindrada.objects.create(cilindrada_cc=nombre, estado=1)
    return redirect('cilindradas')

def editar(request):
    id = request.POST.get('idCilindrada')
    nombre = request.POST.get('nameCilindrada')

    cilindrada = Cilindrada.objects.get(idcilindrada=id)
    cilindrada.cilindrada_cc = nombre
    cilindrada.save()
    return redirect('cilindradas')
