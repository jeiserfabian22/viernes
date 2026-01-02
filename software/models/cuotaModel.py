from django.db import models

from software.models.comprasModel import Compras

class Cuota(models.Model):
    id_cuota = models.AutoField(primary_key=True)
    idcompra = models.ForeignKey(Compras, on_delete=models.DO_NOTHING, db_column='idcompra', related_name='cuota',null=True, blank=True)
    numero_cuota = models.IntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tasa = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    interes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_adelanto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.IntegerField(default=1) 

    class Meta:
        managed = True
        db_table = 'cuotas'