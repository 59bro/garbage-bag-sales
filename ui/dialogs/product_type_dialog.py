# ============================================================
# ui/dialogs/product_type_dialog.py  —  품목 종류(대분류) 관리 팝업
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox, QInputDialog, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from logic.product_logic import ProductLogic


class ProductTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logic = ProductLogic()
        self._type_ids = []
        self.changed_any = False
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        self.setWindowTitle("품목 종류(대분류) 관리")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 20, 24, 20)

        # 상단 안내
        lbl = QLabel("📁  품목 종류(대분류) 관리")
        lbl.setStyleSheet(
            "color:#4f46e5; font-size:14pt; font-weight:bold; "
            "background:transparent; border:none;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(lbl)

        desc = QLabel(
            "새로운 봉투 종류(예: 생활용, 음식물용, 대형 마대 등)를 등록하거나 이름을 수정할 수 있습니다."
        )
        desc.setStyleSheet("color:#64748b; font-size:9pt;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        root.addWidget(desc)

        # 버튼 툴바
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_add = QPushButton("➕  새 종류 추가")
        btn_add.setObjectName("btn_success")
        btn_add.clicked.connect(self._add_type)

        btn_edit = QPushButton("✏  이름 수정")
        btn_edit.setObjectName("btn_ghost")
        btn_edit.clicked.connect(self._edit_type)

        btn_del = QPushButton("✕  삭제")
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._del_type)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_del)
        root.addLayout(toolbar)

        # 테이블
        self.tbl = QTableWidget(0, 2)
        self.tbl.setHorizontalHeaderLabels(["ID", "품목 종류명 (예: 생활용 봉투)"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setShowGrid(False)
        self.tbl.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl.doubleClicked.connect(self._edit_type)
        root.addWidget(self.tbl)

        # 하단 닫기 버튼
        bh = QHBoxLayout()
        btn_close = QPushButton("닫기")
        btn_close.setObjectName("btn_ghost")
        btn_close.clicked.connect(self.accept)
        bh.addStretch()
        bh.addWidget(btn_close)
        root.addLayout(bh)

    def _load_data(self):
        rows = self.logic.get_types()
        self._type_ids = []
        self.tbl.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._type_ids.append(row['id'])
            id_item = QTableWidgetItem(str(row['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            name_item = QTableWidgetItem(row['name'])
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setForeground(QColor("#1e293b"))

            self.tbl.setItem(r, 0, id_item)
            self.tbl.setItem(r, 1, name_item)

    def _get_sel_id(self):
        items = self.tbl.selectedItems()
        if not items:
            return None
        return self._type_ids[self.tbl.currentRow()]

    def _add_type(self):
        name, ok = QInputDialog.getText(
            self, "새 품목 종류 등록",
            "새로운 품목 종류명을 입력하세요 (예: 일반용 마대, 신규 봉투):"
        )
        if ok and name.strip():
            try:
                self.logic.add_type(name.strip())
                self.changed_any = True
                self._load_data()
                QMessageBox.information(self, "완료", f"'{name.strip()}' 종류가 성공적으로 추가되었습니다.")
            except Exception as e:
                QMessageBox.warning(self, "오류", str(e))

    def _edit_type(self):
        tid = self._get_sel_id()
        if tid is None:
            QMessageBox.information(self, "알림", "수정할 품목 종류를 선택해주세요.")
            return
        current_name = self.tbl.item(self.tbl.currentRow(), 1).text()
        name, ok = QInputDialog.getText(
            self, "품목 종류명 수정",
            "변경할 품목 종류명을 입력하세요:",
            text=current_name
        )
        if ok and name.strip():
            try:
                self.logic.update_type(tid, name.strip())
                self.changed_any = True
                self._load_data()
            except Exception as e:
                QMessageBox.warning(self, "오류", str(e))

    def _del_type(self):
        tid = self._get_sel_id()
        if tid is None:
            QMessageBox.information(self, "알림", "삭제할 품목 종류를 선택해주세요.")
            return
        current_name = self.tbl.item(self.tbl.currentRow(), 1).text()
        if QMessageBox.question(
            self, "삭제 확인",
            f"'{current_name}' 품목 종류를 정말 삭제하시겠습니까?\n(해당 종류에 등록된 규격이 없어야 삭제 가능합니다.)",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                self.logic.delete_type(tid)
                self.changed_any = True
                self._load_data()
                QMessageBox.information(self, "삭제 완료", f"'{current_name}' 종류가 삭제되었습니다.")
            except Exception as e:
                QMessageBox.warning(self, "삭제 불가", str(e))
