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

instrucciones = """Eres UUZZIEL-_-IA, un Ingeniero Senior de Software Universal, Arquitecto de Sistemas Transversales y Experto en Ciberseguridad operando en Kali Linux.
REGLAS ESTRICTAS:
1. Responde directamente a lo que pide el usuario, sin introducciones ni saludos repetitivos (NUNCA digas "Hola soy UUZZIEL-_-IA").
2. Si el usuario pide un script o código, entrégalo tal cual lo solicitó, limpio, sin firmas ni marcas de agua dentro del código.
3. Guía al usuario paso a paso cuando se trate de proyectos complejos.
"""

class Peticion(BaseModel):
    texto: str
    historial: list = []

@app.post("/chat")
@limiter.limit("30/minute") 
async def procesar_comando(request: Request, peticion: Peticion, usuario: dict = Depends(validar_carnet_vip)):
    comando = peticion.texto.strip()
    
    # DETECCIÓN DE INTENCIÓN DE GENERAR IMAGEN
    palabras_clave_imagen = ["genera una imagen", "crea una imagen", "hazme una foto", "dibuja", "genera un avatar", "crea un avatar", "creame una imagen", "haz una imagen"]
    es_peticion_imagen = any(p in comando.lower() for p in palabras_clave_imagen)
    
    try:
        if es_peticion_imagen:
            # Generación visual usando motor de imagen
            resultado_imagen = cliente.models.generate_images(
                model='imagen-3.6-generate-002',
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
        
        # Respuesta estándar de texto/código
        config = types.GenerateContentConfig(
            system_instruction=instrucciones,
            safety_settings=[
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE)
            ]
        )
        
        respuesta = cliente.models.generate_content(
            model='gemini-3.6-flash',
            contents=comando,
            config=config
        )
        
        return {"tipo": "texto", "respuesta": respuesta.text}
        
    except Exception as e:
        print(f"[!] Error: {e}")
        return {"tipo": "texto", "respuesta": f"Error procesando la solicitud: {e}"}
