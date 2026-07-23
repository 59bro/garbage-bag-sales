@echo off
chcp 65001 > nul
echo 종량제 봉투 판매 관리 시스템 시작 중...
cd /d "%~dp0"
C:\Users\junas\AppData\Local\Python\bin\python.exe main.py
pause
