# ============================================================
# ui/dialogs/sale_detail_dialog.py
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QHBoxLayout, QLabel, QMessageBox, QWidget,
    QFormLayout, QSpinBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from utils.format_utils import fmt_currency, fmt_number
from logic.sales_logic import SalesLogic

class SaleItemEditDialog(QDialog):
    def __init__(self, row_data: dict, parent=None):
        super().__init__(parent)
        self.row_data = row_data
        self.setWindowTitle(f"개별 품목 수정 - {row_data.get('spec_name', '')}")
        self.resize(300, 200)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # 수량 입력
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 999999)
        self.spin_qty.setValue(int(self.row_data.get('quantity', 0)))
        form.addRow("수량 (매):", self.spin_qty)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("저장")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_values(self):
        return {
            'quantity': self.spin_qty.value()
        }

class BatchPaymentEditDialog(QDialog):
    def __init__(self, current_payment, parent=None):
        super().__init__(parent)
        self.setWindowTitle("결제수단 일괄 변경")
        self.resize(250, 150)
        self.current_payment = current_payment
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.combo_payment = QComboBox()
        self.combo_payment.addItems(['현금', '미수', '카드'])
        idx = self.combo_payment.findText(self.current_payment)
        if idx >= 0:
            self.combo_payment.setCurrentIndex(idx)
        form.addRow("새 결제수단:", self.combo_payment)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("변경")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
    def get_payment(self):
        return self.combo_payment.currentText()

