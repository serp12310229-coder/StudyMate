# ui/dialogs/settings_dialog.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from core.theme      import T, THEMES, apply_theme, apply_custom, current_snapshot, icon_color_on
from core.assets     import svg_icon
from ui.base_widgets import lbl, mk_btn, ghost_btn, ToggleSwitch, foot_row


class SettingsDialog(QDialog):
    theme_changed=pyqtSignal()
    def __init__(self,data,parent=None):
        super().__init__(parent); self.data=data
        self.setWindowTitle("설정"); self.setFixedWidth(460)
        self.setWindowFlags(self.windowFlags()|Qt.WindowStaysOnTopHint)
        self.setStyleSheet(f"background:{T('CARD')};"); self._color_btns={}; self._build()

    def _grp(self,icon_name,title):
        w=QWidget(); w.setStyleSheet(f"background:{T('GL')};border-radius:12px;")
        vl=QVBoxLayout(w); vl.setContentsMargins(16,14,16,14); vl.setSpacing(10)
        hr=QHBoxLayout(); hr.setSpacing(8)
        ic=QLabel(); ic.setPixmap(svg_icon(icon_name,18,icon_color_on(T("PRI"))).pixmap(18,18))
        hr.addWidget(ic); hr.addWidget(lbl(title,11,True)); hr.addStretch()
        hw=QWidget(); hw.setStyleSheet("background:transparent;"); hw.setLayout(hr); vl.addWidget(hw)
        return w,vl

    def _build(self):
        root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        hdr=QWidget(); hdr.setFixedHeight(60); hdr.setStyleSheet(f"background:{T('PRI')};")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        ic=QLabel(); ic.setPixmap(svg_icon("setting",20,"white").pixmap(20,20)); hl.addWidget(ic); hl.addSpacing(8)
        hl.addWidget(lbl("설정",14,True,"white")); root.addWidget(hdr)
        sc=QScrollArea(); sc.setWidgetResizable(True); sc.setStyleSheet("QScrollArea{border:none;}"); sc.setMinimumHeight(440)
        body=QWidget(); body.setStyleSheet(f"background:{T('CARD')};")
        bl=QVBoxLayout(body); bl.setContentsMargins(20,16,20,16); bl.setSpacing(16)
        tgrp,tgl=self._grp("colorcustom","테마 선택")
        pr=QHBoxLayout(); pr.setSpacing(8); self._theme_btns={}
        cur=self.data.get("theme_name","mono")
        for name,meta in THEMES.items():
            btn=QPushButton(meta["name"]); btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True); btn.setChecked(name==cur); btn.setStyleSheet(self._ps(name==cur))
            btn.clicked.connect(lambda _,n=name: self._pick_preset(n))
            self._theme_btns[name]=btn; pr.addWidget(btn,1)
        tgl.addLayout(pr); bl.addWidget(tgrp)
        cgrp,cgl=self._grp("colorcustom","색상 커스텀")
        for key,label_text in [("BG","배경색"),("CARD","카드 배경"),("PRI","주요 색상"),
                                 ("GRN","완료 색상"),("RED","시험/경고"),("TXT","텍스트"),
                                 ("SUB","보조 텍스트"),("BDR","테두리"),("DDAY_FROM","D-Day 시작색"),("DDAY_TO","D-Day 종료색")]:
            row=QWidget(); row.setStyleSheet("background:transparent;")
            rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0)
            rl.addWidget(lbl(label_text,10)); rl.addStretch()
            btn=QPushButton(); btn.setFixedSize(52,24); btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"background:{T(key)};border:2px solid {T('BDR')};border-radius:7px;")
            btn.clicked.connect(lambda _,k=key: self._pick_color(k))
            self._color_btns[key]=btn; rl.addWidget(btn); cgl.addWidget(row)
        reset=QPushButton("기본값으로 초기화"); reset.setCursor(Qt.PointingHandCursor)
        reset.setStyleSheet(f"QPushButton{{background:transparent;color:{T('RED')};border:1px solid {T('RED')};border-radius:6px;padding:5px 12px;font-size:9pt;}}QPushButton:hover{{background:{T('RED')};color:white;}}")
        reset.clicked.connect(self._reset); cgl.addWidget(reset); bl.addWidget(cgrp)
        cfg=self.data.get("widget_config",{})
        wgrp,wgl=self._grp("widgetsetting","미니 위젯 표시 항목"); self._cfg_tgs={}
        for key,label_text in [("show_timer","타이머"),("show_dday","D-Day 배지"),
                                 ("show_progress","진행도 바"),("show_subject","과목 배지")]:
            row=QWidget(); row.setStyleSheet("background:transparent;")
            rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0)
            rl.addWidget(lbl(label_text,10)); rl.addStretch()
            tg=ToggleSwitch(cfg.get(key,True)); self._cfg_tgs[key]=tg; rl.addWidget(tg); wgl.addWidget(row)
        bl.addWidget(wgrp); sc.setWidget(body); root.addWidget(sc,1)
        root.addWidget(foot_row(self,self._save,"저장",T("PRI")))

    def _ps(self,active):
        if active: return f"QPushButton{{background:{T('PRI')};color:white;border:none;border-radius:8px;padding:8px;font-size:10pt;font-weight:bold;}}"
        return f"QPushButton{{background:{T('BDR')};color:{T('SUB')};border:none;border-radius:8px;padding:8px;font-size:10pt;}}QPushButton:hover{{background:{T('PRI_L')};color:{T('PRI')};}}"

    def _pick_preset(self,name):
        apply_theme(name); self.data["theme_name"]=name; self.data["theme_custom"]={}
        for k,btn in self._theme_btns.items(): btn.setChecked(k==name); btn.setStyleSheet(self._ps(k==name))
        for key,btn in self._color_btns.items(): btn.setStyleSheet(f"background:{T(key)};border:2px solid {T('BDR')};border-radius:7px;")
        # 즉시 반영
        self.theme_changed.emit()

    def _pick_color(self,key):
        c=QColorDialog.getColor(QColor(T(key)),self,f"{key} 색상 선택")
        if c.isValid():
            apply_custom({key:c.name()})
            self._color_btns[key].setStyleSheet(f"background:{c.name()};border:2px solid {T('BDR')};border-radius:7px;")
            # 즉시 반영
            self.theme_changed.emit()

    def _reset(self):
        apply_theme(self.data.get("theme_name","mono")); self.data["theme_custom"]={}
        for key,btn in self._color_btns.items(): btn.setStyleSheet(f"background:{T(key)};border:2px solid {T('BDR')};border-radius:7px;")
        self.theme_changed.emit()

    def _save(self):
        self.data["theme_custom"]=current_snapshot()
        cfg=self.data.setdefault("widget_config",{})
        for key,tg in self._cfg_tgs.items(): cfg[key]=tg.isChecked()
        from core.data import save; save(self.data)
        self.theme_changed.emit(); self.accept()