
from django.http import HttpResponse
from django.shortcuts import redirect, render

from software.models.categoriaModel import Categoria
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

# Create your views here.

def categorias(request):
    #Esto siempre va
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        #Hata acá va 
        cateogiras_registros = Categoria.objects.filter(estado=1)
        
        data = {
            'cateogiras_registros':cateogiras_registros,
            "permisos":permisos #Esto se envía para mostrar los permisos
        }
        
        return render(request, 'categorias/categorias.html',data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")
def eliminar(request, id):

    Categoria.objects.filter(idcategoria=id).update(estado=0)
    # Devuelve los datos JSON directamente sin redirigir
    return redirect('categorias')

def agregar(request):
    nombre = request.POST.get('nameCategoriaAgregar')
    Categoria.objects.create(nomcategoria=nombre,estado=1)
    return redirect('categorias')

def editar(request):
    id= request.POST.get('idCategoria')
    nombre= request.POST.get('nameCategoria')
    
    categoria = Categoria.objects.get(idcategoria=id)
    categoria.nomcategoria=nombre
    categoria.save()
    return redirect('categorias')
    