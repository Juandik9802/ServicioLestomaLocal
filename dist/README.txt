Instalación del Servicio Lestoma
===============================

1. Copie la carpeta "InstaladorServicioLestoma" al equipo donde desea instalar el servicio.

2. Ejecute el archivo "install_service.bat" como administrador:
   - Haga clic derecho sobre el archivo.
   - Seleccione "Ejecutar como administrador".

3. Siga las instrucciones en la ventana de comandos:
   - El servicio se instalará, configurará para inicio automático y se iniciará.

4. Verifique que el servicio esté en ejecución:
   - Abra el Administrador de servicios (services.msc).
   - Busque el servicio "ServicioLestoma" y verifique que esté en estado "En ejecución".

5. Para detener o desinstalar el servicio:
   - Detener: Ejecute "sc stop ServicioLestoma" como administrador.
   - Desinstalar: Ejecute "sc delete ServicioLestoma" como administrador.

Notas:
- Asegúrese de que los archivos de configuración (config.json y mapeo_variables.json) estén en la carpeta "config".
- Los registros del servicio se guardan en la carpeta "logs".