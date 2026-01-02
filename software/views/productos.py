from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from software.models.ProductoModel import Producto
from software.models.categoriaModel import Categoria
from software.models.UnidadesModel import Unidades
from software.models.marcaModel import Marca
from software.models.cilindradaModel import Cilindrada
from software.models.colorModel import Color
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def productos(request):
    id2 = request.session.get('idtipousuario')
    if not id2:
        return redirect('login')
    
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    productos = Producto.objects.filter(estado=1)
    categoria = Categoria.objects.filter(estado=1)
    unidades = Unidades.objects.filter(estado=1)
    marca = Marca.objects.filter(estado=1)
    cilindrada = Cilindrada.objects.filter(estado=1)
    color = Color.objects.filter(estado=1)
    
    data = {
        'productos': productos,
        'categorias': categoria,
        'unidades': unidades,
        'marcas': marca,
        'cilindrada': cilindrada,
        'color': color,
        'permisos': permisos
    }
    return render(request, 'productos/productos.html', data)


def agregar(request):
    if request.method != 'POST':
        return redirect('productos')

    nombreProducto = request.POST.get('nombreProducto')
    categoria_id   = request.POST.get('categoria')
    unidad_id      = request.POST.get('unidad')
    marca_id       = request.POST.get('marca')
    cilindrada_id  = request.POST.get('cilindrada')
    color_id       = request.POST.get('color')
    imagenprod     = request.POST.get('imagenprod', '')

    categoria  = get_object_or_404(Categoria, idcategoria=categoria_id)
    unidad     = get_object_or_404(Unidades, idunidad=unidad_id)
    marca      = get_object_or_404(Marca, idmarca=marca_id)
    cilindrada = get_object_or_404(Cilindrada, idcilindrada=cilindrada_id)
    color      = get_object_or_404(Color, idcolor=color_id)

    Producto.objects.create(
        idcategoria=categoria,
        idunidad=unidad,
        idmarca=marca,
        idcilindrada=cilindrada,
        idcolor=color,
        nomproducto=nombreProducto,
        imagenprod=imagenprod,
        estado=1
    )
    messages.success(request, f"✅ Producto '{nombreProducto}' guardado correctamente.")
    return redirect('productos')


def editado(request):
    if request.method != 'POST':
        return redirect('productos')

    idproducto    = request.POST.get('idproducto2')
    categoria_id  = request.POST.get('categoria2')
    unidad_id     = request.POST.get('unidad2')
    marca_id      = request.POST.get('marca2')
    cilindrada_id = request.POST.get('cilindrada2')
    color_id      = request.POST.get('color2')
    nombre        = request.POST.get('nombreProducto2')
    imagenprod    = request.POST.get('imagenprod2', '')

    categoria  = get_object_or_404(Categoria, idcategoria=categoria_id)
    unidad     = get_object_or_404(Unidades, idunidad=unidad_id)
    marca      = get_object_or_404(Marca, idmarca=marca_id)
    cilindrada = get_object_or_404(Cilindrada, idcilindrada=cilindrada_id)
    color      = get_object_or_404(Color, idcolor=color_id)

    Producto.objects.filter(idproducto=idproducto).update(
        idcategoria=categoria,
        idunidad=unidad,
        idmarca=marca,
        idcilindrada=cilindrada,
        idcolor=color,
        nomproducto=nombre,
        imagenprod=imagenprod,
        estado=1
    )
    messages.success(request, f"✏️ Producto '{nombre}' actualizado correctamente.")
    return redirect('productos')


# ⭐ ACTUALIZADO: Usar eid
def eliminar(request, eid):
    """
    Eliminar producto (soft delete) - CON ID ENCRIPTADO
    """
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        idproducto = decrypt_id(eid)
        if not idproducto:
            return JsonResponse({
                'success': False,
                'error': 'URL inválida'
            }, status=400)
        
        producto = get_object_or_404(Producto, idproducto=idproducto)
        producto.estado = 0
        producto.save()
        
        # Si es AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Producto '{producto.nomproducto}' eliminado correctamente"
            })
        
        # Si no es AJAX, redirigir
        messages.success(request, f"🗑️ Producto '{producto.nomproducto}' eliminado correctamente.")
        return redirect('productos')
        
    except Producto.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Producto no encontrado'
            }, status=404)
        
        messages.error(request, "❌ Producto no encontrado.")
        return redirect('productos')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        messages.error(request, f"❌ Error al eliminar: {str(e)}")
        return redirect('productos')