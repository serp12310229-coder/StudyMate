# ui/mini_widget.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from datetime        import datetime
from core.theme      import T, dk, subj_color, dday_color, icon_color_on, is_dark
from core.data       import calc_progress
from core.assets     import svg_icon, svg_pixmap, app_icon
from ui.base_widgets import lbl, sbadge, dbadge, ToggleSwitch


def _diff(dl,fmt="%Y-%m-%d %H:%M"):
    try:
        dt=datetime.strptime(dl,fmt)
        return int((dt-datetime.now()).total_seconds()//86400)
    except Exception: return None

def _dc(d):
    return dday_color(d)

def _dt(d):
    if d is None: return ""
    if d<0: return "기간 지남"
    if d==0: return "D-Day!"
    return f"D-{d}"

def _clear_layout(layout):
    if layout is None: return
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue
        w = item.widget()
        if w:
            try: w.deleteLater()
            except Exception: pass
        else:
            sub = item.layout()
            if sub:
                _clear_layout(sub)


class ChecklistPopup(QFrame):
    changed=pyqtSignal()
    def __init__(self,item_data,itype,color,on_save,parent=None):
        super().__init__(None,Qt.Tool|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.item=item_data; self.itype=itype; self.color=color; self.on_save=on_save
        self.setFixedWidth(290)
        self.setStyleSheet(f"QFrame{{background:{T('CARD')};border-radius:14px;border:1px solid {T('BDR')};}}")
        sh=QGraphicsDropShadowEffect(self); sh.setBlurRadius(22); sh.setOffset(0,5); sh.setColor(QColor(0,0,0,45))
        self.setGraphicsEffect(sh); self._build()

    def _build(self):
        vl=QVBoxLayout(self); vl.setContentsMargins(0,0,0,0); vl.setSpacing(0)
        hdr=QWidget(); hdr.setStyleSheet(f"background:{self.color};border-radius:13px 13px 0 0;")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(14,9,10,9)
        title=self.item.get("name") or self.item.get("subject","")
        hl.addWidget(lbl(title,10,True,"white")); hl.addStretch()
        xb=QPushButton("x"); xb.setFixedSize(22,22); xb.setCursor(Qt.PointingHandCursor)
        xb.setStyleSheet("QPushButton{background:rgba(255,255,255,0.2);color:white;border:none;border-radius:11px;font-size:10pt;}QPushButton:hover{background:rgba(255,255,255,0.4);}")
        xb.clicked.connect(self.hide); hl.addWidget(xb); vl.addWidget(hdr)
        body=QWidget(); body.setStyleSheet(f"background:{T('CARD')};border-radius:0 0 13px 13px;")
        bl=QVBoxLayout(body); bl.setContentsMargins(12,10,12,12); bl.setSpacing(4)
        if self.itype=="assignment":
            for task in self.item.get("tasks",[]): bl.addWidget(self._task_row(task,False))
        else:
            FIXED=[("read1","1회독"),("read2","2회독"),("read_extra","추가 회독")]
            for key,lt in FIXED:
                row=QWidget(); row.setStyleSheet("background:transparent;")
                rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
                cb=QCheckBox(lt); cb.setChecked(self.item.get(key,False))
                cb.setStyleSheet(f"QCheckBox{{color:{T('TXT')};font-size:9pt;background:transparent;spacing:6px;}}QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;border:2px solid {T('BDR')};background:{T('CARD')};}}QCheckBox::indicator:checked{{background:{self.color};border:2px solid {self.color};}}")
                cb.stateChanged.connect(lambda s,k=key: self._tog_fixed(k,s))
                rl.addWidget(cb); rl.addStretch(); bl.addWidget(row)
            for task in self.item.get("extra_tasks",[]): bl.addWidget(self._task_row(task,True))
        vl.addWidget(body); self.adjustSize()

    def _task_row(self,task,is_extra):
        row=QWidget(); row.setStyleSheet("background:transparent;")
        rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(6)
        cb=QCheckBox(); cb.setChecked(task["done"])
        cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;border:2px solid {T('BDR')};background:{T('CARD')};}}QCheckBox::indicator:checked{{background:{self.color};border:2px solid {self.color};}}")
        cb.stateChanged.connect(lambda s,tid=task["id"]: self._tog_task(tid,s,is_extra))
        rl.addWidget(cb)
        sx="text-decoration:line-through;" if task["done"] else ""
        tl=lbl(task["text"],9,False,T("SUB") if task["done"] else T("TXT"))
        tl.setStyleSheet(tl.styleSheet()+sx); rl.addWidget(tl,1)
        return row

    def _tog_task(self,tid,state,is_extra):
        key="extra_tasks" if is_extra else "tasks"
        for t in self.item.get(key,[]):
            if t["id"]==tid: t["done"]=(state==Qt.Checked); break
        self.on_save(); self.changed.emit()

    def _tog_fixed(self,key,state):
        self.item[key]=(state==Qt.Checked); self.on_save(); self.changed.emit()


