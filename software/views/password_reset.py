# software/views/password_reset.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from software.models.passwordResetModel import PasswordResetToken 
from software.models.UsuarioModel import Usuario 
from software.utils.encryption_utils import EncryptionManager, PasswordManager

def solicitar_recuperacion(request):
    """
    Muestra el formulario para solicitar recuperación de contraseña
    """
    if request.method == 'GET':
        return render(request, 'password_reset/solicitar.html')
    
    elif request.method == 'POST':
        correo_ingresado = request.POST.get('correo', '').strip()
        
        if not correo_ingresado:
            return JsonResponse({
                'error': 'Por favor ingrese su correo electrónico'
            }, status=400)
        
        try:
            # ⭐ NUEVO: Buscar usuario descifrando correos
            usuarios_todos = Usuario.objects.filter(estado=1)
            usuario_encontrado = None
            
            for usuario in usuarios_todos:
                try:
                    correo_descifrado = EncryptionManager.decrypt_email(usuario.correo)
                    if correo_descifrado == correo_ingresado:
                        usuario_encontrado = usuario
                        break
                except Exception as e:
                    print(f"Error al descifrar correo del usuario {usuario.idusuario}: {e}")
                    continue
            
            if usuario_encontrado:
                # Invalidar tokens anteriores
                PasswordResetToken.objects.filter(
                    usuario=usuario_encontrado,
                    usado=False
                ).update(usado=True)
                
                # Crear nuevo token
                reset_token = PasswordResetToken.objects.create(usuario=usuario_encontrado)
                
                # Construir URL de recuperación
                reset_url = request.build_absolute_uri(
                    reverse('restablecer_contrasena', args=[reset_token.token])
                )
                
                # ⭐ Descifrar correo para envío
                correo_descifrado = EncryptionManager.decrypt_email(usuario_encontrado.correo)
                
                # Enviar correo
                asunto = 'Recuperación de Contraseña - MotoVentas'
                mensaje = f"""
Hola {usuario_encontrado.nombrecompleto},

Has solicitado restablecer tu contraseña en MotoVentas.

Para crear una nueva contraseña, haz clic en el siguiente enlace:
{reset_url}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Saludos,
Equipo MotoVentas
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [correo_descifrado],  # ✅ Usar correo descifrado
                    fail_silently=False,
                )
                
                print(f"✅ Correo de recuperación enviado a: {correo_descifrado}")
            
            # Por seguridad, siempre devolvemos el mismo mensaje
            # (no revelamos si el correo existe o no)
            return JsonResponse({
                'success': True,
                'mensaje': 'Si el correo está registrado, recibirás las instrucciones para restablecer tu contraseña'
            })
            
        except Exception as e:
            print(f"Error al enviar correo: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': 'Error al enviar el correo. Intenta nuevamente.'
            }, status=500)

def restablecer_contrasena(request, token):
    """
    Muestra el formulario para restablecer contraseña
    """
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            return render(request, 'password_reset/token_invalido.html', {
                'mensaje': 'Este enlace ha expirado o ya fue utilizado'
            })
        
        if request.method == 'GET':
            # ⭐ Descifrar correo para mostrar
            correo_descifrado = EncryptionManager.decrypt_email(reset_token.usuario.correo)
            
            return render(request, 'password_reset/restablecer.html', {
                'token': token,
                'usuario': reset_token.usuario,
                'correo': correo_descifrado  # Mostrar correo descifrado
            })
        
        elif request.method == 'POST':
            nueva_contrasena = request.POST.get('nueva_contrasena')
            confirmar_contrasena = request.POST.get('confirmar_contrasena')
            
            if not nueva_contrasena or not confirmar_contrasena:
                return JsonResponse({
                    'error': 'Todos los campos son obligatorios'
                }, status=400)
            
            if nueva_contrasena != confirmar_contrasena:
                return JsonResponse({
                    'error': 'Las contraseñas no coinciden'
                }, status=400)
            
            if len(nueva_contrasena) < 6:
                return JsonResponse({
                    'error': 'La contraseña debe tener al menos 6 caracteres'
                }, status=400)
            
            # ⭐ IMPORTANTE: Hashear la nueva contraseña
            usuario = reset_token.usuario
            usuario.contrasena = PasswordManager.hash_password(nueva_contrasena)
            usuario.save()
            
            # Marcar token como usado
            reset_token.usado = True
            reset_token.save()
            
            print(f"✅ Contraseña actualizada para: {usuario.nombrecompleto}")
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Contraseña actualizada correctamente. Ya puedes iniciar sesión.'
            })
    
    except PasswordResetToken.DoesNotExist:
        return render(request, 'password_reset/token_invalido.html', {
            'mensaje': 'Enlace inválido'
        })
    except Exception as e:
        print(f"Error al restablecer contraseña: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': 'Error al actualizar la contraseña'
        }, status=500)