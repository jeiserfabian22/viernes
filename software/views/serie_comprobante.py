from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from software.models.SeriecomprobanteModel import Seriecomprobante
from software.models.TipocomprobanteModel import Tipocomprobante
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def serie_comprobante(request):
    """Vista principal que lista todas las series de comprobante activas"""
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        series_comprobante = Seriecomprobante.objects.filter(estado=1).select_related('idtipocomprobante').order_by('idtipocomprobante__codigo', 'serie')
        tipos_comprobante = Tipocomprobante.objects.filter(estado=1).order_by('codigo')

        data = {
            'series_comprobante': series_comprobante,
            'tipos_comprobante': tipos_comprobante,
            'permisos': permisos
        }
        
        return render(request, 'serie_comprobante/serie_comprobante.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso</h1>")


def eliminar_serie_comprobante(request, id):
    """Eliminación lógica de la serie de comprobante (cambia estado a 0)"""
    try:
        serie_comprobante = Seriecomprobante.objects.get(idseriecomprobante=id)
        serie_comprobante.estado = 0
        serie_comprobante.save()
        return redirect('serie_comprobante')
    except Seriecomprobante.DoesNotExist:
        return HttpResponse("La serie de comprobante no existe", status=404)
    except Exception as e:
        return HttpResponse(f"Error al eliminar: {str(e)}", status=500)


def agregar_serie_comprobante(request):
    """Agregar una nueva serie de comprobante con validaciones - Compatible con AJAX"""
    try:
        idtipocomprobante = request.POST.get('tipoComprobanteSerieComprobante', '').strip()
        serie = request.POST.get('serieSerieComprobante', '').strip().upper()
        numero_actual = request.POST.get('numeroActualSerieComprobante', '').strip()

        # ========== VALIDACIONES ==========
        
        # 1. Validar tipo de comprobante
        if not idtipocomprobante:
            error_msg = "Debe seleccionar un tipo de comprobante"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        try:
            tipo_comprobante = Tipocomprobante.objects.get(idtipocomprobante=idtipocomprobante, estado=1)
        except Tipocomprobante.DoesNotExist:
            error_msg = "El tipo de comprobante seleccionado no existe"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 2. Validar serie
        if not serie:
            error_msg = "La serie es obligatoria"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(serie) != 4:
            error_msg = "La serie debe tener exactamente 4 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # Validar formato alfanumérico
        if not serie.isalnum():
            error_msg = "La serie solo puede contener letras y números (sin espacios ni caracteres especiales)"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 3. Validar que la serie no esté duplicada para el mismo tipo de comprobante
        if Seriecomprobante.objects.filter(idtipocomprobante=tipo_comprobante, serie=serie, estado=1).exists():
            error_msg = f"Ya existe una serie {serie} para el tipo de comprobante {tipo_comprobante.nombre}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 4. Validar número actual
        if not numero_actual:
            error_msg = "El número actual es obligatorio"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        try:
            numero_actual_int = int(numero_actual)
        except ValueError:
            error_msg = "El número actual debe ser un número entero"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if numero_actual_int < 0:  # ✅ PERMITE 0
            error_msg = "El número actual debe ser mayor o igual a 0"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if numero_actual_int > 99999999:
            error_msg = "El número actual no puede exceder 99999999 (8 dígitos)"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # ========== CREAR SERIE DE COMPROBANTE ==========
        serie_comprobante = Seriecomprobante.objects.create(
            idtipocomprobante=tipo_comprobante,
            serie=serie,
            numero_actual=numero_actual_int,
            estado=1
        )
        
        # ✅ DETECTAR SI ES AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'idseriecomprobante': serie_comprobante.idseriecomprobante,
                'serie': serie_comprobante.serie,
                'numero_actual': serie_comprobante.numero_actual,
                'tipo_comprobante': serie_comprobante.idtipocomprobante.nombre,
                'serie_completa': serie_comprobante.serie_completa,
                'siguiente_numero': serie_comprobante.siguiente_numero
            })
        
        # Si NO es AJAX, redireccionar normalmente
        return redirect('serie_comprobante')
        
    except ValidationError as e:
        error_msg = str(e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': error_msg}, status=400)
        return HttpResponse(error_msg, status=400)
    except Exception as e:
        error_msg = f"Error al guardar la serie de comprobante: {str(e)}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': error_msg}, status=500)
        return HttpResponse(error_msg, status=500)


def editar_serie_comprobante(request):
    """Editar una serie de comprobante existente con validaciones"""
    try:
        id = request.POST.get('idSerieComprobante', '').strip()
        idtipocomprobante = request.POST.get('tipoComprobanteSerieComprobante', '').strip()
        serie = request.POST.get('serieSerieComprobante', '').strip().upper()
        numero_actual = request.POST.get('numeroActualSerieComprobante', '').strip()

        # ========== VALIDACIONES ==========
        
        # 1. Validar ID de la serie de comprobante
        if not id:
            return HttpResponse("ID de serie de comprobante inválido", status=400)
        
        try:
            serie_comprobante = Seriecomprobante.objects.get(idseriecomprobante=id)
        except Seriecomprobante.DoesNotExist:
            return HttpResponse("La serie de comprobante no existe", status=404)
        
        # 2. Validar tipo de comprobante
        if not idtipocomprobante:
            return HttpResponse("Debe seleccionar un tipo de comprobante", status=400)
        
        try:
            tipo_comprobante = Tipocomprobante.objects.get(idtipocomprobante=idtipocomprobante, estado=1)
        except Tipocomprobante.DoesNotExist:
            return HttpResponse("El tipo de comprobante seleccionado no existe", status=400)
        
        # 3. Validar serie
        if not serie:
            return HttpResponse("La serie es obligatoria", status=400)
        
        if len(serie) != 4:
            return HttpResponse("La serie debe tener exactamente 4 caracteres", status=400)
        
        # Validar formato alfanumérico
        if not serie.isalnum():
            return HttpResponse("La serie solo puede contener letras y números (sin espacios ni caracteres especiales)", status=400)
        
        # 4. Validar que la serie no esté duplicada (excepto la actual)
        if Seriecomprobante.objects.filter(
            idtipocomprobante=tipo_comprobante,
            serie=serie,
            estado=1
        ).exclude(idseriecomprobante=id).exists():
            return HttpResponse(f"Ya existe otra serie {serie} para el tipo de comprobante {tipo_comprobante.nombre}", status=400)
        
        # 5. Validar número actual
        if not numero_actual:
            return HttpResponse("El número actual es obligatorio", status=400)
        
        try:
            numero_actual_int = int(numero_actual)
        except ValueError:
            return HttpResponse("El número actual debe ser un número entero", status=400)
        
        if numero_actual_int < 0:  # ✅ PERMITE 0
            return HttpResponse("El número actual debe ser mayor o igual a 0", status=400)
        
        if numero_actual_int > 99999999:
            return HttpResponse("El número actual no puede exceder 99999999 (8 dígitos)", status=400)
        
        # ========== ACTUALIZAR SERIE DE COMPROBANTE ==========
        serie_comprobante.idtipocomprobante = tipo_comprobante
        serie_comprobante.serie = serie
        serie_comprobante.numero_actual = numero_actual_int
        serie_comprobante.save()
        
        return redirect('serie_comprobante')
        
    except ValidationError as e:
        return HttpResponse(str(e), status=400)
    except Exception as e:
        return HttpResponse(f"Error al editar la serie de comprobante: {str(e)}", status=500)