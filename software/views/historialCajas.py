# software/views/historialCajas.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime, date
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
import random

from software.models.AperturaCierreCajaModel import AperturaCierreCaja
from software.models.ReaperturaCajaModel import ReaperturaCaja
from software.models.UsuarioModel import Usuario
from software.models.cajaModel import Caja
from software.models.twoFactorModel import TwoFactorCode
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos


def historial_cajas(request):
    """
    Vista principal del historial de cajas
    """
    idusuario = request.session.get('idusuario')
    id_tipo_usuario = request.session.get('idtipousuario')
    
    if not idusuario or not id_tipo_usuario:
        return redirect('login')
    
    # Verificar permisos
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id_tipo_usuario)
    es_admin = id_tipo_usuario == 1
    
    # Obtener filtros
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    estado_filtro = request.GET.get('estado', 'todos')
    id_caja_filtro = request.GET.get('id_caja', '')
    
    # Query base
    if es_admin:
        aperturas = AperturaCierreCaja.objects.all()
    else:
        aperturas = AperturaCierreCaja.objects.filter(idusuario_id=idusuario)
    
    aperturas = aperturas.select_related('id_caja', 'idusuario').order_by('-fecha_apertura')
    
    # Aplicar filtros
    if fecha_desde:
        aperturas = aperturas.filter(fecha_apertura__gte=fecha_desde)
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
            aperturas = aperturas.filter(fecha_apertura__lte=fecha_hasta_dt)
        except:
            pass
    
    if estado_filtro != 'todos':
        aperturas = aperturas.filter(estado=estado_filtro)
    
    if id_caja_filtro:
        aperturas = aperturas.filter(id_caja_id=id_caja_filtro)
    
    # Obtener cajas para el filtro
    cajas = Caja.objects.filter(estado=1)
    
    # Verificar si tiene caja abierta actualmente
    tiene_caja_abierta = AperturaCierreCaja.objects.filter(
        idusuario_id=idusuario,
        estado__in=['abierta', 'reabierta']
    ).exists()
    
    # Usar datetime.now() en lugar de timezone.now() cuando USE_TZ=False
    from django.conf import settings
    
    if settings.USE_TZ:
        hoy = timezone.now()
    else:
        hoy = datetime.now()
    
    hace_7_dias = hoy - timedelta(days=7)
    
    for apertura in aperturas:
        fecha_apertura = apertura.fecha_apertura
        
        if not fecha_apertura:
            apertura.puede_reabrirse = False
            apertura.fue_reabierta = False
            continue
        
        # Convertir a datetime si es date
        if isinstance(fecha_apertura, date) and not isinstance(fecha_apertura, datetime):
            fecha_apertura = datetime.combine(fecha_apertura, datetime.min.time())
        
        # Solo hacer aware si USE_TZ=True
        if settings.USE_TZ and isinstance(fecha_apertura, datetime):
            if timezone.is_naive(fecha_apertura):
                fecha_apertura = timezone.make_aware(fecha_apertura)
        
        # Puede reabrirse si está cerrada, es de los últimos 7 días y no tiene caja abierta
        try:
            apertura.puede_reabrirse = (
                apertura.estado == 'cerrada' and
                fecha_apertura >= hace_7_dias and
                not tiene_caja_abierta
            )
        except:
            apertura.puede_reabrirse = False
        
        # Verificar si ya fue reabierta antes
        apertura.fue_reabierta = ReaperturaCaja.objects.filter(
            id_movimiento=apertura
        ).exists()
    
    data = {
        'aperturas': aperturas,
        'cajas': cajas,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado_filtro': estado_filtro,
        'id_caja_filtro': id_caja_filtro,
        'tiene_caja_abierta': tiene_caja_abierta,
        'es_admin': es_admin,
        'permisos': permisos,
    }
    
    return render(request, 'historial_cajas/historial.html', data)


