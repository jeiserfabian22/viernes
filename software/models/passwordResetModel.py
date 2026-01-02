# software/models/passwordResetModel.py
from django.db import models
from software.models.UsuarioModel import Usuario
import secrets
from django.utils import timezone
from datetime import timedelta

class PasswordResetToken(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idusuario')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    usado = models.BooleanField(default=False)
    
    class Meta:
        managed = True
        db_table = 'password_reset_tokens'
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)  # Expira en 1 hora
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.usado and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Token para {self.usuario.correo}"