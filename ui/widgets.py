# ============================================================
# ui/widgets.py  —  재사용 커스텀 위젯 (라이트 테마)
# ============================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QDateEdit
)
from PyQt5.QtCore import Qt


class NoScrollDateEdit(QDateEdit):
    """마우스 휠·방향키·스핀버튼으로 날짜가 변경되지 않도록 막은 QDateEdit.
    
    달력 팝업을 통해서만 날짜를 변경할 수 있습니다.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 업/다운 스핀 버튼 완전 제거
        from PyQt5.QtWidgets import QAbstractSpinBox
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        # 위/아래 방향키·PageUp/PageDown 으로 날짜가 바뀌는 것을 차단
        blocked = (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown)
        if event.key() in blocked:
            event.ignore()
            return
        super().keyPressEvent(event)


class StatCard(QWidget):
    """KPI 요약 카드."""

    def __init__(self, icon: str, label: str, value: str = "—",
                 accent: str = "#2563eb", parent=None):
        super().__init__(parent)
        self.accent = accent
        self._build(icon, label, value)

    def _build(self, icon, label, value):
        self.setStyleSheet(
            f"""
            StatCard {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                border-top: 3px solid {self.accent};
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        top = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(
            f"background:transparent; font-size:16pt; color:{self.accent}; border:none;"
        )
        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet(
            "background:transparent; font-size:13pt; font-weight:bold; "
            "color:#111827; border:none;"
        )
        self.lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(lbl_icon)
        top.addStretch()
        top.addWidget(self.lbl_val)

        lbl_label = QLabel(label.upper())
        lbl_label.setStyleSheet(
            f"color:{self.accent}; font-size:7.5pt; font-weight:bold; "
            f"letter-spacing:1px; border:none; background:transparent;"
        )

        layout.addLayout(top)
        layout.addWidget(lbl_label)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(80)

    def set_value(self, text: str):
        self.lbl_val.setText(text)


class SectionCard(QFrame):
    """콘텐츠 섹션 카드."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 16)
        outer.setSpacing(10)

        if title:
            lbl = QLabel(title.upper())
            lbl.setObjectName("card_title")
            outer.addWidget(lbl)

            div = QFrame()
            div.setObjectName("divider")
            div.setFrameShape(QFrame.HLine)
            outer.addWidget(div)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        outer.addLayout(self.body)

    def add_widget(self, w: QWidget):
        self.body.addWidget(w)

    def add_layout(self, layout):
        self.body.addLayout(layout)


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.HLine)
