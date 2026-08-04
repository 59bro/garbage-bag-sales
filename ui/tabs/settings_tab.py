# ============================================================
# ui/tabs/settings_tab.py  —  설정 탭 (모던 재설계)
# ============================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTabWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from logic.customer_logic import CustomerLogic
from logic.product_logic import ProductLogic
from ui.dialogs.customer_dialog import CustomerDialog
from ui.dialogs.product_dialog import ProductDialog
from ui.widgets import SectionCard
from utils.format_utils import fmt_currency
from database.models import DISTRICTS


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customer_logic = CustomerLogic()
        self.product_logic  = ProductLogic()
        self._cust_ids = []
        self._spec_ids = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        # 상단 시스템 관리 액션 바
        sys_h = QHBoxLayout()
        sys_h.setSpacing(10)

        btn_users = QPushButton("👥   시스템 사용자 및 로그인 권한 관리")
        btn_users.setObjectName("btn_primary")
        btn_users.setFixedHeight(40)
        btn_users.clicked.connect(self._open_user_management)
        sys_h.addWidget(btn_users)

        btn_db = QPushButton("🌐   DB 연결 및 공유 경로 설정")
        btn_db.setObjectName("btn_warning")
        btn_db.setFixedHeight(40)
        btn_db.clicked.connect(self._open_db_config)
        sys_h.addWidget(btn_db)

        sys_h.addStretch()
        root.addLayout(sys_h)

        inner = QTabWidget()
        inner.addTab(self._customer_tab(), "🏢  거래처 관리")
        inner.addTab(self._product_tab(),  "📦  규격 / 단가 관리")
        inner.addTab(self._contract_tab(), "📜  입고 계약 관리")
        root.addWidget(inner)

    def _open_user_management(self):
        from ui.dialogs.user_management_dialog import UserManagementDialog
        UserManagementDialog(self).exec_()

    def _open_db_config(self):
        from ui.dialogs.db_config_dialog import DBConfigDialog
        DBConfigDialog(self).exec_()

    # ── 거래처 ───────────────────────────────────────────────
    def _customer_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        # ── 필터 바 ──────────────────────────────────────────
        filter_h = QHBoxLayout(); filter_h.setSpacing(8)
        lbl_dist = QLabel("지역 필터")
        lbl_dist.setObjectName("form_label")
        filter_h.addWidget(lbl_dist)
        self.combo_cust_dist = QComboBox()
        self.combo_cust_dist.setFixedWidth(130)
        self.combo_cust_dist.addItem("전체", "")
        for d in DISTRICTS:
            self.combo_cust_dist.addItem(d, d)
        self.combo_cust_dist.currentIndexChanged.connect(self._load_customers)
        filter_h.addWidget(self.combo_cust_dist)
        filter_h.addStretch()
        v.addLayout(filter_h)

        # ── 버튼 바 ──────────────────────────────────────────
        toolbar = QHBoxLayout(); toolbar.setSpacing(8)
        btn_add  = QPushButton("거래처 등록")
        btn_add.setObjectName("btn_success")
        btn_add.setFixedHeight(38)
        btn_add.clicked.connect(self._add_customer)

        btn_edit = QPushButton("수정")
        btn_edit.setObjectName("btn_ghost")
        btn_edit.setFixedHeight(38)
        btn_edit.clicked.connect(self._edit_customer)

        btn_deact = QPushButton("비활성화")
        btn_deact.setObjectName("btn_ghost")
        btn_deact.setFixedHeight(38)
        btn_deact.clicked.connect(self._deactivate_customer)

        btn_del  = QPushButton("삭제")
        btn_del.setObjectName("btn_danger")
        btn_del.setFixedHeight(38)
        btn_del.clicked.connect(self._delete_customer)

        btn_export = QPushButton("엑셀 출력")
        btn_export.setObjectName("btn_ghost")
        btn_export.setFixedHeight(38)
        btn_export.clicked.connect(self._export_customers)

        btn_ref  = QPushButton("새로고침")
        btn_ref.setObjectName("btn_ghost")
        btn_ref.setFixedHeight(38)
        btn_ref.clicked.connect(self._load_customers)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_deact)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_ref)
        v.addLayout(toolbar)

        c = SectionCard("등록된 거래처")
        # 지역(동) 컬럼 추가
        self.tbl_cust = self._tbl(['ID', '구분', '거래처명', '지역(동)', '전화번호', '주소', '상태'])
        hh = self.tbl_cust.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.Stretch)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        c.add_widget(self.tbl_cust)
        v.addWidget(c)
        self._load_customers()
        return w

    def _load_customers(self):
        district = self.combo_cust_dist.currentData() if hasattr(self, 'combo_cust_dist') else ''
        rows = self.customer_logic.get_all(
            include_inactive=True, district=district or None
        )
        self._cust_ids = []
        self.tbl_cust.setUpdatesEnabled(False)
        try:
            self.tbl_cust.setRowCount(len(rows))
            for r, row in enumerate(rows):
                self._cust_ids.append(row['id'])
                active = row['is_active']
                dist   = row.get('district', '') or ''
                ctype  = row.get('customer_type', '출고처')
                # 구분 열 추가
                vals = [str(row['id']), ctype, row['name'], dist,
                        row.get('phone', ''), row.get('address', ''),
                        "활성" if active else "비활성"]
                for c, val in enumerate(vals):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    if not active:
                        item.setForeground(QColor('#334155'))
                    if c == 1: # 구분 (출고처/입고처)
                        item.setForeground(QColor('#0284c7' if ctype == '입고처' else '#ea580c'))
                    if c == 3 and dist: # 지역 컬럼 색상
                        item.setForeground(QColor('#818cf8'))
                    if c == 6 and active:
                        item.setForeground(QColor('#10b981'))
                    self.tbl_cust.setItem(r, c, item)
        finally:
            self.tbl_cust.setUpdatesEnabled(True)

    def _sel_cust_id(self):
        items = self.tbl_cust.selectedItems()
        if not items:
            return None
        return self._cust_ids[self.tbl_cust.currentRow()]

    def _add_customer(self):
        if CustomerDialog(self).exec_():
            self._load_customers()
            self._notify()

    def _edit_customer(self):
        cid = self._sel_cust_id()
        if cid is None:
            QMessageBox.information(self, "알림", "수정할 거래처를 선택해주세요.")
            return
        if CustomerDialog(self, customer_id=cid).exec_():
            self._load_customers()
            self._notify()

    def _deactivate_customer(self):
        cid = self._sel_cust_id()
        if cid is None:
            QMessageBox.information(self, "알림", "비활성화할 거래처를 선택해주세요.")
            return
        if QMessageBox.question(self, "확인", "선택한 거래처를 비활성화 하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.customer_logic.deactivate(cid)
            self._load_customers()
            self._notify()

    def _delete_customer(self):
        cid = self._sel_cust_id()
        if cid is None:
            QMessageBox.information(self, "알림", "삭제할 거래처를 선택해주세요.")
            return
        cust = self.customer_logic.get_by_id(cid)
        cust_name = cust['name'] if cust else "선택한 거래처"

        ref = self.customer_logic.has_references(cid)
        if ref['has_ref']:
            msg = (
                f"'{cust_name}' 거래처는 기존 거래/수금/계약 내역(총 {ref['total_cnt']}건)이 존재하여 완전 삭제할 수 없습니다.\n\n"
                f"• 판매 내역: {ref['sales_cnt']}건\n"
                f"• 수금 내역: {ref['ar_cnt']}건\n"
                f"• 입고 계약: {ref['contract_cnt']}건\n\n"
                "대신 '비활성화' 처리를 진행하시겠습니까?"
            )
            reply = QMessageBox.warning(
                self, "완전 삭제 불가", msg,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.customer_logic.deactivate(cid)
                self._load_customers()
                self._notify()
            return

        if QMessageBox.question(
            self, "거래처 완전 삭제",
            f"'{cust_name}' 거래처를 정말로 완전 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                self.customer_logic.delete(cid)
                self._load_customers()
                self._notify()
                QMessageBox.information(self, "성공", f"'{cust_name}' 거래처가 삭제되었습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"거래처 삭제 실패: {e}")


    # ── 규격/단가 ─────────────────────────────────────────────
    def _product_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        # 필터 + 버튼
        top = QHBoxLayout()
        top.setSpacing(8)

        lbl_f = QLabel("품목 종류")
        lbl_f.setObjectName("form_label")
        top.addWidget(lbl_f)
        self.combo_type_f = QComboBox()
        self.combo_type_f.setFixedWidth(160)
        self._reload_type_combo()
        self.combo_type_f.currentIndexChanged.connect(self._load_specs)
        top.addWidget(self.combo_type_f)

        btn_type_mgr = QPushButton("📁  품목 종류 관리")
        btn_type_mgr.setObjectName("btn_ghost")
        btn_type_mgr.setFixedHeight(38)
        btn_type_mgr.clicked.connect(self._open_type_dialog)
        top.addWidget(btn_type_mgr)

        top.addStretch()

        btn_add  = QPushButton("➕  규격 등록")
        btn_add.setObjectName("btn_success")
        btn_add.setFixedHeight(38)
        btn_add.clicked.connect(self._add_spec)

        btn_edit = QPushButton("✏  수정")
        btn_edit.setObjectName("btn_ghost")
        btn_edit.setFixedHeight(38)
        btn_edit.clicked.connect(self._edit_spec)

        btn_del  = QPushButton("✕  비활성화")
        btn_del.setObjectName("btn_danger")
        btn_del.setFixedHeight(38)
        btn_del.clicked.connect(self._deactivate_spec)

        btn_export = QPushButton("엑셀 출력")
        btn_export.setObjectName("btn_ghost")
        btn_export.setFixedHeight(38)
        btn_export.clicked.connect(self._export_specs)

        btn_ref  = QPushButton("🔄")
        btn_ref.setObjectName("btn_icon")
        btn_ref.clicked.connect(self._load_specs)

        top.addWidget(btn_add)
        top.addWidget(btn_edit)
        top.addWidget(btn_del)
        top.addWidget(btn_export)
        top.addWidget(btn_ref)
        v.addLayout(top)

        c = SectionCard("등록된 규격 / 단가")
        self.tbl_spec = self._tbl(['ID', '품목 종류', '상품코드', '규격명', '단가', '상태'])
        self.tbl_spec.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        c.add_widget(self.tbl_spec)
        v.addWidget(c)
        self._load_specs()
        return w

    # ── 입고 계약 관리 ──────────────────────────────────────────
    def _contract_tab(self) -> QWidget:
        from logic.contract_logic import ContractLogic
        self.contract_logic = ContractLogic()

        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        # ── 필터 & 버튼 ──────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        lbl_sup = QLabel("입고처 필터")
        lbl_sup.setObjectName("form_label")
        top.addWidget(lbl_sup)

        self.combo_contract_sup = QComboBox()
        self.combo_contract_sup.setFixedWidth(160)
        self.combo_contract_sup.currentIndexChanged.connect(self._load_contracts)
        top.addWidget(self.combo_contract_sup)

        top.addStretch()

        btn_add = QPushButton("➕  계약 수량 추가")
        btn_add.setObjectName("btn_success")
        btn_add.setFixedHeight(38)
        btn_add.clicked.connect(self._add_contract)
        top.addWidget(btn_add)

        btn_export = QPushButton("엑셀 출력")
        btn_export.setObjectName("btn_ghost")
        btn_export.setFixedHeight(38)
        btn_export.clicked.connect(self._export_contracts)
        top.addWidget(btn_export)

        btn_ref = QPushButton("🔄")
        btn_ref.setObjectName("btn_icon")
        btn_ref.clicked.connect(self._load_contracts)
        top.addWidget(btn_ref)

        v.addLayout(top)

        c = SectionCard("입고처별 납품 현황 및 잔여 수량")
        self.tbl_contract = self._tbl(['입고처', '품목 종류', '규격명', '총 계약수량', '납품된 수량', '잔여 수량'])
        self.tbl_contract.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        c.add_widget(self.tbl_contract)
        v.addWidget(c)

        # 초기 콤보 로드
        self._reload_contract_combo()
        self._load_contracts()

        return w

    def _reload_contract_combo(self):
        self.combo_contract_sup.blockSignals(True)
        self.combo_contract_sup.clear()
        self.combo_contract_sup.addItem("전체", None)
        # 입고처만 필터링
        for c in self.customer_logic.get_all(include_inactive=False):
            if c.get('customer_type') == '입고처':
                self.combo_contract_sup.addItem(c['name'], c['id'])
        self.combo_contract_sup.blockSignals(False)

    def _load_contracts(self):
        sup_id = self.combo_contract_sup.currentData() if hasattr(self, 'combo_contract_sup') else None
        rows = self.contract_logic.get_remaining_contracts(supplier_id=sup_id)
        
        self.tbl_contract.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [
                row['supplier_name'],
                row['type_name'],
                row['spec_name'],
                f"{row['total_contract_quantity']:,}",
                f"{row['total_delivered_quantity']:,}",
                f"{row['remaining_quantity']:,}"
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                # 잔여 수량 강조
                if c == 5:
                    if row['remaining_quantity'] < 0:
                        item.setForeground(QColor('#ef4444'))  # 초과 납품
                    elif row['remaining_quantity'] == 0:
                        item.setForeground(QColor('#22c55e'))  # 완료
                    else:
                        item.setForeground(QColor('#0284c7'))  # 잔여
                self.tbl_contract.setItem(r, c, item)

    def _add_contract(self):
        from ui.dialogs.contract_dialog import ContractDialog
        dlg = ContractDialog(self)
        if dlg.exec_():
            self._load_contracts()


    def _load_specs(self):
        type_id = self.combo_type_f.currentData()
        rows    = (self.product_logic.get_specs_by_type(type_id, True)
                   if type_id else self.product_logic.get_all_specs(True))
        self._spec_ids = []
        self.tbl_spec.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._spec_ids.append(row['id'])
            active = row['is_active']
            vals   = [str(row['id']), row['type_name'],
                      row.get('product_code', ''), row['spec_name'], 
                      fmt_currency(row['unit_price']),
                      "활성" if active else "비활성"]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if not active:
                    item.setForeground(QColor('#334155'))
                if c == 5 and active:
                    item.setForeground(QColor('#10b981'))
                self.tbl_spec.setItem(r, c, item)

    def _sel_spec_id(self):
        items = self.tbl_spec.selectedItems()
        if not items:
            return None
        return self._spec_ids[self.tbl_spec.currentRow()]

    def _add_spec(self):
        tid = self.combo_type_f.currentData()
        if ProductDialog(self, default_type_id=tid).exec_():
            self._load_specs()
            self._notify()

    def _edit_spec(self):
        sid = self._sel_spec_id()
        if sid is None:
            QMessageBox.information(self, "알림", "수정할 규격을 선택해주세요.")
            return
        if ProductDialog(self, spec_id=sid).exec_():
            self._load_specs()
            self._notify()

    def _deactivate_spec(self):
        sid = self._sel_spec_id()
        if sid is None:
            QMessageBox.information(self, "알림", "비활성화할 규격을 선택해주세요.")
            return
        if QMessageBox.question(self, "확인", "선택한 규격을 비활성화 하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.product_logic.deactivate_spec(sid)
            self._load_specs()
            self._notify()

    def _reload_type_combo(self):
        current = self.combo_type_f.currentData()
        self.combo_type_f.blockSignals(True)
        self.combo_type_f.clear()
        self.combo_type_f.addItem("전체", None)
        for t in self.product_logic.get_types():
            self.combo_type_f.addItem(t['name'], t['id'])
        # re-select previous
        for i in range(self.combo_type_f.count()):
            if self.combo_type_f.itemData(i) == current:
                self.combo_type_f.setCurrentIndex(i)
                break
        self.combo_type_f.blockSignals(False)

    def _open_type_dialog(self):
        from ui.dialogs.product_type_dialog import ProductTypeDialog
        dlg = ProductTypeDialog(self)
        dlg.exec_()
        if dlg.changed_any:
            self._reload_type_combo()
            self._load_specs()
            self._notify()

    # ── 공통 ─────────────────────────────────────────────────
    def _tbl(self, headers) -> QTableWidget:
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        return tbl

    def _notify(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'refresh_all_tabs'):
                parent.refresh_all_tabs()
                break
            parent = parent.parent()

    def refresh(self):
        self._load_customers()
        self._load_specs()

    def _export_customers(self):
        from PyQt5.QtWidgets import QFileDialog
        from utils.export_utils import export_to_excel
        import datetime
        
        district = self.combo_cust_dist.currentData() if hasattr(self, 'combo_cust_dist') else ''
        title = f"거래처_목록_{district}" if district else "거래처_목록_전체"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "엑셀 저장",
            f"{title}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return
            
        rows = self.customer_logic.get_all(include_inactive=True, district=district or None)
        headers = ['ID', '구분', '거래처명', '지역(동)', '전화번호', '주소', '상태']
        data = []
        for r in rows:
            active = "활성" if r['is_active'] else "비활성"
            dist = r.get('district', '') or ''
            ctype = r.get('customer_type', '출고처')
            data.append([
                str(r['id']),
                ctype,
                r['name'],
                dist,
                r.get('phone', ''),
                r.get('address', ''),
                active
            ])
            
        res = export_to_excel(headers, data, title, path)
        if res:
            QMessageBox.information(self, "성공", f"엑셀 파일이 저장되었습니다.\n{path}")
        else:
            QMessageBox.warning(self, "오류", "엑셀 저장에 실패했습니다. (openpyxl 모듈 확인)")

    def _export_specs(self):
        from PyQt5.QtWidgets import QFileDialog
        from utils.export_utils import export_to_excel
        import datetime
        
        type_id = self.combo_type_f.currentData()
        title = "품목_및_단가_목록"
        if type_id and type_id > 0:
            title += f"_{self.combo_type_f.currentText()}"
            
        path, _ = QFileDialog.getSaveFileName(
            self,
            "엑셀 저장",
            f"{title}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return
            
        if type_id and type_id > 0:
            rows = self.product_logic.get_specs_by_type(type_id, include_inactive=True)
        else:
            rows = self.product_logic.get_all_specs(include_inactive=True)
            
        headers = ['ID', '품목 종류', '상품코드', '규격명', '단가', '상태']
        data = []
        for r in rows:
            active = "활성" if r['is_active'] else "비활성"
            data.append([
                str(r['id']),
                r.get('type_name', ''),
                r.get('product_code', ''),
                r['name'],
                r['price'],
                active
            ])
            
        res = export_to_excel(headers, data, title, path)
        if res:
            QMessageBox.information(self, "성공", f"엑셀 파일이 저장되었습니다.\n{path}")
        else:
            QMessageBox.warning(self, "오류", "엑셀 저장에 실패했습니다. (openpyxl 모듈 확인)")

    def _export_contracts(self):
        from PyQt5.QtWidgets import QFileDialog
        from utils.export_utils import export_to_excel
        import datetime
        
        sup_id = self.combo_contract_sup.currentData() if hasattr(self, 'combo_contract_sup') else None
        title = "입고계약_및_잔여수량"
        if sup_id:
            title += f"_{self.combo_contract_sup.currentText()}"
            
        path, _ = QFileDialog.getSaveFileName(
            self,
            "엑셀 저장",
            f"{title}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return
            
        rows = self.contract_logic.get_remaining_contracts(supplier_id=sup_id)
        headers = ['입고처', '품목 종류', '규격명', '총 계약수량', '납품된 수량', '잔여 수량']
        data = []
        for r in rows:
            data.append([
                r['supplier_name'],
                r['type_name'],
                r['spec_name'],
                r['total_contract_quantity'],
                r['total_delivered_quantity'],
                r['remaining_quantity']
            ])
            
        res = export_to_excel(headers, data, title, path)
        if res:
            QMessageBox.information(self, "성공", f"엑셀 파일이 저장되었습니다.\n{path}")
        else:
            QMessageBox.warning(self, "오류", "엑셀 저장에 실패했습니다. (openpyxl 모듈 확인)")

