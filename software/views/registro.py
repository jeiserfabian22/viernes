# software/views/registro.py

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from software.models.UsuarioModel import Usuario
from software.models.TipousuarioModel import Tipousuario
from software.models.ModulosModel import Modulos
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.utils.encryption_utils import EncryptionManager, PasswordManager
from django.core.mail import send_mail
from django.conf import settings

# ⭐ IMPORTAR LA API DE TOKENPERU (igual que en clientes)
from software.tokenperu_api import consultar_documento


def registro_usuario(request):
    """
    Vista para registro público de usuarios con permisos limitados.
    Los usuarios creados obtienen automáticamente el tipo "ejemplo" (ID: 10)
    """
    if request.method == 'GET':
        return render(request, 'auth/registro_usuario.html')
    
    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_completo = request.POST.get('nombre_completo')
            correo = request.POST.get('correo')
            contrasena = request.POST.get('contrasena')
            confirmar_contrasena = request.POST.get('confirmar_contrasena')
            celular = request.POST.get('celular')
            dni = request.POST.get('dni')
            
            # Validaciones básicas
            if not all([nombre_completo, correo, contrasena, confirmar_contrasena, celular, dni]):
                return JsonResponse({
                    'error': 'Todos los campos son obligatorios'
                }, status=400)
            
            # Validar DNI (solo 8 dígitos)
            if not dni.isdigit() or len(dni) != 8:
                return JsonResponse({
                    'error': 'El DNI debe tener exactamente 8 dígitos numéricos'
                }, status=400)
            
            if contrasena != confirmar_contrasena:
                return JsonResponse({
                    'error': 'Las contraseñas no coinciden'
                }, status=400)
            
            if len(contrasena) < 8:
                return JsonResponse({
                    'error': 'La contraseña debe tener al menos 8 caracteres'
                }, status=400)
            
            # Validar celular (9 dígitos)
            if not celular.isdigit() or len(celular) != 9:
                return JsonResponse({
                    'error': 'El celular debe tener exactamente 9 dígitos'
                }, status=400)
            
            # Verificar si el DNI ya existe
            if Usuario.objects.filter(dni=dni, estado=1).exists():
                return JsonResponse({
                    'error': f'Ya existe un usuario registrado con el DNI {dni}'
                }, status=400)
            
            # Verificar si el correo ya existe
            usuarios_existentes = Usuario.objects.filter(estado=1)
            for usuario in usuarios_existentes:
                try:
                    correo_descifrado = EncryptionManager.decrypt_email(usuario.correo)
                    if correo_descifrado == correo:
                        return JsonResponse({
                            'error': 'Este correo ya está registrado'
                        }, status=400)
                except:
                    continue
            
            # Cifrar correo y hashear contraseña
            correo_cifrado = EncryptionManager.encrypt_email(correo)
            contrasena_hasheada = PasswordManager.hash_password(contrasena)
            
            # ⭐ TIPO DE USUARIO: "ejemplo" (ID: 10)
            ID_TIPO_USUARIO_EJEMPLO = 10
            
            # Obtener tipo de usuario "ejemplo"
            try:
                tipo_usuario_ejemplo = Tipousuario.objects.get(
                    idtipousuario=ID_TIPO_USUARIO_EJEMPLO
                )
            except Tipousuario.DoesNotExist:
                return JsonResponse({
                    'error': 'Error: El tipo de usuario "ejemplo" no está configurado correctamente'
                }, status=500)
            
            # Crear usuario con permisos limitados
            nuevo_usuario = Usuario.objects.create(
                nombrecompleto=nombre_completo,
                correo=correo_cifrado,
                contrasena=contrasena_hasheada,
                idtipousuario=tipo_usuario_ejemplo,
                celular=celular,
                dni=dni,
                es_dueno=False,
                estado=1,
                idempresa=None,
                id_sucursal=None
            )
            
            print(f"✅ Usuario registrado: {nombre_completo}")
            print(f"   DNI: {dni}")
            print(f"   Tipo de usuario: {tipo_usuario_ejemplo.nombretipousuario} (ID: {ID_TIPO_USUARIO_EJEMPLO})")
            print(f"   Correo: {correo}")
            
            # ⭐ VERIFICAR SI EL TIPO "ejemplo" YA TIENE PERMISOS ASIGNADOS
            permisos_existentes = Detalletipousuarioxmodulos.objects.filter(
                idtipousuario=tipo_usuario_ejemplo
            )
            
            if permisos_existentes.exists():
                print(f"✅ El tipo 'ejemplo' ya tiene {permisos_existentes.count()} permisos asignados")
            else:
                print("⚠️ ADVERTENCIA: El tipo 'ejemplo' no tiene permisos asignados")
                print("   Debes asignar permisos desde el panel de permisos o ejecutar el SQL")
            
            # Enviar correo de bienvenida (opcional)
            try:
                asunto = 'Bienvenido a MotoVentas'
                mensaje = f"""
Hola {nombre_completo},

¡Tu cuenta ha sido creada exitosamente en MotoVentas!

Datos de acceso:
━━━━━━━━━━━━━━━━━━━━━
📧 Correo: {correo}
🔐 Contraseña: (la que elegiste)
🆔 DNI: {dni}

Ya puedes iniciar sesión en el sistema.

📌 IMPORTANTE:
• Tu cuenta tiene permisos limitados de consulta
• Para obtener acceso completo, contacta con un administrador
• Nunca compartas tu contraseña con nadie

¿Tienes dudas? Contacta a soporte.

¡Bienvenido a bordo! 🏍️

Saludos,
Equipo MotoVentas
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [correo],
                    fail_silently=True,
                )
                print(f"✅ Correo de bienvenida enviado a {correo}")
            except Exception as e:
                print(f"⚠️ No se pudo enviar el correo de bienvenida: {e}")
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Usuario registrado exitosamente. Ya puedes iniciar sesión.'
            })
            
        except Exception as e:
            print(f"❌ Error en registro: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': f'Error al registrar usuario: {str(e)}'
            }, status=500)


# ⭐ NUEVA FUNCIÓN: Autocompletar nombre por DNI (igual que en clientes)
@csrf_exempt
def autocompletar_dni_registro(request):
    """Vista AJAX para autocompletar nombre completo desde RENIEC vía TokenPeru"""
    dni = request.GET.get('dni', '').strip()
    
    if not dni:
        return JsonResponse({
            'success': False,
            'error': 'Se requiere el DNI'
        })
    
    # Validar que sea DNI (8 dígitos) - NO permitir RUC
    if not dni.isdigit() or len(dni) != 8:
        return JsonResponse({
            'success': False,
            'error': 'El DNI debe tener exactamente 8 dígitos'
        })
    
    try:
        # Verificar si el DNI ya está registrado
        if Usuario.objects.filter(dni=dni, estado=1).exists():
            return JsonResponse({
                'success': False,
                'error': f'El DNI {dni} ya está registrado en el sistema'
            })
        
        # Consultar TokenPeru (igual que en clientes)
        resultado = consultar_documento(dni)
        
        # Validar que sea DNI
        if resultado['tipo_documento'] != 'DNI':
            return JsonResponse({
                'success': False,
                'error': 'Solo se permiten DNI (8 dígitos) para el registro'
            })
        
        # Formatear respuesta
        response_data = {
            'success': True,
            'dni': resultado.get('dni', dni),
            'nombre_completo': resultado.get('nombre_completo', ''),
            'direccion': resultado.get('direccion', '')
        }
        
        return JsonResponse(response_data)
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al consultar DNI: {str(e)}'})


def verificar_permisos_usuario(request):
    """
    Vista auxiliar para verificar los permisos de un usuario
    Útil para debugging
    """
    idusuario = request.session.get('idusuario')
    
    if not idusuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        usuario = Usuario.objects.get(idusuario=idusuario)
        
        # Obtener permisos del tipo de usuario
        permisos = Detalletipousuarioxmodulos.objects.filter(
            idtipousuario=usuario.idtipousuario
        ).select_related('idmodulo')
        
        modulos_permitidos = [
            {
                'id': p.idmodulo.idmodulo,
                'nombre': p.idmodulo.nombremodulo,
                'url': p.idmodulo.url,
                'logo': p.idmodulo.logo,
                'es_padre': p.idmodulo.idmodulo_padre is None
            }
            for p in permisos
        ]
        
        return JsonResponse({
            'usuario': usuario.nombrecompleto,
            'tipo_usuario': usuario.idtipousuario.nombretipousuario,
            'id_tipo_usuario': usuario.idtipousuario.idtipousuario,
            'total_permisos': len(modulos_permitidos),
            'modulos': modulos_permitidos
        })
        
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)