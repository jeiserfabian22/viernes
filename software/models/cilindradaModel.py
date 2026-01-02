from django.db import models

class Cilindrada(models.Model):
    idcilindrada = models.AutoField(primary_key=True)
    cilindrada_cc = models.CharField(max_length=255)
    estado = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'cilindrada'
