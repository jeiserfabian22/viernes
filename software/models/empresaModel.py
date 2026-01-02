from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator
from django.utils import timezone


class Empresa(models.Model):
    """
    Modelo para almacenar información de las empresas.
    Incluye datos tributarios, ubicación, credenciales SUNAT y campos adicionales.
    """
    
    idempresa = models.AutoField(primary_key=True, db_column='idempresa')
    
    # Información Tributaria
    ruc = models.CharField(
        max_length=11,
        unique=True,
        validators=[
            MinLengthValidator(11, message="El RUC debe tener 11 dígitos"),
            MaxLengthValidator(11, message="El RUC debe tener 11 dígitos"),
            RegexValidator(
                regex=r'^\d{11}$',
                message='El RUC debe contener solo números'
            )
        ],
        verbose_name='RUC',
        help_text='Registro Único de Contribuyentes (11 dígitos)'
    )
    
    razonsocial = models.CharField(
        max_length=255,
        verbose_name='Razón Social',
        help_text='Razón social de la empresa'
    )
    
    nombrecomercial = models.CharField(
        max_length=255,
        verbose_name='Nombre Comercial',
        help_text='Nombre comercial de la empresa'
    )
    
    # Ubicación
    direccion = models.CharField(
        max_length=255,
        verbose_name='Dirección',
        help_text='Dirección fiscal de la empresa'
    )
    
    ubigueo = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name='Ubigeo',
        help_text='Código de ubicación geográfica (ubigeo)'
    )
    
    # Información de Contacto
    telefono = models.CharField(
        max_length=25,
        null=True,
        blank=True,
        verbose_name='Teléfono',
        help_text='Teléfono de contacto'
    )
    
    # Logo
    logo = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Logo',
        help_text='Ruta del archivo de logo de la empresa'
    )
    
    # Credenciales SUNAT
    usersec = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Usuario SUNAT',
        help_text='Usuario para acceso a servicios SUNAT'
    )
    
    passwordsec = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Clave SUNAT',
        help_text='Clave de seguridad para servicios SUNAT'
    )
    
    # Configuración del Sistema
    mododev = models.IntegerField(
        default=0,
        choices=[
            (0, 'Desarrollo'),
            (1, 'Producción')
        ],
        verbose_name='Modo de Operación',
        help_text='0: Desarrollo, 1: Producción'
    )
    
    # Información Adicional de Marketing
    slogan = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Slogan',
        help_text='Slogan o frase promocional de la empresa'
    )

    pagina = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Pagina',
        help_text='Pagina web de la empresa'
    )
    
    
    publicidad = models.TextField(
        null=True,
        blank=True,
        verbose_name='Publicidad',
        help_text='Descripción de actividades o mensaje publicitario'
    )
    
    # Parámetros Tributarios
    igv = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        verbose_name='IGV (%)',
        help_text='Porcentaje de IGV aplicable'
    )
    
    icbper = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name='ICBPER',
        help_text='Impuesto al Consumo de Bolsas Plásticas'
    )
    
    isc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name='ISC (%)',
        help_text='Impuesto Selectivo al Consumo'
    )
    
    afectacion_sunat = models.IntegerField(
        default=20,
        verbose_name='Afectación General SUNAT',
        help_text='Código de afectación tributaria general'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación',
        null=True,
        blank=True
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización',
        null=True,
        blank=True
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si la empresa está activa en el sistema'
    )
    
    
    class Meta:
        db_table = 'empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombrecomercial']
    
    def __str__(self):
        return f"{self.nombrecomercial} - RUC: {self.ruc}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para realizar validaciones adicionales.
        """
        # Convertir RUC a mayúsculas y eliminar espacios
        if self.ruc:
            self.ruc = self.ruc.strip()
        
        # Normalizar textos
        if self.razonsocial:
            self.razonsocial = self.razonsocial.strip().upper()
        
        if self.nombrecomercial:
            self.nombrecomercial = self.nombrecomercial.strip()
        
        super().save(*args, **kwargs)
    
    def es_produccion(self):
        """Verifica si la empresa está en modo producción."""
        return self.mododev == 1
    
    def es_desarrollo(self):
        """Verifica si la empresa está en modo desarrollo."""
        return self.mododev == 0
    
    def get_modo_display_custom(self):
        """Retorna el modo de operación en formato legible."""
        return "PRODUCCIÓN" if self.es_produccion() else "DESARROLLO"
    
    def get_igv_decimal(self):
        """Retorna el IGV en formato decimal (ej: 0.18 para 18%)."""
        return self.igv / 100
    
    def calcular_igv(self, monto):
        """Calcula el IGV sobre un monto dado."""
        return monto * self.get_igv_decimal()
    
    def tiene_credenciales_sunat(self):
        """Verifica si tiene configuradas las credenciales SUNAT."""
        return bool(self.usersec and self.passwordsec)
    
    def tiene_logo(self):
        """Verifica si la empresa tiene logo configurado."""
        return bool(self.logo)
    
    def tiene_slogan(self):
        """Verifica si la empresa tiene slogan configurado."""
        return bool(self.slogan)
    
    def tiene_publicidad(self):
        """Verifica si la empresa tiene publicidad configurada."""
        return bool(self.publicidad)