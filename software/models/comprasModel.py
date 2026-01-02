from django.db import models
from software.models.ProveedoresModel import Proveedor
from software.models.FormaPagoModel import FormaPago
from software.models.TipoPagoModel import TipoPago
from software.models.TipoclienteModel import Tipocliente
from software.models.sucursalesModel import Sucursales

class Compras(models.Model):
    idcompra = models.AutoField(primary_key=True)
    idproveedor = models.ForeignKey(Proveedor, on_delete=models.DO_NOTHING, db_column='idproveedor', related_name='compras')
    idtipocliente = models.ForeignKey(Tipocliente, on_delete=models.DO_NOTHING, db_column='idtipocliente', related_name='compras')
    id_forma_pago = models.ForeignKey(FormaPago, on_delete=models.DO_NOTHING, db_column='id_forma_pago', related_name='compras')
    id_tipo_pago = models.ForeignKey(TipoPago, on_delete=models.DO_NOTHING, db_column='id_tipo_pago', related_name='compras')
    numcorrelativo = models.CharField(max_length=11)
    fechacompra = models.DateField()
    total_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.IntegerField(db_column='estado')
    id_sucursal = models.ForeignKey(Sucursales,on_delete=models.RESTRICT,db_column='id_sucursal',related_name='compras',null=True,blank=True)
    

    class Meta:
        managed = True  
        db_table = 'compras'


    
