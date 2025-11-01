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


def numeroserie(request):
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)

        numseries = Numserie.objects.filter(estado=1)
        documentos = Tipodocumento.objects.filter(estado=1)
        usuarios = Usuario.objects.filter(estado=1)
        data = {
            'numseries': numseries,
            "permisos": permisos,
            "documentos": documentos,
            "usuarios":usuarios
        }

        return render(request, 'numserie/numserie.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


def numeroserieEliminar(request, id):

    Numserie.objects.filter(idnumserie=id).update(estado=0)
    # Devuelve los datos JSON directamente sin redirigir
    return redirect('numeroserie')


def numeroserieAgregar(request):
    nombre = request.POST.get('nombreSerie')
    idUsuario = request.POST.get('usuario')

    iddocumento = request.POST.get('iddocumento')
    documento = Tipodocumento.objects.get(idtipodocumento=iddocumento)

    usuario = Usuario.objects.get(idusuario=idUsuario)
    
    serie = Numserie()
    serie.idtipodocumento = documento
    serie.numserie = nombre
    serie.idusuario = usuario
    serie.estado = 1
    serie.save()

    return redirect('numeroserie')


def numeroserieEditar(request):
    id = request.POST.get('idnumserie2')
    nombre = request.POST.get('nombreSerie2')
    idUsuario = request.POST.get('usuario2')
    
    print(idUsuario)

    iddocumento = request.POST.get('iddocumento2')
    documento = Tipodocumento.objects.get(idtipodocumento=iddocumento)
    
    usuario = Usuario.objects.get(idusuario=idUsuario)

    serie = Numserie.objects.get(idnumserie=id)
    serie.idtipodocumento = documento
    serie.idusuario = usuario
    serie.numserie = nombre

    serie.save()

    return redirect('numeroserie')
