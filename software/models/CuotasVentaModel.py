from django.db import models
from software.models.VentasModel import Ventas

class CuotasVenta(models.Model):
    idcuotaventa = models.AutoField(primary_key=True)
    idventa = models.ForeignKey(Ventas, on_delete=models.CASCADE, db_column='idventa')
    numero_cuota = models.IntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tasa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    monto_adelanto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado_pago = models.CharField(max_length=20, default='Pendiente')
    estado = models.IntegerField(default=1)

    class Meta:
        db_table = 'cuotasventa'

    def __str__(self):
        return f"Cuota {self.numero_cuota} - Venta {self.idventa.numero_comprobante}"