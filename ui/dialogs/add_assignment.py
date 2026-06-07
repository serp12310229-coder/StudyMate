# ui/dialogs/add_assignment.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from datetime        import datetime
from core.theme      import T
from core.data       import new_id, new_task
from core.assets     import svg_icon
from ui.base_widgets import lbl, mk_btn, ghost_btn, inp_style, foot_row, ChecklistEditor
from ui.dialogs.calendar_dialog import CalendarDialog


# 날짜 선택 전용 위젯
class _DateButton(QFrame):
    clicked = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.TabFocus)
        self.setCursor(Qt.PointingHandCursor)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 9, 12, 9)
        self._layout.setSpacing(8)
        self._icon_lbl = QLabel()
        self._icon_lbl.setStyleSheet("background:transparent;")
        self._text_lbl = QLabel(text)
        self._text_lbl.setStyleSheet(
            f"background:transparent;font-size:10pt;color:{T('TXT')};"
        )
        self._layout.addWidget(self._icon_lbl)
        self._layout.addWidget(self._text_lbl, 1)
        self._apply_style(focused=False)

    def set_icon(self, icon, size):
        self._icon_lbl.setPixmap(icon.pixmap(size, size))

    def setText(self, text):
        self._text_lbl.setText(text)
        self._text_lbl.setStyleSheet(
            f"background:transparent;font-size:10pt;color:{T('TXT')};"
        )

    def _apply_style(self, focused: bool):
        border_color = T("PRI") if focused else T("BDR")
        self.setStyleSheet(
            f"QFrame{{background:{T('GL')};border:1.5px solid {border_color};"
            f"border-radius:8px;}}"
        )

    # 이벤트 처리
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clicked.emit()
        else:
            super().keyPressEvent(e)

    def focusInEvent(self, e):
        self._apply_style(focused=True)
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self._apply_style(focused=False)
        super().focusOutEvent(e)


# 다이얼로그 본체
class AddAssignmentDialog(QDialog):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.result_data = None
        self._initial    = initial
        self._deadline   = datetime.now().strftime("%Y-%m-%d 23:59")
        if initial:
            self._deadline = initial.get("deadline", self._deadline)
        self.setWindowTitle("새 과제 추가")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(f"background:{T('CARD')};")
        self._build()

    def _frow(self, label_text, widget):
        w  = QWidget()
        w.setStyleSheet(f"background:{T('CARD')};")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(4)
        vl.addWidget(lbl(label_text, 10, True))
        vl.addWidget(widget)
        return w

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr = QWidget()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet(f"background:{T('PRI')};")
        hl  = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.addWidget(lbl("새 과제 추가", 14, True, "white"))
        root.addWidget(hdr)

        sc   = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setStyleSheet("QScrollArea{border:none;}")
        sc.setMinimumHeight(360)

        body = QWidget()
        body.setStyleSheet(f"background:{T('CARD')};")
        bl   = QVBoxLayout(body)
        bl.setContentsMargins(24, 16, 24, 16)
        bl.setSpacing(14)

        # 1. 과제 이름
        self.f_name = QLineEdit()
        self.f_name.setPlaceholderText("예) 데이터구조 4주차 과제")
        self.f_name.setStyleSheet(inp_style())
        self.f_name.returnPressed.connect(
            lambda: QTimer.singleShot(0, lambda: self.f_subj.setFocus())
        )

        # 2. 과목명
        self.f_subj = QLineEdit()
        self.f_subj.setPlaceholderText("예) 데이터구조론")
        self.f_subj.setStyleSheet(inp_style())
        self.f_subj.returnPressed.connect(
            lambda: QTimer.singleShot(0, lambda: self._dl_btn.setFocus())
        )

        # 3. 날짜 버튼
        self._dl_btn = _DateButton("  " + self._deadline)
        ic = svg_icon("deadline", 15, T("SUB"))
        if ic:
            self._dl_btn.set_icon(ic, 15)
        self._dl_btn.clicked.connect(self._pick_date)

        # 초기값 채우기
        items = None
        if self._initial:
            self.f_name.setText(self._initial.get("name", ""))
            self.f_subj.setText(self._initial.get("subject", ""))
            items = self._initial.get("tasks", [])

        # 4. 세부 할일 목록
        self._task_ed = ChecklistEditor(items=items, placeholder="할 일을 입력하세요")
        task_sc = QScrollArea()
        task_sc.setWidgetResizable(True)
        task_sc.setFixedHeight(200)
        task_sc.setStyleSheet(
            f"QScrollArea{{border:1.5px solid {T('BDR')};border-radius:8px;"
            f"background:{T('CARD')};}}"
        )
        task_sc.setWidget(self._task_ed)

        bl.addWidget(self._frow("과제 이름  *", self.f_name))
        bl.addWidget(self._frow("과목명  *",    self.f_subj))
        bl.addWidget(self._frow("마감 일시  *", self._dl_btn))
        bl.addWidget(self._frow("세부 할일 목록", task_sc))

        sc.setWidget(body)
        root.addWidget(sc, 1)
        root.addWidget(foot_row(self, self._submit, "추가하기", T("PRI")))

    def _pick_date(self):
        dlg = CalendarDialog(include_time=True, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._deadline = dlg.result_dt
            self._dl_btn.setText("  " + self._deadline)
        # 날짜 선택 후 → 체크리스트 첫 번째 입력칸으로 포커스
        QTimer.singleShot(0, self._focus_task_editor)

    def _focus_task_editor(self):
        try:
            rows = getattr(self._task_ed, "_rows", [])
            if rows:
                rows[0][1].setFocus()
        except Exception:
            pass

    def _submit(self):
        name = self.f_name.text().strip()
        subj = self.f_subj.text().strip()
        if not name:
            QMessageBox.warning(self, "오류", "과제 이름을 입력해주세요.")
            return
        if not subj:
            QMessageBox.warning(self, "오류", "과목명을 입력해주세요.")
            return
        tasks = self._task_ed.get_items()
        if not tasks:
            tasks = [new_task(name)]
        aid = self._initial.get("id", new_id()) if self._initial else new_id()
        self.result_data = {
            "id":       aid,
            "name":     name,
            "subject":  subj,
            "color":    self._initial.get("color") if self._initial else None,
            "deadline": self._deadline,
            "tasks":    tasks,
        }
        self.accept()