# core/assets.py
import os, sys, re
from PyQt5.QtGui  import QFontDatabase, QFont, QIcon, QPixmap, QPainter, QImage
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
    for fn in ['Pretendard-Regular.ttf','Pretendard-Medium.ttf',
               'Pretendard-Bold.ttf','Pretendard-SemiBold.ttf']:
        p = os.path.join(FONT_DIR, fn)
        if os.path.exists(p): QFontDatabase.addApplicationFont(p)
    if   'Pretendard' in db.families():   _FAM = 'Pretendard'
    elif sys.platform == 'win32':         _FAM = '맑은 고딕'
    elif sys.platform == 'darwin':        _FAM = 'Apple SD Gothic Neo'
    else:                                  _FAM = 'NanumGothic'
    return _FAM

def get_font(size=10, bold=False):
    return QFont(setup_font(), size, QFont.Bold if bold else QFont.Normal)

def _load_svg_raw(path):
    with open(path, "rb") as f:
        return f.read()

def svg_pixmap(name, size=20, color=None):
    """
    SVG 렌더러:
    - color 가 주어지면
      1) 'currentColor' 를 치환
      2) 하드코드된 fill/stroke=\"#xxxxxx\" 를 치환
      3) (fill/stroke 명시가 전혀 없을 경우) <svg ...> 루트에 기본 fill 속성을 주입
    """
    path = os.path.join(ICON_DIR, f"{name}.svg")
    px = QPixmap(size, size); px.fill(Qt.transparent)
    if not os.path.exists(path): return px
    raw = _load_svg_raw(path)
    if color:
        # currentColor 치환
        raw = raw.replace(b"currentColor", color.encode())
        # 하드코드된 hex 색상(fill/stroke) 치환 (fill="#......" 또는 fill='......')
        raw = re.sub(rb'fill="#[0-9A-Fa-f]{3,6}"', f'fill="{color}"'.encode(), raw)
        raw = re.sub(rb"fill='#[0-9A-Fa-f]{3,6}'", f"fill='{color}'".encode(), raw)
        raw = re.sub(rb'stroke="#[0-9A-Fa-f]{3,6}"', f'stroke="{color}"'.encode(), raw)
        raw = re.sub(rb"stroke='#[0-9A-Fa-f]{3,6}'", f"stroke='{color}'".encode(), raw)
        # 루트 <svg>에 fill 속성이 없으면 기본 fill 주입 (path에 fill이 없을 때 기본 적용될 수 있도록)
        if b'fill="' not in raw.split(b'>', 1)[0] and b"style=" not in raw.split(b'>', 1)[0]:
            raw = re.sub(rb'(<svg[^>]*?)>', lambda m: (m.group(1) + f' fill="{color}">'.encode()), raw, count=1)
        else:
            # 루트에 style이 있으나 fill: 이 없으면 style에 fill 추가
            header = raw.split(b'>', 1)[0]
            if b"style=" in header and b"fill:" not in header:
                raw = re.sub(rb'(style=["\'])([^"\']*)(["\'])', lambda m: (m.group(1) + m.group(2) + f';fill:{color}' + m.group(3)).encode(), raw, count=1)
    r = QSvgRenderer(QByteArray(raw))
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(0)
    painter = QPainter(img)
    painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    r.render(painter)
    painter.end()
    return QPixmap.fromImage(img)

def svg_icon(name, size=20, color=None):
    return QIcon(svg_pixmap(name, size, color))

def app_icon(white=False):
    candidates = []
    if white:
        candidates += [os.path.join(ICON_DIR, "app_white.ico"), os.path.join(ICON_DIR, "app_white.png")]
    candidates += [os.path.join(ICON_DIR, "app.ico"), os.path.join(ICON_DIR, "app.png")]
    for p in candidates:
        if os.path.exists(p): return QIcon(p)
    return svg_icon("app", 64, "#5C5C5C")
