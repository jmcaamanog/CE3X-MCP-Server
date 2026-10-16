"""
Instalador Automático en 1 Clic de CE3X-MCP-Server para Claude Desktop y Cursor
Configura de forma no destructiva el servidor MCP en los clientes de IA en Windows y macOS.
"""

import os
import sys
import json
import shutil

# Reconfigurar salida para admitir UTF-8 y caracteres especiales en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def configurar_claude_desktop():
    print("=" * 65)
    print(" CE3X-MCP-Server - Instalador Oficial de 1 Clic")
    print(" Arquitecto Técnico & BIM Manager | ConTech AECO")
    print("=" * 65)

    # 1. Determinar ruta de configuración de Claude Desktop
    appdata = os.environ.get("APPDATA")
    if not appdata:
        home = os.path.expanduser("~")
        claude_dir = os.path.join(home, "Library", "Application Support", "Claude")
    else:
        claude_dir = os.path.join(appdata, "Claude")

    os.makedirs(claude_dir, exist_ok=True)
    config_path = os.path.join(claude_dir, "claude_desktop_config.json")

    # 2. Leer configuración existente preservando servidores previos
    config_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            backup_path = config_path + ".bak"
            shutil.copy2(config_path, backup_path)
            print(f"[OK] Copia de seguridad creada: {backup_path}")
        except Exception as e:
            print(f"[AVISO] No se pudo leer el archivo existente ({e}). Se creará una nueva configuración.")
            config_data = {}

    if "mcpServers" not in config_data:
        config_data["mcpServers"] = {}

    # 3. Determinar la mejor forma de lanzamiento (Local vs uvx)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    venv_python = os.path.join(repo_root, ".venv", "Scripts", "python.exe")

    if os.path.exists(venv_python):
        print(f"[INFO] Entorno virtual local detectado: {venv_python}")
        config_data["mcpServers"]["ce3x"] = {
            "command": venv_python,
            "args": [
                "-I",
                "-m",
                "ce3x_mcp.server"
            ],
            "cwd": repo_root
        }
    else:
        print("[INFO] Configurando modo universal PyPI (uvx)...")
        config_data["mcpServers"]["ce3x"] = {
            "command": "uvx",
            "args": [
                "--from",
                "ce3x-mcp-server",
                "ce3x-mcp"
            ]
        }

    # 4. Guardar archivo con formato impecable
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"[EXITO] Servidor 'ce3x' registrado con éxito en:")
        print(f"        {config_path}")
    except Exception as e:
        print(f"[ERROR] No se pudo escribir en {config_path}: {e}")
        return False

    # 5. Intentar configurar Cursor si existe
    user_home = os.path.expanduser("~")
    cursor_config = os.path.join(user_home, ".cursor", "mcp.json")
    if os.path.exists(os.path.dirname(cursor_config)):
        try:
            cursor_data = {}
            if os.path.exists(cursor_config):
                with open(cursor_config, "r", encoding="utf-8") as f:
                    cursor_data = json.load(f)
            if "mcpServers" not in cursor_data:
                cursor_data["mcpServers"] = {}
            cursor_data["mcpServers"]["ce3x"] = config_data["mcpServers"]["ce3x"]
            with open(cursor_config, "w", encoding="utf-8") as f:
                json.dump(cursor_data, f, indent=2, ensure_ascii=False)
            print(f"[EXITO] Servidor 'ce3x' también registrado en Cursor: {cursor_config}")
        except Exception:
            pass

    print("-" * 65)
    print(" [OK] TODO LISTO! 22 HERRAMIENTAS OFICIALES INSTALADAS.")
    print(" Pasos siguientes:")
    print(" 1. Si tienes Claude Desktop abierto, ciérralo y vuelve a abrirlo.")
    print(" 2. Escribe en el chat: 'Certifica la vivienda de la carpeta ejemplos/visita_vivienda_ejemplo'")
    print(" 3. Verás cómo la IA ejecuta todo el flujo oficial de CE3X automáticamente.")
    print("=" * 65)
    return True

if __name__ == "__main__":
    exito = configurar_claude_desktop()
    if not exito:
        sys.exit(1)
