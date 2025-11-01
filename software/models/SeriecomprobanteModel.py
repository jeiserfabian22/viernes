from django.db import models
from software.models.TipocomprobanteModel import Tipocomprobante

class Seriecomprobante(models.Model):
    idseriecomprobante = models.AutoField(primary_key=True)
    idtipocomprobante = models.ForeignKey(Tipocomprobante, on_delete=models.CASCADE, db_column='idtipocomprobante', related_name='seriecomprobante')
    serie = models.CharField(max_length=4)
    numero_actual = models.IntegerField(default=0)
    estado = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'seriecomprobante'

    def __str__(self):
        return f"{self.serie}"