# ⭐ ACTUALIZADO: Usar eid
def solicitar_reapertura(request, eid):
    """
    Solicita la reapertura de una caja cerrada
    Envía código 2FA al dueño del negocio
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from software.utils.url_encryptor import decrypt_id
        from django.conf import settings
        
        # ⭐ DESENCRIPTAR ID
        id_movimiento = decrypt_id(eid)
        if not id_movimiento:
            return JsonResponse({
                'ok': False,
                'error': 'URL inválida'
            }, status=400)
        
        idusuario = request.session.get('idusuario')
        
        if not idusuario:
            return JsonResponse({
                'ok': False,
                'error': 'No autenticado'
            }, status=401)
        
        apertura = get_object_or_404(AperturaCierreCaja, id_movimiento=id_movimiento)
        
        if apertura.estado != 'cerrada':
            return JsonResponse({
                'ok': False,
                'error': 'Solo se pueden reabrir cajas cerradas'
            }, status=400)
        
        # Usar datetime.now() o timezone.now() según configuración
        if settings.USE_TZ:
            hoy = timezone.now()
        else:
            hoy = datetime.now()
        
        hace_7_dias = hoy - timedelta(days=7)
        
        fecha_apertura = apertura.fecha_apertura
        
        if fecha_apertura:
            if isinstance(fecha_apertura, date) and not isinstance(fecha_apertura, datetime):
                fecha_apertura = datetime.combine(fecha_apertura, datetime.min.time())
            
            if settings.USE_TZ and isinstance(fecha_apertura, datetime):
                if timezone.is_naive(fecha_apertura):
                    fecha_apertura = timezone.make_aware(fecha_apertura)
            
            try:
                if fecha_apertura < hace_7_dias:
                    return JsonResponse({
                        'ok': False,
                        'error': 'Solo se pueden reabrir cajas de los últimos 7 días'
                    }, status=400)
            except:
                pass
        else:
            return JsonResponse({
                'ok': False,
                'error': 'La apertura no tiene fecha válida'
            }, status=400)
        
        # Verificar que el usuario NO tenga otra caja abierta
        tiene_caja_abierta = AperturaCierreCaja.objects.filter(
            idusuario_id=idusuario,
            estado__in=['abierta', 'reabierta']
        ).exists()
        
        if tiene_caja_abierta:
            return JsonResponse({
                'ok': False,
                'error': 'Debe cerrar su caja actual antes de reabrir una anterior'
            }, status=400)
        
        # Resto del código igual...
        motivo = request.POST.get('motivo', '').strip()
        
        if not motivo or len(motivo) < 10:
            return JsonResponse({
                'ok': False,
                'error': 'Debe proporcionar un motivo válido (mínimo 10 caracteres)'
            }, status=400)
        
        try:
            dueno = Usuario.objects.get(es_dueno=True, estado=1)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'No se ha configurado el dueño del negocio. Contacte al administrador.'
            }, status=400)
        except Usuario.MultipleObjectsReturned:
            dueno = Usuario.objects.filter(es_dueno=True, estado=1).first()
        
        codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        request.session['reapertura_codigo'] = codigo
        request.session['reapertura_id_movimiento'] = id_movimiento
        request.session['reapertura_motivo'] = motivo
        request.session['reapertura_usuario_solicitante'] = idusuario
        
        from software.utils.encryption_utils import EncryptionManager
        try:
            correo_dueno = EncryptionManager.decrypt_email(dueno.correo)
        except:
            correo_dueno = dueno.correo
        
        usuario_solicitante = Usuario.objects.get(idusuario=idusuario)
        
        asunto = '🔐 Código de Verificación - Reapertura de Caja'
        mensaje = f"""
Hola {dueno.nombrecompleto},

{usuario_solicitante.nombrecompleto} ha solicitado reabrir una caja cerrada.

DETALLES:
- Caja: {apertura.id_caja.nombre_caja if apertura.id_caja else 'N/A'}
- Fecha apertura original: {apertura.fecha_apertura.strftime('%d/%m/%Y %H:%M') if apertura.fecha_apertura else 'N/A'}
- Fecha cierre: {apertura.fecha_cierre.strftime('%d/%m/%Y %H:%M') if apertura.fecha_cierre else 'N/A'}
- Motivo: {motivo}

Tu código de verificación es:

{codigo}

Este código expirará en 10 minutos.

Si no autorizas esta acción, ignora este mensaje.

