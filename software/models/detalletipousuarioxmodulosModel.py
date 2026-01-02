from django.db import models

from software.models.ModulosModel import Modulos
from software.models.TipousuarioModel import Tipousuario


class Detalletipousuarioxmodulos(models.Model):
    iddetalletipousuarioxmodulos = models.AutoField(primary_key=True)
    idmodulo = models.ForeignKey(Modulos, models.DO_NOTHING, db_column='idmodulo')
    idtipousuario = models.ForeignKey(Tipousuario, models.DO_NOTHING, db_column='idtipousuario')

    class Meta:
        managed = True
        db_table = 'detalletipousuarioxmodulos'