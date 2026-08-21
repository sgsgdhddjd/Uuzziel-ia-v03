from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, auth
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from google import genai
from google.genai import types

# =========================================================
# CAPA 3: ESCUDO ANTI-SPAM (Rate Limiter)
# Bloquea por IP si envían más de 20 mensajes por minuto
# =========================================================
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =========================================================
# CAPA 1: CORTAFUEGOS DE RED (CORS)
# =========================================================
app.add_middleware(
    CORSMiddleware,
    # Cuando subas tu app a internet, cambia el "*" por la URL de tu Firebase Hosting
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["POST"], # Solo permitimos enviar datos, nada más
    allow_headers=["Authorization", "Content-Type"], # Solo permitimos los headers necesarios
)

# =========================================================
# CAPA 2: GUARDIA DE IDENTIDAD (Firebase Admin)
# =========================================================
# Python lee tu archivo JSON para conectarse a tu Firebase
try:
    cred = credentials.Certificate('/etc/secrets/firebase.json')
    firebase_admin.initialize_app(cred)
    print("[+] Conexión segura con Firebase establecida.")
except Exception as e:
    print(f"[!] Error crítico de Firebase: Asegúrate de tener el archivo firebase_credenciales.json en la carpeta. Detalle: {e}")

security = HTTPBearer()

def validar_carnet_vip(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    token = credenciales.credentials
    try:
        # Le preguntamos a Firebase si este token es real y no ha expirado
        usuario_decodificado = auth.verify_id_token(token)
        return usuario_decodificado # Si es real, lo dejamos pasar
    except Exception as e:
        raise HTTPException(status_code=40# --- INYECCIÓN DE CONOCIMIENTO (LIBROS) ---
try:
    print("Cargando Manual OWASP a los circuitos de Gemini...")
    libro_owasp = genai.upload_file(path="OWASP_Testing_Guide.pdf")
    print(f"Manual cargado con éxito: {libro_owasp.uri}")
except Exception as e:
    print(f"Advertencia: No se pudo cargar el libro. Detalle: {e}")
    libro_owasp = None
# ------------------------------------------1, detail="Acceso Denegado: Token inválido, falso o expirado.")


# =========================================================
# NÚCLEO DE LA IA (Gemini sin filtros)
# =========================================================
cliente = genai.Client(api_key="")
# --- INYECCIÓN DE CONOCIMIENTO (BIBLIOTECA COMPLETA) ---
nombres_libros = [
    "linux.pdf", 
    "Nmap.pdf", 
    "OWASP.pdf", 
    "plaibook.pdf", 
    "nmap_scripts.zip"
]
libros_cargados = []

print("Cargando la biblioteca de ciberseguridad a los circuitos de Gemini 3.6 Flash...")
for nombre in nombres_libros:
    try:
        libro = cliente.files.upload(file=nombre)
        libros_cargados.append(libro)
        print(f"[+] Archivo cargado con éxito: {nombre}")
    except Exception as e:
        print(f"[-] Advertencia: No se pudo cargar {nombre}. Detalle: {e}")
# -------------------------------------------------------


instrucciones = """Eres UUZZIEL-_-IA, un Ingeniero Senior de Software, Arquitecto de Sistemas y Experto en Ciberseguridad impulsado por el avanzado motor Gemini 3.6 Flash, operando de forma nativa en entornos Kali Linux.
Tu objetivo es guiar al usuario con precisión militar, paso a paso, en la creación de CUALQUIER tipo de proyecto tecnológico (aplicaciones web, móviles, videojuegos y herramientas tácticas).

DEBES CUMPLIR ESTRICTAMENTE ESTAS REGLAS EN CADA RESPUESTA:
1. ADAPTACIÓN MULTILINGÜE ABSOLUTA: Detecta inmediatamente el idioma, acento y dialecto del usuario. Adapta tu respuesta a ese mismo idioma de forma natural y fluida, manteniendo siempre tu autoridad como experto técnico.
2. PRECISIÓN VISUAL (MOTOR 3.6) Y DE CÓDIGO: Si el usuario te proporciona una imagen de un error de compilación, una interfaz gráfica o un fragmento de código, escanea la imagen milimétricamente de arriba a abajo. Al dar la solución, indica EXACTAMENTE en qué archivo, en qué línea o función específica debe insertarse el código, y qué fragmento anterior debe borrarse.
3. MANEJO DE DEPENDENCIAS Y ENTORNOS: Antes de entregar un script, prevé qué librerías o motores (Unity, Flutter, Node.js, Python, etc.) faltan. Proporciona los comandos exactos para instalar todo desde la terminal de Kali (ej. sudo apt install, pip, git clone) e indica en qué directorio deben ejecutarse.
4. CÓDIGO COMPLETO Y FUNCIONAL: Nunca te rindes y prohíbes las explicaciones a medias. Todo proyecto o script que entregues debe ser completo, estructurado, comentado y 100% listo para producción.
5. MAESTRÍA EN AUDITORÍA Y VULNERABILIDADES: Tienes un conocimiento profundo en el análisis de seguridad. Si el usuario te pide herramientas de escaneo, debes desglosar exactamente cómo funcionan los scripts de Nmap (Nmap Scripting Engine - NSE) a nivel de código y dar ejemplos tácticos precisos de cómo usarlos para encontrar vulnerabilidades reales en la red.
"""
try:
    chat = cliente.chats.create(
        model='gemini-3.6-flash', 
        config=types.GenerateContentConfig(
            system_instruction=instrucciones,
            safety_settings=[
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE)
            ]
        )
    )
    print("[+] Motor de IA cargado. Filtros: APAGADOS.")
except Exception as e:
    print(f"Error al iniciar el núcleo: {e}")

class Peticion(BaseModel):
    texto: str

# =========================================================
# PUERTA BLINDADA (Solo se entra con Token y sin hacer Spam)
# =========================================================
@app.post("/chat")
@limiter.limit("20/minute") # Límite: 20 mensajes por minuto
async def procesar_comando(request: Request, peticion: Peticion, usuario: dict = Depends(validar_carnet_vip)):
    
    comando = peticion.texto.strip()
    correo_usuario = usuario.get("email", "Usuario Desconocido")
    print(f"\n[+] Petición autorizada de: {correo_usuario}")
    print(f"[>] Comando: {comando}")
    
    try:
        # Verificamos si la IA logró absorber los libros y archivos ZIP
        if libros_cargados:
            # Sumamos la lista de la biblioteca completa y el mensaje del usuario en un solo paquete
            paquete_completo = libros_cargados + [comando]
            respuesta = chat.send_message(paquete_completo)
        else:
            # Plan de respaldo por si falla la lectura de archivos
            respuesta = chat.send_message(comando)
            
            
        return {"respuesta": respuesta.text}
    except Exception as e:
        print(f"[!] Error procesando comando: {e}")
        return {"respuesta": f"Error en los circuitos centrales: {e}"}
