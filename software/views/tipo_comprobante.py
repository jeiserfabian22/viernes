from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from software.models.TipocomprobanteModel import Tipocomprobante
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def tipo_comprobante(request):
    """Vista principal que lista todos los tipos de comprobante activos"""
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        tipos_comprobante = Tipocomprobante.objects.filter(estado=1).order_by('codigo')

        data = {
            'tipos_comprobante': tipos_comprobante,
            'permisos': permisos
        }
        
        return render(request, 'tipo_comprobante/tipo_comprobante.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso</h1>")


def eliminar_tipo_comprobante(request, id):
    """Eliminación lógica del tipo de comprobante (cambia estado a 0)"""
    try:
        tipo_comprobante = Tipocomprobante.objects.get(idtipocomprobante=id)
        tipo_comprobante.estado = 0
        tipo_comprobante.save()
        return redirect('tipo_comprobante')
    except Tipocomprobante.DoesNotExist:
        return HttpResponse("El tipo de comprobante no existe", status=404)
    except Exception as e:
        return HttpResponse(f"Error al eliminar: {str(e)}", status=500)


def agregar_tipo_comprobante(request):
    """Agregar un nuevo tipo de comprobante con validaciones - Compatible con AJAX"""
    try:
        codigo = request.POST.get('codigoTipoComprobante', '').strip().upper()
        nombre = request.POST.get('nombreTipoComprobante', '').strip()
        abreviatura = request.POST.get('abreviaturaTipoComprobante', '').strip().upper()

        # ========== VALIDACIONES ==========
        
        # 1. Validar código
        if not codigo:
            error_msg = "El código es obligatorio"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(codigo) < 2:
            error_msg = "El código debe tener al menos 2 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(codigo) > 10:
            error_msg = "El código no puede exceder 10 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # Validar formato de código (solo números, letras mayúsculas y guiones)
        import re
        if not re.match(r'^[0-9A-Z\-]+$', codigo):
            error_msg = "El código solo puede contener números, letras mayúsculas y guiones"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 2. Validar que el código no esté duplicado
        if Tipocomprobante.objects.filter(codigo=codigo, estado=1).exists():
            error_msg = f"Ya existe un tipo de comprobante con el código {codigo}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 3. Validar nombre
        if not nombre:
            error_msg = "El nombre es obligatorio"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(nombre) < 3:
            error_msg = "El nombre debe tener al menos 3 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(nombre) > 255:
            error_msg = "El nombre no puede exceder 255 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 4. Validar abreviatura
        if not abreviatura:
            error_msg = "La abreviatura es obligatoria"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(abreviatura) < 2:
            error_msg = "La abreviatura debe tener al menos 2 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(abreviatura) > 50:
            error_msg = "La abreviatura no puede exceder 50 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # ========== CREAR TIPO DE COMPROBANTE ==========
        tipo_comprobante = Tipocomprobante.objects.create(
            codigo=codigo,
            nombre=nombre,
            abreviatura=abreviatura,
            estado=1
        )
        
        # ✅ DETECTAR SI ES AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'idtipocomprobante': tipo_comprobante.idtipocomprobante,
                'codigo': tipo_comprobante.codigo,
                'nombre': tipo_comprobante.nombre,
                'abreviatura': tipo_comprobante.abreviatura
            })
        
        # Si NO es AJAX, redireccionar normalmente
        return redirect('tipo_comprobante')
        
    except ValidationError as e:
        error_msg = str(e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': error_msg}, status=400)
        return HttpResponse(error_msg, status=400)
    except Exception as e:
        error_msg = f"Error al guardar el tipo de comprobante: {str(e)}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': error_msg}, status=500)
        return HttpResponse(error_msg, status=500)


def editar_tipo_comprobante(request):
    """Editar un tipo de comprobante existente con validaciones"""
    try:
        id = request.POST.get('idTipoComprobante', '').strip()
        codigo = request.POST.get('codigoTipoComprobante', '').strip().upper()
        nombre = request.POST.get('nombreTipoComprobante', '').strip()
        abreviatura = request.POST.get('abreviaturaTipoComprobante', '').strip().upper()

        # ========== VALIDACIONES ==========
        
        # 1. Validar ID del tipo de comprobante
        if not id:
            return HttpResponse("ID de tipo de comprobante inválido", status=400)
        
        try:
            tipo_comprobante = Tipocomprobante.objects.get(idtipocomprobante=id)
        except Tipocomprobante.DoesNotExist:
            return HttpResponse("El tipo de comprobante no existe", status=404)
        
        # 2. Validar código
        if not codigo:
            return HttpResponse("El código es obligatorio", status=400)
        
        if len(codigo) < 2:
            return HttpResponse("El código debe tener al menos 2 caracteres", status=400)
        
        if len(codigo) > 10:
            return HttpResponse("El código no puede exceder 10 caracteres", status=400)
        
        # Validar formato de código
        import re
        if not re.match(r'^[0-9A-Z\-]+$', codigo):
            return HttpResponse("El código solo puede contener números, letras mayúsculas y guiones", status=400)
        
        # 3. Validar que el código no esté duplicado (excepto el actual)
        if Tipocomprobante.objects.filter(codigo=codigo, estado=1).exclude(idtipocomprobante=id).exists():
            return HttpResponse(f"Ya existe otro tipo de comprobante con el código {codigo}", status=400)
        
        # 4. Validar nombre
        if not nombre:
            return HttpResponse("El nombre es obligatorio", status=400)
        
        if len(nombre) < 3:
            return HttpResponse("El nombre debe tener al menos 3 caracteres", status=400)
        
        if len(nombre) > 255:
            return HttpResponse("El nombre no puede exceder 255 caracteres", status=400)
        
        # 5. Validar abreviatura
        if not abreviatura:
            return HttpResponse("La abreviatura es obligatoria", status=400)
        
        if len(abreviatura) < 2:
            return HttpResponse("La abreviatura debe tener al menos 2 caracteres", status=400)
        
        if len(abreviatura) > 50:
            return HttpResponse("La abreviatura no puede exceder 50 caracteres", status=400)
        
        # ========== ACTUALIZAR TIPO DE COMPROBANTE ==========
        tipo_comprobante.codigo = codigo
        tipo_comprobante.nombre = nombre
        tipo_comprobante.abreviatura = abreviatura
        tipo_comprobante.save()
        
        return redirect('tipo_comprobante')
        
    except ValidationError as e:
        return HttpResponse(str(e), status=400)
    except Exception as e:
        return HttpResponse(f"Error al editar el tipo de comprobante: {str(e)}", status=500)