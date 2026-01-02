# software/models/twoFactorModel.py
from django.db import models
from software.models.UsuarioModel import Usuario
import random
from django.utils import timezone
from datetime import timedelta

class TwoFactorCode(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idusuario')
    codigo = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    usado = models.BooleanField(default=False)
    intentos = models.IntegerField(default=0)
    
    class Meta:
        managed = True
        db_table = 'two_factor_codes'
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = str(random.randint(100000, 999999))
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # Expira en 10 minutos
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.usado and timezone.now() < self.expires_at and self.intentos < 3
    
    def __str__(self):
        return f"Código 2FA para {self.usuario.correo}"