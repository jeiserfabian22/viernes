from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from software.models.UnidadesModel import Unidades
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def unidades(request):
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        unidades = Unidades.objects.all()
        
        data = {
            'unidades': unidades,
            'permisos': permisos
        }
        return render(request, 'unidades/unidades.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


# ⭐ ACTUALIZADO: Usar eid
def activo(request, eid):
    """
    Activar unidad - CON ID ENCRIPTADO
    """
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        idunidad = decrypt_id(eid)
        if not idunidad:
            return JsonResponse({
                'status': 'error',
                'message': 'URL inválida'
            }, status=400)
        
        # Obtener y activar la unidad
        unidad = get_object_or_404(Unidades, idunidad=idunidad)
        unidad.estado = 1
        unidad.save()
        
        print(f"✅ Unidad activada: {unidad.abrunidad} (ID: {idunidad})")
        
        return JsonResponse({
            'status': 'success',
            'new_state': 'activo',
            'message': f'Unidad {unidad.abrunidad} activada correctamente'
        })
        
    except Unidades.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Unidad no encontrada'
        }, status=404)
    except Exception as e:
        print(f"❌ Error al activar unidad: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error al activar unidad: {str(e)}'
        }, status=500)


# ⭐ ACTUALIZADO: Usar eid
def desactivo(request, eid):
    """
    Desactivar unidad - CON ID ENCRIPTADO
    """
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        idunidad = decrypt_id(eid)
        if not idunidad:
            return JsonResponse({
                'status': 'error',
                'message': 'URL inválida'
            }, status=400)
        
        # Obtener y desactivar la unidad
        unidad = get_object_or_404(Unidades, idunidad=idunidad)
        unidad.estado = 0
        unidad.save()
        
        print(f"⚠️ Unidad desactivada: {unidad.abrunidad} (ID: {idunidad})")
        
        return JsonResponse({
            'status': 'success',
            'new_state': 'desactivado',
            'message': f'Unidad {unidad.abrunidad} desactivada correctamente'
        })
        
    except Unidades.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Unidad no encontrada'
        }, status=404)
    except Exception as e:
        print(f"❌ Error al desactivar unidad: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error al desactivar unidad: {str(e)}'
        }, status=500)