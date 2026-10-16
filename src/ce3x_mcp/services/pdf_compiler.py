import os
import subprocess
import shutil
from typing import Optional, Tuple

XML2CERT_DEFAULT_PATH = r"C:\Program Files (x86)\CE3Xv3.2\moduloXML\xmlcert_20260703\xml2cert.exe"
JAVA_KNOWN_PATHS = [
    r"C:\Program Files\AutoFirma\AutoFirma\jre\bin\java.exe",
    r"C:\Program Files\Android\Android Studio1\jbr\bin\java.exe"
]

def compilar_pdf_desde_xml(xml_path: str, output_dir: str, xml2cert_bin: Optional[str] = None) -> Tuple[bool, str]:
    """
    Compila el archivo XML oficial a un documento PDF oficial utilizando xml2cert (Typst).
    """
    bin_path = xml2cert_bin or XML2CERT_DEFAULT_PATH
    if not os.path.exists(bin_path):
        return False, f"No se encontró el ejecutable xml2cert en: {bin_path}"
    
    if not os.path.exists(xml_path):
        return False, f"El archivo XML no existe: {xml_path}"
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Asegurar que Java esté disponible en el entorno de ejecución para jing.jar
    env = os.environ.copy()
    if not shutil.which("java", path=env.get("PATH", "")):
        for jpath in JAVA_KNOWN_PATHS:
            if os.path.exists(jpath):
                java_bin_dir = os.path.dirname(jpath)
                env["PATH"] = java_bin_dir + os.pathsep + env.get("PATH", "")
                break
                
    cmd = [bin_path, "-o", output_dir, xml_path]
    try:
        proc = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if proc.returncode == 0:
            # El PDF generado tiene el mismo nombre base que el XML
            base_name = os.path.splitext(os.path.basename(xml_path))[0]
            pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
            if os.path.exists(pdf_path):
                return True, pdf_path
            return True, f"PDF generado exitosamente en directorio: {output_dir}"
        else:
            return False, f"Error de xml2cert (código {proc.returncode}): {proc.stderr}"
    except Exception as e:
        return False, f"Excepción al ejecutar xml2cert: {str(e)}"


