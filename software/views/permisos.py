from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
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
        newPermiso.idmodulo = modulo
        newPermiso.save()
    
    return redirect('permisos')


def editarPermiso(request):
    """
    Edita los permisos de un tipo de usuario específico
    Elimina los permisos existentes y crea los nuevos seleccionados
    """
    if request.method == 'POST':
        idTipoUsuario = request.POST.get('idTipoUsuario')
        permisos = request.POST.getlist("permisosEdit[idmodulo][]")
        
        try:
            # Obtener el tipo de usuario
            getTipoUsuarios = Tipousuario.objects.get(idtipousuario=idTipoUsuario)
            
            # Eliminar los permisos existentes de este tipo de usuario
            Detalletipousuarioxmodulos.objects.filter(idtipousuario=idTipoUsuario).delete()
            
            # Crear los nuevos permisos seleccionados
            for idPermiso in permisos:
                modulo = Modulos.objects.get(idmodulo=idPermiso)
                
                newPermiso = Detalletipousuarioxmodulos()
                newPermiso.idtipousuario = getTipoUsuarios
                newPermiso.idmodulo = modulo
                newPermiso.save()
            
            return redirect('permisos')
            
        except Exception as e:
            return HttpResponse(f"<h1>Error al editar permisos: {str(e)}</h1>")
    
    return redirect('permisos')


# ⭐ ACTUALIZADO: Usar eid
def eliminarPermiso(request, eid):
    """
    Eliminar todos los permisos de un tipo de usuario - CON ID ENCRIPTADO
    """
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        id_tipo_usuario = decrypt_id(eid)
        if not id_tipo_usuario:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'URL inválida'
                }, status=400)
            return HttpResponse("<h1>URL inválida</h1>")
        
        # Eliminar permisos
        permisos_eliminados = Detalletipousuarioxmodulos.objects.filter(
            idtipousuario=id_tipo_usuario
        ).delete()
        
        print(f"✅ Permisos eliminados: {permisos_eliminados[0]} registros del tipo de usuario ID: {id_tipo_usuario}")
        
        # Si es AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Permisos eliminados correctamente'
            })
        
        # Si no es AJAX, redirigir
        return redirect('permisos')
        
    except Exception as e:
        print(f"❌ Error al eliminar permisos: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        return HttpResponse(f"<h1>Error al eliminar permisos: {str(e)}</h1>")