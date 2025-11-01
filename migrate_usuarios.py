"""
Script de migración para cifrar correos y hashear contraseñas de usuarios existentes
Ejecutar: python migrate_usuarios.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'raiz.settings')
django.setup()

from software.models.UsuarioModel import Usuario
from software.utils.encryption_utils import EncryptionManager, PasswordManager

def es_correo_cifrado(correo):
    """
    Verifica si un correo ya está cifrado
    Los correos cifrados son strings base64 largos sin @ en el medio
    """
    if not correo:
        return False
    
    # Si tiene @ pero también tiene caracteres raros, probablemente esté cifrado
    # Los correos cifrados de Fernet son muy largos (>100 caracteres)
    if len(correo) > 100 and correo.count('@') <= 1:
        return True
    
    # Intentar descifrar para verificar
    try:
        descifrado = EncryptionManager.decrypt_email(correo)
        # Si se pudo descifrar y tiene formato de email, está cifrado
        if descifrado and '@' in descifrado:
            return True
    except:
        pass
    
    return False

def es_contrasena_hasheada(contrasena):
    """
    Verifica si una contraseña ya está hasheada
    Las contraseñas hasheadas con Django empiezan con 'pbkdf2_'
    """
    if not contrasena:
        return False
    return contrasena.startswith('pbkdf2_')

def migrar_usuarios():
    """
    Migra todos los usuarios cifrando correos y hasheando contraseñas
    """
    print("\n" + "="*70)
    print("INICIANDO MIGRACION DE USUARIOS")
    print("="*70 + "\n")
    
    usuarios = Usuario.objects.all()
    total = usuarios.count()
    migrados_correo = 0
    migrados_password = 0
    ya_cifrados = 0
    errores = 0
    
    print(f"Total de usuarios a revisar: {total}\n")
    
    for i, usuario in enumerate(usuarios, 1):
        print(f"[{i}/{total}] Procesando: {usuario.nombrecompleto} (ID: {usuario.idusuario})")
        
        correo_modificado = False
        password_modificado = False
        
        # ====== MIGRAR CORREO ======
        try:
            if es_correo_cifrado(usuario.correo):
                print(f"  OK - Correo ya cifrado")
                ya_cifrados += 1
            else:
                print(f"  Correo sin cifrar: {usuario.correo}")
                correo_cifrado = EncryptionManager.encrypt_email(usuario.correo)
                if correo_cifrado:
                    usuario.correo = correo_cifrado
                    correo_modificado = True
                    migrados_correo += 1
                    print(f"  EXITO - Correo cifrado")
                else:
                    print(f"  ERROR al cifrar correo")
                    errores += 1
        except Exception as e:
            print(f"  ERROR procesando correo: {str(e)}")
            errores += 1
        
        # ====== MIGRAR CONTRASEÑA ======
        try:
            if es_contrasena_hasheada(usuario.contrasena):
                print(f"  OK - Contraseña ya hasheada")
            else:
                print(f"  Contraseña sin hashear (longitud: {len(usuario.contrasena)})")
                contrasena_hasheada = PasswordManager.hash_password(usuario.contrasena)
                if contrasena_hasheada:
                    usuario.contrasena = contrasena_hasheada
                    password_modificado = True
                    migrados_password += 1
                    print(f"  EXITO - Contraseña hasheada")
                else:
                    print(f"  ERROR al hashear contraseña")
                    errores += 1
        except Exception as e:
            print(f"  ERROR procesando contraseña: {str(e)}")
            errores += 1
        
        # ====== GUARDAR CAMBIOS ======
        if correo_modificado or password_modificado:
            try:
                usuario.save()
                print(f"  Usuario guardado con exito")
            except Exception as e:
                print(f"  ERROR al guardar usuario: {str(e)}")
                errores += 1
        
        print()  # Línea en blanco
    
    # ====== RESUMEN ======
    print("="*70)
    print("RESUMEN DE MIGRACION")
    print("="*70)
    print(f"Correos cifrados: {migrados_correo}")
    print(f"Contraseñas hasheadas: {migrados_password}")
    print(f"Correos ya cifrados: {ya_cifrados}")
    print(f"Errores: {errores}")
    print(f"Total procesados: {total}")
    print("="*70)
    
    if errores == 0:
        print("\nMIGRACION COMPLETADA EXITOSAMENTE!")
    else:
        print(f"\nMigracion completada con {errores} errores. Revisa los mensajes arriba.")
    
    print("\nAhora puedes usar tu sistema con los datos cifrados de forma segura.\n")

def verificar_migracion():
    """
    Verifica que la migración se haya realizado correctamente
    """
    print("\n" + "="*70)
    print("VERIFICANDO MIGRACION")
    print("="*70 + "\n")
    
    usuarios = Usuario.objects.all()
    sin_cifrar = 0
    sin_hashear = 0
    
    for usuario in usuarios:
        if not es_correo_cifrado(usuario.correo):
            print(f"ADVERTENCIA - Usuario {usuario.nombrecompleto} - Correo SIN cifrar: {usuario.correo}")
            sin_cifrar += 1
        
        if not es_contrasena_hasheada(usuario.contrasena):
            print(f"ADVERTENCIA - Usuario {usuario.nombrecompleto} - Contraseña SIN hashear")
            sin_hashear += 1
    
    if sin_cifrar == 0 and sin_hashear == 0:
        print("EXITO - Todos los usuarios estan correctamente cifrados y hasheados!")
    else:
        print(f"\nADVERTENCIA - Encontrados:")
        print(f"   - {sin_cifrar} correos sin cifrar")
        print(f"   - {sin_hashear} contraseñas sin hashear")
    
    print("="*70 + "\n")

if __name__ == '__main__':
    import sys
    
    print("\nSCRIPT DE MIGRACION DE USUARIOS")
    print("Este script cifrara los correos y hasheara las contraseñas\n")
    
    respuesta = input("Deseas continuar con la migracion? (s/n): ").lower()
    
    if respuesta in ['s', 'si', 'y', 'yes']:
        try:
            migrar_usuarios()
            verificar_migracion()
        except Exception as e:
            print(f"\nERROR CRITICO: {str(e)}")
            print("\nVerifica que:")
            print("1. La libreria cryptography este instalada: pip install cryptography")
            print("2. La ENCRYPTION_KEY este configurada en raiz/settings.py")
            print("3. Los archivos encryption_utils.py esten en software/utils/")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("\nMigracion cancelada por el usuario.")
        sys.exit(0)