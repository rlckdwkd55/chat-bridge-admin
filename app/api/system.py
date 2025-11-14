# app/api/system.py
from fastapi import APIRouter
from datetime import datetime
import psutil
import shutil
import platform
import GPUtil

router = APIRouter(
    prefix="/api/system",
    tags=["system"]
)


def get_gpu_info():
    """첫 번째 GPU 정보만 반환"""
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return None

        g = gpus[0]
        return {
            "name": g.name,
            "load_percent": round(g.load * 100, 1),
            "mem_used": g.memoryUsed,      # MB
            "mem_total": g.memoryTotal,    # MB
            "mem_percent": round(g.memoryUtil * 100, 1),
            "temperature": g.temperature,  # °C
        }
    except Exception:
        return None


def get_top_processes(limit=10):
    """CPU 사용률 기준 상위 프로세스 반환"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                pinfo = proc.info
                # cpu_percent는 계산된 값 사용
                if pinfo.get('cpu_percent') is None:
                    pinfo['cpu_percent'] = 0
                if pinfo.get('memory_percent') is None:
                    pinfo['memory_percent'] = 0
                # 0보다 큰 것만 추가
                if pinfo['cpu_percent'] > 0 or pinfo['memory_percent'] > 0:
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # CPU 사용률 기준 정렬
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        return processes[:limit]
    except Exception as e:
        print(f"Error getting processes: {e}")
        return []


def get_system_info() -> dict:
    """psutil + GPUtil로 시스템 정보 수집해서 dict로 반환"""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)

    # 메모리
    mem = psutil.virtual_memory()

    # 디스크 (루트 기준, Windows는 C: 드라이브)
    try:
        if platform.system() == "Windows":
            disk = shutil.disk_usage("C:\\")
        else:
            disk = shutil.disk_usage("/")
    except Exception:
        # 기본값 설정
        disk = type('obj', (object,), {
            'total': 0,
            'used': 0,
            'free': 0
        })()

    # 부팅 시간
    boot_time = datetime.fromtimestamp(
        psutil.boot_time()
    ).isoformat(timespec="seconds")

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
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "percent": round(disk.used / disk.total * 100, 1),
        },
        "gpu": gpu,
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "boot_time": boot_time,
        },
        "processes": processes,
    }


@router.get("/info")
def system_info():
    """GET /api/system/info"""
    return get_system_info()
