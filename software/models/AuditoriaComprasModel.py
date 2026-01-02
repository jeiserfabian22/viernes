from django.db import models
from software.models.UsuarioModel import Usuario

class AuditoriaCompras(models.Model):
    idauditoria = models.AutoField(primary_key=True)
    idcompra = models.IntegerField()
    accion = models.CharField(max_length=50) 
    motivo = models.TextField(blank=True, null=True)
    idusuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='idusuario', related_name='auditorias_compras')
    fecha = models.DateTimeField(auto_now_add=True)
    datos_anteriores = models.JSONField(null=True, blank=True) 
    
    class Meta:
        managed = True
        db_table = 'auditoria_compras'
        ordering = ['-fecha']
        
    def __str__(self):
        return f"{self.accion} - Compra #{self.idcompra} - {self.fecha}"