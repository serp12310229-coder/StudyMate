# ui/base_widgets.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from core.theme      import T, dk, is_dark
from core.assets     import svg_icon, svg_pixmap, get_font
from core.data       import new_task


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)
    def __init__(self, checked=False, parent=None):
        super().__init__(parent); self._on=checked
        self.setFixedSize(46,26); self.setCursor(Qt.PointingHandCursor)
    def isChecked(self): return self._on
    def setChecked(self,v): self._on=v; self.update()
    def mousePressEvent(self,e):
        self._on=not self._on; self.toggled.emit(self._on); self.update()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(T("PRI")) if self._on else QColor(T("BDR"))); p.setPen(Qt.NoPen)
        p.drawRoundedRect(0,0,46,26,13,13)
        p.setBrush(QColor("white")); p.drawEllipse(22 if self._on else 2,3,20,20)


def lbl(text,size=10,bold=False,color=None,wrap=False):
    w=QLabel(text); c=color or T("TXT"); fw="bold" if bold else "normal"
    w.setStyleSheet(f"color:{c};font-size:{size}pt;font-weight:{fw};background:transparent;")
    if wrap: w.setWordWrap(True)
    return w

def hdiv():
    f=QFrame(); f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background:{T('BDR')};"); f.setFixedHeight(1); return f

def sbadge(text,color):
    w=QLabel(f"  {text}  ")
    w.setStyleSheet(
        f"background:{color};color:white;border-radius:5px;"
        f"font-size:8pt;font-weight:bold;padding:1px 0;"
    )
    w.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed); return w

def dbadge(text,color):
    from core.theme import dk as _dk
    fg = "white" if is_dark(color) else T("TXT")
    bdr = _dk(color, 26)
    w=QLabel(f"  {text}  ")
    w.setStyleSheet(
        f"background:{color};color:{fg};border:1px solid {bdr};"
        f"border-radius:5px;font-size:8pt;font-weight:bold;padding:1px 0;"
    )
    w.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed); return w

