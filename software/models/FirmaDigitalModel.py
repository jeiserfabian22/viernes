# software/models/FirmaDigitalModel.py

from django.db import models
from software.models.UsuarioModel import Usuario
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import hashlib
import base64
from datetime import datetime


class CertificadoDigital(models.Model):
    """Certificado digital único por usuario administrador"""
    
    idusuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        primary_key=True,
        db_column='idusuario',
        related_name='certificado_digital'
    )
    clave_privada = models.TextField(help_text="Clave privada encriptada (PEM)")
    clave_publica = models.TextField(help_text="Clave pública (PEM)")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    huella_digital = models.CharField(max_length=64, unique=True)
    estado = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'certificados_digitales'
        verbose_name = 'Certificado Digital'
        verbose_name_plural = 'Certificados Digitales'
    
    def __str__(self):
        return f"Certificado de {self.idusuario.nombrecompleto}"
    
    @staticmethod
    def generar_par_claves():
        """Genera un par de claves RSA de 2048 bits"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Serializar clave privada
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serializar clave pública
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')
    
    @staticmethod
    def calcular_huella_digital(clave_publica_pem):
        """Calcula SHA-256 de la clave pública"""
        return hashlib.sha256(clave_publica_pem.encode()).hexdigest()


class DocumentoFirmado(models.Model):
    """Registro de documentos firmados digitalmente"""
    
    iddocumento = models.AutoField(primary_key=True)
    usuario_firmante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idusuario',
        related_name='documentos_firmados'
    )
    # ⭐ CORREGIDO
    certificado = models.ForeignKey(
        CertificadoDigital,
        on_delete=models.CASCADE,
        db_column='certificado_idusuario',
        to_field='idusuario',
        related_name='documentos'
    )
    
    # Archivos
    nombre_original = models.CharField(max_length=255)
    archivo_original = models.FileField(upload_to='documentos/originales/')
    archivo_firmado = models.FileField(upload_to='documentos/firmados/')
    
    # Firma visual
    firma_visual = models.TextField(help_text="Firma en base64 (canvas)")
    
    # Criptografía
    hash_documento = models.CharField(max_length=64, help_text="SHA-256 del documento original")
    hash_archivo_firmado = models.CharField(max_length=64, help_text="SHA-256 del archivo YA firmado", default='')
    firma_digital = models.TextField(help_text="Hash encriptado con clave privada")
    
    # Metadatos
    fecha_firma = models.DateTimeField(auto_now_add=True)
    ip_firmante = models.GenericIPAddressField(null=True)
    tipo_documento = models.CharField(max_length=10)
    
    # Verificación
    verificado = models.BooleanField(default=True)
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    
    estado = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'documentos_firmados'
        verbose_name = 'Documento Firmado'
        verbose_name_plural = 'Documentos Firmados'
        ordering = ['-fecha_firma']
    
    def __str__(self):
        return f"{self.nombre_original} - Firmado por {self.usuario_firmante.nombrecompleto}"


    @staticmethod
    def calcular_hash_archivo(archivo):
        """Calcula SHA-256 de un archivo"""
        sha256 = hashlib.sha256()
        archivo.seek(0)
        for chunk in iter(lambda: archivo.read(4096), b''):
            sha256.update(chunk)
        archivo.seek(0)
        return sha256.hexdigest()
    
    def firmar_hash(self, clave_privada_pem):
        """Firma el hash del documento con la clave privada"""
        from cryptography.hazmat.primitives import serialization
        
        # Cargar clave privada
        private_key = serialization.load_pem_private_key(
            clave_privada_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Firmar el hash
        signature = private_key.sign(
            self.hash_documento.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Convertir a base64 para almacenar
        return base64.b64encode(signature).decode('utf-8')
    
    def verificar_firma(self):
        """Verifica la integridad del documento firmado"""
        from cryptography.hazmat.primitives import serialization
        from cryptography.exceptions import InvalidSignature
        
        try:
            # Cargar clave pública
            public_key = serialization.load_pem_public_key(
                self.certificado.clave_publica.encode(),
                backend=default_backend()
            )
            
            # Decodificar firma
            signature = base64.b64decode(self.firma_digital)
            
            # Verificar firma
            public_key.verify(
                signature,
                self.hash_documento.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Error en verificación: {e}")
            return False


class LogVerificacion(models.Model):
    """Log de verificaciones de documentos"""
    
    idlog = models.AutoField(primary_key=True)
    documento = models.ForeignKey(
        DocumentoFirmado,
        on_delete=models.CASCADE,
        db_column='iddocumento',  # ⭐ CORREGIDO
        related_name='verificaciones'
    )
    fecha_verificacion = models.DateTimeField(auto_now_add=True)
    ip_verificador = models.GenericIPAddressField(null=True)
    resultado = models.BooleanField()
    
    class Meta:
        db_table = 'log_verificaciones'
        verbose_name = 'Log de Verificación'
        verbose_name_plural = 'Logs de Verificación'