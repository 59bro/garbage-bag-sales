# ============================================================
# build_exe.py  —  종량제 봉투 판매 관리 시스템 실행파일(.exe) 빌드 스크립트
# ============================================================

import os
import sys
import shutil
import PyInstaller.__main__

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    root_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(root_dir, 'dist')
    build_dir = os.path.join(root_dir, 'build')

    print("======================================================")
    print(" [BUILD START] 종량제 봉투 판매 관리 시스템 (.exe) 빌드 시작")
    print("======================================================")

    sys.setrecursionlimit(100000)

    # 1. 빌드 파라미터 구성 (.spec 파일 사용하여 재귀 한도 문제 방지)
    spec_path = os.path.join(root_dir, '종량제봉투_판매관리시스템.spec')
    if os.path.exists(spec_path):
        params = [
            spec_path,
            '--noconfirm',
            '--clean'
        ]
    else:
        params = [
            'main.py',
            '--name=종량제봉투_판매관리시스템',
            '--windowed',
            '--noconfirm',
            '--clean',
            '--hidden-import=PyQt5',
            '--hidden-import=PyQt5.QtCore',
            '--hidden-import=PyQt5.QtGui',
            '--hidden-import=PyQt5.QtWidgets',
            '--hidden-import=sqlite3',
            '--hidden-import=xlrd',
            '--hidden-import=xlwt',
            '--hidden-import=xlutils',
            '--hidden-import=xlutils.copy',
            '--hidden-import=win32com.client',
            '--exclude-module=torch',
            '--exclude-module=torchvision',
            '--exclude-module=easyocr',
            '--exclude-module=scipy',
            '--exclude-module=pandas',
            '--exclude-module=matplotlib',
            '--add-data=config;config',
        ]

    # PyInstaller 실행
    PyInstaller.__main__.run(params)

    # 2. dist 폴더 내 필수 기본 구조(data 폴더 등) 생성
    output_folder = os.path.join(dist_dir, '종량제봉투_판매관리시스템')
    os.makedirs(os.path.join(output_folder, 'data'), exist_ok=True)
    os.makedirs(os.path.join(output_folder, 'config'), exist_ok=True)

    # config 파일이 있으면 복사
    cfg_src = os.path.join(root_dir, 'config', 'db_config.json')
    cfg_dst = os.path.join(output_folder, 'config', 'db_config.json')
    if os.path.exists(cfg_src):
        shutil.copyfile(cfg_src, cfg_dst)

    print("\n======================================================")
    print(" [BUILD SUCCESS] 빌드 성공!")
    print(f" 실행 파일 경로: {os.path.join(output_folder, '종량제봉투_판매관리시스템.exe')}")
    print("======================================================")

if __name__ == '__main__':
    main()
