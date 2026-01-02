from django.db import models

class Departamentos(models.Model):
    iddepartamentos = models.CharField(primary_key=True, max_length=11)
    nombredepartamento = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'departamentos'