def mk_btn(text,bg,fg="white",size=10,r=8,pad="8px 18px",icon_name=None,icon_color=None):
    b=QPushButton(text); b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton{{background:{bg};color:{fg};border:none;"
        f"border-radius:{r}px;padding:{pad};font-size:{size}pt;font-weight:bold;}}"
        f"QPushButton:hover{{background:{dk(bg,14)};}}"
        f"QPushButton:pressed{{background:{dk(bg,28)};}}"
    )
    if icon_name:
        ic = icon_color if icon_color is not None else _icon_col(bg)
        b.setIcon(svg_icon(icon_name,15,ic)); b.setIconSize(QSize(15,15))
    return b

def ghost_btn(text,color=None):
    c=color or T("SUB"); b=QPushButton(text); b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton{{background:{T('GL')};color:{c};"
        f"border:1px solid {T('BDR')};border-radius:8px;"
        f"padding:8px 16px;font-size:10pt;}}"
        f"QPushButton:hover{{background:{T('BDR')};}}"
    )
    return b

def icon_btn(icon_name=None,text="",size=28,color=None):
    c=color or T("SUB"); b=QPushButton(text)
    b.setFixedSize(size,size); b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton{{background:transparent;color:{c};border:none;"
        f"font-size:13pt;border-radius:{size//2}px;}}"
        f"QPushButton:hover{{background:{T('BDR')};color:{T('TXT')};}}"
    )
    if icon_name:
        b.setIcon(svg_icon(icon_name,size-10,c)); b.setIconSize(QSize(size-10,size-10))
    return b

def inp_style(focus=None):
    fc=focus or T("PRI")
    return (
        f"QLineEdit{{background:{T('GL')};border:1.5px solid {T('BDR')};"
        f"border-radius:8px;padding:9px 12px;font-size:10pt;color:{T('TXT')};}}"
        f"QLineEdit:focus{{border:2px solid {fc};background:{T('CARD')};}}"
    )

def prog_bar(value,color):
    bar=QProgressBar(); bar.setFixedHeight(8); bar.setRange(0,100)
    bar.setValue(value); bar.setTextVisible(False)
    bar.setStyleSheet(
        f"QProgressBar{{background:{T('BDR')};border-radius:4px;border:none;}}"
        f"QProgressBar::chunk{{background:{color};border-radius:4px;}}"
    )
    return bar

def foot_row(dialog,ok_fn,ok_text="저장",ok_color=None):
    bg=ok_color or T("PRI")
    ic=_icon_col(bg)
    foot=QWidget(); foot.setStyleSheet(f"background:{T('CARD')};border-top:1px solid {T('BDR')};")
    fl=QHBoxLayout(foot); fl.setContentsMargins(24,12,24,14); fl.addStretch()
    cancel=ghost_btn("취소"); cancel.clicked.connect(dialog.reject); fl.addWidget(cancel); fl.addSpacing(8)
    ok=mk_btn(ok_text,bg,fg=ic,pad="9px 20px"); ok.clicked.connect(ok_fn); fl.addWidget(ok)
    return foot

def _icon_col(bg_color):
    return T("SUB") if is_dark(bg_color) else T("GRN")


class ConfirmDialog(QDialog):
    def __init__(self,title,message,ok_text="확인",ok_color=None,icon_name=None,parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setFixedWidth(360)
        outer=QVBoxLayout(self); outer.setContentsMargins(12,12,12,12)
        frame=QFrame()
        frame.setStyleSheet(f"QFrame{{background:{T('CARD')};border-radius:18px;}}")
        sh=QGraphicsDropShadowEffect(frame); sh.setBlurRadius(28); sh.setOffset(0,6); sh.setColor(QColor(0,0,0,45))
        frame.setGraphicsEffect(sh)
        vl=QVBoxLayout(frame); vl.setContentsMargins(28,28,28,22); vl.setSpacing(12)
        col=ok_color or T("PRI")
        if icon_name:
            ic=QLabel(); ic.setPixmap(svg_pixmap(icon_name,38,"#7D7D7D")); ic.setAlignment(Qt.AlignCenter); vl.addWidget(ic)
        t=lbl(title,13,True); t.setAlignment(Qt.AlignCenter); vl.addWidget(t)
        m=lbl(message,10,False,T("SUB"),wrap=True); m.setAlignment(Qt.AlignCenter); vl.addWidget(m)
        vl.addSpacing(4)
        br=QHBoxLayout(); br.setSpacing(8)
        cb=ghost_btn("취소"); cb.clicked.connect(self.reject)
        ob=mk_btn(ok_text,col,fg=_icon_col(col),pad="10px 0"); ob.setMinimumWidth(120); ob.clicked.connect(self.accept)
        br.addWidget(cb,1); br.addWidget(ob,1); vl.addLayout(br)
        outer.addWidget(frame)


class InputDialog(QDialog):
    def __init__(self,title,prompt,parent=None):
        super().__init__(parent); self.value=None
        self.setWindowFlags(Qt.Dialog|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setFixedWidth(360)
        outer=QVBoxLayout(self); outer.setContentsMargins(12,12,12,12)
        frame=QFrame()
        frame.setStyleSheet(f"QFrame{{background:{T('CARD')};border-radius:18px;}}")
        sh=QGraphicsDropShadowEffect(frame); sh.setBlurRadius(24); sh.setOffset(0,5); sh.setColor(QColor(0,0,0,38))
        frame.setGraphicsEffect(sh)
        vl=QVBoxLayout(frame); vl.setContentsMargins(24,22,24,20); vl.setSpacing(10)
        vl.addWidget(lbl(title,13,True)); vl.addWidget(lbl(prompt,10,False,T("SUB")))
        self._inp=QLineEdit(); self._inp.setStyleSheet(inp_style()); self._inp.returnPressed.connect(self._ok)
        vl.addWidget(self._inp)
        br=QHBoxLayout(); br.setSpacing(8)
        cb=ghost_btn("취소"); cb.clicked.connect(self.reject)
        ok=mk_btn("추가",T("PRI"),fg=_icon_col(T("PRI")),pad="9px 0"); ok.setMinimumWidth(100); ok.clicked.connect(self._ok)
        br.addWidget(cb,1); br.addWidget(ok,1); vl.addLayout(br)
        outer.addWidget(frame); self._inp.setFocus()
    def _ok(self):
        v=self._inp.text().strip()
        if v: self.value=v; self.accept()


class ChecklistEditor(QWidget):
    def __init__(self,items=None,placeholder="항목을 입력하세요",parent=None):
        super().__init__(parent); self.setStyleSheet(f"background:{T('CARD')};")
        self._ph=placeholder; self._rows=[]
        vl=QVBoxLayout(self); vl.setContentsMargins(0,0,0,0); vl.setSpacing(5)
        self._list_w=QWidget(); self._list_w.setStyleSheet("background:transparent;")
        self._list_l=QVBoxLayout(self._list_w)
        self._list_l.setContentsMargins(0,0,0,0); self._list_l.setSpacing(5)
        vl.addWidget(self._list_w)
        add_btn=QPushButton("항목 추가")
        add_btn.setIcon(svg_icon("plus", 13, "#ffffff"))
        add_btn.setIconSize(QSize(13,13))
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton{{background:{T('GL')};color:{T('SUB')};"
            f"border:1.5px dashed {T('BDR')};border-radius:8px;padding:7px;font-size:9pt;}}"
            f"QPushButton:hover{{background:{T('PRI_L')};color:{T('PRI')};border-color:{T('PRI')};}}"
        )
        add_btn.clicked.connect(lambda: self._add_row()); vl.addWidget(add_btn)
        for item in (items if items else [None]):
            self._add_row(item.get("text","") if item else "")

    def _add_row(self,text=""):
        row=QWidget()
        row.setStyleSheet(f"background:{T('GL')};border-radius:8px;border:1px solid {T('BDR')};")
        rl=QHBoxLayout(row); rl.setContentsMargins(10,5,8,5); rl.setSpacing(8)
        dot=QLabel("·"); dot.setStyleSheet(f"color:{T('PRI')};font-size:16pt;font-weight:bold;background:transparent;"); rl.addWidget(dot)
        inp=QLineEdit(text); inp.setPlaceholderText(self._ph)
        inp.setStyleSheet(f"QLineEdit{{background:transparent;border:none;font-size:10pt;color:{T('TXT')};}}")
        inp.returnPressed.connect(lambda i=inp: self._on_enter(i)); rl.addWidget(inp,1)
        xb=QPushButton("×"); xb.setFixedSize(20,20); xb.setCursor(Qt.PointingHandCursor)
        xb.setStyleSheet(
            f"QPushButton{{background:transparent;color:{T('SUB')};border:none;"
            f"font-size:13pt;border-radius:10px;}}"
            f"QPushButton:hover{{background:{T('RED')};color:white;}}"
        )
        xb.clicked.connect(lambda _,r=row,i=inp: self._del_row(r,i)); rl.addWidget(xb)
        self._list_l.addWidget(row); self._rows.append((row,inp)); inp.setFocus(); return inp

    def _on_enter(self,inp):
        for i,(_,e) in enumerate(self._rows):
            if e is inp:
                if i==len(self._rows)-1: self._add_row()
                else: self._rows[i+1][1].setFocus()
                return

    def _del_row(self,row,inp):
        self._rows=[(r,e) for r,e in self._rows if e is not inp]; row.deleteLater()

    def get_items(self):
        return [new_task(e.text().strip()) for _,e in self._rows if e.text().strip()]
