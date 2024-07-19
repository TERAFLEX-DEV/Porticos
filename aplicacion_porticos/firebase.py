from firebase_admin import messaging, credentials, initialize_app, get_app
import firebase_admin
from django.contrib.auth.models import User


class Firebase:
    def __init__(self):
        super().__init__()
        firebase_json='aplicacion_porticos/teraflex.json'

        try:
            get_app()
        except ValueError:
            firebase_credentials = credentials.Certificate(firebase_json)
            firebase_admin.initialize_app(firebase_credentials)
    
    def send(user):

        print(f'El usuario es: {token}')

        token = 'dBTBpZ1bUx7H-anXtLxdBd:APA91bF5iMjr9ASlY5cuORyK79JhwN2Btb3oyCBOJAjSIb1aMm89oa_75H7SpXO0HoZEpPlq1BAWNAbdiYci0eyW-38J2i3xCaRZqIs6Ke5zUnw_8UcIVmH6Qz_pcBdh67BSmXZbxsGT'
        message = messaging.Message(
            notification=messaging.Notification(
                title="Title",
                body="Body"
            ),
            token= token
        )

        response = messaging.send(message)
        print(f'Response {response}')

    def sends(users):
        token = 'dBTBpZ1bUx7H-anXtLxdBd:APA91bF5iMjr9ASlY5cuORyK79JhwN2Btb3oyCBOJAjSIb1aMm89oa_75H7SpXO0HoZEpPlq1BAWNAbdiYci0eyW-38J2i3xCaRZqIs6Ke5zUnw_8UcIVmH6Qz_pcBdh67BSmXZbxsGT'
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title="Title",
                body="Body"
            ),
            token= token
        )

        response = messaging.send_multicast(message)
        print(f'Response {response}')