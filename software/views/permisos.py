from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import HttpResponse
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.models.ModulosModel import Modulos
from software.models.TipousuarioModel import Tipousuario

def permisos(request):
    id2 = request.session.get('idtipousuario')
    if id2:
        # Obtener permisos del usuario
        permisos = Detalletipousuarioxmodulos.objects.filter(
            idtipousuario=id2
        ).select_related('idmodulo', 'idmodulo__idmodulo_padre')
        
        # Organizar módulos en estructura jerárquica
        modulos_organizados = {}
        
        for permiso in permisos:
            modulo = permiso.idmodulo
            
            # Si el módulo tiene padre
            if modulo.idmodulo_padre:
                padre = modulo.idmodulo_padre
                padre_nombre = padre.nombremodulo
                
                # Crear entrada del padre si no existe
                if padre_nombre not in modulos_organizados:
                    modulos_organizados[padre_nombre] = {
                        'padre': padre,
                        'hijos': []
                    }
                # Agregar el hijo
                modulos_organizados[padre_nombre]['hijos'].append(modulo)
            else:
                # Es módulo padre o independiente
                if modulo.nombremodulo not in modulos_organizados:
                    modulos_organizados[modulo.nombremodulo] = {
                        'padre': modulo,
                        'hijos': []
                    }
        
        # Ordenar hijos por orden
        for nombre, grupo in modulos_organizados.items():
            grupo['hijos'].sort(key=lambda x: x.orden)
        
        # Datos para gestión de permisos
        permisos2 = Detalletipousuarioxmodulos.objects.all()
        modulos = Modulos.objects.filter(estado=1)
        tipoUsuarios = Tipousuario.objects.filter(estado=1)
        
        permisos_por_tipo_usuario = defaultdict(list)
        for permiso in permisos2:
            permisos_por_tipo_usuario[permiso.idtipousuario.nombretipousuario].append(permiso)
            
        data = {
            'permisos_por_tipo_usuario': permisos_por_tipo_usuario.items(),
            'permisos': permisos,
            'modulos_organizados': modulos_organizados,
            'modulos': modulos,
            'tipoUsuarios': tipoUsuarios
        }
        
        return render(request, 'permisos/permisos.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")

def agregaPermiso(request):
    idTipoUsuario2 = request.POST.get('tipoUsuario')
    permisos = request.POST.getlist("permisosTu[idmodulo][]")
    
    getTipoUsuarios = Tipousuario.objects.get(idtipousuario=idTipoUsuario2)
    
    for idPErmiso in permisos:
        
        modulo = Modulos.objects.get(idmodulo=idPErmiso)
        
        newPermiso = Detalletipousuarioxmodulos()
        newPermiso.idtipousuario = getTipoUsuarios
        newPermiso.idmodulo=modulo
        newPermiso.save()
    
    return redirect('permisos')

def eliminarPermiso(request,id):
    Detalletipousuarioxmodulos.objects.filter(idtipousuario=id).delete()
    return redirect('permisos')