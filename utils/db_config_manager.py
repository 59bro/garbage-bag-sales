# ============================================================
# utils/db_config_manager.py  —  DB 연결(로컬/클라우드/네트워크 공유) 설정 관리
# ============================================================

import os
import sys
import json


def get_root_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_path():
    root = get_root_dir()
    if getattr(sys, 'frozen', False):
        p1 = os.path.join(root, 'db_config.json')
        if os.path.exists(p1):
            return p1
        p2 = os.path.join(root, 'config', 'db_config.json')
        if os.path.exists(p2):
            return p2
        return p1
    else:
        return os.path.join(root, 'config', 'db_config.json')


def resolve_sqlite_path(path_str: str) -> str:
    if not path_str:
        return ""
    if os.path.exists(path_str):
        return path_str
    
    # 1. 다른 PC에서 구글 드라이브 드라이브 문자(G:, D:, E:, Z: 등)가 다를 경우 자동 탐색
    if ":" in path_str and ("내 드라이브" in path_str or "Google Drive" in path_str or "종량제봉투_통합DB" in path_str):
        sub_path = path_str.split(":", 1)[-1]
        for drive in ['G:', 'D:', 'E:', 'F:', 'H:', 'I:', 'J:', 'K:', 'Z:', 'C:']:
            candidate = drive + sub_path
            if os.path.exists(candidate):
                return candidate

    # 2. 만약 실행 파일 옆이나 data 폴더 내에 sales.db가 있으면 대체
    root = get_root_dir()
    local_db = os.path.join(root, 'data', 'sales.db')
    if os.path.exists(local_db):
        return local_db
    local_db2 = os.path.join(root, 'sales.db')
    if os.path.exists(local_db2):
        return local_db2

    return path_str


def get_db_config() -> dict:
    root = get_root_dir()
    config_path = get_config_path()
    default_config = {
        "db_mode": "sqlite",           # 'sqlite' or 'postgres'
        "sqlite_path": os.path.join(root, 'data', 'sales.db'),
        "cloud_host": "",
        "cloud_port": 5432,
        "cloud_dbname": "garbage_sales",
        "cloud_user": "postgres",
        "cloud_password": ""
    }
    if not os.path.exists(config_path):
        save_db_config(default_config)
        return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for k, v in default_config.items():
                if k not in data:
                    data[k] = v
            if data.get("db_mode", "sqlite") == "sqlite" and data.get("sqlite_path"):
                resolved = resolve_sqlite_path(data["sqlite_path"])
                if resolved != data["sqlite_path"] and os.path.exists(resolved):
                    data["sqlite_path"] = resolved
            return data
    except Exception:
        return default_config


def save_db_config(config_dict: dict):
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=4)
