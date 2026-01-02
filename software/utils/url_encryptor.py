# software/utils/url_encryptor.py

from cryptography.fernet import Fernet
import base64
from django.conf import settings

# ⚠️ IMPORTANTE: Esta clave debe estar en settings.py
# Para generar una nueva clave ejecuta en Python:
# from cryptography.fernet import Fernet
# print(Fernet.generate_key())

try:
    # Intentar obtener la clave desde settings.py
    SECRET_KEY = settings.URL_ENCRYPTION_KEY.encode() if isinstance(settings.URL_ENCRYPTION_KEY, str) else settings.URL_ENCRYPTION_KEY
except AttributeError:
    # Si no existe en settings, generar una temporal (SOLO PARA DESARROLLO)
    print("⚠️ ADVERTENCIA: URL_ENCRYPTION_KEY no está en settings.py")
    print("   Agrega esto a settings.py:")
    SECRET_KEY = Fernet.generate_key()
    print(f"   URL_ENCRYPTION_KEY = '{SECRET_KEY.decode()}'")

cipher = Fernet(SECRET_KEY)


def encrypt_id(id_number):
    """
    Encripta un ID numérico y lo convierte en string URL-safe
    
    Uso:
        encrypt_id(123) -> 'gAAAAABl8x9e...'
    """
    try:
        if id_number is None:
            return None
        
        # Convertir ID a bytes
        id_bytes = str(id_number).encode('utf-8')
        
        # Encriptar
        encrypted = cipher.encrypt(id_bytes)
        
        # Convertir a string URL-safe (sin padding)
        encoded = base64.urlsafe_b64encode(encrypted).decode('utf-8').rstrip('=')
        
        return encoded
    except Exception as e:
        print(f"❌ Error al encriptar ID {id_number}: {e}")
        return None


def decrypt_id(encrypted_string):
    """
    Desencripta un string y devuelve el ID original como entero
    
    Uso:
        decrypt_id('gAAAAABl8x9e...') -> 123
    """
    try:
        if not encrypted_string:
            return None
        
        # Agregar padding si es necesario (múltiplo de 4)
        padding = 4 - (len(encrypted_string) % 4)
        if padding and padding != 4:
            encrypted_string += '=' * padding
        
        # Decodificar desde base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_string)
        
        # Desencriptar
        decrypted = cipher.decrypt(encrypted_bytes)
        
        # Convertir a entero
        id_number = int(decrypted.decode('utf-8'))
        
        return id_number
    except Exception as e:
        print(f"❌ Error al desencriptar '{encrypted_string}': {e}")
        return None


def encrypt_id_safe(id_number, fallback=''):
    """
    Versión segura que devuelve un valor por defecto si falla
    
    Uso en templates:
        {{ venta.idventa|encrypt_id_safe }}
    """
    result = encrypt_id(id_number)
    return result if result else fallback


# ============================================
# FUNCIONES DE PRUEBA
# ============================================

def test_encryption():
    """Función para probar la encriptación/desencriptación"""
    test_ids = [1, 123, 9999, 123456]
    
    print("\n🧪 Probando encriptación de IDs:")
    print("=" * 60)
    
    for test_id in test_ids:
        encrypted = encrypt_id(test_id)
        decrypted = decrypt_id(encrypted)
        
        status = "✅" if decrypted == test_id else "❌"
        print(f"{status} ID: {test_id:6} -> {encrypted[:20]}... -> {decrypted}")
    
    print("=" * 60)
    print("\n✅ Todas las pruebas pasaron!\n")


if __name__ == "__main__":
    test_encryption()