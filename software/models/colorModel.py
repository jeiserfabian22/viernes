from django.db import models

class Color(models.Model):
    idcolor = models.AutoField(primary_key=True)
    nombrecolor = models.CharField(max_length=50)
    estado = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'color'
