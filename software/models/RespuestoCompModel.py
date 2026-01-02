
from django.db import models

from software.models.RepuestoModel import Repuesto

class RepuestoComp(models.Model):
    id_repuesto_comprado= models.AutoField(primary_key=True, db_column='id_repuesto_comprado')
    id_repuesto= models.ForeignKey(Repuesto, on_delete=models.DO_NOTHING, db_column='id_repuesto', related_name='repuestocomprados')
    descripcion = models.CharField(max_length=200)
    codigo_barras = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    estado = models.IntegerField(db_column='estado')
    

    class Meta:
        managed = True
        db_table = 'repuestoscomprado'