class MiniWidget(QWidget):
    open_main=pyqtSignal()
    data_changed=pyqtSignal()

    def __init__(self,data,on_save,parent=None):
        super().__init__(None,Qt.Tool|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.data=data; self.on_save=on_save
        self._locked=False; self._drag_pos=None
        self._cur_tab="assignment"; self._popup=None; self._cmap={}
        self._elapsed=0; self._running=False
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._timer=QTimer(self); self._timer.setInterval(1000); self._timer.timeout.connect(self._tick)
        self._inact=QTimer(self); self._inact.setSingleShot(True)
        self._inact.setInterval(60000); self._inact.timeout.connect(self._auto_pause)
        self._settings_popup=None
        # 처음 빌드
        self._build()
        pos=self.data.get("widget_pos")
        if pos: self.move(pos[0],pos[1])
        else:
            scr=QApplication.primaryScreen().geometry(); self.move(scr.width()-354,60)

    def _color(self,item):
        if item.get("color"): self._cmap[item.get("subject","")]=item["color"]; return item["color"]
        return subj_color(item.get("subject","?"),self._cmap)

    def _build(self):
        existing = self.layout()
        if existing:
            _clear_layout(existing)
            try:
                QWidget().setLayout(existing)
            except Exception:
                pass

        outer=QVBoxLayout(self); outer.setContentsMargins(8,8,8,8); outer.setSpacing(0)
        self._frame=QFrame(); self._frame.setObjectName("mf")
        self._frame.setStyleSheet(f"QFrame#mf{{background:{T('CARD')};border-radius:16px;border:1px solid {T('BDR')};}}")
        self._frame.setFixedWidth(320)
        sh=QGraphicsDropShadowEffect(self._frame); sh.setBlurRadius(26); sh.setOffset(0,6); sh.setColor(QColor(0,0,0,48))
        self._frame.setGraphicsEffect(sh); outer.addWidget(self._frame)
        ml=QVBoxLayout(self._frame); ml.setContentsMargins(0,0,0,12); ml.setSpacing(0)
        tbar=QWidget(); tbar.setStyleSheet(f"background:{T('PRI')};border-radius:16px 16px 0 0;"); tbar.setFixedHeight(42)
        tbl=QHBoxLayout(tbar); tbl.setContentsMargins(12,0,8,0); tbl.setSpacing(6)
        ob=QPushButton(); ob.setFixedSize(28,28); ob.setCursor(Qt.PointingHandCursor); ob.setToolTip("메인 창 열기")
        
        ob.setIcon(app_icon(True)); ob.setIconSize(QSize(16,16))
        ob.setStyleSheet("QPushButton{background:rgba(255,255,255,0.18);border:none;border-radius:14px;}QPushButton:hover{background:rgba(255,255,255,0.32);}")
        ob.clicked.connect(self.open_main); tbl.addWidget(ob)
        tbl.addStretch()

        # 설정 버튼
        self._settings_btn=QPushButton(); self._settings_btn.setFixedSize(26,26); self._settings_btn.setCursor(Qt.PointingHandCursor)
        self._settings_btn.setIcon(svg_icon("setting",14,"#ffffff")); self._settings_btn.setIconSize(QSize(14,14))
        self._settings_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.12);border:none;border-radius:13px;}QPushButton:hover{background:rgba(255,255,255,0.26);}")
        self._settings_btn.setToolTip("미니 위젯 설정")
        self._settings_btn.clicked.connect(self._toggle_widget_settings); tbl.addWidget(self._settings_btn)
        self._lock_btn=QPushButton(); self._lock_btn.setFixedSize(26,26); self._lock_btn.setCursor(Qt.PointingHandCursor)
        self._lock_btn.setCheckable(True); self._lock_btn.setToolTip("위치 잠금")

        # 잠금 아이콘: 비활성 pinned, 활성 pinned_x
        self._lock_btn.setIcon(svg_icon("pinned",14,"#ffffff")); self._lock_btn.setIconSize(QSize(14,14))
        self._lock_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.15);border:none;border-radius:13px;}QPushButton:hover{background:rgba(255,255,255,0.3);}")
        self._lock_btn.clicked.connect(self._toggle_lock); tbl.addWidget(self._lock_btn); ml.addWidget(tbar)
        body=QWidget(); body.setStyleSheet("background:transparent;")
        bl=QVBoxLayout(body); bl.setContentsMargins(12,10,12,0); bl.setSpacing(8)
        cfg=self.data.get("widget_config",{})
        
        if cfg.get("show_timer",True):
            tw=QWidget(); tw.setStyleSheet(f"background:{T('GL')};border-radius:10px;")
            tl=QVBoxLayout(tw); tl.setContentsMargins(12,10,12,10); tl.setSpacing(6)
            self._time_lbl=QLabel("00:00:00"); self._time_lbl.setAlignment(Qt.AlignCenter)
            self._time_lbl.setStyleSheet(f"color:{T('TXT')};font-size:22pt;font-weight:bold;background:transparent;letter-spacing:2px;")
            tl.addWidget(self._time_lbl)
            br=QHBoxLayout(); br.setSpacing(6)
            self._s_btn=QPushButton("시작"); self._s_btn.setCursor(Qt.PointingHandCursor)
            self._s_btn.setStyleSheet(f"QPushButton{{background:{T('PRI')};color:white;border:none;border-radius:7px;padding:5px 0;font-size:9pt;font-weight:bold;}}QPushButton:hover{{background:{dk(T('PRI'))};}}")
            self._s_btn.setIcon(svg_icon("play",14,icon_color_on(T("PRI")))); self._s_btn.setIconSize(QSize(14,14))
            self._s_btn.clicked.connect(self._start)

            self._p_btn=QPushButton("일시정지"); self._p_btn.setCursor(Qt.PointingHandCursor); self._p_btn.setEnabled(False); self._p_btn.hide();
            self._p_btn.setStyleSheet(f"QPushButton{{background:{T('PRI')};color:white;border:none;border-radius:7px;padding:5px 0;font-size:9pt;font-weight:bold;}}QPushButton:disabled{{background:{T('BDR')};color:{T('SUB')};}}QPushButton:hover:!disabled{{background:{dk(T('PRI'))};}}")
            self._p_btn.setIcon(svg_icon("pause",14,T("SUB") if not self._p_btn.isEnabled() else icon_color_on(T("ORG")))); self._p_btn.setIconSize(QSize(14,14))
            self._p_btn.clicked.connect(self._pause)

            self._x_btn=QPushButton("중단"); self._x_btn.setCursor(Qt.PointingHandCursor); self._x_btn.setEnabled(False)
            self._x_btn.setStyleSheet(f"QPushButton{{background:{T('BDR')};color:{T('SUB')};border:none;border-radius:7px;padding:5px 0;font-size:9pt;font-weight:bold;}}QPushButton:enabled:hover{{background:{T('RED')};color:white;}}")
            self._x_btn.setIcon(svg_icon("stop",14,T("SUB"))); self._x_btn.setIconSize(QSize(14,14))
            self._x_btn.clicked.connect(self._stop)

            for b in [self._s_btn,self._p_btn,self._x_btn]: br.addWidget(b,1)
            tl.addLayout(br); bl.addWidget(tw)

        tabw=QWidget(); tabw.setStyleSheet(f"background:{T('GL')};border-radius:10px;")
        tabl=QHBoxLayout(tabw); tabl.setContentsMargins(4,4,4,4); tabl.setSpacing(4)
        self._ta=QPushButton(); self._ta.setText("과제"); self._ta.setCursor(Qt.PointingHandCursor); self._ta.setCheckable(True)
        self._te=QPushButton(); self._te.setText("시험"); self._te.setCursor(Qt.PointingHandCursor); self._te.setCheckable(True)
        self._ta.setAutoExclusive(True); self._te.setAutoExclusive(True)
        for btn,key in [(self._ta,"assignment"),(self._te,"exam")]:
            btn.clicked.connect(lambda _,k=key: self._switch_tab(k)); tabl.addWidget(btn,1)
        self._upd_tab_style(); bl.addWidget(tabw)
        lsc=QScrollArea(); lsc.setWidgetResizable(True); lsc.setStyleSheet("QScrollArea{background:transparent;border:none;}"); lsc.setMaximumHeight(240)
        self._list_w=QWidget(); self._list_w.setStyleSheet("background:transparent;")
        self._list_l=QVBoxLayout(self._list_w); self._list_l.setContentsMargins(0,0,0,0); self._list_l.setSpacing(6)
        lsc.setWidget(self._list_w); bl.addWidget(lsc); ml.addWidget(body); self._refresh_list()
        self._switch_tab(self._cur_tab)
        if self.isVisible():
            self.show()

    def _upd_tab_style(self):
        for btn,key in [(self._ta,"assignment"),(self._te,"exam")]:
            active=key==self._cur_tab
            btn.setChecked(active)
            if active: btn.setStyleSheet(f"QPushButton{{background:{T('PRI')};color:white;border:none;border-radius:7px;padding:5px 8px;font-size:9pt;font-weight:bold;}}")
            else: btn.setStyleSheet(f"QPushButton{{background:transparent;color:{T('SUB')};border:none;border-radius:7px;padding:5px 8px;font-size:9pt;font-weight:normal;}}QPushButton:hover{{background:{T('BDR')};color:{T('TXT')};}}")

    def _switch_tab(self,key): self._cur_tab=key; self._upd_tab_style(); self._refresh_list()

    def refresh(self): self._refresh_list()

    def _refresh_list(self):
        while self._list_l.count():
            i=self._list_l.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        cfg=self.data.get("widget_config",{})
        items=self.data.get("assignments" if self._cur_tab=="assignment" else "exams",[])
        if not items:
            e=lbl("항목이 없습니다",9,False,T("SUB")); e.setAlignment(Qt.AlignCenter); self._list_l.addWidget(e)
        else:
            for item in items:
                color=self._color(item)
                row=self._asgn_row(item,cfg,color) if self._cur_tab=="assignment" else self._exam_row(item,cfg,color)
                self._list_l.addWidget(row)
        self._list_l.addStretch()

    def _asgn_row(self,asgn,cfg,color):
        row=QFrame(); row.setStyleSheet(f"QFrame{{background:{T('GL')};border-radius:8px;border:1px solid {T('BDR')};}}"); row.setCursor(Qt.PointingHandCursor)
        rl=QVBoxLayout(row); rl.setContentsMargins(10,8,10,8); rl.setSpacing(4)
        top=QHBoxLayout(); top.setSpacing(6)
        if cfg.get("show_subject",True): top.addWidget(sbadge(asgn["subject"],color))
        top.addWidget(lbl(asgn["name"],9,True)); top.addStretch()
        if cfg.get("show_dday",True):
            diff=_diff(asgn.get("deadline",""))
            if diff is not None: top.addWidget(dbadge(_dt(diff),_dc(diff)))
        rl.addLayout(top)
        if cfg.get("show_progress",True):
            prog=calc_progress(asgn.get("tasks",[])); cp=T("GRN") if prog==100 else color
            bar=QProgressBar(); bar.setFixedHeight(4); bar.setRange(0,100); bar.setValue(prog); bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar{{background:{T('BDR')};border-radius:2px;border:none;}}QProgressBar::chunk{{background:{cp};border-radius:2px;}}"); rl.addWidget(bar)
        row.mousePressEvent=lambda e,a=asgn,c=color: self._show_popup(e,a,"assignment",c)
        return row

    def _exam_row(self,exam,cfg,color):
        row=QFrame(); row.setStyleSheet(f"QFrame{{background:{T('GL')};border-radius:8px;border:1px solid {T('BDR')};}}"); row.setCursor(Qt.PointingHandCursor)
        rl=QHBoxLayout(row); rl.setContentsMargins(10,8,10,8); rl.setSpacing(6)
        if cfg.get("show_subject",True): rl.addWidget(sbadge(exam["subject"],color))
        rl.addWidget(lbl(exam["subject"],9,True)); rl.addStretch()
        if cfg.get("show_dday",True):
            diff=_diff(exam.get("date",""),"%Y-%m-%d")
            if diff is not None: rl.addWidget(dbadge(_dt(diff),_dc(diff)))
        row.mousePressEvent=lambda e,ex=exam,c=color: self._show_popup(e,ex,"exam",c)
        return row

    def _show_popup(self,e,item_data,itype,color):
        if self._popup: self._popup.hide(); self._popup=None
        self._popup=ChecklistPopup(item_data,itype,color,self._save_refresh)
        self._popup.changed.connect(self.data_changed)
        gpos=self.mapToGlobal(QPoint(0,0))
        px=gpos.x()-310 if gpos.x()>350 else gpos.x()+self.width()+10
        self._popup.move(px,gpos.y()+50); self._popup.show()

    def _save_refresh(self): self.on_save(); self._refresh_list(); self.data_changed.emit()

    def _toggle_lock(self):
        # 토글 상태에 따라 아이콘을 변경하고 내부 잠금 상태를 갱신
        checked = self._lock_btn.isChecked()
        self._locked = checked
        if checked:
            self._lock_btn.setIcon(svg_icon("pinned_x",14,"#ffffff"))
        else:
            self._lock_btn.setIcon(svg_icon("pinned",14,"#ffffff"))

    def set_always_on_top(self,on):
        flags=self.windowFlags()
        if on: flags|=Qt.WindowStaysOnTopHint
        else: flags&=~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if self.isVisible(): self.show()

    def _toggle_widget_settings(self):
        if self._settings_popup and self._settings_popup.isVisible():
            self._settings_popup.hide(); return
        cfg=self.data.setdefault("widget_config",{})
        popup=QFrame(None, Qt.Tool|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        popup.setStyleSheet(f"QFrame{{background:{T('CARD')};border-radius:18px;}}")
        popup.setFixedWidth(260)
        vl=QVBoxLayout(popup); vl.setContentsMargins(12,10,12,10); vl.setSpacing(8)
        vl.addWidget(lbl("미니 위젯 표시 항목",11,True))
        pairs=[("show_timer","타이머"),("show_dday","D-Day 배지"),("show_progress","진행도 바"),("show_subject","과목 배지")]
        rows=[]
        for key,text in pairs:
            w=QWidget(); rl=QHBoxLayout(w); rl.setContentsMargins(0,0,0,0)
            rl.addWidget(lbl(text,10)); rl.addStretch()
            tg=ToggleSwitch(cfg.get(key,True))
            def make_toggled(k,tg):
                tg.toggled.connect(lambda v,kk=k: self._on_widget_cfg_changed(kk,v))
            make_toggled(key,tg)
            rl.addWidget(tg); vl.addWidget(w); rows.append((key,tg))
        btn=QPushButton("닫기"); btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton{{background:{T('PRI')};color:white;border:none;border-radius:7px;padding:6px 10px;font-weight:bold;}}")
        btn.clicked.connect(popup.hide); vl.addWidget(btn,alignment=Qt.AlignRight)
        gpos=self.mapToGlobal(QPoint(self.width()-popup.width()-20,40))
        popup.move(gpos); popup.show()
        self._settings_popup=popup

    def _on_widget_cfg_changed(self,key,val):
        cfg=self.data.setdefault("widget_config",{})
        cfg[key]=val; self.on_save(); self._refresh_list()

    def _tick(self):
        self._elapsed+=1; h,r=divmod(self._elapsed,3600); m,s=divmod(r,60)
        self._time_lbl.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _start(self):
        self._s_btn.hide()
        self._p_btn.show()

        self._running=True; self._timer.start(); self._inact.start()
        self._s_btn.setText("실행 중"); self._s_btn.setEnabled(False)
        self._p_btn.setEnabled(True); self._p_btn.setIcon(svg_icon("pause",14,icon_color_on(T("BDR"))))
        self._x_btn.setEnabled(True); self._x_btn.setIcon(svg_icon("stop",14,icon_color_on(T("RED"))))

    def _pause(self):
        self._p_btn.hide()
        self._s_btn.show()

        self._running=False; self._timer.stop(); self._inact.stop()
        self._s_btn.setText("시작"); self._s_btn.setEnabled(True); self._p_btn.setEnabled(False)
        
        self._p_btn.setIcon(svg_icon("pause",14,T("SUB")))
        self._x_btn.setIcon(svg_icon("stop",14,T("SUB")))

    def _auto_pause(self):
        if self._running: self._pause()

    def _stop(self):
        self._running=False; self._timer.stop(); self._inact.stop()
        self._elapsed=0; self._time_lbl.setText("00:00:00")
        
        self._p_btn.hide()
        self._s_btn.show()

        self._s_btn.setText("시작"); self._s_btn.setEnabled(True)
        self._p_btn.setEnabled(False); self._x_btn.setEnabled(False)
        self._p_btn.setIcon(svg_icon("pause",14,T("SUB")))
        self._x_btn.setIcon(svg_icon("stop",14,T("SUB")))

    def reset_inactivity(self):
        if self._running: self._inact.start()

    def mousePressEvent(self,e):
        if not self._locked and e.button()==Qt.LeftButton:
            self._drag_pos=e.globalPos()-self.frameGeometry().topLeft()

    def mouseMoveEvent(self,e):
        if not self._locked and self._drag_pos and e.buttons()==Qt.LeftButton:
            self.move(e.globalPos()-self._drag_pos)

    def mouseReleaseEvent(self,e):
        if self._drag_pos:
            pos=self.pos(); self.data["widget_pos"]=[pos.x(),pos.y()]; self.on_save()
        self._drag_pos=None