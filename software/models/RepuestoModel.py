
from django.db import models
from software.models.UnidadesModel import Unidades
from software.models.marcaModel import Marca
from software.models.colorModel import Color

class Repuesto(models.Model):
    id_repuesto = models.AutoField(primary_key=True, db_column='id_repuesto')
    nombre = models.CharField(max_length=255, db_column='nombre')
    idunidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, db_column='idunidad', related_name='repuestos')
    idmarca = models.ForeignKey(Marca, on_delete=models.DO_NOTHING, db_column='idmarca', related_name='repuestos')
    idcolor = models.ForeignKey(Color, on_delete=models.DO_NOTHING, db_column='idcolor', related_name='repuestos')
    estado = models.IntegerField(db_column='estado')

    class Meta:
        managed = True   # porque la tabla ya existe
        db_table = 'repuestos'
        indexes = [models.Index(fields=['nombre'])]

    def __str__(self):
        return self.nombre
