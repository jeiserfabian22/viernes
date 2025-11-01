from django.db import models

class Region(models.Model):
    id_region = models.AutoField(primary_key=True)
    nombre_region = models.CharField(max_length=100)

    class Meta:
        managed = False  # porque la tabla ya existe en tu base de datos
        db_table = 'region'
