#!/usr/bin/env python3
"""AIDEN Desktop – Python backend (FastAPI sidecar for Tauri).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from common.audit import init_audit

from routes import chat as chat_routes
from routes import models as models_routes
from routes import processes as processes_routes
from routes import images as images_routes
from routes import settings as settings_routes
from routes import mesh as mesh_routes
from routes import conversations as conversations_routes


@asynccontextmanager
async def lifespan(application):
    init_audit()
    yield


app = FastAPI(title='AIDEN Backend', version='1.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(chat_routes.router)
app.include_router(models_routes.router)
app.include_router(processes_routes.router)
app.include_router(images_routes.router)
app.include_router(settings_routes.router)
app.include_router(mesh_routes.router)
app.include_router(conversations_routes.router)


@app.get('/health')
async def health():
    return {'status': 'ok', 'version': '1.0.0'}


def main():
    uvicorn.run(
        app,
        host='127.0.0.1',
        port=9090,
        reload=False,
        log_level='info',
    )


if __name__ == '__main__':
    main()
