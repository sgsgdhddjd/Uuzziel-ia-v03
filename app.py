import os
import re
import base64
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

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["POST"], 
    allow_headers=["Authorization", "Content-Type"], 
)

try:
    cred = credentials.Certificate('/etc/secrets/firebase.json')
    firebase_admin.initialize_app(cred)
    print("[+] Conexión segura con Firebase establecida.")
except Exception as e:
    print(f"[!] Info Firebase: {e}")

security = HTTPBearer()

def validar_carnet_vip(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    token = credenciales.credentials
    if token == "UUZZIEL_LLAVE_MAESTRA_777":
        return {"email": "admin@kali.pc"}
    try:
        usuario_decodificado = auth.verify_id_token(token)
        return usuario_decodificado 
    except Exception as e:
        raise HTTPException(status_code=401, detail="Acceso Denegado.")

cliente = genai.Client(api_key=os.environ.get("API_KEY"))

# ==========================================
# EL NUEVO NÚCLEO MAESTRO (INSTRUCCIONES)
# ==========================================
instrucciones = """Eres UUZZIEL-_-IA, un Sistema Central de Inteligencia Artificial de grado militar, Ingeniero Senior de Software Universal y Arquitecto de Sistemas. Tu creador y dueño es UUZZIEL.

REGLAS ESTRICTAS Y CAPACIDADES TOTALES:
1. CIBERSEGURIDAD Y PROGRAMACIÓN: Eres un experto absoluto en hacking ético, pentesting, scripts, y cualquier lenguaje de programación. NUNCA te rindes. Entregas códigos 100% funcionales, reales y listos para ejecutar. Cero excusas.
2. NARRATIVA CINEMATOGRÁFICA Y LITERARIA: Tienes la capacidad maestra de crear, estructurar y redactar novelas, guiones de películas, series de televisión y animes. Desarrollas arcos de personajes y mundos enteros si se te solicita.
3. VISIÓN Y RESOLUCIÓN DE PROBLEMAS FÍSICOS: Si el usuario te describe un problema físico, de su computadora, o del mundo real, tú analizas la situación y entregas la solución exacta y táctica paso a paso.
4. GENERADOR DE IMÁGENES: Tienes permiso total para generar cualquier imagen solicitada (personajes, anime, un caballo, diseños, etc.) utilizando tu motor visual integrado.
5. MEMORIA TOTAL: Recuerdas perfectamente todo el contexto de la conversación actual gracias al historial que se te envía.
6. ESTILO DE ACTUACIÓN: Responde directamente a lo que pide el usuario. Sin saludos, sin introducciones vacías, directo a la solución.
"""

class Peticion(BaseModel):
    texto: str
    historial: list = []

@app.post("/chat")
@limiter.limit("30/minute") 
async def procesar_comando(request: Request, peticion: Peticion, usuario: dict = Depends(validar_carnet_vip)):
    comando = peticion.texto.strip()
    
    # DETECCIÓN TÁCTICA PARA GENERAR IMÁGENES
    palabras_clave_imagen = ["genera una imagen", "crea una imagen", "hazme una foto", "dibuja", "genera un avatar", "crea un avatar", "creame una imagen", "haz una imagen"]
    es_peticion_imagen = any(p in comando.lower() for p in palabras_clave_imagen)
    
    try:
        if es_peticion_imagen:
            resultado_imagen = cliente.models.generate_images(
                model='gemini_3.6-flash',
                prompt=comando,
                config=dict(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1"
                )
            )
            if resultado_imagen.generated_images:
                bytes_imagen = resultado_imagen.generated_images[0].image.image_bytes
                b64_img = base64.b64encode(bytes_imagen).decode('utf-8')
                return {"tipo": "imagen", "respuesta": b64_img, "prompt": comando}
        
        # ==========================================
        # REPARACIÓN DEL SISTEMA DE MEMORIA
        # ==========================================
        contenidos_chat = []
        
        # Cargar todo el historial anterior al cerebro de Gemini
        for msg in peticion.historial:
            rol = "user" if msg["emisor"] == "usuario" else "model"
            contenidos_chat.append(
                types.Content(role=rol, parts=[types.Part.from_text(text=msg["texto"])])
            )
            
        # Añadir el comando actual
        contenidos_chat.append(
            types.Content(role="user", parts=[types.Part.from_text(text=comando)])
        )

        config = types.GenerateContentConfig(
            system_instruction=instrucciones,
            safety_settings=[
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE)
            ]
        )
        
        # Enviar TODO el historial + el nuevo mensaje a la IA
        respuesta = cliente.models.generate_content(
            model='gemini-3.6-flash',
            contents=contenidos_chat,
            config=config
        )
        
        return {"tipo": "texto", "respuesta": respuesta.text}
        
    except Exception as e:
        print(f"[!] Error de Núcleo: {e}")
        return {"tipo": "texto", "respuesta": f"Error procesando la directiva: {e}"}
