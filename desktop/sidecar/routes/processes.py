"""Process management – code execution, systemd services, system info."""
import os
import json
import signal
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from common.sandbox import run_sandboxed
from common.audit import emit_code_exec, emit_privileged
from settings import load_settings, get_code_exec_mode

router = APIRouter(prefix="/processes", tags=["processes"])


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 30
    session_id: str = ""


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    sandbox: str
    timeout: bool


class ServiceAction(BaseModel):
    name: str
    action: str  # start, stop, restart, status


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(req: ExecuteRequest):
    settings = load_settings()
    mode = get_code_exec_mode()

    import hashlib
    code_hash = hashlib.sha256(req.code.encode()).hexdigest()[:16]

    result = run_sandboxed(
        code=req.code,
        language=req.language,
        timeout=req.timeout,
    )

    emit_code_exec(
        user=os.getenv("USER", "unknown"),
        session=req.session_id or "none",
        lang=req.language,
        code_hash=code_hash,
        approved=(mode != "click_to_run"),
        sandbox="bubblewrap",
        exit_code=result["exit_code"],
        mode=mode,
    )

    return ExecuteResponse(
        stdout=result["stdout"],
        stderr=result["stderr"],
        exit_code=result["exit_code"],
        sandbox="bubblewrap",
        timeout=result["timeout"],
    )


@router.get("/services")
async def list_services():
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--no-pager",
             "--no-legend", "--plain"],
            capture_output=True, text=True, timeout=10,
        )
        services = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(None, 4)
            if len(parts) >= 4:
                services.append({
                    "name": parts[0],
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3],
                    "description": parts[4] if len(parts) > 4 else "",
                })
        return {"services": services}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Service list timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="systemctl not found")


@router.post("/services/{action}")
async def service_action(name: str, action: str):
    allowed_actions = {"start", "stop", "restart", "status"}
    if action not in allowed_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    try:
        result = subprocess.run(
            ["systemctl", action, name],
            capture_output=True, text=True, timeout=30,
        )
        emit_privileged(
            user=os.getenv("USER", "unknown"),
            action=f"service_{action}",
            status="success" if result.returncode == 0 else "failed",
            details=name,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Service action timed out")


@router.get("/info")
async def system_info():
    import psutil
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(),
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
        }
    except ImportError:
        return {"error": "psutil not installed"}
