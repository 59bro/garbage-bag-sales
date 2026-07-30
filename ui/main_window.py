# ============================================================
# ui/main_window.py  —  사이드바 메인 윈도우 (AR 탭 추가)
# ============================================================

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime

from ui.styles import APP_STYLE
from ui.tabs.sales_tab    import SalesTab
from ui.tabs.stock_tab    import StockTab
from ui.tabs.search_tab   import SearchTab
from ui.tabs.ar_tab       import ARTab
from ui.tabs.vehicle_tab  import VehicleTab
from ui.tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    NAV_ITEMS = [
        ("🧾", "판매 입력",    "일별 납품내역 등록"),
        ("📦", "재고 관리",    "입고 · 현재고 현황"),
        ("🔍", "조회 · 보고서", "기간별 판매 분석"),
        ("📝", "미수 관리",    "미수 현황 · 수금 등록"),
        ("🚚", "차량 · 반입 관리", "차량 운행 및 폐기물 반입 일지"),
        ("⚙",  "설정",        "거래처 · 규격 · 단가"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("종량제 봉투 판매 관리")
        self.resize(1380, 880)
        self.setMinimumSize(1100, 740)
        self.setStyleSheet(APP_STYLE)
        self._nav_buttons = []
        self._build_ui()
        self._start_clock()
        self._switch_page(0)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0,0,0,0)
        h.setSpacing(0)

        # ── 사이드바 ─────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        sv = QVBoxLayout(sidebar)
        sv.setContentsMargins(0,0,0,0)
        sv.setSpacing(0)

        logo_area = QWidget()
        logo_area.setFixedHeight(80)
        logo_area.setStyleSheet(
            "background:#1b2139; border-bottom:1px solid #252d4a;"
        )
        la = QVBoxLayout(logo_area)
        la.setContentsMargins(20,0,20,0); la.setSpacing(2)
        lbl_logo = QLabel("🗑  봉투 관리")
        lbl_logo.setObjectName("sidebar_logo")
        lbl_sub  = QLabel("Sales Management")
        lbl_sub.setObjectName("sidebar_logo_sub")
        la.addWidget(lbl_logo); la.addWidget(lbl_sub)
        sv.addWidget(logo_area)
        sv.addSpacing(14)

        lbl_sec = QLabel("MENU")
        lbl_sec.setObjectName("nav_section_label")
        sv.addWidget(lbl_sec)
        sv.addSpacing(4)

        for idx, (icon, title, _) in enumerate(self.NAV_ITEMS):
            btn = QPushButton(f"  {icon}   {title}")
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(46)
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            self._nav_buttons.append(btn)
            sv.addWidget(btn)

        sv.addStretch()

        div = QFrame(); div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background:#252d4a; max-height:1px;")
        sv.addWidget(div)
        lbl_ver = QLabel("v 1.1.0")
        lbl_ver.setObjectName("sidebar_logo_sub")
        lbl_ver.setAlignment(Qt.AlignCenter)
        lbl_ver.setContentsMargins(0,8,0,12)
        sv.addWidget(lbl_ver)
        h.addWidget(sidebar)

        # ── 우측 ─────────────────────────────────────────────
        right = QWidget()
        right.setObjectName("content_area")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0,0,0,0); rv.setSpacing(0)

        self.header = QWidget()
        self.header.setObjectName("page_header")
        self.header.setFixedHeight(64)
        hh = QHBoxLayout(self.header)
        hh.setContentsMargins(28,0,28,0); hh.setSpacing(8)
        tc = QVBoxLayout(); tc.setSpacing(2)
        self.lbl_title    = QLabel()
        self.lbl_title.setObjectName("page_title")
        self.lbl_subtitle = QLabel()
        self.lbl_subtitle.setObjectName("page_subtitle")
        tc.addWidget(self.lbl_title); tc.addWidget(self.lbl_subtitle)
        hh.addLayout(tc); hh.addStretch()
        self.lbl_clock = QLabel()
        self.lbl_clock.setObjectName("clock_label")
        hh.addWidget(self.lbl_clock)

        from logic.auth_logic import AuthLogic
        self.lbl_user = QLabel()
        self.lbl_user.setStyleSheet("color: #4f46e5; font-weight: bold; font-size: 10pt; padding: 6px 12px; background: #e0e7ff; border-radius: 6px;")
        if AuthLogic.current_user:
            u = AuthLogic.current_user
            self.lbl_user.setText(f"👤 {u['name']} ({u['role']})")
        else:
            self.lbl_user.setText("👤 로그인 없음")
        hh.addWidget(self.lbl_user)

        btn_logout = QPushButton("로그아웃")
        btn_logout.setObjectName("btn_ghost")
        btn_logout.setFixedHeight(34)
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.clicked.connect(self._logout)
        hh.addWidget(btn_logout)
        rv.addWidget(self.header)

        self.stack = QStackedWidget()
        self.tab_sales    = SalesTab()
        self.tab_stock    = StockTab()
        self.tab_search   = SearchTab()
        self.tab_ar       = ARTab()
        self.tab_vehicle  = VehicleTab()
        self.tab_settings = SettingsTab()
        for tab in (self.tab_sales, self.tab_stock, self.tab_search,
                    self.tab_ar, self.tab_vehicle, self.tab_settings):
            self.stack.addWidget(tab)
        rv.addWidget(self.stack)
        h.addWidget(right)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_db_info()

    def _update_status_db_info(self):
        from database.db_manager import DBManager
        db = DBManager()
        if db.db_mode == 'postgres':
            msg = "  ●  [☁️ 클라우드 (Supabase) DB 접속 중]"
            self.status_bar.setStyleSheet("color: #10b981; font-weight: bold; background: #ecfdf5;")
        else:
            path = db.db_path or ""
            if "드라이브" in path or "Drive" in path or "OneDrive" in path:
                msg = f"  ●  [☁️ 구글 드라이브 실시간 연동 중]  {path}"
                self.status_bar.setStyleSheet("color: #1d4ed8; font-weight: bold; background: #eff6ff;")
            else:
                msg = f"  ●  [💻 로컬/공유 PC DB 접속 중]  {path}"
                self.status_bar.setStyleSheet("color: #334155;")
        self.status_bar.showMessage(msg)

    def _switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        icon, title, subtitle = self.NAV_ITEMS[idx]
        self.lbl_title.setText(f"{icon}  {title}")
        self.lbl_subtitle.setText(subtitle)

        for i, btn in enumerate(self._nav_buttons):
            btn.setObjectName("nav_btn_active" if i == idx else "nav_btn")
            btn.setStyleSheet("")

        tab = self.stack.currentWidget()
        if hasattr(tab, 'refresh'):
            tab.refresh()

    def _start_clock(self):
        self._update_clock()
        t = QTimer(self); t.timeout.connect(self._update_clock); t.start(1000)

    def _update_clock(self):
        self.lbl_clock.setText(datetime.now().strftime("%Y. %m. %d   %H : %M : %S"))

    def refresh_all_tabs(self):
        for tab in (self.tab_sales, self.tab_stock, self.tab_search, self.tab_ar, self.tab_vehicle):
            if hasattr(tab, 'refresh'):
                tab.refresh()
        self._update_status_db_info()

    def _logout(self):
        from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication
        if QMessageBox.question(self, "로그아웃", "현재 계정에서 로그아웃하시겠습니까?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            from logic.auth_logic import AuthLogic
            AuthLogic().logout()
            self.close()
            from ui.dialogs.login_dialog import LoginDialog
            dlg = LoginDialog()
            if dlg.exec_() == QDialog.Accepted:
                new_win = MainWindow()
                new_win.show()
            else:
                QApplication.quit()