Saludos,
Sistema de Gestión
        """
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [correo_dueno],
            fail_silently=False,
        )
        
        print(f"✅ Código 2FA enviado al dueño: {codigo}")
        
        correo_oculto = correo_dueno[:3] + '***@' + correo_dueno.split('@')[1] if '@' in correo_dueno else '***'
        
        return JsonResponse({
            'ok': True,
            'message': f'Código de verificación enviado al correo del dueño',
            'correo_dueno': correo_oculto
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al solicitar reapertura: {str(e)}'
        }, status=500)


def verificar_codigo_reapertura(request):
    """
    Verifica el código 2FA y reabre la caja
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        codigo_ingresado = request.POST.get('codigo', '').strip()
        
        if not codigo_ingresado:
            return JsonResponse({
                'ok': False,
                'error': 'Por favor ingrese el código'
            }, status=400)
        
        # Obtener datos de sesión
        codigo_correcto = request.session.get('reapertura_codigo')
        id_movimiento = request.session.get('reapertura_id_movimiento')
        motivo = request.session.get('reapertura_motivo')
        usuario_solicitante_id = request.session.get('reapertura_usuario_solicitante')
        
        if not codigo_correcto or not id_movimiento:
            return JsonResponse({
                'ok': False,
                'error': 'Sesión expirada. Solicite un nuevo código.'
            }, status=400)
        
        # Verificar código
        if codigo_ingresado != codigo_correcto:
            return JsonResponse({
                'ok': False,
                'error': 'Código incorrecto'
            }, status=400)
        
        # ✅ Código correcto - REABRIR CAJA
        apertura = get_object_or_404(AperturaCierreCaja, id_movimiento=id_movimiento)
        
        # Cambiar estado a "reabierta"
        apertura.estado = 'reabierta'
        apertura.save()
        
        # Registrar en auditoría
        reapertura = ReaperturaCaja.objects.create(
            id_movimiento=apertura,
            usuario_solicitante_id=usuario_solicitante_id,
            motivo=motivo,
            codigo_2fa_enviado=codigo_correcto,
            estado='reabierta'
        )
        
        # Actualizar sesión del usuario
        request.session['id_caja'] = apertura.id_caja.id_caja
        
        # Limpiar datos temporales
        request.session.pop('reapertura_codigo', None)
        request.session.pop('reapertura_id_movimiento', None)
        request.session.pop('reapertura_motivo', None)
        request.session.pop('reapertura_usuario_solicitante', None)
        
        print(f"✅ CAJA REABIERTA")
        print(f"   ID Movimiento: {apertura.id_movimiento}")
        print(f"   Caja: {apertura.id_caja.nombre_caja}")
        print(f"   Usuario: {apertura.idusuario.nombrecompleto}")
        print(f"   Motivo: {motivo}")
        
        return JsonResponse({
            'ok': True,
            'success': True,
            'message': 'Caja reabierta correctamente. Puede realizar los movimientos necesarios.',
            'id_reapertura': reapertura.id_reapertura
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al verificar código: {str(e)}'
        }, status=500)


# ⭐ ACTUALIZADO: Usar eid
def cerrar_caja_reabierta(request, eid):
    """
    Cierra una caja que fue reabierta
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        id_movimiento = decrypt_id(eid)
        if not id_movimiento:
            return JsonResponse({
                'ok': False,
                'error': 'URL inválida'
            }, status=400)
        
        idusuario = request.session.get('idusuario')
        
        apertura = get_object_or_404(AperturaCierreCaja, id_movimiento=id_movimiento)
        
        # Validar que esté reabierta
        if apertura.estado != 'reabierta':
            return JsonResponse({
                'ok': False,
                'error': 'La caja no está reabierta'
            }, status=400)
        
        # Obtener saldo final (desde el POST o calcularlo)
        saldo_final = request.POST.get('saldo_final')
        
        if saldo_final:
            apertura.saldo_final = Decimal(saldo_final)
        
        # Cambiar estado a cerrada nuevamente
        ahora = timezone.now()
        apertura.estado = 'cerrada'
        apertura.fecha_cierre = ahora
        apertura.hora_cierre = ahora.time()
        apertura.save()
        
        # Actualizar auditoría
        reapertura = ReaperturaCaja.objects.filter(
            id_movimiento=apertura,
            estado='reabierta'
        ).order_by('-fecha_reapertura').first()
        
        if reapertura:
            reapertura.estado = 'cerrada_nuevamente'
            reapertura.fecha_cierre_reapertura = ahora
            reapertura.save()
        
        # Limpiar sesión
        request.session.pop('id_caja', None)
        
        print(f"✅ CAJA REABIERTA CERRADA NUEVAMENTE")
        print(f"   ID Movimiento: {apertura.id_movimiento}")
        
        return JsonResponse({
            'ok': True,
            'success': True,
            'message': 'Caja cerrada correctamente'
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al cerrar caja: {str(e)}'
        }, status=500)