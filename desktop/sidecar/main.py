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

from common.audit import init_audit

app = FastAPI(title='AIDEN Backend', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
async def startup():
    init_audit()

@app.get('/health')
async def health():
    return {'status': 'ok', 'version': '1.0.0'}


def main():
    uvicorn.run(
        'main:app',
        host='127.0.0.1',
        port=9090,
        reload=False,
        log_level='info',
    )


if __name__ == '__main__':
    main()
