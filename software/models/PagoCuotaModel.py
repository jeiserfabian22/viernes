from django.db import models
from software.models.CuotasVentaModel import CuotasVenta
from software.models.UsuarioModel import Usuario
from software.models.TipoPagoModel import TipoPago

class PagoCuota(models.Model):
    """
    Modelo para registrar cada pago realizado a una cuota
    Permite pagos parciales y múltiples pagos por cuota
    """
    idpagocuota = models.AutoField(primary_key=True)
    idcuotaventa = models.ForeignKey(
        CuotasVenta, 
        on_delete=models.CASCADE, 
        db_column='idcuotaventa', 
        related_name='pagos'
    )
    idusuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        db_column='idusuario'
    )
    id_tipo_pago = models.ForeignKey(
        TipoPago, 
        on_delete=models.CASCADE, 
        db_column='id_tipo_pago'
    )
    monto_pago = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    numero_operacion = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.IntegerField(default=1)

    class Meta:
        managed = True
        db_table = 'pagos_cuota'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago S/ {self.monto_pago} - Cuota {self.idcuotaventa.numero_cuota}"
    


    