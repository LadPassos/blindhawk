import time
import random
import hashlib
import base64
import secrets
import logging
import io
import requests
import os
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
from fastapi.staticfiles import StaticFiles

# Rate-Limiting (opcional)
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import aioredis

# NLP e NLTK
from unidecode import unidecode
from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.corpus import mac_morpho

# Baixa corpus NLTK
nltk.download('mac_morpho')

# Áudio, Ruído e TTS
from pydub import AudioSegment
from pydub.generators import WhiteNoise
from gtts import gTTS

# =========================================
# CONFIGURAÇÕES E INICIALIZAÇÕES
# =========================================

app = FastAPI()

# Logger
logger = logging.getLogger("captcha_app")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Rate-Limiting (Ex.: 5 req/min em /audio-captcha)
@app.on_event("startup")
async def startup():
    redis_url = os.getenv("REDIS_URL", "redis://meu-redis.fly.dev:6379")
    redis = await aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="templates"), name="static")

# Modelo de Similaridade
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Armazena sessões de captcha
captcha_sessions = {}

CAPTCHA_LIFETIME = 120  # 2 minutos
key = Fernet.generate_key()  # Se precisar criptografia
cipher_suite = Fernet(key)

# =========================================
# FUNÇÕES AUXILIARES
# =========================================

def generate_session_token():
    """Gera um token de sessão randômico."""
    return secrets.token_urlsafe(16)

def is_captcha_expired(captcha_data: dict) -> bool:
    """Verifica se o captcha expirou baseado no tempo."""
    return time.time() > captcha_data["expire_time"]

def generate_random_word():
    """Pega uma palavra com mais de 4 letras do corpus mac_morpho."""
    words = list(set(mac_morpho.words()))
    long_words = [w.lower() for w in words if len(w) > 4]
    return random.choice(long_words) if long_words else "captcha"

def semantic_similarity(user_input, correct_text, threshold=0.6) -> bool:
    """Compara similaridade semântica entre input do usuário e a resposta correta."""
    user_input = unidecode(user_input.strip().lower())
    user_emb = model.encode(user_input, convert_to_tensor=True)
    correct_emb = model.encode(correct_text, convert_to_tensor=True)
    sim = util.cos_sim(user_emb, correct_emb).max().item()
    logger.info(f"Similaridade calculada: {sim}")
    return sim > threshold

def download_freesound_sound(query, duration=5000):
    """
    Baixa um som do Freesound.org com base em query.
    Se falhar, retorna None.
    """
    # Substitua pela sua API key do Freesound
    API_KEY = "OdsllSfqInRvKosXn6bPrL8wUT3il47PBsww8BBh"

    url = f"https://freesound.org/apiv2/search/text/?query={query}&fields=id,previews,duration&token={API_KEY}"
    logger.info(f"Buscando FreedSound para: {query}")
    resp = requests.get(url)
    if resp.status_code != 200:
        logger.error("Erro na busca FreedSound")
        return None

    data = resp.json()
    results = data.get("results")
    if not results:
        logger.warning("Nenhum resultado FreedSound")
        return None

    chosen = random.choice(results)
    preview_url = chosen["previews"]["preview-hq-mp3"]
    logger.info(f"Baixando FreedSound de: {preview_url}")
    sound_resp = requests.get(preview_url)
    if sound_resp.status_code != 200:
        return None

    audio = AudioSegment.from_file(io.BytesIO(sound_resp.content), format="mp3")
    # Limita a 'duration' se for maior
    if len(audio) > duration:
        audio = audio[:duration]
    # Diminui volume para mesclar
    audio = audio - 10
    return audio

# =========================================
# ROTAS
# =========================================

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    # Ex.: cabeçalhos de segurança
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.get("/audio-captcha", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def generate_audio_captcha():
    """
    Gera um captcha de áudio, 50% chance TTS, 50% FreedSound.
    Retorna session_token para posterior verificação.
    """
    try:
        expire_time = time.time() + CAPTCHA_LIFETIME
        captcha_id = hashlib.sha256(str(time.time()).encode()).hexdigest()
        session_token = generate_session_token()

        # Decide 50% -> palavra TTS ; 50% -> FreedSound
        use_word = random.choice([True, False])
        if use_word:
            # Gera texto do NLTK e converte via gTTS
            correct_text = generate_random_word()
            tts = gTTS(correct_text, lang="pt")
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            audio_segment = AudioSegment.from_file(buf, format="mp3")
        else:
            # FreedSound
            possible_queries = ["dog barking", "siren", "talking", "birds chirping",
                                "car horn", "rain", "wind", "laughing"]
            chosen_query = random.choice(possible_queries)
            audio_segment = download_freesound_sound(chosen_query, duration=5000)
            if audio_segment is None:
                # fallback => ruído + "noise"
                correct_text = "noise"
                audio_segment = WhiteNoise().to_audio_segment(duration=3000)
            else:
                correct_text = chosen_query

        # Adiciona ruído adversário
        noise = WhiteNoise().to_audio_segment(duration=len(audio_segment))
        noise = noise - random.randint(15, 25)
        audio_segment = audio_segment.overlay(noise)

        # Exporta
        out_buf = io.BytesIO()
        audio_segment.export(out_buf, format="mp3", bitrate="192k")
        out_buf.seek(0)
        encoded_audio = base64.b64encode(out_buf.read()).decode('utf-8')

        # Armazena
        captcha_sessions[captcha_id] = {
            "answer": correct_text,
            "session_token": session_token,
            "expire_time": expire_time
        }

        logger.info(f"Gerei captcha_id={captcha_id}, Resposta='{correct_text}'")

        return {
            "audio": encoded_audio,
            "captcha_id": captcha_id,
            "session_token": session_token,
            "expire_time": expire_time
        }
    except Exception as e:
        logger.exception("Erro ao gerar captcha de áudio.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erro interno ao gerar CAPTCHA")

class CaptchaVerifyModel(BaseModel):
    captcha_text: str
    captcha_id: str
    session_token: str = None

@app.post("/verify-captcha")
async def verify_captcha(body: CaptchaVerifyModel):
    """
    Verifica a similaridade do captcha_text com a resposta.
    Exige session_token para segurança (se front enviar).
    """
    try:
        captcha_id = body.captcha_id
        session_token = body.session_token
        user_input = body.captcha_text

        # Limita tamanho do input
        if len(user_input) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entrada muito longa."
            )

        if captcha_id not in captcha_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Captcha expirado ou inexistente."
            )

        data = captcha_sessions[captcha_id]
        if is_captcha_expired(data):
            del captcha_sessions[captcha_id]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este CAPTCHA expirou. Gere um novo."
            )

        # Checa token
        if session_token is not None and session_token != data["session_token"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de sessão inválido."
            )

        correct_text = data["answer"]
        if semantic_similarity(user_input, correct_text):
            del captcha_sessions[captcha_id]  # remove após uso
            return {"success": True, "message": "CAPTCHA correto!"}
        else:
            return {"success": False, "message": "CAPTCHA incorreto. Tente novamente."}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Erro ao verificar CAPTCHA.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na verificação do CAPTCHA"
        )

@app.get("/")
async def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
