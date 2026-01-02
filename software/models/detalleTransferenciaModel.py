from django.db import models
from software.models.transferenciaModel import Transferencia
from software.models.VehiculosModel import Vehiculo
from software.models.RespuestoCompModel import RepuestoComp


class DetalleTransferencia(models.Model):
    id_detalle_transferencia = models.AutoField(primary_key=True)
    id_transferencia = models.ForeignKey(Transferencia, on_delete=models.CASCADE, db_column='id_transferencia', related_name='detalles')
    
    # Producto puede ser vehículo o repuesto
    id_vehiculo = models.ForeignKey(Vehiculo, on_delete=models.RESTRICT, db_column='id_vehiculo', related_name='transferencias', null=True, blank=True)
    id_repuesto_comprado = models.ForeignKey(RepuestoComp, on_delete=models.RESTRICT, db_column='id_repuesto_comprado', related_name='transferencias', null=True, blank=True)
    
    cantidad = models.IntegerField(default=1, db_column='cantidad')
    estado = models.IntegerField(default=1, db_column='estado')
    
    class Meta:
        managed = True
        db_table = 'detalle_transferencia'
    
    def __str__(self):
        if self.id_vehiculo:
            return f"Detalle: {self.id_vehiculo.idproducto.nomproducto} - Cant: {self.cantidad}"
        elif self.id_repuesto_comprado:
            return f"Detalle: {self.id_repuesto_comprado.id_repuesto.nombre} - Cant: {self.cantidad}"
        return f"Detalle #{self.id_detalle_transferencia}"