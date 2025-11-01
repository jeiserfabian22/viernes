from datetime import datetime, date
from decimal import Decimal
from django.db import connection
from software.views.apiBusquedaRUcDni import ApisNetPe
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import templates
from software.models.comprasModel import Compras
from software.models.ProveedoresModel import Proveedores
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
from software.models.ProveedoresModel import Proveedores
from software.models.NumserieModel import Numserie
from software.models.ModulosModel import Modulos
from software.models.empresaModel import Empresa
from software.models.empleadoModel import Empleado
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.detallecategoriaxunidadesModel import Detallecategoriaxunidades
from software.models.departamentosModel import Departamentos
from software.models.codigocorreoModel import CodigoCorreo
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

def tipousuariosEliminar(request, id):

    Tipousuario.objects.filter(idtipousuario=id).update(estado=0)
    # Devuelve los datos JSON directamente sin redirigir
    return redirect('tipoUsuarios')


def tipousuariosAgregar(request):
    nombre = request.POST.get('nombreTipo')
    Tipousuario.objects.create(nombretipousuario=nombre,estado=1)
    return redirect('tipoUsuarios')


def tipousuariosEditar(request):
    id= request.POST.get('idtipousuario')
    nombre= request.POST.get('nombreTipo')
    
    tipoUser = Tipousuario.objects.get(idtipousuario=id)
    tipoUser.nombretipousuario=nombre
    tipoUser.save()
    return redirect('tipoUsuarios')
    