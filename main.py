from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
 
from config import db

from routes.reclamos.reclamos import router as reclamos_router
from routes.recuperacion.recuperacion import router as recuperacion_router
from routes.notificar.nuevoencargado import router as notificar_router

load_dotenv()

app = FastAPI(title="API Mortadela Mail", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reclamos_router)
app.include_router(recuperacion_router)
app.include_router(notificar_router)