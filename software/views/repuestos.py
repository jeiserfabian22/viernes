from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from software.models.RepuestoModel import Repuesto
from software.models.UnidadesModel import Unidades
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.marcaModel import Marca
from software.models.colorModel import Color

def repuestos(request):
    id2 = request.session.get('idtipousuario')
    if not id2:
        return redirect('login')

    # Agrega esta lógica de permisos aquí también
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    
    repuestos = Repuesto.objects.filter(estado=1).select_related("idunidad", "idmarca", "idcolor")
    unidades = Unidades.objects.filter(estado=1)
    marcas = Marca.objects.filter(estado=1)
    colores = Color.objects.filter(estado=1)

    data = {
        'repuestos': repuestos,
        'unidades': unidades,
        'marcas': marcas,
        'colores': colores,
        'permisos': permisos,  # Aquí se añaden los permisos
    }
    return render(request, 'repuestos/repuestos.html', data)



def agregar_repuesto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        unidad = get_object_or_404(Unidades, idunidad=request.POST.get('unidad'))
        marca = get_object_or_404(Marca, idmarca=request.POST.get('marca'))
        color = get_object_or_404(Color, idcolor=request.POST.get('color'))

        Repuesto.objects.create(
            nombre=nombre,
            idunidad=unidad,
            idmarca=marca,
            idcolor=color,
            estado=1
        )
        messages.success(request, f"✅ Repuesto '{nombre}' agregado correctamente.")
    return redirect('repuestos')


def editar_repuesto(request):
    if request.method == 'POST':
        id_repuesto = request.POST.get('id_repuesto')
        repuesto = get_object_or_404(Repuesto, id_repuesto=id_repuesto)

        repuesto.nombre = request.POST.get('nombre2')
        repuesto.idunidad = get_object_or_404(Unidades, idunidad=request.POST.get('unidad2'))
        repuesto.idmarca = get_object_or_404(Marca, idmarca=request.POST.get('marca2'))
        repuesto.idcolor = get_object_or_404(Color, idcolor=request.POST.get('color2'))
        repuesto.save()

        messages.success(request, f"✏️ Repuesto '{repuesto.nombre}' actualizado.")
    return redirect('repuestos')


def eliminar_repuesto(request, id_repuesto):
    repuesto = get_object_or_404(Repuesto, id_repuesto=id_repuesto)
    repuesto.estado = 0
    repuesto.save()
    messages.success(request, f"🗑 Repuesto '{repuesto.nombre}' eliminado.")
    return redirect('repuestos')
