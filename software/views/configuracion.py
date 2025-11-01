from django.shortcuts import redirect, render
from software.models.empresaModel import Empresa
from software.models.departamentosModel import Departamentos
from software.models.ProvinciaModel import Provincia
from software.models.DistritoModel import Distrito
from django.http import HttpResponse, JsonResponse
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
import templates


def configuracion(request):

    id2 = request.session.get('idtipousuario')
    if id2:

        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        empresa = Empresa.objects.all()
        departamentos = Departamentos.objects.all()
        modo = empresa[0].mododev
        data = {
            'empresas': empresa,
            'departamentos': departamentos,
            'modo': modo,
            'permisos': permisos
        }

        return render(request, 'configuracion/configuracion.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


def buscarProvincias(request):
    id = request.GET.get('selected_value')
    provincias = Provincia.objects.filter(iddepartamento=id)

    provincias_list = list(provincias.values())
    return JsonResponse(provincias_list, safe=False)


def buscarDistritos(request):
    id = request.GET.get('selected_value')
    distritos = Distrito.objects.filter(idprovincia=id)

    distritos_list = list(distritos.values())
    return JsonResponse(distritos_list, safe=False)


def ubigueo(request):
    id = request.GET.get('selected_value')
    distritos = Distrito.objects.filter(iddistrito=id)

    distritos_list = list(distritos.values())
    return JsonResponse(distritos_list, safe=False)


def editarEmpresa(request):
    ruc = request.POST.get('ruc')
    razonSocial = request.POST.get('razonSocial')
    nombreComercia = request.POST.get('nombreComercia')
    Direccion = request.POST.get('Direccion')
    telefono = request.POST.get('telefono')
    user = request.POST.get('user')
    password = request.POST.get('password')
    ubigueo = request.POST.get('ubigueo')
    idempresaPost = request.POST.get('idempresa')

    empresa = Empresa.objects.get(idempresa=idempresaPost)
    empresa.ruc = ruc
    empresa.razonsocial = razonSocial
    empresa.nombrecomercial = nombreComercia
    empresa.direccion = Direccion
    empresa.telefono = telefono
    empresa.passwordsec = password
    empresa.ubigueo = ubigueo
    empresa.save()

    return redirect('configuracion')


def produccion(request, id):
    empresa = Empresa.objects.get(idempresa=id)
    empresa.mododev = 1
    empresa.save()
    return redirect('configuracion')


def desarrollo(request, id):
    empresa = Empresa.objects.get(idempresa=id)
    empresa.mododev = 0
    empresa.save()
    return redirect('configuracion')
