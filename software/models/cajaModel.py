# software/models/cajaModel.py
from django.db import models
from software.models.sucursalesModel import Sucursales


class Caja(models.Model):
    id_caja = models.AutoField(primary_key=True)
    id_sucursal = models.ForeignKey(Sucursales, models.DO_NOTHING, db_column='id_sucursal', null=True, blank=True)
    nombre_caja = models.CharField(max_length=50, blank=True, null=True)
    numero_caja = models.IntegerField(blank=True, null=True)
    estado = models.IntegerField()

    
    class Meta:
        managed = False
        db_table = 'cajas'
    
    def __str__(self):
        return self.nombre_caja
    


