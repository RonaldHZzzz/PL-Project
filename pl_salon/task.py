import requests
import time

# URL de tu servidor en Render
SERVER_URL = "https://pl-project-s39q.onrender.com"

def keep_server_alive():
    """
    Función para realizar una petición al servidor cada 15 minutos
    y asegurarse de que se mantenga activo.
    """
    while True:
        try:
            response = requests.get(SERVER_URL)
            if response.status_code == 200:
                print("Servidor activo y funcionando correctamente.")
            else:
                print(f"Advertencia: El servidor respondió con el código {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error al intentar conectarse al servidor: {e}")

        # Esperar 15 minutos antes de la próxima solicitud
        time.sleep(15 * 60)

if __name__ == "__main__":
    keep_server_alive()
