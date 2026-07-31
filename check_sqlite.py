"""SQLite -> PostgreSQL 마이그레이션 스크립트"""
import sqlite3
import sys
import os

SQLITE_PATH = r"G:\내 드라이브\종량제봉투_통합DB\sales.db"

# 1단계: SQLite 데이터 확인
print("=" * 60)
print(" SQLite 데이터 확인")
print("=" * 60)

if not os.path.exists(SQLITE_PATH):
    print(f"[ERROR] SQLite DB 파일을 찾을 수 없습니다: {SQLITE_PATH}")
    sys.exit(1)

conn = sqlite3.connect(SQLITE_PATH)
conn.row_factory = sqlite3.Row

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"테이블 목록: {tables}")
for t in tables:
    cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"  {t}: {cnt} rows")

conn.close()
print("\n[OK] SQLite DB 확인 완료")
