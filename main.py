from servicio_lestoma import ServicioLestoma
import time

if __name__ == "__main__":
    servicio = ServicioLestoma()
    try:
        servicio.iniciar()
        while True:
            time.sleep(1)  # Mantener el programa en ejecución
    except KeyboardInterrupt:
        servicio.detener()