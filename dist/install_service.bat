@echo off
pip install -r requirements.txt
echo Instalando el servicio ServicioLestoma...

:: Instalar el servicio
main.exe install
if errorlevel 1 (
    echo Error al instalar el servicio.
    pause
    exit /b 1
)

:: Configurar el servicio para inicio automático
sc config ServicioLestoma start= auto
if errorlevel 1 (
    echo Error al configurar el servicio para inicio automático.
    pause
    exit /b 1
)

:: Iniciar el servicio
sc start ServicioLestoma
if errorlevel 1 (
    echo Error al iniciar el servicio.
    pause
    exit /b 1
)

echo Servicio instalado, configurado para inicio automático e iniciado correctamente.
pause