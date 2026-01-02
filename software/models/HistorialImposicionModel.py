from django.db import models
from software.models.UsuarioModel import Usuario
from software.models.ImposicionPlacaModel import ImposicionPlaca



class HistorialImposicion(models.Model):

    id_historial = models.AutoField(primary_key=True)
    id_imposicion = models.ForeignKey(
        ImposicionPlaca, 
        on_delete=models.CASCADE, 
        db_column='id_imposicion',
        related_name='historial'
    )
    idusuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        db_column='idusuario'
    )
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    comentario = models.TextField(blank=True, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'historial_imposicion'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Cambio {self.id_historial} - Imposición {self.id_imposicion.id_imposicion}"