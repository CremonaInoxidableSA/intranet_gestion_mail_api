from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routers.reclamos.reclamos import router as reclamos_router
from routers.recuperacion.recuperacion import router as recuperacion_router

load_dotenv()

app = FastAPI(title="API Mortadela Mail", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://{os.getenv('FRONTEND_IP')}:3000",
        "http://localhost:3000",
        "http://192.168.20.59:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reclamos_router)
app.include_router(recuperacion_router)

@app.get("/")
def hola():
    return {"mensaje": "API de Reclamos y Reportes"}