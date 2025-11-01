from django.db import models
from software.models.TipoclienteModel import Tipocliente
class Proveedores(models.Model):
    idproveedor = models.AutoField(primary_key=True)
    idtipocliente = models.ForeignKey('Tipocliente', models.DO_NOTHING, db_column='idtipocliente')
    numdoc = models.CharField(max_length=255)
    razonsocial = models.CharField(max_length=255)
    estado = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'proveedores'