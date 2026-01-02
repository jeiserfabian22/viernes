# software/views.py
from django.http import HttpResponse,  JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from software.models.UsuarioModel import Usuario
from software.models.sucursalesModel import Sucursales
from software.models.cajaModel import Caja
from software.models.almacenesModel import Almacenes
from software.models.AperturaCierreCajaModel import AperturaCierreCaja
from software.models.twoFactorModel import TwoFactorCode
from django.core.mail import send_mail
from django.conf import settings


def index(request):
    return render(request, 'index.html')

def login(request):
    from software.utils.encryption_utils import EncryptionManager, PasswordManager
    
    email = request.POST.get('email_1')
    contrasena2 = request.POST.get('contrasena')
    
    if email and contrasena2:
        # ⭐ NUEVO: Buscar usuario por correo cifrado
        usuarios_todos = Usuario.objects.select_related(
            'idempresa', 'id_sucursal', 'idtipousuario'
        ).filter(estado=1)  # Solo usuarios activos
        
        usuario_encontrado = None
        
        # Buscar el usuario descifrando cada correo
        for usuario in usuarios_todos:
            try:
                correo_descifrado = EncryptionManager.decrypt_email(usuario.correo)
                if correo_descifrado == email:
                    # Verificar contraseña hasheada
                    if PasswordManager.verify_password(contrasena2, usuario.contrasena):
                        usuario_encontrado = usuario
                        break
            except Exception as e:
                print(f"Error al descifrar correo del usuario {usuario.idusuario}: {e}")
                continue

        if usuario_encontrado:
            # ✅ Credenciales correctas - Generar código 2FA
            
            # Invalidar códigos 2FA anteriores
            TwoFactorCode.objects.filter(
                usuario=usuario_encontrado,
                usado=False
            ).update(usado=True)
            
            # Generar nuevo código 2FA
            codigo_2fa = TwoFactorCode.objects.create(usuario=usuario_encontrado)
            
            # Descifrar correo para envío
            correo_descifrado = EncryptionManager.decrypt_email(usuario_encontrado.correo)
            
            # Enviar código por correo
            try:
                asunto = 'Código de Verificación - MotoVentas'
                mensaje = f"""
Hola {usuario_encontrado.nombrecompleto},

Tu código de verificación es:

{codigo_2fa.codigo}

Este código expirará en 10 minutos.

Si no intentaste iniciar sesión, ignora este mensaje.

Saludos,
Equipo MotoVentas
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [correo_descifrado],  # Usar correo descifrado
                    fail_silently=False,
                )
                
                print(f"✅ Código 2FA enviado: {codigo_2fa.codigo} a {correo_descifrado}")
                
            except Exception as e:
                print(f"❌ Error al enviar código 2FA: {str(e)}")
                error = "Error al enviar el código de verificación"
                return render(request, 'index.html', {'error': error})
            
            # Guardar temporalmente el ID del usuario en sesión
            request.session['pending_2fa_user'] = usuario_encontrado.idusuario
            request.session['pending_2fa_code_id'] = codigo_2fa.id
            
            # Redirigir a página de verificación 2FA
            return redirect('verificar_2fa')
        else:
            error = "Correo o contraseña incorrecta"
            data = {"error": error}
            return render(request, 'index.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")



def verificar_2fa(request):
    """
    Muestra el formulario para ingresar el código 2FA
    """
    pending_user_id = request.session.get('pending_2fa_user')
    
    if not pending_user_id:
        return redirect('index')
    
    if request.method == 'GET':
        try:
            usuario = Usuario.objects.get(idusuario=pending_user_id)
            return render(request, 'auth/verificar_2fa.html', {
                'correo': usuario.correo,
                'nombre': usuario.nombrecompleto
            })
        except Usuario.DoesNotExist:
            return redirect('index')
    
    elif request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()
        
        if not codigo_ingresado:
            return JsonResponse({
                'error': 'Por favor ingrese el código'
            }, status=400)
        
        try:
            codigo_2fa_id = request.session.get('pending_2fa_code_id')
            codigo_2fa = TwoFactorCode.objects.get(id=codigo_2fa_id)
            
            if not codigo_2fa.is_valid():
                return JsonResponse({
                    'error': 'El código ha expirado o alcanzó el máximo de intentos'
                }, status=400)
            
            codigo_2fa.intentos += 1
            codigo_2fa.save()
            
            if codigo_ingresado == codigo_2fa.codigo:
                # ✅ Código correcto - Completar login SIN apertura de caja
                codigo_2fa.usado = True
                codigo_2fa.save()
                
                usuario = codigo_2fa.usuario
                es_admin = usuario.idtipousuario.idtipousuario == 1  # Ajusta según tu BD
                
                # Guardar datos básicos en sesión
                request.session['idtipousuario'] = usuario.idtipousuario.idtipousuario
                request.session['nombrecompleto'] = usuario.nombrecompleto
                request.session['idusuario'] = usuario.idusuario
                request.session['es_admin'] = es_admin
                
                if usuario.idempresa:
                    request.session['idempresa'] = usuario.idempresa.idempresa
                
                # Asignar sucursal del usuario
                if usuario.id_sucursal:
                    request.session['id_sucursal'] = usuario.id_sucursal.id_sucursal
                elif es_admin:
                    # Admin sin sucursal: usar la primera de su empresa
                    primera_sucursal = Sucursales.objects.filter(
                        idempresa=usuario.idempresa
                    ).first()
                    if primera_sucursal:
                        request.session['id_sucursal'] = primera_sucursal.id_sucursal
                
                # ⭐ NUEVO: Verificar si tiene caja abierta de sesiones anteriores
                apertura_abierta = AperturaCierreCaja.objects.filter(
                    idusuario=usuario,
                    estado__in=['abierta', 'reabierta']
                ).first()
                
                if apertura_abierta:
                    # Restaurar contexto de caja abierta
                    request.session['id_caja'] = apertura_abierta.id_caja.id_caja
                    if apertura_abierta.id_caja.id_sucursal:
                        request.session['id_sucursal'] = apertura_abierta.id_caja.id_sucursal.id_sucursal
                    print(f"✅ Caja abierta restaurada: {apertura_abierta.id_caja.nombre_caja}")
                
                # Limpiar datos temporales de 2FA
                request.session.pop('pending_2fa_user', None)
                request.session.pop('pending_2fa_code_id', None)
                
                print(f"✅ Login exitoso: {usuario.nombrecompleto} ({'Admin' if es_admin else 'Usuario'})")
                print(f"   Sucursal: {request.session.get('id_sucursal')}")
                print(f"   Caja: {request.session.get('id_caja', 'Sin caja')}")
                
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Verificación exitosa'
                })
            else:
                intentos_restantes = 3 - codigo_2fa.intentos
                
                if intentos_restantes > 0:
                    return JsonResponse({
                        'error': f'Código incorrecto. Te quedan {intentos_restantes} intento(s)'
                    }, status=400)
                else:
                    return JsonResponse({
                        'error': 'Has alcanzado el máximo de intentos. Solicita un nuevo código'
                    }, status=400)
        
        except TwoFactorCode.DoesNotExist:
            return JsonResponse({
                'error': 'Código no encontrado'
            }, status=404)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': 'Error al verificar el código'
            }, status=500)

def reenviar_codigo_2fa(request):
    """
    Reenvía un nuevo código 2FA
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    pending_user_id = request.session.get('pending_2fa_user')
    
    if not pending_user_id:
        return JsonResponse({'error': 'Sesión expirada'}, status=401)
    
    try:
        usuario = Usuario.objects.get(idusuario=pending_user_id)
        
        # Invalidar códigos anteriores
        TwoFactorCode.objects.filter(
            usuario=usuario,
            usado=False
        ).update(usado=True)
        
        # Generar nuevo código
        codigo_2fa = TwoFactorCode.objects.create(usuario=usuario)
        
        # Enviar por correo
        asunto = 'Nuevo Código de Verificación - MotoVentas'
        mensaje = f"""
Hola {usuario.nombrecompleto},

Tu nuevo código de verificación es:

{codigo_2fa.codigo}

Este código expirará en 10 minutos.

Saludos,
Equipo MotoVentas
        """
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.correo],
            fail_silently=False,
        )
        
        # Actualizar ID del código en sesión
        request.session['pending_2fa_code_id'] = codigo_2fa.id
        
        print(f"✅ Nuevo código 2FA enviado: {codigo_2fa.codigo}")
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Se ha enviado un nuevo código a tu correo'
        })
        
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'error': 'Error al reenviar el código'
        }, status=500)



