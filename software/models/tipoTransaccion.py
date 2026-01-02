from django.db import models


class TipoTransaccion(models.Model):
    id_tipo_transaccion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60, blank=True, null=True)
    ingresoegreso = models.IntegerField(blank=True, null=True) #Para saber si es ingres 1 o egreso 0

    class Meta:
        managed = True
        db_table = 'tipo_transaccion'