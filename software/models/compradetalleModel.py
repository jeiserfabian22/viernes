from django.db import models

from software.models.RespuestoCompModel import RepuestoComp
from software.models.VehiculosModel import Vehiculo
from software.models.comprasModel import Compras

class CompraDetalle(models.Model):
    idcompradetalle = models.AutoField(primary_key=True)
    id_repuesto_comprado= models.ForeignKey(RepuestoComp, on_delete=models.DO_NOTHING, db_column='id_repuesto_comprado', related_name='compradetalle',null=True, blank=True)
    id_vehiculo= models.ForeignKey(Vehiculo, on_delete=models.DO_NOTHING, db_column='id_vehiculo', related_name='compradetalle',null=True, blank=True)
    idcompra = models.ForeignKey(Compras, on_delete=models.DO_NOTHING, db_column='idcompra', related_name='compradetalle',null=True, blank=True)
    cantidad = models.IntegerField()
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00 )
    subtotal = models.FloatField()

    class Meta:
        managed = True
        db_table = 'compra_detalle'