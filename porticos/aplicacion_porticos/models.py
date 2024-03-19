from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Ciudad(models.Model):
    nombre = models.TextField(max_length=255)

    def __str__(self):
        return self.nombre

class ListaNegra(models.Model):
    patente = models.TextField(max_length=6)
    motivo = models.TextField(max_length=255)

    def __str__(self):
        return self.patente

class Infraccion(models.Model):
    nombre = models.TextField(max_length=255)
    descripcion = models.TextField(max_length=255)

    def __str__(self):
        return self.nombre

class Carpeta(models.Model):
    nombre = models.TextField(max_length=255)
    ubicacion = models.TextField(max_length=255)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class CarpetaUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE)

    def __str__(self):
        return self.usuario

class Alerta(models.Model):
    ciudad_envia = models.ForeignKey(Ciudad, related_name='alertas_enviadas', on_delete=models.CASCADE)
    ciudad_recibe = models.ForeignKey(Ciudad, related_name='alertas_recibidas', on_delete=models.CASCADE)
    fecha= models.DateTimeField()
    estado = models.IntegerField() #Estado 1= Visto --- Estado 2 = No visto

    def __str__(self):
        return self.estado

class Registro(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    patente = models.TextField(max_length=6)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    imagen_binaria = models.TextField(null=True, blank=True)
    infraccion = models.ForeignKey(Infraccion, on_delete=models.CASCADE)
    observacion = models.TextField(max_length=255)

    def __str__(self):
        return self.patente

