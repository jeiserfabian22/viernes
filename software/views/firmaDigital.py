# software/views/firmaDigital.py

from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.contrib import messages
from datetime import datetime, timedelta
import os

from software.models.UsuarioModel import Usuario
from software.models.FirmaDigitalModel import CertificadoDigital, DocumentoFirmado, LogVerificacion
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos
from software.utils.firma_digital import FirmaDigitalManager


def firma_digital(request):
    """Vista principal del módulo de firma digital"""
    id2 = request.session.get('idtipousuario')
    idusuario = request.session.get('idusuario')
    
    if not id2:
        return HttpResponse("<h1>No tiene acceso</h1>")
    
    # Verificar si es administrador (tipo 1)
    if id2 != 1:
        return HttpResponse("<h1>Solo administradores pueden acceder a este módulo</h1>")
    
    permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
    
    # Obtener o crear certificado del usuario
    try:
        usuario = Usuario.objects.get(idusuario=idusuario)
        certificado, created = CertificadoDigital.objects.get_or_create(
            idusuario=usuario,
            defaults={
                'clave_privada': '',
                'clave_publica': '',
                'huella_digital': '',
                'estado': 0  # Inactivo hasta generar claves
            }
        )
        
        # Si no tiene claves generadas, generarlas
        if not certificado.clave_privada or created:
            private_pem, public_pem, huella = FirmaDigitalManager.generar_certificado_usuario(usuario)
            certificado.clave_privada = private_pem
            certificado.clave_publica = public_pem
            certificado.huella_digital = huella
            certificado.fecha_expiracion = datetime.now() + timedelta(days=365*2)  # 2 años
            certificado.estado = 1
            certificado.save()
            
            print(f"✅ Certificado digital creado para {usuario.nombrecompleto}")
        
    except Exception as e:
        print(f"❌ Error al obtener/crear certificado: {e}")
        certificado = None
    
    # Obtener documentos firmados por el usuario
    documentos_firmados = DocumentoFirmado.objects.filter(
        usuario_firmante=usuario,
        estado=1
    ).select_related('certificado').order_by('-fecha_firma')[:20]
    
    data = {
        'permisos': permisos,
        'certificado': certificado,
        'documentos_firmados': documentos_firmados,
        'usuario': usuario
    }
    
    return render(request, 'firma_digital/firma_digital.html', data)


