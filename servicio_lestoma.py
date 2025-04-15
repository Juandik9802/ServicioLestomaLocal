import json
import logging
import threading
import time
import serial
import requests
import urllib3
import uuid
from typing import Dict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import paho.mqtt.client as mqtt

# Desactivar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración del logger
logging.basicConfig(
    filename='logs/servicio_lestoma.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ServicioLestoma:
    def __init__(self):
        self._is_running = False
        self._serial_port = None
        self._config = self._cargar_configuracion()
        self._worker_thread = None
        self._session = self._crear_session()
        self._mqtt_client = None
        self._setup_mqtt_client()

    def _crear_session(self):
        """Crea una sesión HTTP con reintentos."""
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _cargar_configuracion(self) -> Dict:
        """Carga la configuración desde el archivo JSON."""
        try:
            with open('config/config.json', 'r') as f:
                config = json.load(f)
                # Valores por defecto
                config.setdefault('tipo_com', 1)
                config.setdefault('dir_registro', 0)
                return config
        except Exception as e:
            logging.error(f"Error al cargar configuración: {e}")
            raise

    def _setup_mqtt_client(self):
        """Configura y conecta el cliente MQTT."""
        try:
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.on_connect = self._on_mqtt_connect
            self._mqtt_client.on_message = self._on_mqtt_message

            # Conexión sin autenticación
            self._mqtt_client.connect(
                self._config['mqtt']['server'],
                self._config['mqtt']['port']
            )
            self._mqtt_client.loop_start()
        except Exception as e:
            logging.error(f"Error configurando MQTT: {e}")

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback de conexión MQTT."""
        if rc == 0:
            logging.info("Conectado a MQTT Broker")
            client.subscribe("/Write")
        else:
            logging.error(f"Error de conexión MQTT: Código {rc}")

    def _on_mqtt_message(self, client, userdata, msg):
        """Procesa mensajes MQTT entrantes."""
        try:
            payload = msg.payload.decode('utf-8')
            logging.info(f"Mensaje recibido: {payload}")
            self._procesar_comando_mqtt(msg.topic, payload)
        except Exception as e:
            logging.error(f"Error procesando mensaje MQTT: {e}")

    def iniciar(self):
        """Inicia el servicio."""
        try:
            self._is_running = True
            self._serial_port = serial.Serial(
                port=self._config['puerto_serial'],
                baudrate=self._config['baud_rate'],
                timeout=1
            )
            self._worker_thread = threading.Thread(target=self._worker_loop)
            self._worker_thread.start()
            logging.info("Servicio iniciado correctamente")
        except serial.SerialException as e:
            logging.error(f"Error al abrir puerto serial: {e}")
            self._is_running = False

    def detener(self):
        """Detiene el servicio."""
        self._is_running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        if self._serial_port and self._serial_port.is_open:
            self._serial_port.close()
        if self._mqtt_client:
            self._mqtt_client.disconnect()
        logging.info("Servicio detenido correctamente")

    def _worker_loop(self):
        """Bucle principal del servicio."""
        while self._is_running:
            try:
                # Procesar datos entrantes del serial
                if self._serial_port and self._serial_port.is_open:
                    data = self._serial_port.readline().decode('utf-8').strip()
                    if data:
                        self._procesar_datos_serial(data)
            except serial.SerialException as e:
                logging.error(f"Error serial: {e}")
                self._reconectar_serial()
            except Exception as e:
                logging.error(f"Error en bucle principal: {e}")
            time.sleep(0.1)

    def _procesar_comando_mqtt(self, topic: str, payload: str):
        """Procesa comandos recibidos por MQTT."""
        try:
            mqtt_data = json.loads(payload)

            # Validar campo obligatorio
            if "Dir_Esclavo" not in mqtt_data:
                raise ValueError("Campo 'Dir_Esclavo' es obligatorio")

            # Construir estructura base
            comando_serial = {
                "Tipo_Com": self._config['tipo_com'],
                "Funcion": "Write",
                "Dir_Registro": self._config['dir_registro'],
                "Dir_Esclavo": mqtt_data["Dir_Esclavo"]
            }

            # Manejar parámetros
            if "Sistemas" in mqtt_data:
                nombre_sistema = mqtt_data.pop("Sistemas")
                parametros = {k: v for k, v in mqtt_data.items() if k != "Dir_Esclavo"}
                comando_serial[nombre_sistema] = [parametros]
            else:
                comando_serial.update({k: v for k, v in mqtt_data.items() if k != "Dir_Esclavo"})

            # Enviar por serial
            self._enviar_por_serial(json.dumps(comando_serial, separators=(',', ':')))

        except json.JSONDecodeError:
            logging.error("JSON inválido recibido por MQTT")
        except Exception as e:
            logging.error(f"Error procesando comando: {e}")

    def _enviar_por_serial(self, data: str):
        """Envía datos por el puerto serial."""
        try:
            if self._serial_port and self._serial_port.is_open:
                self._serial_port.write(f"{data}\n".encode('utf-8'))
                logging.info(f"Datos enviados por serial: {data}")
        except serial.SerialException as e:
            logging.error(f"Error de escritura serial: {e}")
            self._reconectar_serial()

    def _reconectar_serial(self):
        """Intenta reconectar el puerto serial."""
        try:
            if self._serial_port:
                self._serial_port.close()
            self._serial_port = serial.Serial(
                port=self._config['puerto_serial'],
                baudrate=self._config['baud_rate'],
                timeout=1
            )
            logging.info("Reconexión serial exitosa")
        except Exception as e:
            logging.error(f"Error reconectando serial: {e}")

    def _procesar_datos_serial(self, data: str):
        """Procesa datos recibidos desde el Arduino."""
        try:
            logging.info(f"Datos recibidos del serial: {data}")
            # Aquí iría tu lógica para procesar datos entrantes
            # Ejemplo: Enviar a API o publicar en MQTT
        except Exception as e:
            logging.error(f"Error procesando datos serial: {e}")