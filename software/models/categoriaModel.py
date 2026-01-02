from django.db import models


class Categoria(models.Model):
    idcategoria = models.AutoField(primary_key=True)
    nomcategoria = models.CharField(max_length=255)
    estado = models.IntegerField()
    class Meta:
        managed = True
        db_table = 'categoria'