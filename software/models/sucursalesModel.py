from django.db import models
from software.models.empresaModel import Empresa
from software.models.DistritoModel import Distrito

class Sucursales(models.Model):
    id_sucursal = models.AutoField(primary_key=True)
    idempresa = models.ForeignKey(Empresa, on_delete=models.DO_NOTHING, db_column='idempresa', related_name='sucursales')
    id_distrito = models.ForeignKey(Distrito, on_delete=models.DO_NOTHING, db_column='id_distrito', related_name='sucursales')
    nombre_sucursal = models.CharField(max_length=100)
    codigo_sucursal = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    fecha_apertura = models.DateField()
    estado = models.IntegerField(default=1, db_column='estado')
    es_principal = models.BooleanField(default=False, db_column='es_principal')

    class Meta:
        managed = True  
        db_table = 'sucursales'
