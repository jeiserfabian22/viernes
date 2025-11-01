from django.db import models

from software.models.TipodocumentoModel import Tipodocumento

class Numserie(models.Model):
    idnumserie = models.AutoField(primary_key=True)
    idtipodocumento = models.ForeignKey(Tipodocumento, on_delete=models.CASCADE, db_column='idtipodocumento')
    idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='idusuario')
    numserie = models.CharField(max_length=4, blank=True, null=True)
    estado = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'numserie'
