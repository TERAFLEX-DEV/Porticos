from django.db import models

# Create your models here.
class Ciudad(models.Model):
    nombre = models.TextField(max_lenght=255)

class ListaNegra(models.Model):
    patente = models.TextField(max_lenght=6)
    motivo = models.TextField(max_lenght=255)

class Infraccion(models.Model):
    nombre = models.TextField(max_lenght=255)
    descripcion = models.TextField(max_lenght=255)