@csrf_exempt
def firmar_documento(request):
    """Procesar firma digital de documento"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Validar sesión
        idusuario = request.session.get('idusuario')
        if not idusuario:
            return JsonResponse({'error': 'No autenticado'}, status=401)
        
        usuario = get_object_or_404(Usuario, idusuario=idusuario)
        
        # Validar que sea administrador
        try:
            if usuario.idtipousuario.idtipousuario != 1:
                return JsonResponse({
                    'error': 'Solo los administradores pueden firmar documentos'
                }, status=403)
        except AttributeError:
            return JsonResponse({
                'error': 'Usuario sin tipo asignado'
            }, status=403)
        
        # Validar que tenga certificado
        try:
            certificado = CertificadoDigital.objects.get(idusuario=usuario, estado=1)
        except CertificadoDigital.DoesNotExist:
            return JsonResponse({
                'error': 'No tiene un certificado digital activo'
            }, status=400)
        
        # Obtener datos del formulario
        archivo_original = request.FILES.get('documento')
        firma_canvas = request.POST.get('firma_canvas')
        
        if not archivo_original or not firma_canvas:
            return JsonResponse({
                'error': 'Debe proporcionar documento y firma'
            }, status=400)
        
        # Validar tipo de archivo
        nombre_archivo = archivo_original.name.lower()
        if nombre_archivo.endswith('.pdf'):
            tipo_doc = 'PDF'
        elif nombre_archivo.endswith('.docx'):
            tipo_doc = 'DOCX'
        else:
            return JsonResponse({
                'error': 'Solo se permiten archivos PDF o DOCX'
            }, status=400)
        
        print(f"\n{'='*60}")
        print(f"🔐 INICIANDO PROCESO DE FIRMA DIGITAL")
        print(f"{'='*60}")
        print(f"📄 Documento: {archivo_original.name}")
        print(f"👤 Firmante: {usuario.nombrecompleto}")
        print(f"📋 Tipo: {tipo_doc}")
        
        # ⭐ PASO 1: Calcular hash del documento ORIGINAL (sin firma visual)
        from software.utils.firma_digital import FirmaDigitalManager
        
        hash_original = FirmaDigitalManager.calcular_hash_archivo(archivo_original)
        print(f"🔑 Hash documento original: {hash_original[:32]}...")
        
        # ⭐ PASO 2: Firmar el hash con la clave privada
        firma_digital = FirmaDigitalManager.firmar_hash(
            hash_original,
            certificado.clave_privada
        )
        print(f"✍️ Firma digital generada: {firma_digital[:32]}...")
        
        # ⭐ PASO 3: Agregar firma visual al documento
        metadata = {
            'usuario': usuario.nombrecompleto,
            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'huella': certificado.huella_digital
        }
        
        if tipo_doc == 'PDF':
            archivo_con_firma = FirmaDigitalManager.agregar_firma_visual_pdf(
                archivo_original,
                firma_canvas,
                metadata
            )
        else:  # DOCX
            archivo_con_firma = FirmaDigitalManager.agregar_firma_visual_docx(
                archivo_original,
                firma_canvas,
                metadata
            )
        
        print(f"🎨 Firma visual agregada al documento")
        
        # ⭐ PASO 4: Calcular hash del archivo YA firmado (con firma visual)
        hash_firmado = FirmaDigitalManager.calcular_hash_archivo(archivo_con_firma)
        print(f"🔑 Hash archivo firmado: {hash_firmado[:32]}...")
        
        # ⭐ PASO 5: Guardar archivos
        # Archivo original
        nombre_original = archivo_original.name
        archivo_original.seek(0)
        archivo_original_django = ContentFile(archivo_original.read(), name=nombre_original)
        
        # Archivo firmado
        extension = '.pdf' if tipo_doc == 'PDF' else '.docx'
        nombre_firmado = f"FIRMADO_{nombre_original.replace(extension, '')}{extension}"
        archivo_con_firma.seek(0)
        archivo_firmado_django = ContentFile(archivo_con_firma.read(), name=nombre_firmado)
        
        # ⭐ PASO 6: Crear registro en base de datos
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        documento_firmado = DocumentoFirmado.objects.create(
            usuario_firmante=usuario,
            certificado=certificado,
            nombre_original=nombre_original,
            archivo_original=archivo_original_django,
            archivo_firmado=archivo_firmado_django,
            firma_visual=firma_canvas,
            hash_documento=hash_original,  # ⭐ Hash del documento ORIGINAL
            hash_archivo_firmado=hash_firmado,  # ⭐ Hash del archivo YA firmado
            firma_digital=firma_digital,
            ip_firmante=ip,
            tipo_documento=tipo_doc
        )
        
        # Generar código de verificación
        codigo_verificacion = FirmaDigitalManager.generar_codigo_verificacion(
            documento_firmado.iddocumento
        )
        
        print(f"✅ Documento firmado exitosamente")
        print(f"📝 ID: {documento_firmado.iddocumento}")
        print(f"🔐 Código verificación: {codigo_verificacion}")
        print(f"{'='*60}\n")
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Documento firmado digitalmente',
            'codigo_verificacion': codigo_verificacion,
            'iddocumento': documento_firmado.iddocumento
        })
        
    except Exception as e:
        print(f"❌ Error al firmar documento: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Error al firmar documento: {str(e)}'
        }, status=500)


def descargar_documento_firmado(request, iddocumento):
    """Descargar documento firmado"""
    try:
        documento = get_object_or_404(DocumentoFirmado, iddocumento=iddocumento, estado=1)
        
        # Verificar que el usuario sea el firmante o admin
        idusuario = request.session.get('idusuario')
        if documento.usuario_firmante.idusuario != idusuario:
            return HttpResponse("<h1>No tiene permiso para descargar este documento</h1>")
        
        # Abrir archivo firmado
        archivo = documento.archivo_firmado.open('rb')
        
        # Determinar el content type
        if documento.tipo_documento == 'PDF':
            content_type = 'application/pdf'
        else:
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        response = FileResponse(
            archivo,
            content_type=content_type
        )
        
        # Nombre del archivo para descarga
        nombre_archivo = documento.archivo_firmado.name.split('/')[-1]
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        print(f"📥 Descargando: {documento.nombre_original}")
        print(f"   Archivo: {nombre_archivo}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error al descargar: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"<h1>Error al descargar documento: {str(e)}</h1>")


def verificar_documento(request):
    """Vista pública para verificar documentos firmados"""
    if request.method == 'GET':
        return render(request, 'firma_digital/verificar_documento.html')
    
    elif request.method == 'POST':
        try:
            archivo = request.FILES.get('documento_verificar')
            
            if not archivo:
                return JsonResponse({
                    'success': False,
                    'error': 'Debe proporcionar un documento'
                }, status=400)
            
            print(f"\n{'='*60}")
            print(f"🔍 VERIFICANDO DOCUMENTO")
            print(f"{'='*60}")
            print(f"📄 Archivo: {archivo.name}")
            print(f"📦 Tamaño: {archivo.size} bytes")
            
            # ⭐ PASO 1: Calcular hash del archivo subido
            from software.utils.firma_digital import FirmaDigitalManager
            hash_subido = FirmaDigitalManager.calcular_hash_archivo(archivo)
            print(f"🔑 Hash calculado: {hash_subido[:32]}...")
            
            # ⭐ PASO 2: Buscar documento por hash del ARCHIVO FIRMADO
            documento = DocumentoFirmado.objects.filter(
                hash_archivo_firmado=hash_subido,
                estado=1
            ).first()
            
            if not documento:
                print("⚠️ Documento no encontrado por hash del archivo firmado")
                
                # ⭐ PASO 2B: Buscar por NOMBRE para detectar si fue modificado
                import re
                
                # Limpiar el nombre del archivo
                nombre_limpio = archivo.name
                
                # Quitar prefijos comunes
                for prefijo in ['MODIFICADO_', 'FIRMADO_', 'firmado_', 'modificado_']:
                    nombre_limpio = nombre_limpio.replace(prefijo, '')
                
                # Quitar números entre paréntesis (ej: " (1)", " (2)")
                nombre_limpio = re.sub(r'\s*\(\d+\)', '', nombre_limpio)
                
                # ⭐ NORMALIZAR: Reemplazar guiones bajos por espacios
                nombre_limpio = nombre_limpio.replace('_', ' ')
                
                print(f"🔍 Buscando por nombre: {nombre_limpio}")
                
                # Extraer solo el nombre sin extensión
                nombre_sin_extension = nombre_limpio.rsplit('.', 1)[0].strip()
                
                print(f"   Nombre sin extensión: '{nombre_sin_extension}'")
                
                # ⭐ Buscar de manera más flexible
                documento_original = None
                
                # Primero: búsqueda exacta (sin case sensitive)
                documento_original = DocumentoFirmado.objects.filter(
                    nombre_original__iexact=nombre_limpio,
                    estado=1
                ).order_by('-fecha_firma').first()
                
                # Segundo: búsqueda por nombre sin extensión
                if not documento_original:
                    documento_original = DocumentoFirmado.objects.filter(
                        nombre_original__icontains=nombre_sin_extension,
                        estado=1
                    ).order_by('-fecha_firma').first()
                
                # Tercero: búsqueda más flexible (reemplazando espacios y guiones)
                if not documento_original:
                    # Normalizar el nombre de búsqueda: quitar espacios, guiones, etc.
                    nombre_normalizado = re.sub(r'[\s_-]+', '', nombre_sin_extension.lower())
                    
                    print(f"   Buscando normalizado: '{nombre_normalizado}'")
                    
                    # Buscar todos los documentos y comparar normalizados
                    for doc in DocumentoFirmado.objects.filter(estado=1).order_by('-fecha_firma'):
                        nombre_doc_normalizado = re.sub(r'[\s_-]+', '', doc.nombre_original.rsplit('.', 1)[0].lower())
                        if nombre_normalizado == nombre_doc_normalizado:
                            documento_original = doc
                            print(f"   ✅ Encontrado por nombre normalizado: {doc.nombre_original}")
                            break
                
                if documento_original:
                    # ⭐ DOCUMENTO ENCONTRADO PERO HASH NO COINCIDE = MODIFICADO
                    print(f"❌ DOCUMENTO MODIFICADO DETECTADO")
                    print(f"   Documento original: {documento_original.nombre_original}")
                    print(f"   Hash original firmado: {documento_original.hash_archivo_firmado[:32]}...")
                    print(f"   Hash archivo subido:   {hash_subido[:32]}...")
                    print(f"{'='*60}\n")
                    
                    # Registrar verificación fallida
                    LogVerificacion.objects.create(
                        documento=documento_original,
                        ip_verificador=request.META.get('REMOTE_ADDR'),
                        resultado=False
                    )
                    
                    # Actualizar estado del documento
                    documento_original.verificado = False
                    documento_original.fecha_verificacion = datetime.now()
                    documento_original.save()
                    
                    return JsonResponse({
                        'success': True,
                        'valido': False,
                        'mensaje': '❌ DOCUMENTO MODIFICADO',
                        'detalles': {
                            'firmante': documento_original.usuario_firmante.nombrecompleto,
                            'fecha_firma': documento_original.fecha_firma.strftime('%d/%m/%Y %H:%M:%S'),
                            'advertencia': 'El contenido del documento ha sido alterado después de la firma digital. El hash SHA-256 no coincide con el original.'
                        }
                    })
                else:
                    # No se encontró ni por hash ni por nombre
                    print("❌ Documento no encontrado en el sistema")
                    print(f"\n📋 Documentos en el sistema:")
                    for d in DocumentoFirmado.objects.filter(estado=1).order_by('-fecha_firma')[:5]:
                        print(f"   • {d.nombre_original}")
                        print(f"     Hash firmado: {d.hash_archivo_firmado[:32]}...")
                    print(f"{'='*60}\n")
                    
                    return JsonResponse({
                        'success': False,
                        'error': 'Documento no encontrado',
                        'mensaje': 'Este archivo no corresponde a ningún documento firmado en el sistema. Asegúrese de subir un documento que haya sido firmado digitalmente por MotoVentas.'
                    }, status=404)
            
            # ⭐ PASO 3: Documento encontrado por hash - Verificar firma criptográfica
            print(f"✅ Documento encontrado: {documento.nombre_original}")
            print(f"👤 Firmante: {documento.usuario_firmante.nombrecompleto}")
            
            firma_valida = FirmaDigitalManager.verificar_firma(
                documento.hash_documento,  # Hash del documento ORIGINAL
                documento.firma_digital,
                documento.certificado.clave_publica
            )
            
            # ⭐ PASO 4: Verificar que el archivo no fue modificado
            archivo_integro = (hash_subido == documento.hash_archivo_firmado)
            
            print(f"🔐 Firma criptográfica válida: {firma_valida}")
            print(f"📄 Archivo íntegro: {archivo_integro}")
            print(f"   Hash original doc: {documento.hash_documento[:32]}...")
            print(f"   Hash firmado BD:   {documento.hash_archivo_firmado[:32]}...")
            print(f"   Hash archivo subido: {hash_subido[:32]}...")
            
            # ⭐ PASO 5: Registrar verificación
            LogVerificacion.objects.create(
                documento=documento,
                ip_verificador=request.META.get('REMOTE_ADDR'),
                resultado=firma_valida and archivo_integro
            )
            
            # ⭐ PASO 6: Actualizar estado del documento
            documento.verificado = firma_valida and archivo_integro
            documento.fecha_verificacion = datetime.now()
            documento.save()
            
            # ⭐ PASO 7: Responder
            if firma_valida and archivo_integro:
                print(f"✅ VERIFICACIÓN EXITOSA - Documento válido")
                print(f"{'='*60}\n")
                
                return JsonResponse({
                    'success': True,
                    'valido': True,
                    'mensaje': '✅ DOCUMENTO VÁLIDO',
                    'detalles': {
                        'firmante': documento.usuario_firmante.nombrecompleto,
                        'fecha_firma': documento.fecha_firma.strftime('%d/%m/%Y %H:%M:%S'),
                        'certificado': documento.certificado.huella_digital[:24],
                        'tipo': documento.tipo_documento,
                        'hash': documento.hash_documento[:16]
                    }
                })
            else:
                print(f"❌ VERIFICACIÓN FALLIDA - Documento modificado")
                print(f"{'='*60}\n")
                
                return JsonResponse({
                    'success': True,
                    'valido': False,
                    'mensaje': '❌ DOCUMENTO MODIFICADO',
                    'detalles': {
                        'firmante': documento.usuario_firmante.nombrecompleto,
                        'fecha_firma': documento.fecha_firma.strftime('%d/%m/%Y %H:%M:%S'),
                        'advertencia': 'El documento ha sido modificado después de ser firmado. La firma digital no es válida.'
                    }
                })
            
        except Exception as e:
            print(f"❌ Error en verificación: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error al verificar documento: {str(e)}'
            }, status=500)