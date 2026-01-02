from django.db import models
from software.models.RegionModel import Region

class Provincia(models.Model):
    id_provincia = models.AutoField(primary_key=True)
    nombre_provincia = models.CharField(max_length=100)
    id_region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, db_column='id_region', related_name='provincias')
    estado = models.IntegerField(default=1)

    class Meta:
        managed = True  
        db_table = 'provincia'
