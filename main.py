# ============================================================
# main.py  –  종량제 봉투 판매 관리 시스템 진입점
# ============================================================

import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from ui.main_window import MainWindow


def main():
    # 고DPI 지원
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 한글 폰트
    font = QFont("맑은 고딕", 10)
    app.setFont(font)

    from ui.dialogs.login_dialog import LoginDialog
    from PyQt5.QtWidgets import QDialog

    login_dlg = LoginDialog()
    if login_dlg.exec_() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