def cancelar_2fa(request):
    """
    Cancela el proceso de 2FA y vuelve al login
    """
    request.session.pop('pending_2fa_user', None)
    request.session.pop('pending_2fa_code_id', None)
    return redirect('index')


def logout(request):
    request.session.flush()
    return redirect('index')


def cambiar_contexto(request):
    """
    Permite cambiar sucursal, caja y almacén (para todos los usuarios)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    idusuario = request.session.get('idusuario')
    es_admin = request.session.get('es_admin', False)
    
    if not idusuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    id_sucursal = request.POST.get('id_sucursal')
    id_caja = request.POST.get('id_caja')
    id_almacen = request.POST.get('id_almacen')
    
    try:
        usuario = Usuario.objects.get(idusuario=idusuario)
        
        # Actualizar sucursal
        if id_sucursal:
            if es_admin:
                # Admin puede cambiar a cualquier sucursal de su empresa
                sucursal = Sucursales.objects.get(
                    id_sucursal=id_sucursal,
                    idempresa=usuario.idempresa
                )
            else:
                # Usuario normal: verificar que sea su sucursal
                if usuario.id_sucursal and usuario.id_sucursal.id_sucursal == int(id_sucursal):
                    sucursal = usuario.id_sucursal
                else:
                    return JsonResponse({
                        'error': 'No tienes permiso para cambiar a esta sucursal'
                    }, status=403)
            
            request.session['id_sucursal'] = sucursal.id_sucursal
            print(f"✅ Sucursal cambiada a: {sucursal.nombre_sucursal}")
        
        # Actualizar caja (sin aperturar)
        if id_caja:
            caja = Caja.objects.get(id_caja=id_caja)
            request.session['id_caja'] = caja.id_caja
            print(f"✅ Caja seleccionada: {caja.nombre_caja}")
        else:
            request.session.pop('id_caja', None)
        
        # Actualizar almacén
        if id_almacen:
            almacen = Almacenes.objects.get(id_almacen=id_almacen)
            request.session['id_almacen'] = almacen.id_almacen
            print(f"✅ Almacén seleccionado: {almacen.nombre_almacen}")
        else:
            request.session.pop('id_almacen', None)
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Contexto actualizado correctamente'
        })
        
    except (Sucursales.DoesNotExist, Caja.DoesNotExist, Almacenes.DoesNotExist):
        return JsonResponse({
            'error': 'Registro no encontrado'
        }, status=404)
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({
            'error': 'Error al cambiar contexto'
        }, status=500)

def obtener_datos_apertura(request):
    """
    Devuelve las opciones disponibles según el tipo de usuario
    """
    idusuario = request.session.get('idusuario')
    idtipousuario = request.session.get('idtipousuario')
    
    if not idusuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    usuario = Usuario.objects.get(idusuario=idusuario)
    es_admin = idtipousuario == 1
    
    data = {
        'es_admin': es_admin,
        'sucursales': [],
        'cajas': [],
        'almacenes': []
    }
    
    if es_admin:
        # Admin: puede ver todas las sucursales de su empresa
        sucursales = Sucursales.objects.filter(idempresa=usuario.idempresa)
        data['sucursales'] = [
            {'id': s.id_sucursal, 'nombre': s.nombre_sucursal} 
            for s in sucursales
        ]
    else:
        # Usuario normal: solo su sucursal
        if usuario.id_sucursal:
            data['sucursales'] = [{
                'id': usuario.id_sucursal.id_sucursal,
                'nombre': usuario.id_sucursal.nombre_sucursal
            }]
            
            # Cargar cajas y almacenes de su sucursal
            cajas = Caja.objects.filter(
                id_sucursal=usuario.id_sucursal,
                estado=1
            )
            
            # Filtrar cajas disponibles (sin apertura activa de otro usuario)
            cajas_disponibles = []
            for caja in cajas:
                apertura_activa = AperturaCierreCaja.objects.filter(
                    id_caja=caja,
                    estado__in=['abierta', 'reabierta']
                ).exclude(idusuario=usuario).exists()  # Excluir aperturas propias
                
                if not apertura_activa:
                    cajas_disponibles.append({
                        'id': caja.id_caja,
                        'nombre': caja.nombre_caja,
                        'numero': caja.numero_caja
                    })
            
            data['cajas'] = cajas_disponibles
            
            # Almacenes
            almacenes = Almacenes.objects.filter(
                id_sucursal=usuario.id_sucursal,
                estado=1
            )
            data['almacenes'] = [
                {'id': a.id_almacen, 'nombre': a.nombre_almacen}
                for a in almacenes
            ]
    
    return JsonResponse(data)

def obtener_cajas_almacenes(request):
    """
    Obtiene cajas y almacenes de una sucursal específica
    """
    id_sucursal = request.GET.get('id_sucursal')
    idusuario = request.session.get('idusuario')
    
    print(f"🔍 DEBUG obtener_cajas_almacenes:")
    print(f"   id_sucursal recibido: {id_sucursal}")
    print(f"   idusuario: {idusuario}")
    
    if not id_sucursal:
        return JsonResponse({'error': 'Sucursal no especificada'}, status=400)
    
    try:
        # Obtener cajas activas de la sucursal
        cajas = Caja.objects.filter(
            id_sucursal_id=id_sucursal,
            estado=1
        )
        
        print(f"   Total cajas encontradas: {cajas.count()}")
        for caja in cajas:
            print(f"   - Caja: {caja.nombre_caja} (ID: {caja.id_caja})")
        
        # Filtrar cajas disponibles
        cajas_disponibles = []
        for caja in cajas:
            apertura_activa = AperturaCierreCaja.objects.filter(
                id_caja=caja,
                estado__in=['abierta', 'reabierta']
            ).exclude(idusuario_id=idusuario).exists()
            
            print(f"   - Caja {caja.nombre_caja}: apertura_activa={apertura_activa}")
            
            if not apertura_activa:
                cajas_disponibles.append({
                    'id': caja.id_caja,
                    'nombre': caja.nombre_caja,
                    'numero': caja.numero_caja
                })
        
        print(f"   Cajas disponibles: {len(cajas_disponibles)}")
        
        # Almacenes activos
        almacenes = Almacenes.objects.filter(
            id_sucursal_id=id_sucursal,
            estado=1
        )
        
        print(f"   Total almacenes encontrados: {almacenes.count()}")
        
        data = {
            'cajas': cajas_disponibles,
            'almacenes': [
                {'id': a.id_almacen, 'nombre': a.nombre_almacen}
                for a in almacenes
            ]
        }
        
        print(f"   ✅ Respuesta: {data}")
        
        return JsonResponse(data)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Error al obtener datos'}, status=500)
    

def abrir_caja(request):
    """
    Apertura una caja (se llama cuando el usuario va a vender)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Aceptar datos JSON o POST normales
    import json
    try:
        data = json.loads(request.body)
        monto = data.get('monto')
        id_caja = data.get('id_caja')
        id_almacen = data.get('id_almacen')
        id_sucursal = data.get('id_sucursal')
    except:
        monto = request.POST.get('monto')
        id_caja = request.POST.get('id_caja')
        id_almacen = request.POST.get('id_almacen')
        id_sucursal = request.POST.get('id_sucursal')
    
    idusuario = request.session.get('idusuario')
    es_admin = request.session.get('es_admin', False)
    
    if not idusuario:
        return JsonResponse({'ok': False, 'error': 'No autenticado'}, status=401)
    
    if not id_caja or not monto:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos'}, status=400)
    
    try:
        usuario = Usuario.objects.get(idusuario=idusuario)
        caja = Caja.objects.get(id_caja=id_caja)
        
        # Verificar que no tenga otra caja abierta
        apertura_propia = AperturaCierreCaja.objects.filter(
            idusuario=usuario,
            estado__in=['abierta', 'reabierta']
        ).first()
        
        if apertura_propia:
            return JsonResponse({
                'ok': False,
                'error': f'Ya tienes la caja "{apertura_propia.id_caja.nombre_caja}" abierta. Ciérrala primero.'
            }, status=400)
        
        # Verificar que la caja no esté abierta por otro usuario
        apertura_otra = AperturaCierreCaja.objects.filter(
            id_caja=caja,
            estado__in=['abierta', 'reabierta']
        ).first()
        
        if apertura_otra:
            return JsonResponse({
                'ok': False,
                'error': f'La caja está siendo usada por {apertura_otra.idusuario.nombrecompleto}'
            }, status=400)
        
        # Actualizar contexto si es admin y cambió sucursal
        if es_admin and id_sucursal:
            request.session['id_sucursal'] = int(id_sucursal)
        
        # ⭐ CORRECCIÓN: Usar timezone.now() directamente
        ahora = timezone.now()
        
        # Crear apertura
        apertura = AperturaCierreCaja.objects.create(
            id_caja=caja,
            idusuario=usuario,
            saldo_inicial=monto,
            fecha_apertura=ahora,  # Guardar fecha y hora completa
            hora_apertura=ahora.time(),  # Extraer solo la hora
            estado='abierta'
        )
        
        # Guardar en sesión
        request.session['id_caja'] = caja.id_caja
        if id_almacen:
            request.session['id_almacen'] = int(id_almacen)
        if caja.id_sucursal:
            request.session['id_sucursal'] = caja.id_sucursal.id_sucursal
        
        print(f"✅ Caja aperturada: {caja.nombre_caja}")
        print(f"   Usuario: {usuario.nombrecompleto}")
        print(f"   Saldo inicial: S/ {monto}")
        
        return JsonResponse({
            'ok': True,
            'success': True,
            'mensaje': f'Caja {caja.nombre_caja} aperturada correctamente',
            'id_movimiento': apertura.id_movimiento,
            'datos': {
                'caja': caja.nombre_caja,
                'saldo_inicial': float(monto),
                'fecha_apertura': ahora.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Caja.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Caja no encontrada'}, status=404)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        print(f"❌ Error al aperturar caja: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al aperturar caja: {str(e)}'
        }, status=500)


def cerrar_caja(request):
    """
    Cierra la caja actual del usuario
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    idusuario = request.session.get('idusuario')
    
    # Aceptar datos JSON o POST normales
    import json
    try:
        data = json.loads(request.body)
        saldo_final = data.get('saldo_final')
    except:
        saldo_final = request.POST.get('saldo_final')
    
    if not idusuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        # Buscar apertura activa del usuario
        apertura_abierta = AperturaCierreCaja.objects.filter(
            idusuario_id=idusuario,
            estado__in=['abierta', 'reabierta']
        ).first()
        
        if not apertura_abierta:
            return JsonResponse({
                'ok': False,
                'error': 'No tienes una caja abierta'
            }, status=400)
        
        # ⭐ CORRECCIÓN: Usar timezone.now() directamente
        ahora = timezone.now()
        
        # Cerrar caja
        apertura_abierta.saldo_final = saldo_final if saldo_final else apertura_abierta.saldo_inicial
        apertura_abierta.fecha_cierre = ahora  # Guardar fecha y hora completa
        apertura_abierta.hora_cierre = ahora.time()  # Extraer solo la hora
        apertura_abierta.estado = 'cerrada'
        apertura_abierta.save()
        
        # Limpiar sesión
        request.session.pop('id_caja', None)
        
        print(f"✅ Caja cerrada: {apertura_abierta.id_caja.nombre_caja}")
        print(f"   Saldo inicial: {apertura_abierta.saldo_inicial}")
        print(f"   Saldo final: {apertura_abierta.saldo_final}")
        
        return JsonResponse({
            'ok': True,
            'success': True,
            'mensaje': 'Caja cerrada correctamente',
            'datos': {
                'caja': apertura_abierta.id_caja.nombre_caja,
                'saldo_inicial': float(apertura_abierta.saldo_inicial),
                'saldo_final': float(apertura_abierta.saldo_final)
            }
        })
        
    except Exception as e:
        print(f"❌ Error al cerrar caja: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': f'Error al cerrar caja: {str(e)}'
        }, status=500)
    

def obtener_saldo_actual(request):
    """
    Devuelve el saldo actual de la caja abierta O reabierta del usuario
    """
    idusuario = request.session.get('idusuario')
    
    if not idusuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        # Buscar apertura activa O reabierta
        apertura = AperturaCierreCaja.objects.filter(
            idusuario_id=idusuario,
            estado__in=['abierta', 'reabierta']  # ✅ Agregar 'reabierta'
        ).first()
        
        if not apertura:
            return JsonResponse({
                'ok': False,
                'error': 'No hay caja abierta'
            }, status=400)
        
        from software.models.movimientoCajaModel import MovimientoCaja
        from django.db.models import Sum
        
        # Filtrar movimientos de esta apertura
        movimientos = MovimientoCaja.objects.filter(
            id_movimiento=apertura,
            estado=1
        )
        
        print("=" * 60)
        print("🔍 DEBUG SALDO ACTUAL")
        print(f"   Caja: {apertura.id_caja.nombre_caja}")
        print(f"   ID Apertura (id_movimiento): {apertura.id_movimiento}")
        print(f"   Estado: {apertura.estado}")  # ✅ Mostrar si es reabierta
        print(f"   Saldo inicial: S/ {apertura.saldo_inicial}")
        print(f"   Total movimientos: {movimientos.count()}")
        
        # Calcular ingresos y egresos
        total_ingresos = movimientos.filter(
            tipo_movimiento='ingreso'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        total_egresos = movimientos.filter(
            tipo_movimiento='egreso'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        print(f"   Total ingresos: S/ {total_ingresos}")
        print(f"   Total egresos: S/ {total_egresos}")
        
        # Saldo actual = Saldo inicial + Ingresos - Egresos
        saldo_actual = float(apertura.saldo_inicial) + float(total_ingresos) - float(total_egresos)
        
        print(f"   ✅ SALDO ACTUAL: S/ {saldo_actual}")
        print("=" * 60)
        
        return JsonResponse({
            'ok': True,
            'saldo_actual': saldo_actual,
            'saldo_inicial': float(apertura.saldo_inicial),
            'total_ingresos': float(total_ingresos),
            'total_egresos': float(total_egresos),
            'caja': apertura.id_caja.nombre_caja,
            'fecha_apertura': apertura.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
            'es_reabierta': apertura.estado == 'reabierta'  # ✅ Nuevo
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'ok': False,
            'error': 'Error al obtener saldo'
        }, status=500)





