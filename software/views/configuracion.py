from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from software.models.empresaModel import Empresa
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
import os


def configuracion(request):
    """
    Vista principal de configuración de empresa.
    Muestra la información de todas las empresas registradas.
    """
    id_tipo_usuario = request.session.get('idtipousuario')
    
    if not id_tipo_usuario:
        return render(request, 'error.html', {
            'mensaje': 'No tiene acceso. Por favor, inicie sesión.'
        })
    
    try:
        # Obtener permisos del usuario
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id_tipo_usuario)
        
        # Obtener datos de empresa
        empresas = Empresa.objects.all()
        
        # Obtener modo de desarrollo de la primera empresa
        modo = empresas.first().mododev if empresas.exists() else 0
        
        context = {
            'empresas': empresas,
            'modo': modo,
            'permisos': permisos
        }
        
        return render(request, 'configuracion/configuracion.html', context)
    
    except Exception as e:
        messages.error(request, f'Error al cargar la configuración: {str(e)}')
        return render(request, 'configuracion/configuracion.html', {
            'empresas': [],
            'modo': 0,
            'permisos': []
        })


def editarEmpresa(request):
    """
    Edita la información de una empresa.
    Método: POST
    Incluye manejo de archivo de logo, slogan y publicidad.
    """
    if request.method != 'POST':
        messages.warning(request, 'Método no permitido')
        return redirect('configuracion')
    
    try:
        # Obtener datos del formulario
        idempresa = request.POST.get('idempresa')
        ruc = request.POST.get('ruc', '').strip()
        razon_social = request.POST.get('razonSocial', '').strip()
        nombre_comercial = request.POST.get('nombreComercia', '').strip()
        direccion = request.POST.get('Direccion', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        user_sec = request.POST.get('user', '').strip()
        password_sec = request.POST.get('password', '').strip()
        ubigueo_value = request.POST.get('ubigueo', '').strip()
        
        # Nuevos campos
        slogan = request.POST.get('slogan', '').strip()
        pagina = request.POST.get('pagina', '').strip()
        publicidad = request.POST.get('publicidad', '').strip()
        
        # Validaciones básicas
        if not idempresa:
            messages.error(request, 'ID de empresa no proporcionado')
            return redirect('configuracion')
        
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            messages.error(request, 'El RUC debe tener 11 dígitos numéricos')
            return redirect('configuracion')
        
        if not razon_social:
            messages.error(request, 'La razón social es obligatoria')
            return redirect('configuracion')
        
        if not nombre_comercial:
            messages.error(request, 'El nombre comercial es obligatorio')
            return redirect('configuracion')
        
        if not direccion:
            messages.error(request, 'La dirección es obligatoria')
            return redirect('configuracion')
        
        # Usar transacción para asegurar integridad de datos
        with transaction.atomic():
            # Obtener la empresa
            empresa = get_object_or_404(Empresa, idempresa=idempresa)
            
            # Actualizar campos básicos
            empresa.ruc = ruc
            empresa.razonsocial = razon_social.upper()
            empresa.nombrecomercial = nombre_comercial
            empresa.direccion = direccion
            empresa.telefono = telefono if telefono else None
            empresa.usersec = user_sec if user_sec else None
            empresa.passwordsec = password_sec if password_sec else None
            empresa.ubigueo = ubigueo_value if ubigueo_value else None
            
            # Actualizar campos nuevos
            empresa.slogan = slogan if slogan else None
            empresa.pagina = pagina if pagina else None
            empresa.publicidad = publicidad if publicidad else None
            
            # Manejo de archivo de logo
            if 'logo' in request.FILES:
                logo_file = request.FILES['logo']
                
                # Validar tipo de archivo
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                file_extension = os.path.splitext(logo_file.name)[1].lower()
                
                if file_extension not in allowed_extensions:
                    messages.error(request, 'Formato de imagen no permitido. Use: JPG, PNG, GIF o WEBP')
                    return redirect('configuracion')
                
                # Validar tamaño (2MB máximo)
                if logo_file.size > 2 * 1024 * 1024:  # 2MB en bytes
                    messages.error(request, 'El archivo es demasiado grande. Tamaño máximo: 2MB')
                    return redirect('configuracion')
                
                # Crear carpeta si no existe
                logo_dir = 'media/logos'
                os.makedirs(logo_dir, exist_ok=True)
                
                # Guardar archivo
                fs = FileSystemStorage(location=logo_dir)
                filename = fs.save(f'logo_{ruc}{file_extension}', logo_file)
                empresa.logo = f'logos/{filename}'
            
            # Guardar cambios
            empresa.save()
            
            messages.success(request, 'Información de empresa actualizada correctamente')
            
            # Si es AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'message': 'Información de empresa actualizada correctamente'
                })
    
    except Empresa.DoesNotExist:
        messages.error(request, 'Empresa no encontrada')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': False,
                'error': 'Empresa no encontrada'
            }, status=404)
    
    except Exception as e:
        messages.error(request, f'Error al actualizar la empresa: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': False,
                'error': str(e)
            }, status=500)
    
    return redirect('configuracion')


