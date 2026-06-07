# core/theme.py
THEMES = {
    "mono": {
        "name":"모노크롬","BG":"#F2F2F2","CARD":"#FFFFFF",
        "PRI":"#5C5C5C","PRI_L":"#EBEBEB","GRN":"#6A9E7F","RED":"#C0605A",
        "ORG":"#B8885A","TXT":"#1A1A1A","SUB":"#888888","BDR":"#DEDEDE","GL":"#F8F8F8",
        "SUBJ":["#8A8A8A","#A09898","#7A8A8A","#8A7A8A","#8A8A7A","#9A8A8A","#7A8A7A","#8A9A8A"],
        "DDAY_FROM":"#DEDEDE","DDAY_TO":"#5C5C5C",
    },
    "pastel": {
        "name":"파스텔","BG":"#F2F2F2","CARD":"#FFFFFF",
        "PRI":"#A4DEAB","PRI_L":"#EDE9FF","GRN":"#6BBFA0","RED":"#E8909A",
        "ORG":"#F0B27A","TXT":"#2D2D3A","SUB":"#9090A8","BDR":"#E0D8F0","GL":"#FAF8FF",
        "SUBJ":["#9B8EC4","#E8909A","#6BBFA0","#F0B27A","#7EB8D4","#C4A0C8","#D4BC7A","#88C4C0"],
        "DDAY_FROM":"#F0F0F6","DDAY_TO":"#A4DEAB",
    },
}
_cur: dict = dict(THEMES["mono"])

def T(k: str) -> str:
    return _cur.get(k, "#888888")

def apply_theme(name: str):
    _cur.clear()
    _cur.update(THEMES.get(name, THEMES["mono"]))

def apply_custom(ov: dict):
    _cur.update(ov)

def current_snapshot() -> dict:
    return dict(_cur)

def current_name() -> str:
    for k, v in THEMES.items():
        if v["BG"] == _cur.get("BG"):
            return k
    return "custom"

def subj_color(name: str, cmap: dict) -> str:
    if name not in cmap:
        pal = _cur.get("SUBJ", THEMES["mono"]["SUBJ"])
        cmap[name] = pal[len(cmap) % len(pal)]
    return cmap[name]

def dk(c: str, a: int = 18) -> str:
    h = c.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"#{max(0,r-a):02x}{max(0,g-a):02x}{max(0,b-a):02x}"

def _hex_to_rgb(h: str):
    hh = h.lstrip("#")
    return int(hh[0:2],16), int(hh[2:4],16), int(hh[4:6],16)

def _rgb_to_hex(r, g, b) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def _lerp(a, b, t):
    return int(a + (b - a) * t)

def lerp_color(c1: str, c2: str, t: float) -> str:
    r1,g1,b1 = _hex_to_rgb(c1)
    r2,g2,b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(_lerp(r1,r2,t), _lerp(g1,g2,t), _lerp(b1,b2,t))

def is_dark(color: str, threshold: str = "#B8B8B8") -> bool:
    # 배경색이 어두우면 True, 밝으면 False.
    r, g, b = _hex_to_rgb(color)
    tr, tg, tb = _hex_to_rgb(threshold)
    return (r + g + b) / 3 < (tr + tg + tb) / 3

def icon_color_on(bg_color: str) -> str:
    """
    배경색에 맞는 아이콘/텍스트 색 반환.
    is_dark(bg) == True  → T('SUB')  (보조 텍스트, 밝은 색)
    is_dark(bg) == False → T('GRN')  (완료 색상, 주요 강조)
    """
    if is_dark(bg_color):
        return T("SUB")
    return T("GRN")

def dday_color(days, max_days: int = 14) -> str:
    if days is None:
        return T("SUB")
    try:
        d = int(days)
    except Exception:
        return T("SUB")
    if d <= 0:
        return _cur.get("DDAY_TO", T("PRI"))
    t = min(1.0, d / float(max_days))
    from_col = _cur.get("DDAY_FROM", T("BDR"))
    to_col   = _cur.get("DDAY_TO",   T("PRI"))
    return lerp_color(to_col, from_col, t)
