# ============================================================
# ui/tabs/stock_tab.py  —  재고 관리 탭 (모던 재설계)
# ============================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor

from logic.stock_logic import StockLogic
from logic.product_logic import ProductLogic
from ui.dialogs.initial_stock_dialog import StockInDialog
from ui.widgets import StatCard, SectionCard, NoScrollDateEdit
from utils.format_utils import fmt_number, fmt_currency


class StockTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stock_logic   = StockLogic()
        self.product_logic = ProductLogic()
        self._hist_ids     = []
        self._build_ui()
        self._load_current_stock()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── 상단 액션 바 ─────────────────────────────────────
        action_h = QHBoxLayout()
        action_h.setSpacing(10)

        btn_init = QPushButton("📦   초기재고 설정")
        btn_init.setObjectName("btn_warning")
        btn_init.setFixedHeight(40)
        btn_init.clicked.connect(self._set_initial_stock)
        action_h.addWidget(btn_init)

        btn_in = QPushButton("➕   입고 등록")
        btn_in.setObjectName("btn_success")
        btn_in.setFixedHeight(40)
        btn_in.clicked.connect(self._add_inbound)
        action_h.addWidget(btn_in)

        action_h.addStretch()

        btn_ref = QPushButton("🔄   새로고침")
        btn_ref.setObjectName("btn_ghost")
        btn_ref.setFixedHeight(40)
        btn_ref.clicked.connect(self._load_current_stock)
        action_h.addWidget(btn_ref)
        root.addLayout(action_h)

        # ── 현재고 카드 영역 ─────────────────────────────────
        stock_card = SectionCard("현재고 현황")

        self.tbl_stock = self._make_table(['품목 종류', '규격', '단가', '현재고'])
        hh = self.tbl_stock.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        stock_card.add_widget(self.tbl_stock)
        root.addWidget(stock_card)

        # ── 재고 이동 내역 ────────────────────────────────────
        hist_card = SectionCard("재고 이동 내역 조회")

        # 필터 바
        fh = QHBoxLayout()
        fh.setSpacing(8)

        def fl(text):
            l = QLabel(text)
            l.setObjectName("form_label")
            return l

        fh.addWidget(fl("규격"))
        self.combo_spec = QComboBox()
        self.combo_spec.setMinimumWidth(180)
        fh.addWidget(self.combo_spec)

        fh.addWidget(fl("유형"))
        self.combo_type_f = QComboBox()
        self.combo_type_f.setMinimumWidth(90)
        for label, val in [("전체", None), ("입고", "입고"), ("출고", "출고"), ("초기재고", "초기재고")]:
            self.combo_type_f.addItem(label, val)
        fh.addWidget(self.combo_type_f)

        fh.addWidget(fl("시작"))
        self.date_s = NoScrollDateEdit(QDate.currentDate().addDays(-30))
        self.date_s.setCalendarPopup(True)
        self.date_s.setDisplayFormat("yyyy-MM-dd")
        self.date_s.setFixedWidth(150)
        fh.addWidget(self.date_s)

        fh.addWidget(fl("종료"))
        self.date_e = NoScrollDateEdit(QDate.currentDate())
        self.date_e.setCalendarPopup(True)
        self.date_e.setDisplayFormat("yyyy-MM-dd")
        self.date_e.setFixedWidth(150)
        fh.addWidget(self.date_e)

        btn_q = QPushButton("조회")
        btn_q.setObjectName("btn_ghost")
        btn_q.setFixedWidth(70)
        btn_q.setFixedHeight(36)
        btn_q.clicked.connect(self._load_history)
        fh.addWidget(btn_q)
        fh.addStretch()
        hist_card.add_layout(fh)

        self.tbl_hist = self._make_table(['날짜', '품목 종류', '규격', '유형', '입고처', '수량', '메모'])
        self.tbl_hist.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        hist_card.add_widget(self.tbl_hist)

        dh = QHBoxLayout()
        dh.addStretch()
        btn_del = QPushButton("선택 입고 삭제")
        btn_del.setObjectName("btn_danger")
        btn_del.setFixedHeight(34)
        btn_del.clicked.connect(self._delete_inbound)
        dh.addWidget(btn_del)
        hist_card.add_layout(dh)
        root.addWidget(hist_card)

        self._load_spec_filter()

    def _make_table(self, headers):
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        return tbl

    # ─────────────────────── 데이터 ──────────────────────────
    def _load_spec_filter(self):
        self.combo_spec.clear()
        self.combo_spec.addItem("전체", None)
        for s in self.product_logic.get_all_specs():
            self.combo_spec.addItem(f"{s['type_name']} — {s['spec_name']}", s['id'])

    def _load_current_stock(self):
        rows = self.stock_logic.get_all_current_stocks()
        self.tbl_stock.setRowCount(len(rows))
        for r, row in enumerate(rows):
            stock = row['current_stock']
            vals = [row['type_name'], row['spec_name'],
                    fmt_currency(row['unit_price']), fmt_number(stock)]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c == 3:
                    item.setForeground(QColor('#ef4444' if stock <= 0 else
                                              '#f59e0b' if stock < 10 else '#10b981'))
                self.tbl_stock.setItem(r, c, item)

    def _load_history(self):
        spec_id    = self.combo_spec.currentData()
        trans_type = self.combo_type_f.currentData()
        start      = self.date_s.date().toString("yyyy-MM-dd")
        end        = self.date_e.date().toString("yyyy-MM-dd")
        rows       = self.stock_logic.get_transactions(spec_id, start, end, trans_type)
        TYPE_COLOR = {'입고': '#10b981', '출고': '#ef4444', '초기재고': '#f59e0b'}
        self._hist_ids = []
        self.tbl_hist.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._hist_ids.append((row['id'], row['transaction_type']))
            
            sup_name = row.get('supplier_name', '') or ''
            
            vals = [row['transaction_date'], row['type_name'], row['spec_name'],
                    row['transaction_type'], sup_name, fmt_number(row['quantity']),
                    row.get('memo', '')]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c == 3:
                    item.setForeground(QColor(TYPE_COLOR.get(val, '#e2e8f0')))
                elif c == 4 and sup_name: # 입고처 색상
                    item.setForeground(QColor('#0284c7'))
                self.tbl_hist.setItem(r, c, item)

    def _set_initial_stock(self):
        if StockInDialog(self, mode='initial').exec_():
            self._load_current_stock()
            QMessageBox.information(self, "완료", "✅  초기재고가 설정되었습니다.")

    def _add_inbound(self):
        if StockInDialog(self, mode='inbound').exec_():
            self._load_current_stock()
            self._load_history()
            QMessageBox.information(self, "완료", "✅  입고가 등록되었습니다.")

    def _delete_inbound(self):
        sel = sorted(set(i.row() for i in self.tbl_hist.selectedItems()))
        if not sel:
            QMessageBox.information(self, "알림", "삭제할 행을 선택해주세요.")
            return
        for r in sel:
            _, ttype = self._hist_ids[r]
            if ttype == '출고':
                QMessageBox.warning(self, "경고", "출고 내역은 판매 탭에서 삭제해주세요.")
                return
        if QMessageBox.question(self, "삭제 확인",
            f"{len(sel)}건을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        for r in sorted(sel, reverse=True):
            tid, _ = self._hist_ids[r]
            self.stock_logic.delete_inbound(tid)
        self._load_current_stock()
        self._load_history()

    def refresh(self):
        self._load_spec_filter()
        self._load_current_stock()
