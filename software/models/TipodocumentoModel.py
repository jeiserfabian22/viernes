from django.db import models

class Tipodocumento(models.Model):
    idtipodocumento = models.AutoField(primary_key=True)
    codigosunat = models.CharField(max_length=10)
    nombredocumento = models.CharField(max_length=255)
    abrrdoc = models.CharField(max_length=10)
    estado = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'tipodocumento'