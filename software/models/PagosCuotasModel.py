from django.db import models
from software.models.CuotasVentaModel import CuotasVenta
from software.models.TipoPagoModel import TipoPago

class PagosCuotas(models.Model):
    idpagocuota = models.AutoField(primary_key=True)
    idcuotaventa = models.ForeignKey(CuotasVenta, on_delete=models.CASCADE, db_column='idcuotaventa')
    monto_pago = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField()
    id_tipo_pago = models.ForeignKey(TipoPago, on_delete=models.CASCADE, db_column='id_tipo_pago')
    observaciones = models.TextField(blank=True, null=True)
    estado = models.IntegerField(default=1)

    class Meta:
        db_table = 'pagoscuotas'

    def __str__(self):
        return f"Pago Cuota {self.idcuotaventa.numero_cuota}"