class SaleDetailDialog(QDialog):
    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.items = items
        self.sales_logic = SalesLogic()
        self.deleted_any = False
        self.setWindowTitle("납품 상세 품목")
        self.resize(700, 350)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Header info
        if self.items:
            first = self.items[0]
            date_str = first.get('sale_date', '')
            cust_name = first.get('customer_name', '')
            payment_str = first.get('payment_method', '')
            lbl_info = QLabel(f"📅 {date_str}   🏢 {cust_name}   💳 결제: {payment_str}")
            lbl_info.setStyleSheet("font-size: 11pt; font-weight: bold; color: #1f2937;")
            root.addWidget(lbl_info)

        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(['종류', '규격', '수량', '단가', '금액', '관리'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tbl.setColumnWidth(5, 140)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.verticalHeader().setDefaultSectionSize(46)  # 줄간격 늘리기
        self.tbl.setShowGrid(False)
        root.addWidget(self.tbl)

        btn_del_all = QPushButton("해당 납품건 전체 삭제")
        btn_del_all.setObjectName("btn_danger")
        btn_del_all.clicked.connect(self._delete_all)
        
        btn_edit_payment = QPushButton("결제수단 일괄 변경")
        btn_edit_payment.setObjectName("btn_warning")
        btn_edit_payment.clicked.connect(self._edit_all_payment)

        btn_close = QPushButton("닫기")
        btn_close.setObjectName("btn_ghost")
        btn_close.clicked.connect(self.accept)
        
        hh = QHBoxLayout()
        hh.addWidget(btn_edit_payment)
        hh.addWidget(btn_del_all)
        hh.addStretch()
        hh.addWidget(btn_close)
        root.addLayout(hh)

    def _load_data(self):
        self.tbl.setRowCount(len(self.items))
        for r, row in enumerate(self.items):
            tname = row.get('type_name', '')
            vals = [
                tname,
                row.get('spec_name', ''),
                fmt_number(row.get('quantity', 0)),
                fmt_currency(row.get('unit_price', 0)),
                fmt_currency(row.get('total_amount', 0)),
            ]
            
            # 텍스트 색상 결정
            if '음식' in tname:
                color = QColor("#16a34a")
            elif '생활' in tname or '재사용' in tname or '일반' in tname:
                color = QColor("#2563eb")
            elif '특수' in tname or '불연' in tname or '마대' in tname:
                color = QColor("#d97706")
            elif '대형' in tname or '스티커' in tname or '폐기물' in tname:
                color = QColor("#9333ea")
            else:
                color = QColor("#475569")
                
            font = QFont("맑은 고딕", 10, QFont.Bold)
            
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c in (0, 1):
                    item.setForeground(color)
                    item.setFont(font)
                self.tbl.setItem(r, c, item)
                
            # 관리 열 (수정, 삭제 버튼)
            w = QWidget()
            ly = QHBoxLayout(w)
            ly.setContentsMargins(5, 0, 5, 0)
            ly.setSpacing(10)
            ly.setAlignment(Qt.AlignCenter)

            edit_btn = QPushButton("수정")
            edit_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #eff6ff; 
                    color: #2563eb; 
                    font-weight: bold; 
                    border: 1px solid #bfdbfe; 
                    border-radius: 4px; 
                    padding: 4px 8px;
                    min-height: 24px;
                    max-height: 24px;
                    min-width: 40px;
                }
                QPushButton:hover { background-color: #dbeafe; }
            """)
            edit_btn.setCursor(Qt.PointingHandCursor)

            del_btn = QPushButton("삭제")
            del_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #fef2f2; 
                    color: #ef4444; 
                    font-weight: bold; 
                    border: 1px solid #fecaca; 
                    border-radius: 4px; 
                    padding: 4px 8px;
                    min-height: 24px;
                    max-height: 24px;
                    min-width: 40px;
                }
                QPushButton:hover { background-color: #fee2e2; }
            """)
            del_btn.setCursor(Qt.PointingHandCursor)
            
            # 클로저 바인딩
            sale_id = row.get('id')
            if sale_id is not None:
                edit_btn.clicked.connect(lambda _, rid=r, row_data=row: self._edit_item(row_data))
                del_btn.clicked.connect(lambda _, rid=r, sid=sale_id: self._delete_item(sid))
            else:
                edit_btn.hide()
                del_btn.hide() # ID가 없는 경우 숨김
                
            ly.addWidget(edit_btn)
            ly.addWidget(del_btn)
            self.tbl.setCellWidget(r, 5, w)

    def _edit_item(self, row_data):
        dlg = SaleItemEditDialog(row_data, self)
        if dlg.exec_() == QDialog.Accepted:
            new_vals = dlg.get_values()
            try:
                self.sales_logic.update_sale(
                    sale_id=row_data['id'],
                    quantity=new_vals['quantity'],
                    unit_price=row_data.get('unit_price', 0),
                    payment_method=row_data.get('payment_method', ''),
                    memo=row_data.get('memo', '')
                )
                QMessageBox.information(self, "수정 완료", "품목 내역이 성공적으로 수정되었습니다.")
                self.deleted_any = True # 부모 창 새로고침을 위한 트리거로 사용
                self.accept() # 상세 모달을 닫아 search_tab이 리프레시하도록 유도
            except Exception as e:
                QMessageBox.critical(self, "수정 실패", f"오류가 발생했습니다: {e}")

    def _delete_item(self, sale_id):
        reply = QMessageBox.question(self, '삭제 확인', '선택한 품목을 삭제하시겠습니까?\n(해당 건의 재고 출고 내역도 함께 취소됩니다.)', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.sales_logic.delete_sale(sale_id)
                self.deleted_any = True
                self.items = [i for i in self.items if i.get('id') != sale_id]
                self._load_data() # 데이터 재렌더링
                if not self.items:
                    self.accept() # 모두 지우면 창 닫기
            except Exception as e:
                QMessageBox.critical(self, "삭제 실패", str(e))

    def _edit_all_payment(self):
        if not self.items: return
        current_payment = self.items[0].get('payment_method', '현금')
        
        dlg = BatchPaymentEditDialog(current_payment, self)
        if dlg.exec_() == QDialog.Accepted:
            new_payment = dlg.get_payment()
            if new_payment == current_payment:
                return
                
            try:
                for row in self.items:
                    sale_id = row.get('id')
                    if sale_id is not None:
                        self.sales_logic.update_sale(
                            sale_id=sale_id,
                            quantity=row.get('quantity', 0),
                            unit_price=row.get('unit_price', 0),
                            payment_method=new_payment,
                            memo=row.get('memo', '')
                        )
                QMessageBox.information(self, "변경 완료", "이 납품건의 모든 결제수단이 변경되었습니다.")
                self.deleted_any = True
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "변경 실패", f"오류가 발생했습니다: {e}")

    def _delete_all(self):
        reply = QMessageBox.question(
            self, '전체 삭제 확인', 
            '이 납품건에 포함된 모든 품목을 한 번에 삭제하시겠습니까?\n(해당 거래처/날짜의 이 내역이 완전히 취소됩니다.)', 
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                for row in self.items:
                    sale_id = row.get('id')
                    if sale_id is not None:
                        self.sales_logic.delete_sale(sale_id)
                self.deleted_any = True
                self.items = []
                QMessageBox.information(self, "삭제 완료", "전체 내역이 정상적으로 삭제되었습니다.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "삭제 실패", f"오류가 발생했습니다: {e}")
