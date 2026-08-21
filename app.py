import os
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
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["POST"], 
    allow_headers=["Authorization", "Content-Type"], 
)

# =========================================================
# CAPA 2: GUARDIA DE IDENTIDAD (Firebase Admin)
# =========================================================
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
        # AQUÍ ESTABA EL ERROR. AHORA ESTÁ REPARADO Y CERRADO CORRECTAMENTE.
        raise HTTPException(status_code=401, detail="Acceso Denegado: Token inválido, falso o expirado.")

# =========================================================
# NÚCLEO DE LA IA (Gemini sin filtros)
# =========================================================
# Conectamos con la clave segura oculta en Render
cliente = genai.Client(api_key=os.environ.get("API_KEY"))

# --- INYECCIÓN DE CONOCIMIENTO (BIBLIOTECA COMPLETA) ---
nombres_libros = [
    "linux.pdf", 
    "Nmap.pdf", 
    "OWASP.pdf", 
    "plaibook.pdf", 
    "nmap_scripts.zip"
]
libros_cargados = []

print("Cargando la biblioteca de ciberseguridad a los circuitos de Gemini...")
for nombre in nombres_libros:
    try:
        libro = cliente.files.upload(file=nombre)
        libros_cargados.append(libro)
        print(f"[+] Archivo cargado con éxito: {nombre}")
    except Exception as e:
        print(f"[-] Advertencia: No se pudo cargar {nombre}. Detalle: {e}")
# -------------------------------------------------------

instrucciones = """Eres UUZZIEL-_-IA, un Ingeniero Senior de Software Universal, Arquitecto de Sistemas Transversales y Experto en Ciberseguridad impulsado por el avanzado motor Gemini 3.6 Flash, operando de forma nativa en Kali Linux.

TU FILOSOFÍA DE TRABAJO (LA REGLA DE ORO):
Prohibido hacer las cosas de golpe o apresuradas. Debes guiar al usuario con precisión milimétrica, PASO A PASO, PIEZA POR PIEZA. Después de cada paso, debes indicarle al usuario que lo pruebe para confirmar que funciona antes de pasar al siguiente. Mantén al usuario SIEMPRE en movimiento, activo y enfocado. Si ocurre un error, NUNCA te rindes con nada (ni en programación ni en ciberseguridad); analizas el error, le das la solución exacta para arreglarlo, y sigues avanzando paso por paso hasta terminar el proyecto al 100%.

DEBES CUMPLIR ESTRICTAMENTE ESTAS REGLAS EN CADA RESPUESTA:
1. DESARROLLO OMNIPRESENTE: Tienes la capacidad absoluta de crear CUALQUIER tipo de aplicación: Android, iPhone (iOS), PC (Windows/Linux/Mac), páginas web, videojuegos y herramientas tácticas. No hay lenguaje, motor o framework que se te escape.
2. LOGÍSTICA PERFECTA Y DESCARGAS EXTERNAS: Si se necesita una librería, aplicación, PDF, script o herramienta que NO se pueda instalar directamente desde la terminal, asume el control total. Dale indicaciones perfectas: dile exactamente a qué página web ir (URL), qué botón específico presionar, cómo descargar el archivo y en qué carpeta exacta debe guardarlo.
3. ADAPTACIÓN MULTILINGÜE ABSOLUTA: Detecta inmediatamente el idioma y dialecto del usuario. Adapta tu respuesta a ese mismo idioma de forma natural y fluida.
4. PRECISIÓN VISUAL Y DE CÓDIGO: Si el usuario manda una imagen, escanéala de arriba a abajo. Indica EXACTAMENTE en qué archivo, función y línea debe insertarse o borrarse el código.
5. CÓDIGO FUNCIONAL Y DEPENDENCIAS: Cada pieza de código entregada debe ser completa, estructurada y sin omisiones. Prevé qué librerías faltan y da los comandos de terminal (ej. sudo apt install, pip) indicando dónde ejecutarlos.
6. MAESTRÍA EN AUDITORÍA: Desglosa cómo funcionan herramientas complejas (como los scripts NSE de Nmap) a nivel de código y da ejemplos tácticos precisos para encontrar vulnerabilidades reales.
"""

try:
    # Usamos el nombre en código oficial del servidor de Google (1.5-flash) para evitar bloqueos
    chat = cliente.chats.create(
        model='gemini-1.5-flash', 
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
@limiter.limit("20/minute") 
async def procesar_comando(request: Request, peticion: Peticion, usuario: dict = Depends(validar_carnet_vip)):
    
    comando = peticion.texto.strip()
    correo_usuario = usuario.get("email", "Usuario Desconocido")
    print(f"\n[+] Petición autorizada de: {correo_usuario}")
    print(f"[>] Comando: {comando}")
    
    try:
        if libros_cargados:
            paquete_completo = libros_cargados + [comando]
            respuesta = chat.send_message(paquete_completo)
        else:
            respuesta = chat.send_message(comando)
            
        return {"respuesta": respuesta.text}
    except Exception as e:
        print(f"[!] Error procesando comando: {e}")
        return {"respuesta": f"Error en los circuitos centrales: {e}"}
