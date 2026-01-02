from django.db import models

class Tipousuario(models.Model):
    idtipousuario = models.AutoField(primary_key=True)
    nombretipousuario = models.CharField(max_length=255)
    estado = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'tipousuario'