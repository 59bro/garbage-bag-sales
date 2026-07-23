# ============================================================
# ui/styles.py  —  라이트 SaaS 테마 (Clova OCR 스타일)
#   사이드바: 다크 네이비  /  콘텐츠: 화이트 클린
# ============================================================

APP_STYLE = """
/* ══ 기반 ══════════════════════════════════════════════════ */
* { font-family: '맑은 고딕'; font-size: 10pt; outline: none; }
QMainWindow { background-color: #f0f2f5; color: #1f2937; }
QWidget     { background-color: #f0f2f5; color: #1f2937; }

/* ══ 사이드바 ═══════════════════════════════════════════════ */
#sidebar {
    background-color: #1b2139;
    border-right: none;
    min-width: 200px; max-width: 200px;
}
#sidebar_logo {
    background: transparent; color: #ffffff;
    font-size: 12pt; font-weight: bold;
    padding: 0; border: none;
}
#sidebar_logo_sub {
    background: transparent; color: #64748b;
    font-size: 8pt; padding: 0; border: none;
}
#nav_btn {
    background: transparent; color: #94a3b8;
    border: none; border-radius: 6px;
    padding: 0 16px; text-align: left;
    font-size: 10pt; font-weight: bold;
    min-height: 42px; max-height: 42px;
    margin: 1px 8px;
}
#nav_btn:hover {
    background: rgba(255,255,255,0.06);
    color: #cbd5e1;
}
#nav_btn_active {
    background: #2563eb;
    color: #ffffff;
    border: none; border-radius: 6px;
    padding: 0 16px; text-align: left;
    font-size: 10pt; font-weight: bold;
    min-height: 42px; max-height: 42px;
    margin: 1px 8px;
}
#nav_section_label {
    background: transparent; color: #374151;
    font-size: 7.5pt; font-weight: bold;
    padding: 4px 20px 2px; border: none;
    letter-spacing: 2px;
}

/* ══ 헤더 ═══════════════════════════════════════════════════ */
#content_area { background: #f0f2f5; }
#page_header {
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    min-height: 64px; max-height: 64px;
}
#page_title {
    background: transparent; color: #111827;
    font-size: 15pt; font-weight: bold; border: none;
}
#page_subtitle {
    background: transparent; color: #9ca3af;
    font-size: 9pt; border: none;
}
#clock_label {
    background: transparent; color: #9ca3af;
    font-size: 9pt; border: none;
}

/* ══ 카드 ═══════════════════════════════════════════════════ */
#card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
#card_title {
    background: transparent; color: #6b7280;
    font-size: 8.5pt; font-weight: bold;
    letter-spacing: 1px; border: none;
}

/* ══ 스탯 카드 ══════════════════════════════════════════════ */
#stat_icon { background:transparent; font-size:17pt; border:none; }
#stat_label {
    background:transparent; font-size:8pt;
    font-weight:bold; letter-spacing:1px; border:none;
}
#stat_value {
    background:transparent; font-size:14pt;
    font-weight:bold; border:none; color:#111827;
}

/* ══ 입력 위젯 ══════════════════════════════════════════════ */
QLineEdit, QTextEdit {
    background: #ffffff; border: 1px solid #d1d5db;
    border-radius: 6px; padding: 6px 10px;
    color: #111827; selection-background-color: #4361EE;
    min-height: 28px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid #4361EE;
}
QLineEdit::placeholder { color: #9ca3af; }

QSpinBox {
    background: #ffffff; border: 1px solid #d1d5db;
    border-radius: 6px; padding: 6px 28px 6px 10px;
    color: #111827; min-height: 28px;
}
QSpinBox:focus { border: 1.5px solid #4361EE; }

QDateEdit {
    background: #ffffff; border: 1px solid #d1d5db;
    border-radius: 6px; padding: 6px 28px 6px 10px;
    color: #111827; min-height: 28px;
}
QDateEdit:focus { border: 1.5px solid #4361EE; }
QDateEdit::drop-down { border: none; width: 26px; }

QComboBox {
    background: #ffffff; border: 1px solid #d1d5db;
    border-radius: 6px; padding: 6px 30px 6px 10px;
    color: #111827; min-height: 28px;
}
QComboBox:focus { border: 1.5px solid #4361EE; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow {
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #6b7280;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background: #ffffff; border: 1px solid #d1d5db;
    border-radius: 6px; selection-background-color: #eff4ff;
    selection-color: #4361EE; color: #111827;
    padding: 4px; outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 12px; border-radius: 4px; min-height: 28px;
    color: #111827;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: #f3f4f6; border: none; width: 18px; border-radius: 3px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #e0e7ff;
}

/* ══ 버튼 (38px 통일, 세련된 팔레트) ══════════════════════
   Primary  : 슬레이트 블루  #4361EE  (인디고 계열, 차분)
   Success  : 포레스트 그린  #2E7D5E  (자연스러운 녹색)
   Danger   : 로즈 레드     #B84040  (과하지 않은 붉은색)
   Warning  : 브론즈 앰버   #A0621A  (따뜻한 황갈색)
   Ghost    : 슬레이트 테두리 (배경 없음)
══════════════════════════════════════════════════════════ */
QPushButton {
    background: #4361EE;
    color: #ffffff;
    border: none; border-radius: 6px;
    padding: 0 20px; font-weight: bold; font-size: 9.5pt;
    min-height: 38px; max-height: 38px;
    letter-spacing: 0.2px;
}
QPushButton:hover {
    background: #3451d1;
}
QPushButton:pressed { background: #2a40a8; }
QPushButton:disabled {
    background: #e5e7eb; color:#9ca3af; border:none;
}

QPushButton#btn_success {
    background: #2E7D5E;
    color: #ffffff;
}
QPushButton#btn_success:hover { background: #236347; }
QPushButton#btn_success:pressed { background: #1a4d37; }

QPushButton#btn_danger {
    background: #B84040;
    color: #ffffff;
}
QPushButton#btn_danger:hover { background: #9e3434; }
QPushButton#btn_danger:pressed { background: #832b2b; }

QPushButton#btn_warning {
    background: #A0621A;
    color: #ffffff;
}
QPushButton#btn_warning:hover { background: #884f12; }
QPushButton#btn_warning:pressed { background: #703f0b; }

/* Ghost — 테두리만, 배경 없음 */
QPushButton#btn_ghost {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #475569;
    font-weight: normal;
}
QPushButton#btn_ghost:hover {
    background: #f8fafc;
    border-color: #4361EE;
    color: #4361EE;
}
QPushButton#btn_ghost:pressed {
    background: #eff4ff;
}

/* 아이콘 전용 (정사각) */
QPushButton#btn_icon {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px; padding: 0;
    color: #64748b;
    min-width: 38px; max-width: 38px;
    min-height: 38px; max-height: 38px;
    font-size: 12pt;
}
QPushButton#btn_icon:hover {
    background: #eff4ff;
    color: #4361EE;
    border-color: #4361EE;
}

/* ══ 테이블 ═════════════════════════════════════════════════ */
QTableWidget {
    background: #ffffff; border:1px solid #e5e7eb;
    border-radius:8px; gridline-color:#f3f4f6;
    color:#1f2937; alternate-background-color:#f9fafb;
    selection-background-color:#dbeafe;
    selection-color:#1d4ed8; font-size:9.5pt;
}
QTableWidget::item { padding:8px 10px; border:none; }
QTableWidget::item:selected {
    background:#dbeafe; color:#1d4ed8;
}
QHeaderView { background:#ffffff; }
QHeaderView::section {
    background:#f9fafb; color:#6b7280;
    padding:10px 10px; border:none;
    border-bottom:1px solid #e5e7eb;
    font-weight:bold; font-size:8.5pt; letter-spacing:0.5px;
}
QHeaderView::section:first { border-top-left-radius:8px; }
QHeaderView::section:last  { border-top-right-radius:8px; }

/* ══ 라디오버튼 ════════════════════════════════════════════ */
QRadioButton { color:#374151; spacing:8px; padding:4px; }
QRadioButton::indicator {
    width:16px; height:16px; border-radius:8px;
    border:2px solid #d1d5db; background:#ffffff;
}
QRadioButton::indicator:checked {
    border:2px solid #2563eb; background:#2563eb;
}
QRadioButton:checked { color:#1f2937; font-weight:bold; }

/* ══ 스크롤바 ══════════════════════════════════════════════ */
QScrollBar:vertical {
    background:#f3f4f6; width:8px; border-radius:4px;
}
QScrollBar::handle:vertical {
    background:#d1d5db; border-radius:4px; min-height:30px;
}
QScrollBar::handle:vertical:hover { background:#2563eb; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar:horizontal { background:#f3f4f6; height:8px; }
QScrollBar::handle:horizontal {
    background:#d1d5db; border-radius:4px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }

/* ══ 상태바 ════════════════════════════════════════════════ */
QStatusBar {
    background:#ffffff; color:#9ca3af;
    border-top:1px solid #e5e7eb; font-size:8.5pt;
}

/* ══ 메시지박스 ════════════════════════════════════════════ */
QMessageBox { background:#ffffff; color:#1f2937; }
QMessageBox QLabel { color:#1f2937; background:transparent; }
QMessageBox QPushButton { min-width:80px; padding:0 20px; }

/* ══ 다이얼로그 ════════════════════════════════════════════ */
QDialog { background:#ffffff; color:#1f2937; }
QDialog QLabel { color:#1f2937; }

/* ══ 내부 탭 ═══════════════════════════════════════════════ */
QTabWidget::pane {
    border:1px solid #e5e7eb;
    background:#ffffff;
    border-radius: 0 8px 8px 8px;
}
QTabBar::tab {
    background:#f3f4f6; color:#6b7280;
    padding:9px 22px; border:1px solid #e5e7eb;
    border-bottom:none; border-radius:6px 6px 0 0;
    font-weight:bold; margin-right:3px; min-width:100px;
}
QTabBar::tab:selected {
    background:#ffffff; color:#2563eb;
    border-color:#e5e7eb; border-bottom:none;
}
QTabBar::tab:hover:!selected { color:#374151; background:#e5e7eb; }

/* ══ 구분선 ════════════════════════════════════════════════ */
#divider {
    background:#e5e7eb; max-height:1px;
    min-height:1px; border:none;
}

/* ══ 레이블 ════════════════════════════════════════════════ */
#form_label {
    color:#6b7280; font-size:8.5pt; font-weight:bold;
    background:transparent; border:none;
}
#value_highlight {
    color:#2563eb; font-size:14pt; font-weight:bold;
    background:transparent; border:none;
}
"""
