from datetime import datetime, date
from decimal import Decimal
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from software.models.comprasModel import Compras
from software.models.ProveedoresModel import Proveedor
from software.models.TipoclienteModel import Tipocliente
from software.models.compradetalleModel import CompraDetalle
from software.models.ProductoModel import Producto
from software.models.categoriaModel import Categoria
from software.models.compradetalleModel import CompraDetalle
from software.models.VentasModel import Ventas
from software.models.VentaDetalleModel import VentaDetalle
from software.models.UsuarioModel import Usuario
from software.models.UnidadesModel import Unidades
from software.models.TipousuarioModel import Tipousuario
from software.models.TipodocumentoModel import Tipodocumento
from software.models.TipoclienteModel import Tipocliente
from software.models.ModulosModel import Modulos
from software.models.empresaModel import Empresa
from software.models.empleadoModel import Empleado
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.detallecategoriaxunidadesModel import Detallecategoriaxunidades
from software.models.departamentosModel import Departamentos
from software.models.TipoIgvModel import TipoIgv
from software.models.ClienteModel import Cliente
from django.db.models import Sum
from django.db.models.functions import TruncMonth


def tipoUsuarios(request):
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        tipoUsuariosuarios = Tipousuario.objects.filter(estado=1)

        data = {
            "permisos": permisos,
            'tipoUsuariosuarios': tipoUsuariosuarios,
        }

        return render(request, 'tipousuarios/tipousuarios.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


# ⭐ ACTUALIZADO: Usar eid
def tipousuariosEliminar(request, eid):
    """
    Eliminar tipo de usuario (soft delete) - CON ID ENCRIPTADO
    """
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        idtipousuario = decrypt_id(eid)
        if not idtipousuario:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'URL inválida'
                }, status=400)
            return HttpResponse("<h1>URL inválida</h1>")
        
        # Obtener el tipo de usuario
        tipo_usuario = Tipousuario.objects.get(idtipousuario=idtipousuario)
        
        # Soft delete
        tipo_usuario.estado = 0
        tipo_usuario.save()
        
        print(f"🗑️ Tipo de usuario eliminado: {tipo_usuario.nombretipousuario} (ID: {idtipousuario})")
        
        # Si es AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Tipo de usuario "{tipo_usuario.nombretipousuario}" eliminado correctamente'
            })
        
        # Si no es AJAX, redirigir
        return redirect('tipoUsuarios')
        
    except Tipousuario.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Tipo de usuario no encontrado'
            }, status=404)
        
        return redirect('tipoUsuarios')
        
    except Exception as e:
        print(f"❌ Error al eliminar tipo de usuario: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        return redirect('tipoUsuarios')


def tipousuariosAgregar(request):
    nombre = request.POST.get('nombreTipo')
    Tipousuario.objects.create(nombretipousuario=nombre, estado=1)
    return redirect('tipoUsuarios')


def tipousuariosEditar(request):
    id = request.POST.get('idtipousuario')
    nombre = request.POST.get('nombreTipo')
    
    tipoUser = Tipousuario.objects.get(idtipousuario=id)
    tipoUser.nombretipousuario = nombre
    tipoUser.save()
    return redirect('tipoUsuarios')