# core/assets.py
import os, sys
from PyQt5.QtGui  import QFontDatabase, QFont, QIcon, QPixmap, QPainter
from PyQt5.QtSvg  import QSvgRenderer
from PyQt5.QtCore import Qt, QByteArray

_BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(_BASE, "assets", "icons")
FONT_DIR = os.path.join(_BASE, "assets", "fonts")
_FAM     = ""

def setup_font():
    global _FAM
    if _FAM: return _FAM
    db = QFontDatabase()
    for fn in ["Pretendard-Regular.ttf","Pretendard-Medium.ttf",
               "Pretendard-Bold.ttf","Pretendard-SemiBold.ttf"]:
        p = os.path.join(FONT_DIR, fn)
        if os.path.exists(p): QFontDatabase.addApplicationFont(p)
    if   "Pretendard" in db.families():   _FAM = "Pretendard"
    elif sys.platform == "win32":         _FAM = "맑은 고딕"
    elif sys.platform == "darwin":        _FAM = "Apple SD Gothic Neo"
    else:                                  _FAM = "NanumGothic"
    return _FAM

def get_font(size=10, bold=False):
    return QFont(setup_font(), size, QFont.Bold if bold else QFont.Normal)

def svg_pixmap(name, size=20, color="#888"):
    path = os.path.join(ICON_DIR, f"{name}.svg")
    px = QPixmap(size, size); px.fill(Qt.transparent)
    if not os.path.exists(path): return px
    raw = open(path,"rb").read().replace(b"currentColor", color.encode())
    r = QSvgRenderer(QByteArray(raw)); p = QPainter(px); r.render(p); p.end()
    return px

def svg_icon(name, size=20, color="#888"):
    return QIcon(svg_pixmap(name, size, color))

def app_icon():
    for ext in ["ico","png"]:
        p = os.path.join(ICON_DIR, f"app.{ext}")
        if os.path.exists(p): return QIcon(p)
    return svg_icon("app", 64, "#5C5C5C")
