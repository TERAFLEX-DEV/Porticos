import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        # Aquí puedes definir lo que deseas hacer cuando ocurra un evento
        print(f'Evento detectado: {event.event_type} - {event.src_path}')

def main():
    paths = ['C:/FTP/TCM TRFX', 'C:/FTP/PTZ TRFX']  # Lista de directorios a monitorear, puedes cambiarlos según tus necesidades
    event_handlers = []
    observers = []

    # Configurar un observador para cada carpeta
    for path in paths:
        event_handler = MyHandler()
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        event_handlers.append(event_handler)
        observers.append(observer)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()

if __name__ == "__main__":
    main()
