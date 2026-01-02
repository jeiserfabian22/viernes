from django.db import models
from software.models.UsuarioModel import Usuario


class AuditoriaVentas(models.Model):
    idauditoria_venta = models.AutoField(primary_key=True)
    idventa = models.IntegerField()
    accion = models.CharField(max_length=20)  # 'EDICION' o 'ELIMINACION'
    motivo = models.TextField(blank=True, null=True)
    idusuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='idusuario')
    datos_anteriores = models.JSONField(blank=True, null=True)
    fecha_auditoria = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = True
        db_table = 'auditoria_ventas'
        verbose_name = 'Auditoría de Venta'
        verbose_name_plural = 'Auditorías de Ventas'
    
    def __str__(self):
        return f"Auditoría {self.idauditoria_venta} - Venta {self.idventa}"
