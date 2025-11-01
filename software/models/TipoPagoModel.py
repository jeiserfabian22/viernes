from django.db import models


class TipoPago(models.Model):
    id_tipo_pago = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    estado = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipospago'


        