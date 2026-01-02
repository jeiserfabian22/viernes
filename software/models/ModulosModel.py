from django.db import models

class Modulos(models.Model):
    idmodulo = models.AutoField(primary_key=True)
    nombremodulo = models.CharField(max_length=255)
    estado = models.IntegerField(default=1)
    url = models.CharField(max_length=45, blank=True, null=True)
    logo = models.CharField(max_length=45, blank=True, null=True)
    idmodulo_padre = models.ForeignKey(
        'self', 
        on_delete=models.DO_NOTHING, 
        db_column='idmodulo_padre',
        blank=True, 
        null=True,
        related_name='submodulos'
    )
    orden = models.IntegerField(default=0)

    class Meta:
        managed = True
        db_table = 'modulos'
        ordering = ['orden', 'nombremodulo']