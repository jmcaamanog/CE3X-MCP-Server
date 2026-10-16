@echo off
chcp 65001 >nul
title Publicar CE3X-MCP-Server en PyPI
cls
echo =====================================================================
echo  PUBLICADOR OFICIAL: CE3X-MCP-Server en PyPI (pypi.org)
echo  Jose Manuel Caamaño González | Arquitecto Técnico & BIM Manager
echo =====================================================================
echo.
echo Paquetes listos en la carpeta dist/:
dir dist\*.whl dist\*.tar.gz /b
echo.
set /p PYPI_TOKEN="Pega tu API Token de PyPI (empieza por pypi-...): "
echo.
echo Subiendo paquetes a PyPI de forma segura...
.venv\Scripts\python -m twine upload dist/* -u __token__ -p %PYPI_TOKEN%
echo.
if %ERRORLEVEL% equ 0 (
    echo =====================================================================
    echo  [EXITO] ¡Paquete publicado exitosamente en PyPI!
    echo  Cualquier persona en el mundo puede usarlo ahora con:
    echo    uvx ce3x-mcp
    echo =====================================================================
) else (
    echo [ERROR] No se pudo subir. Comprueba que el token es correcto.
)
echo.
pause
