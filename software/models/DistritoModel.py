from django.db import models
from software.models.ProvinciaModel import Provincia

class Distrito(models.Model):
    id_distrito = models.AutoField(primary_key=True)
    nombre_distrito = models.CharField(max_length=100)
    id_provincia = models.ForeignKey(Provincia, on_delete=models.DO_NOTHING, db_column='id_provincia', related_name='distritos')

    class Meta:
        managed = False  # porque la tabla ya existe
        db_table = 'distrito'
