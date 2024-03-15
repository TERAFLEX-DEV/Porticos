import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        # Aquí puedes definir lo que deseas hacer cuando ocurra un evento
        print(f'Evento detectado: {event.event_type} - {event.src_path}')

def main():
    path = '.'  # Directorio a monitorear, puedes cambiarlo según tus necesidades
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
