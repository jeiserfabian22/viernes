from django.db import models

class Tipocliente(models.Model):
    idtipocliente = models.AutoField(primary_key=True)
    nomtipocliente = models.CharField(max_length=255)
    estado = models.IntegerField(default=1)

    class Meta:
        managed = True
        db_table = 'tipocliente'