# ============================================================
# utils/format_utils.py
# 숫자 / 금액 / 날짜 포맷 유틸
# ============================================================

def fmt_number(value) -> str:
    """숫자에 천 단위 콤마. None이면 '-' 반환."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return '-'


def fmt_currency(value) -> str:
    """금액 포맷 (원). 예: 1,500원"""
    try:
        return f"{int(value):,}원"
    except (TypeError, ValueError):
        return '-'


def fmt_date_display(date_str: str) -> str:
    """'2024-01-15' → '2024년 01월 15일'"""
    try:
        y, m, d = date_str.split('-')
        return f"{y}년 {m}월 {d}일"
    except Exception:
        return date_str


def parse_number(text: str) -> int:
    """콤마 포함 문자열 → 정수. 실패시 0."""
    try:
        return int(text.replace(',', '').strip())
    except (ValueError, AttributeError):
        return 0
