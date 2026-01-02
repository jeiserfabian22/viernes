from django.db import models

class Region(models.Model):
    id_region = models.AutoField(primary_key=True)
    nombre_region = models.CharField(max_length=100)
    estado = models.IntegerField(default=1)

    class Meta:
        managed = True  
        db_table = 'region'
