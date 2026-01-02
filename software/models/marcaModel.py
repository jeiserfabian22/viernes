from django.db import models


class Marca(models.Model):
    idmarca = models.AutoField(primary_key=True)
    nombremarca = models.CharField(max_length=50)
    estado = models.IntegerField()
    class Meta:
        managed = True
        db_table = 'marca'