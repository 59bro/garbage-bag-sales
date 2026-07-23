# ============================================================
# ui/tabs/sales_tab.py  —  일괄 입력 (그리드) 형식 납품서 탭
# ============================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QDateEdit, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QLineEdit, QButtonGroup, QRadioButton, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont

from logic.sales_logic import SalesLogic
from logic.customer_logic import CustomerLogic
from logic.product_logic import ProductLogic
from logic.stock_logic import StockLogic
from utils.format_utils import fmt_currency, fmt_number, parse_number
from ui.widgets import SectionCard, NoScrollDateEdit
from database.models import DISTRICTS


class NoScrollSpinBox(QSpinBox):
    """마우스 휠 스크롤이나 방향키(상/하)로 수량이 의도치 않게 조절되는 것을 방지하는 스핀박스."""
    def wheelEvent(self, event):
        event.ignore()  # 휠 이벤트를 상위 테이블/스크롤 영역으로 전달하여 수량 변경 차단

    def keyPressEvent(self, event):
        # 상하 방향키나 PageUp/PageDown으로 수량이 증감되는 것 차단
        if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
            event.ignore()
            return
        super().keyPressEvent(event)


class SalesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sales_logic    = SalesLogic()
        self.customer_logic = CustomerLogic()
        self.product_logic  = ProductLogic()
        self.stock_logic    = StockLogic()
        self.spin_boxes     = []
        self._all_customers = []   # 전체 거래처 캐시 (검색용)
        self._build_ui()
        self._load_combos()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        # ══ 납품 헤더 ════════════════════════════════════════
        hdr = SectionCard("납품 정보")
        g = QGridLayout()
        g.setSpacing(10)
        g.setColumnStretch(1, 2); g.setColumnStretch(3, 2)

        def fl(t):
            l = QLabel(t); l.setObjectName("form_label")
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter); return l

        g.addWidget(fl("납품일"), 0, 0)
        self.date_edit = NoScrollDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        g.addWidget(self.date_edit, 0, 1)

        g.addWidget(fl("지역 필터"), 0, 2)
        self.combo_district = QComboBox()
        self.combo_district.addItem("전체", "")
        for d in DISTRICTS:
            self.combo_district.addItem(d, d)
        self.combo_district.currentIndexChanged.connect(self._filter_customers)
        g.addWidget(self.combo_district, 0, 3)


        # 거래처 검색 + 콤보
        g.addWidget(fl("거래처 검색"), 1, 0)
        self.edit_cust_search = QLineEdit()
        self.edit_cust_search.setPlaceholderText("이름 입력 (첫 글자로 필터)")
        self.edit_cust_search.textChanged.connect(self._on_search_changed)
        g.addWidget(self.edit_cust_search, 1, 1)

        g.addWidget(fl("거래처"), 2, 0)
        self.combo_customer = QComboBox()
        g.addWidget(self.combo_customer, 2, 1)

        g.addWidget(fl("결제방식"), 2, 2)
        pay_w = QWidget(); pay_w.setStyleSheet("background:transparent;")
        ph = QHBoxLayout(pay_w); ph.setContentsMargins(0,0,0,0); ph.setSpacing(8)
        self.radio_cash   = QRadioButton("현금")
        self.radio_credit = QRadioButton("미수")
        self.radio_card   = QRadioButton("카드")
        self.radio_cash.setChecked(True)
        self.bg_pay = QButtonGroup()
        for rb in (self.radio_cash, self.radio_credit, self.radio_card):
            self.bg_pay.addButton(rb); ph.addWidget(rb)
        ph.addStretch()
        g.addWidget(pay_w, 2, 3)

        hdr.body.addLayout(g)
        root.addWidget(hdr)

        # ══ 납품서 테이블 (품목 리스트 일괄 입력) ══════════════════
        bill_card = SectionCard("품목별 수량 입력")
        self.tbl_bill = self._make_tbl(
            ['종류', '규격', '단가', '현재 재고', '수량 (입력)', '합계 금액']
        )
        hh = self.tbl_bill.horizontalHeader()
        for i, mode in enumerate([
            QHeaderView.Stretch, QHeaderView.Stretch,
            QHeaderView.ResizeToContents, QHeaderView.ResizeToContents,
            QHeaderView.Fixed, QHeaderView.ResizeToContents
        ]):
            hh.setSectionResizeMode(i, mode)
        
        self.tbl_bill.setColumnWidth(4, 100)  # 수량 칸 너비 조절
        self.tbl_bill.verticalHeader().setDefaultSectionSize(40) # 행 높이 키워서 스핀박스 잘림 방지
        bill_card.add_widget(self.tbl_bill)

        bf = QHBoxLayout(); bf.setSpacing(10)
        # 합계 표시
        tot_frame = QFrame()
        tot_frame.setStyleSheet(
            "background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px;"
        )
        tf = QHBoxLayout(tot_frame); tf.setContentsMargins(14,8,14,8)
        lbl_tl = QLabel("납품 합계"); lbl_tl.setObjectName("form_label")
        self.lbl_bill_total = QLabel("0 원")
        self.lbl_bill_total.setStyleSheet(
            "color:#1d4ed8; font-size:14pt; font-weight:bold; background:transparent; border:none;"
        )
        tf.addWidget(lbl_tl); tf.addStretch(); tf.addWidget(self.lbl_bill_total)
        bf.addWidget(tot_frame, 1)

        btn_clear = QPushButton("초기화")
        btn_clear.setObjectName("btn_ghost")
        btn_clear.clicked.connect(self._clear_bill)
        bf.addWidget(btn_clear)

        btn_save = QPushButton("납품 저장  ✓")
        btn_save.setObjectName("btn_success")
        btn_save.clicked.connect(self._save_bill)
        bf.addWidget(btn_save)

        bill_card.add_layout(bf)
        root.addWidget(bill_card)

    def _make_tbl(self, headers):
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        return tbl

    def _ro_item(self, text: str):
        it = QTableWidgetItem(text)
        it.setTextAlignment(Qt.AlignCenter)
        return it

    # ─── 거래처 검색 ──────────────────────────────────────────
    def _load_all_customers(self):
        """전체 거래처 캐시 로드."""
        district = self.combo_district.currentData() or None
        self._all_customers = self.customer_logic.get_all(district=district)

    def _rebuild_customer_combo(self, customers: list):
        self.combo_customer.clear()
        for c in customers:
            label = f"{c['name']}  [{c['district']}]" if c.get('district') else c['name']
            self.combo_customer.addItem(label, c['id'])

    def _on_search_changed(self, text: str):
        norm_text = text.replace(" ", "").lower()
        if not norm_text:
            self._rebuild_customer_combo(self._all_customers)
            return

        def norm(s):
            return str(s).replace(" ", "").lower()

        exact   = []
        starts  = []
        contains = []
        for c in self._all_customers:
            c_norm = norm(c['name'])
            if c_norm == norm_text:
                exact.append(c)
            elif c_norm.startswith(norm_text):
                starts.append(c)
            elif norm_text in c_norm:
                contains.append(c)

        filtered = exact + starts + contains
        self._rebuild_customer_combo(filtered)

    def _filter_customers(self):
        self.edit_cust_search.clear()
        self._load_all_customers()
        self._rebuild_customer_combo(self._all_customers)

    # ─── 콤보 및 그리드 로직 ──────────────────────────────────
    def _load_combos(self):
        self._load_all_customers()
        self._rebuild_customer_combo(self._all_customers)
        self._load_grid()

    def _load_grid(self):
        specs = self.product_logic.get_all_specs() # 전체 품목 가져오기
        self.tbl_bill.setRowCount(len(specs))
        self.spin_boxes = []

        for r, sp in enumerate(specs):
            stock = self.stock_logic.get_current_stock(sp['id'])
            
            # 0: 종류, 1: 규격, 2: 단가, 3: 재고
            tname = sp['type_name']
            type_item = self._ro_item(tname)
            spec_item = self._ro_item(sp['spec_name'])
            
            # 품목별 텍스트 색상 지정
            if '음식' in tname:
                color = QColor("#16a34a") # 초록색
            elif '생활' in tname or '재사용' in tname or '일반' in tname:
                color = QColor("#2563eb") # 파란색
            elif '특수' in tname or '불연' in tname or '마대' in tname:
                color = QColor("#d97706") # 주황/갈색
            elif '대형' in tname or '스티커' in tname or '폐기물' in tname:
                color = QColor("#9333ea") # 보라색
            else:
                color = QColor("#475569") # 기본 짙은 회색
                
            font = QFont("맑은 고딕", 10, QFont.Bold)
            type_item.setForeground(color)
            type_item.setFont(font)
            spec_item.setForeground(color)
            spec_item.setFont(font)
            
            self.tbl_bill.setItem(r, 0, type_item)
            self.tbl_bill.setItem(r, 1, spec_item)
            self.tbl_bill.setItem(r, 2, self._ro_item(fmt_currency(sp['unit_price'])))
            
            stock_item = self._ro_item(fmt_number(stock))
            stock_item.setForeground(QColor("#10b981" if stock > 0 else "#ef4444"))
            self.tbl_bill.setItem(r, 3, stock_item)
            
            # 4: 입력 수량 (투명한 텍스트 입력칸으로 변신)
            spin = NoScrollSpinBox()
            spin.setRange(0, 999999)
            spin.setAlignment(Qt.AlignCenter)
            spin.setButtonSymbols(QSpinBox.NoButtons) # 상하 화살표 제거
            spin.setStyleSheet("""
                QSpinBox { 
                    font-size: 10pt; font-weight: bold; 
                    background: transparent;
                    border: none;
                    margin: 0px; padding: 0px;
                }
                QSpinBox:focus { 
                    background: #e0e7ff; 
                    color: #1d4ed8;
                }
            """)
            spin.setProperty("spec_id", sp['id'])
            spin.setProperty("type_name", sp['type_name'])
            spin.setProperty("spec_name", sp['spec_name'])
            spin.setProperty("unit_price", sp['unit_price'])
            
            # 람다 캡처링 (r, spin)
            spin.valueChanged.connect(lambda v, row=r, s=spin: self._on_grid_qty_changed(row, s))
            
            # Tab 키 감지를 위한 이벤트 필터 등록
            spin.installEventFilter(self)
            
            self.tbl_bill.setCellWidget(r, 4, spin)
            self.spin_boxes.append(spin)
            
            # 5: 합계 금액
            self.tbl_bill.setItem(r, 5, self._ro_item("0"))

    def _on_grid_qty_changed(self, row, spin):
        qty = spin.value()
        price = spin.property("unit_price")
        amt_text = fmt_currency(qty * price) if qty > 0 else "0"
        
        amt_item = self.tbl_bill.item(row, 5)
        if not amt_item:
            amt_item = self._ro_item(amt_text)
            self.tbl_bill.setItem(row, 5, amt_item)
        else:
            amt_item.setText(amt_text)
            
        if qty > 0:
            amt_item.setForeground(QColor("#4361EE")) # 파란색 강조
        else:
            amt_item.setForeground(QColor("#111827"))
            
        self._calc_grand_total()

    def _calc_grand_total(self):
        grand = sum(spin.value() * spin.property("unit_price") for spin in self.spin_boxes)
        self.lbl_bill_total.setText(fmt_currency(grand))

    # ─── 탭(Tab) 키 이동 이벤트 처리 ────────────────────────────
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent, Qt
        # Tab 키가 눌렸을 때
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            if obj in self.spin_boxes:
                idx = self.spin_boxes.index(obj)
                if idx < len(self.spin_boxes) - 1:
                    # 다음 스핀박스로 이동
                    self.spin_boxes[idx + 1].setFocus()
                    self.spin_boxes[idx + 1].selectAll()
                else:
                    # 마지막 칸이면 맨 처음 칸으로 돌아감
                    self.spin_boxes[0].setFocus()
                    self.spin_boxes[0].selectAll()
                return True # 기본 Tab 이동(테이블 셀 이동) 무시
        return super().eventFilter(obj, event)

    def _get_payment(self):
        if self.radio_cash.isChecked():   return '현금'
        if self.radio_credit.isChecked(): return '미수'
        return '카드'



    # ─── 저장 및 초기화 ───────────────────────────────────────
    def _clear_bill(self):
        for spin in self.spin_boxes:
            spin.setValue(0)
        self._calc_grand_total()
        # 재고 정보도 다시 로드하고 싶다면:
        # self._load_grid()

    def _save_bill(self):
        rows = []
        for spin in self.spin_boxes:
            qty = spin.value()
            if qty > 0:
                rows.append({
                    'sale_date':      self.date_edit.date().toString("yyyy-MM-dd"),
                    'customer_id':    self.combo_customer.currentData(),
                    'customer_name':  self.combo_customer.currentText(),
                    'type_name':      spin.property("type_name"),
                    'spec_id':        spin.property("spec_id"),
                    'spec_name':      spin.property("spec_name"),
                    'quantity':       qty,
                    'unit_price':     spin.property("unit_price"),
                    'payment_method': self._get_payment(),
                    'memo':           '',
                    'total_amount':   qty * spin.property("unit_price")
                })
        
        if not rows:
            QMessageBox.information(self, "알림", "입력된 수량이 없습니다.\n납품할 품목의 수량을 입력해주세요.")
            return
            
        if self.combo_customer.count() == 0:
            QMessageBox.warning(self, "경고", "거래처를 선택해주세요.")
            return
            
        try:
            self.sales_logic.add_sales_batch(rows)
            count = len(rows)
            self._clear_bill()
            self.refresh() # 재고 갱신
            QMessageBox.information(self, "저장 완료", f"✓  {count}개 품목의 납품 정보가 저장되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", str(e))

    def refresh(self):
        self._load_combos()
