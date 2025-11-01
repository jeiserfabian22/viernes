# software/utils/encryption_utils.py
"""
Utilidades para cifrar/descifrar datos sensibles
"""
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
import base64
import os

class EncryptionManager:
    """
    Gestor de cifrado para datos sensibles como correos electrónicos
    """
    
    @staticmethod
    def get_encryption_key():
        """
        Obtiene la clave de cifrado desde settings
        Si no existe, genera una nueva (solo para desarrollo)
        """
        if hasattr(settings, 'ENCRYPTION_KEY'):
            return settings.ENCRYPTION_KEY.encode()
        
        # ADVERTENCIA: En producción, la clave debe estar en variables de entorno
        # Esta es solo para desarrollo
        key = Fernet.generate_key()
        print(f"ADVERTENCIA: Genera una clave y agrégala a settings.py: ENCRYPTION_KEY = '{key.decode()}'")
        return key
    
    @staticmethod
    def encrypt_email(email):
        """
        Cifra un correo electrónico
        Args:
            email (str): Correo electrónico en texto plano
        Returns:
            str: Correo cifrado en base64
        """
        if not email:
            return None
            
        try:
            key = EncryptionManager.get_encryption_key()
            fernet = Fernet(key)
            encrypted_email = fernet.encrypt(email.encode())
            return encrypted_email.decode()
        except Exception as e:
            print(f"Error al cifrar email: {e}")
            return None
    
    @staticmethod
    def decrypt_email(encrypted_email):
        """
        Descifra un correo electrónico
        Args:
            encrypted_email (str): Correo cifrado en base64
        Returns:
            str: Correo en texto plano
        """
        if not encrypted_email:
            return None
            
        try:
            key = EncryptionManager.get_encryption_key()
            fernet = Fernet(key)
            decrypted_email = fernet.decrypt(encrypted_email.encode())
            return decrypted_email.decode()
        except Exception as e:
            print(f"Error al descifrar email: {e}")
            return None


class PasswordManager:
    """
    Gestor de contraseñas usando el sistema de hashing de Django
    """
    
    @staticmethod
    def hash_password(plain_password):
        """
        Hashea una contraseña usando el sistema de Django
        Args:
            plain_password (str): Contraseña en texto plano
        Returns:
            str: Hash de la contraseña
        """
        if not plain_password:
            return None
        return make_password(plain_password)
    
    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        Verifica si una contraseña coincide con su hash
        Args:
            plain_password (str): Contraseña en texto plano
            hashed_password (str): Hash de la contraseña
        Returns:
            bool: True si coinciden, False si no
        """
        return check_password(plain_password, hashed_password)