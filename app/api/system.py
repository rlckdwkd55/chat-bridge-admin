# app/api/system.py
from fastapi import APIRouter
from datetime import datetime
import psutil
import shutil
import platform
import GPUtil

router = APIRouter(
    prefix="/api/system",
    tags=["system"],
)


def get_gpu_info():
    """첫 번째 GPU 정보만 반환 (없으면 None)"""
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return None

        g = gpus[0]
        return {
            "name": g.name,
            "load_percent": round(g.load * 100, 1),
            "mem_used": g.memoryUsed,       # MB
            "mem_total": g.memoryTotal,     # MB
            "mem_percent": round(g.memoryUtil * 100, 1),
            "temperature": g.temperature,   # °C
        }
    except Exception:
        return None


def get_top_processes(limit: int = 10):
    """CPU 사용률 기준 상위 프로세스 반환"""
    try:
        processes = []
        # pid, name, memory_percent, cpu_percent 필드만 미리 가져옴
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                pinfo = proc.info

                cpu = pinfo.get('cpu_percent') or 0
                mem = pinfo.get('memory_percent') or 0

                # 완전 0인 프로세스는 굳이 안 보여주고 싶으면 필터링
                if cpu > 0 or mem > 0:
                    processes.append({
                        "pid": pinfo.get("pid"),
                        "name": pinfo.get("name") or "",
                        "cpu_percent": cpu,
                        "memory_percent": mem,
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # CPU 사용률 기준 정렬
        processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        return processes[:limit]
    except Exception as e:
        print(f"Error getting processes: {e}")
        return []


def get_disk_usage() -> dict:
    """OS에 따라 기본 디스크 경로(C: 또는 /) 사용량 반환"""
    try:
        if platform.system() == "Windows":
            path = "C:\\"
        else:
            path = "/"

        usage = shutil.disk_usage(path)
        total = usage.total
        used = usage.used
        if total > 0:
            percent = round(used / total * 100, 1)
        else:
            percent = 0.0

        return {
            "total": total,
            "used": used,
            "percent": percent,
        }
    except Exception:
        # 실패 시 0으로 처리
        return {
            "total": 0,
            "used": 0,
            "percent": 0.0,
        }


def get_system_info() -> dict:
    """psutil + GPUtil로 시스템 정보 수집해서 dict로 반환"""
    # CPU (interval을 약간 줘야 의미 있는 값이 나옴)
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # 메모리
    mem = psutil.virtual_memory()

    # 디스크
    disk = get_disk_usage()

    # GPU
    gpu = get_gpu_info()

    # Top Processes
    processes = get_top_processes(limit=10)

    return {
        "cpu_percent": cpu_percent,
        "memory": {
            "total": mem.total,
            "used": mem.used,
            "percent": mem.percent,
        },
        "disk": disk,
        "gpu": gpu,
        "processes": processes,
    }


@router.get("/info")
def system_info():
    """GET /api/system/info"""
    return get_system_info()
