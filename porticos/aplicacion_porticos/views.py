from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json

# Create your views here.
def get_csrf_token(request):
    csrf_token = get_token(request)
    # Puedes enviar el token CSRF como parte de la respuesta JSON
    return JsonResponse({'csrf_token': csrf_token})

@csrf_exempt
def login_user(request):
    # Asegurarse de que la solicitud provenga de un origen permitido
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"  # Permitir solicitudes de cualquier origen
    response["Access-Control-Allow-Methods"] = "POST"  # Permitir solo solicitudes POST
    response["Access-Control-Allow-Headers"] = "Content-Type"  # Permitir solo el encabezado Content-Type

    r = False
    
    if request.method == 'POST':
        # Obtener el cuerpo de la solicitud como un diccionario
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        # Obtener el nombre de usuario y la contraseña del diccionario
        username = body_data.get('username')
        password = body_data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            r=True
            return JsonResponse(data={'r':r, 'user':user.username})
        else:
            return JsonResponse(data={'r':r, 'user':username})

@csrf_exempt
def logout_user(request):
    logout(request)
    return JsonResponse({'message':'Success'})