# ⭐ ACTUALIZADO: Usar eid
def produccion(request, eid):
    """
    Cambia el modo de la empresa a producción - CON ID ENCRIPTADO
    """
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        idempresa = decrypt_id(eid)
        if not idempresa:
            messages.error(request, 'URL inválida')
            return redirect('configuracion')
        
        empresa = get_object_or_404(Empresa, idempresa=idempresa)
        empresa.mododev = 1  # 1 = Producción
        empresa.save()
        
        print(f"✅ Empresa '{empresa.nombrecomercial}' cambiada a modo PRODUCCIÓN (ID: {idempresa})")
        
        messages.success(request, f'La empresa "{empresa.nombrecomercial}" está ahora en modo PRODUCCIÓN')
    
    except Empresa.DoesNotExist:
        messages.error(request, 'Empresa no encontrada')
    
    except Exception as e:
        print(f"❌ Error al cambiar modo: {str(e)}")
        messages.error(request, f'Error al cambiar modo: {str(e)}')
    
    return redirect('configuracion')


# ⭐ ACTUALIZADO: Usar eid
def desarrollo(request, eid):
    """
    Cambia el modo de la empresa a desarrollo - CON ID ENCRIPTADO
    """
    try:
        from software.utils.url_encryptor import decrypt_id
        
        # ⭐ DESENCRIPTAR ID
        idempresa = decrypt_id(eid)
        if not idempresa:
            messages.error(request, 'URL inválida')
            return redirect('configuracion')
        
        empresa = get_object_or_404(Empresa, idempresa=idempresa)
        empresa.mododev = 0  # 0 = Desarrollo
        empresa.save()
        
        print(f"⚠️ Empresa '{empresa.nombrecomercial}' cambiada a modo DESARROLLO (ID: {idempresa})")
        
        messages.success(request, f'La empresa "{empresa.nombrecomercial}" está ahora en modo DESARROLLO')
    
    except Empresa.DoesNotExist:
        messages.error(request, 'Empresa no encontrada')
    
    except Exception as e:
        print(f"❌ Error al cambiar modo: {str(e)}")
        messages.error(request, f'Error al cambiar modo: {str(e)}')
    
    return redirect('configuracion')


# Funciones auxiliares adicionales

def validar_ruc(ruc):
    """
    Valida el formato del RUC peruano.
    Retorna True si es válido, False en caso contrario.
    """
    if not ruc or len(ruc) != 11:
        return False
    
    if not ruc.isdigit():
        return False
    
    # El primer dígito debe ser 1 (persona natural) o 2 (persona jurídica)
    primer_digito = ruc[0]
    if primer_digito not in ['1', '2']:
        return False
    
    return True


def obtener_datos_empresa_por_ruc(request):
    """
    Endpoint AJAX para obtener datos de una empresa por RUC.
    Útil para autocompletar datos desde SUNAT API (implementación futura).
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    ruc = request.GET.get('ruc', '').strip()
    
    if not validar_ruc(ruc):
        return JsonResponse({
            'ok': False,
            'error': 'RUC inválido'
        }, status=400)
    
    try:
        # Buscar en base de datos local
        empresa = Empresa.objects.filter(ruc=ruc).first()
        
        if empresa:
            return JsonResponse({
                'ok': True,
                'exists': True,
                'data': {
                    'ruc': empresa.ruc,
                    'razon_social': empresa.razonsocial,
                    'nombre_comercial': empresa.nombrecomercial,
                    'direccion': empresa.direccion,
                    'slogan': empresa.slogan,
                    'publicidad': empresa.publicidad,
                }
            })
        else:
            # Aquí podrías integrar con API de SUNAT en el futuro
            return JsonResponse({
                'ok': True,
                'exists': False,
                'message': 'RUC no encontrado en la base de datos'
            })
    
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)