from django.db import models

from software.models.ClienteModel import Cliente
from software.models.UsuarioModel import Usuario
from software.models.TipocomprobanteModel import Tipocomprobante
from software.models.SeriecomprobanteModel import Seriecomprobante
from software.models.FormaPagoModel import FormaPago
from software.models.TipoPagoModel import TipoPago
from software.models.TipoIgvModel import TipoIgv

class Ventas(models.Model):
    idventa = models.AutoField(primary_key=True)
    idseriecomprobante = models.ForeignKey(Seriecomprobante, on_delete=models.CASCADE, db_column='idseriecomprobante')
    idtipocomprobante = models.ForeignKey(Tipocomprobante, on_delete=models.CASCADE, db_column='idtipocomprobante')
    idcliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='idcliente')
    estado = models.IntegerField(default=1)
    id_tipo_igv = models.ForeignKey(TipoIgv, on_delete=models.CASCADE, db_column='id_tipo_igv', blank=True, null=True)
    idempresa = models.IntegerField(blank=True, null=True)
    idusuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idusuario')
    numero_comprobante = models.CharField(max_length=20)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    id_forma_pago = models.ForeignKey(FormaPago, on_delete=models.CASCADE, db_column='id_forma_pago')
    id_tipo_pago = models.ForeignKey(TipoPago, on_delete=models.CASCADE, db_column='id_tipo_pago', blank=True, null=True)
    importe_recibido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vuelto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total_venta = models.DecimalField(max_digits=10, decimal_places=2)
    total_ganancia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)
    id_almacen = models.ForeignKey('Almacenes', on_delete=models.DO_NOTHING, db_column='id_almacen', null=True, blank=True)
    id_caja = models.ForeignKey('Caja', on_delete=models.DO_NOTHING, db_column='id_caja', null=True, blank=True)
    id_sucursal = models.ForeignKey('Sucursales', on_delete=models.DO_NOTHING, db_column='id_sucursal', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'ventas'

    def __str__(self):
        return f"Venta {self.numero_comprobante}"