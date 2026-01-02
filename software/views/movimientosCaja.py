from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal

from software.models.movimientoCajaModel import MovimientoCaja
from software.models.cajaModel import Caja
from software.models.AperturaCierreCajaModel import AperturaCierreCaja
from software.models.UsuarioModel import Usuario
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def movimientos_caja(request):
    """
    Listado de movimientos de caja
    """
    id_tipo_usuario = request.session.get('idtipousuario')
    idusuario = request.session.get('idusuario')
    
    if not id_tipo_usuario or not idusuario:
        return HttpResponse("<h1>No tiene acceso</h1>")
    
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id_tipo_usuario)
    es_admin = id_tipo_usuario == 1
    usuario = Usuario.objects.get(idusuario=idusuario)
    
    id_caja_session = request.session.get('id_caja')
    
    apertura_actual = None
    if id_caja_session:
        apertura_actual = AperturaCierreCaja.objects.filter(
            idusuario_id=idusuario,
            id_caja_id=id_caja_session,
            estado__in=['abierta', 'reabierta']
        ).first()
    
    if apertura_actual:
        movimientos = MovimientoCaja.objects.filter(
            id_movimiento=apertura_actual,
            estado=1
        ).select_related(
            'id_caja', 'idusuario', 'idventa'
        ).order_by('-fecha_movimiento')
    else:
        movimientos = MovimientoCaja.objects.none()
    
    # Calcular totales
    total_ingresos = movimientos.filter(
        tipo_movimiento='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    total_egresos = movimientos.filter(
        tipo_movimiento='egreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    saldo_actual = total_ingresos - total_egresos
    
    if apertura_actual:
        saldo_actual += apertura_actual.saldo_inicial
    
    data = {
        'movimientos': movimientos,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_actual': saldo_actual,
        'apertura_actual': apertura_actual,
        'tiene_caja_abierta': bool(apertura_actual),
        'es_admin': es_admin,
        'permisos': permisos,
    }
    
    return render(request, 'movimientos_caja/movimientos.html', data)


def registrar_egreso(request):
    if request.method != 'POST':
        return redirect('movimientos_caja')
    
    try:
        idusuario = request.session.get('idusuario')
        
        # Verificar caja abierta
        apertura_actual = AperturaCierreCaja.objects.filter(
            idusuario_id=idusuario,
            estado__in=['abierta', 'reabierta']
        ).first()
        
        if not apertura_actual:
            return JsonResponse({
                'ok': False,
                'error': 'No tiene una caja abierta. Debe aperturar una caja primero.',
                'necesita_aperturar': True
            }, status=400)
        
        # Obtener datos del formulario
        monto = Decimal(request.POST.get('monto', 0))
        descripcion = request.POST.get('descripcion', '').strip()
        
        # Validaciones
        if monto <= 0:
            return JsonResponse({
                'ok': False,
                'error': 'El monto debe ser mayor a cero'
            }, status=400)
        
        if not descripcion:
            return JsonResponse({
                'ok': False,
                'error': 'Debe ingresar una descripción del egreso'
            }, status=400)
        
        # Crear movimiento de egreso
        movimiento = MovimientoCaja.objects.create(
            id_caja=apertura_actual.id_caja,
            id_movimiento=apertura_actual,
            idusuario_id=idusuario,
            tipo_movimiento='egreso',
            monto=monto,
            descripcion=descripcion,
            estado=1
        )
        
        print(f"✅ Egreso registrado: S/ {monto} - {descripcion}")
        print(f"   Asociado a apertura: {apertura_actual.id_movimiento}")
        
        return JsonResponse({
            'ok': True,
            'message': 'Egreso registrado correctamente',
            'id_movimiento': movimiento.id_movimiento_caja
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al registrar egreso: {str(e)}'
        }, status=500)


def reporte_caja(request):
    """
    Generar reporte de caja (filtrado por fechas)
    """
    id_tipo_usuario = request.session.get('idtipousuario')
    idusuario = request.session.get('idusuario')
    
    if not id_tipo_usuario or not idusuario:
        return HttpResponse("<h1>No tiene acceso</h1>")
    
    # Obtener filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Base query
    movimientos = MovimientoCaja.objects.all().select_related(
        'id_caja', 'idusuario', 'idventa'
    )
    
    # Aplicar filtros
    if fecha_inicio:
        movimientos = movimientos.filter(fecha_movimiento__gte=fecha_inicio)
    
    if fecha_fin:
        movimientos = movimientos.filter(fecha_movimiento__lte=fecha_fin)
    
    # Si no es admin, solo sus movimientos
    es_admin = id_tipo_usuario == 1
    if not es_admin:
        movimientos = movimientos.filter(idusuario_id=idusuario)
    
    # Calcular totales
    total_ingresos = movimientos.filter(
        tipo_movimiento='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    total_egresos = movimientos.filter(
        tipo_movimiento='egreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    saldo = total_ingresos - total_egresos
    
    data = {
        'movimientos': movimientos.order_by('-fecha_movimiento'),
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo': saldo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'movimientos_caja/reporte.html', data)


# ⭐ FUNCIÓN FUTURA: Editar movimiento (SOLO ADMIN)
def editar_movimiento(request, eid):
    """
    Editar un movimiento de caja (solo egresos manuales)
    """
    if request.method != 'POST':
        return redirect('movimientos_caja')
    
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # Desencriptar ID
        id_movimiento_caja = decrypt_id(eid)
        if not id_movimiento_caja:
            return JsonResponse({
                'ok': False,
                'error': 'URL inválida'
            }, status=400)
        
        # Verificar permisos (solo admin)
        id_tipo_usuario = request.session.get('idtipousuario')
        if id_tipo_usuario != 1:
            return JsonResponse({
                'ok': False,
                'error': 'No tiene permisos para editar movimientos'
            }, status=403)
        
        movimiento = MovimientoCaja.objects.get(
            id_movimiento_caja=id_movimiento_caja,
            tipo_movimiento='egreso',  # Solo egresos manuales
            estado=1
        )
        
        # Actualizar datos
        movimiento.monto = Decimal(request.POST.get('monto'))
        movimiento.descripcion = request.POST.get('descripcion')
        movimiento.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Movimiento actualizado correctamente'
        })
        
    except MovimientoCaja.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Movimiento no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': f'Error: {str(e)}'
        }, status=500)


# ⭐ FUNCIÓN FUTURA: Eliminar movimiento (SOLO ADMIN)
def eliminar_movimiento(request, eid):
    """
    Eliminar un movimiento de caja (solo egresos manuales, solo admin)
    """
    if request.method != 'POST':
        return redirect('movimientos_caja')
    
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # Desencriptar ID
        id_movimiento_caja = decrypt_id(eid)
        if not id_movimiento_caja:
            return JsonResponse({
                'ok': False,
                'error': 'URL inválida'
            }, status=400)
        
        # Verificar permisos (solo admin)
        id_tipo_usuario = request.session.get('idtipousuario')
        if id_tipo_usuario != 1:
            return JsonResponse({
                'ok': False,
                'error': 'No tiene permisos para eliminar movimientos'
            }, status=403)
        
        movimiento = MovimientoCaja.objects.get(
            id_movimiento_caja=id_movimiento_caja,
            tipo_movimiento='egreso',  # Solo egresos manuales
            estado=1
        )
        
        # Soft delete
        movimiento.estado = 0
        movimiento.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Movimiento eliminado correctamente'
        })
        
    except MovimientoCaja.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Movimiento no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': f'Error: {str(e)}'
        }, status=500)