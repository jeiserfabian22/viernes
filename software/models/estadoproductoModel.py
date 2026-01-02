from django.db import models

class EstadoProducto(models.Model):
    idestadoproducto = models.AutoField(primary_key=True)
    nombreestadoproducto = models.CharField(max_length=50)
    estado = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'estadoproducto'
