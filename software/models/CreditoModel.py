from django.db import models
from software.models.VentasModel import Ventas

class Credito(models.Model):
    """
    Modelo para gestionar créditos de ventas
    Cada venta a crédito genera un registro aquí con código único
    """
    idcredito = models.AutoField(primary_key=True)
    codigo_credito = models.CharField(max_length=50, unique=True)
    idventa = models.OneToOneField(
        Ventas, 
        on_delete=models.CASCADE, 
        db_column='idventa', 
        related_name='credito'
    )
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_adelanto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_cuotas = models.IntegerField()
    fecha_credito = models.DateTimeField(auto_now_add=True)
    estado_credito = models.CharField(
        max_length=20, 
        default='activo'
    )  # activo, pagado, mora
    estado = models.IntegerField(default=1)

    class Meta:
        managed = True
        db_table = 'creditos'
        ordering = ['-fecha_credito']

    def __str__(self):
        return f"{self.codigo_credito} - {self.idventa.idcliente.razonsocial}"
    
    def calcular_saldo_pendiente(self):
        """Calcula el saldo pendiente basado en las cuotas pagadas"""
        from software.models.CuotasVentaModel import CuotasVenta
        cuotas = CuotasVenta.objects.filter(idventa=self.idventa, estado=1)
        total_pagado = sum(cuota.monto_pagado for cuota in cuotas)
        return self.monto_total - self.monto_adelanto - total_pagado
    
    def actualizar_estado(self):
        """Actualiza el estado del crédito según el estado de las cuotas"""
        from software.models.CuotasVentaModel import CuotasVenta
        from django.utils import timezone
        
        cuotas = CuotasVenta.objects.filter(idventa=self.idventa, estado=1)
        
        # Si todas las cuotas están pagadas
        if all(cuota.estado_pago == 'Pagado' for cuota in cuotas):
            self.estado_credito = 'pagado'
            self.saldo_pendiente = 0
        else:
            # Verificar si hay cuotas vencidas
            hay_vencidas = cuotas.filter(
                estado_pago__in=['Pendiente', 'Parcial'],
                fecha_vencimiento__lt=timezone.now().date()
            ).exists()
            
            if hay_vencidas:
                self.estado_credito = 'mora'
            else:
                self.estado_credito = 'activo'
            
            self.saldo_pendiente = self.calcular_saldo_pendiente()
        
        self.save()