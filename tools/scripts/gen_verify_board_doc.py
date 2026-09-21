#!/usr/bin/env python3
"""生成《PCIE-1751 GPIO 模拟 I2C 验证板设计说明》PDF 到 docs/hardware/。"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Preformatted, PageBreak)
from reportlab.graphics.shapes import (Drawing, Line, Rect, String, Circle,
                                       Polygon, PolyLine, Wedge)

# ---------------------------------------------------------------- 矢量绘图工具
INK = colors.HexColor('#1a2430')
W = colors.HexColor('#20406a')          # 导线
RED = colors.HexColor('#c0392b')
GRN = colors.HexColor('#1e8449')
GRY = colors.HexColor('#8895a4')
FILL = colors.HexColor('#eef3f9')
CHIPF = colors.HexColor('#fdf7ec')


def wire(d, pts, c=W, w=1.0):
    d.add(PolyLine(pts, strokeColor=c, strokeWidth=w))


def dot(d, x, y, c=W):
    d.add(Circle(x, y, 2.3, fillColor=c, strokeColor=c))


def txt(d, x, y, s, size=6.8, c=INK, anchor='start', bold=False):
    d.add(String(x, y, s, fontName='CNB' if bold else 'CN',
                 fontSize=size, fillColor=c, textAnchor=anchor))


def res_v(d, x, ytop, ybot, ref, val, side=1):
    """竖直电阻：从 ytop 连到 ybot。side=1 标注在右，-1 在左。"""
    ym = (ytop + ybot) / 2.0
    d.add(Line(x, ytop, x, ym + 9, strokeColor=W))
    d.add(Rect(x - 3.5, ym - 9, 7, 18, fillColor=colors.white, strokeColor=W, strokeWidth=0.9))
    d.add(Line(x, ym - 9, x, ybot, strokeColor=W))
    a = 'start' if side > 0 else 'end'
    txt(d, x + 6 * side, ym + 2.5, ref, 6.3, anchor=a)
    txt(d, x + 6 * side, ym - 6, val, 6.3, anchor=a, c=GRY)


def buf(d, xin, y, flip=False, h=17.0):
    """开漏缓冲器三角形，返回输出端 x 坐标。"""
    L = h * 1.35
    xo = xin - L if flip else xin + L
    d.add(Polygon([xin, y - h / 2, xin, y + h / 2, xo, y],
                  fillColor=FILL, strokeColor=W, strokeWidth=1))
    # 开漏输出的菱形标记
    s = 2.6
    xm = xo + (-4.5 if flip else 4.5)
    d.add(Polygon([xm - s, y, xm, y + s, xm + s, y, xm, y - s],
                  fillColor=colors.white, strokeColor=W, strokeWidth=0.8))
    return xo + (-7 if flip else 7)


def chip(d, x, y, w, h, name, sub='', tpos='in', spos='under'):
    """tpos: in=框内顶部 / above=框外上方 / mid=框内居中；spos: under=紧随标题 / bottom=框内底部"""
    d.add(Rect(x, y, w, h, fillColor=CHIPF, strokeColor=INK, strokeWidth=1))
    ty = {'in': y + h - 13, 'above': y + h + 5, 'mid': y + h / 2 + 2}[tpos]
    txt(d, x + w / 2, ty, name, 7.6, anchor='middle', bold=True)
    if sub:
        sy = y + 7 if spos == 'bottom' else ty - 10
        txt(d, x + w / 2, sy, sub, 6.2, anchor='middle', c=GRY)


def nc_mark(d, x, y):
    """悬空标记 ×"""
    s = 3.2
    d.add(Line(x - s, y - s, x + s, y + s, strokeColor=RED, strokeWidth=0.9))
    d.add(Line(x - s, y + s, x + s, y - s, strokeColor=RED, strokeWidth=0.9))


def gnd_sym(d, x, y):
    d.add(Line(x - 6, y, x + 6, y, strokeColor=W, strokeWidth=1.1))
    d.add(Line(x - 3.6, y - 2.6, x + 3.6, y - 2.6, strokeColor=W, strokeWidth=1.1))
    d.add(Line(x - 1.4, y - 5.2, x + 1.4, y - 5.2, strokeColor=W, strokeWidth=1.1))


def fig_schematic():
    """图 1：验证板系统原理图"""
    d = Drawing(500, 352)
    V, G = 330, 20                                   # +5V 轨 / GND 轨
    d.add(Line(28, V, 476, V, strokeColor=W, strokeWidth=1.3))
    txt(d, 28, V + 5, '+5V', 7, c=W, bold=True)
    d.add(Line(28, G, 476, G, strokeColor=W, strokeWidth=1.3))
    txt(d, 28, G - 9, 'GND', 7, c=W, bold=True)

    # ---- J1 连接器
    chip(d, 25, 150, 50, 145, 'J1', '接端子台', tpos='above', spos='bottom')
    ys = {'v': 282, 'g': 258, 'scl': 228, 'sda': 198, 'in': 168}
    lbl = [('v', '1  +5V'), ('g', '2  GND'), ('scl', '3  SCL_OUT'),
           ('sda', '4  SDA_OUT'), ('in', '5  SDA_IN')]
    for k, s in lbl:
        txt(d, 29, ys[k] - 2.5, s, 6.2)
        d.add(Line(75, ys[k], 88, ys[k], strokeColor=W))
    wire(d, [88, ys['v'], 96, ys['v'], 96, V]); dot(d, 96, V)
    wire(d, [88, ys['g'], 84, ys['g'], 84, G]); dot(d, 84, G)

    # ---- J1 到 U1 的三条信号线 + 输入端上拉
    for k, xr, ref in (('scl', 112, 'R3'), ('sda', 138, 'R4')):
        d.add(Line(88, ys[k], 196, ys[k], strokeColor=W))
        res_v(d, xr, V, ys[k], ref, '10k'); dot(d, xr, ys[k])
    d.add(Line(88, ys['in'], 196, ys['in'], strokeColor=W))
    res_v(d, 164, V, ys['in'], 'R5', '4.7k'); dot(d, 164, ys['in'])

    # ---- U1 74HCT07 三个通道
    d.add(Rect(190, 152, 52, 92, fillColor=None, strokeColor=GRY,
               strokeWidth=0.7, strokeDashArray=[2, 2]))
    txt(d, 216, 246, 'U1  74HCT07', 6.6, anchor='middle', bold=True)
    o1 = buf(d, 196, ys['scl'])
    o2 = buf(d, 196, ys['sda'])
    i3 = buf(d, 236, ys['in'], flip=True)   # 回读通道，信号自右向左

    # ---- I2C 总线
    d.add(Line(o1, ys['scl'], 320, ys['scl'], strokeColor=W, strokeWidth=1.2))
    d.add(Line(o2, ys['sda'], 320, ys['sda'], strokeColor=W, strokeWidth=1.2))
    txt(d, 258, ys['scl'] + 6, 'SCL', 7, c=W, bold=True)
    txt(d, 258, ys['sda'] + 6, 'SDA', 7, c=W, bold=True)
    res_v(d, 250, V, ys['scl'], 'R1', '2.2k'); dot(d, 250, ys['scl'])
    res_v(d, 288, V, ys['sda'], 'R2', '2.2k'); dot(d, 288, ys['sda'])
    # 回读通道取自 SDA
    wire(d, [i3, ys['in'], 306, ys['in'], 306, ys['sda']]); dot(d, 306, ys['sda'])

    # ---- U2 DS2482-100
    chip(d, 320, 100, 80, 162, 'DS2482-100', 'U2   从机地址 0x18')
    txt(d, 324, ys['scl'] - 2.5, 'SCL 4', 6.2)
    txt(d, 324, ys['sda'] - 2.5, 'SDA 5', 6.2)
    wire(d, [360, 262, 360, V]); dot(d, 360, V)
    txt(d, 364, 268, '1 VCC', 6.2)
    for x, nm in ((338, '3 GND'), (360, '8 AD0'), (382, '7 AD1')):
        d.add(Line(x, 100, x, G, strokeColor=W))
        dot(d, x, G)
        txt(d, x - 1, 92, nm, 5.9, anchor='middle')
    txt(d, 396, 152, '2 IO', 6.2, anchor='end')
    txt(d, 396, 122, '6 PCTLZ', 6.2, anchor='end')
    d.add(Line(400, 124, 414, 124, strokeColor=W)); nc_mark(d, 419, 124)

    # ---- 1-Wire 到 U3 DS2431
    wire(d, [400, 154, 452, 154, 452, 92], w=1.2)
    txt(d, 406, 158, '1-Wire', 6.4, c=W, bold=True)
    res_v(d, 428, V, 154, 'R6', '1k  不焊'); dot(d, 428, 154)
    chip(d, 415, 42, 75, 50, 'DS2431', 'U3', tpos='mid')
    txt(d, 456, 82, '2 IO', 6.2)
    txt(d, 486, 48, '3 NC 悬空', 5.9, anchor='end', c=GRY)
    d.add(Line(432, 42, 432, G, strokeColor=W)); dot(d, 432, G)
    txt(d, 432, 33, '1 GND', 5.9, anchor='middle')

    return d


def fig_pinout():
    """图 2：74HCT07 DIP-14 引脚使用"""
    d = Drawing(500, 205)
    x0, y0, w, h = 185, 22, 130, 165
    d.add(Rect(x0, y0, w, h, fillColor=CHIPF, strokeColor=INK, strokeWidth=1.1))
    d.add(Wedge(x0 + w / 2, y0 + h, 9, 180, 360, fillColor=colors.white,
                strokeColor=INK, strokeWidth=1.1))
    txt(d, x0 + w / 2, y0 + h / 2 + 12, '74HCT07', 9, anchor='middle', bold=True)
    txt(d, x0 + w / 2, y0 + h / 2 - 2, 'DIP-14 顶视图', 6.5, anchor='middle', c=GRY)
    txt(d, x0 + w / 2, y0 + h / 2 - 15, '六路开漏缓冲 · 非反相', 6.5, anchor='middle', c=GRY)

    left = [('1', '1A', '← J1.3  (P2_6 / SCL_OUT)', W),
            ('2', '1Y', '→ SCL 总线', W),
            ('3', '2A', '← J1.4  (P2_7 / SDA_OUT)', W),
            ('4', '2Y', '→ SDA 总线', W),
            ('5', '3A', '← SDA 总线', W),
            ('6', '3Y', '→ J1.5  (P0_2 / SDA_IN)', W),
            ('7', 'GND', '→ GND', GRY)]
    right = [('14', 'VCC', '→ +5V', W),
             ('13', '6A', '→ GND（未用通道输入）', GRY),
             ('12', '6Y', '悬空', GRY),
             ('11', '5A', '→ GND（未用通道输入）', GRY),
             ('10', '5Y', '悬空', GRY),
             ('9', '4A', '→ GND（未用通道输入）', GRY),
             ('8', '4Y', '悬空', GRY)]
    step = 23
    for i, (n, nm, desc, c) in enumerate(left):
        y = y0 + h - 20 - i * step
        d.add(Line(x0 - 16, y, x0, y, strokeColor=c, strokeWidth=1.1))
        d.add(Rect(x0 - 16, y - 3.2, 16, 6.4, fillColor=colors.white, strokeColor=c, strokeWidth=0.7))
        txt(d, x0 + 4, y - 2.3, n, 6.2, c=GRY)
        txt(d, x0 - 20, y - 2.3, nm, 6.6, c=c, anchor='end', bold=True)
        txt(d, x0 - 46, y - 2.3, desc, 6.4, c=c, anchor='end')
    for i, (n, nm, desc, c) in enumerate(right):
        y = y0 + h - 20 - i * step
        d.add(Line(x0 + w, y, x0 + w + 16, y, strokeColor=c, strokeWidth=1.1))
        d.add(Rect(x0 + w, y - 3.2, 16, 6.4, fillColor=colors.white, strokeColor=c, strokeWidth=0.7))
        txt(d, x0 + w - 4, y - 2.3, n, 6.2, c=GRY, anchor='end')
        txt(d, x0 + w + 20, y - 2.3, nm, 6.6, c=c, bold=True)
        txt(d, x0 + w + 46, y - 2.3, desc, 6.4, c=c)
    return d


def fig_compare():
    """图 3：推挽直连（现状，对冲）与开漏缓冲（本方案）的对比"""
    d = Drawing(500, 190)
    for x0, title, tc in ((6, '现状：板卡推挽输出直连总线', RED),
                          (256, '本方案：经 74HCT07 转开漏', GRN)):
        d.add(Rect(x0, 6, 238, 176, fillColor=None, strokeColor=tc,
                   strokeWidth=0.8, strokeDashArray=[3, 2]))
        txt(d, x0 + 119, 168, title, 7.4, anchor='middle', c=tc, bold=True)

    # ---- 左：现状
    txt(d, 16, 140, 'PCIE-1751', 6.6, bold=True)
    d.add(Polygon([16, 108, 16, 130, 40, 119], fillColor=FILL, strokeColor=W, strokeWidth=1))
    txt(d, 18, 96, '推挽', 6.2, c=RED)
    d.add(Line(40, 119, 128, 119, strokeColor=W, strokeWidth=1.2))
    res_v(d, 96, 152, 119, 'R36', '2.2k', side=-1)
    d.add(Line(76, 152, 116, 152, strokeColor=W)); txt(d, 118, 149, '+5V', 6.2, c=W)
    dot(d, 96, 119)
    # DS2482 开漏 NMOS
    d.add(Line(128, 119, 128, 96, strokeColor=W))
    d.add(Line(122, 96, 134, 96, strokeColor=W, strokeWidth=1.4))
    d.add(Line(118, 90, 118, 102, strokeColor=W, strokeWidth=1.4))
    d.add(Line(128, 90, 128, 66, strokeColor=W))
    gnd_sym(d, 128, 62)
    txt(d, 138, 96, 'DS2482 开漏下拉', 6.3)
    d.add(Circle(68, 119, 9, fillColor=None, strokeColor=RED, strokeWidth=1))
    txt(d, 68, 137, '对冲', 6.6, anchor='middle', c=RED, bold=True)
    txt(d, 68, 40, '节点被拽到 1.9 V', 7.2, anchor='middle', c=RED, bold=True)
    txt(d, 124, 26, '低于 DS2482 的 V_IH(3.5 V)，也在板卡输入灰区',
        6.2, anchor='middle', c=RED)

    # ---- 右：本方案
    txt(d, 266, 140, 'PCIE-1751', 6.6, bold=True)
    d.add(Polygon([266, 108, 266, 130, 288, 119], fillColor=FILL, strokeColor=W, strokeWidth=1))
    txt(d, 268, 96, '推挽', 6.2, c=GRY)
    d.add(Line(288, 119, 300, 119, strokeColor=W))
    ox = buf(d, 300, 119)
    txt(d, 300, 96, '74HCT07 开漏', 6.2, c=GRN)
    d.add(Line(ox, 119, 400, 119, strokeColor=W, strokeWidth=1.2))
    res_v(d, 366, 152, 119, 'R2', '2.2k', side=-1)
    d.add(Line(346, 152, 386, 152, strokeColor=W)); txt(d, 388, 149, '+5V', 6.2, c=W)
    dot(d, 366, 119)
    d.add(Line(400, 119, 400, 96, strokeColor=W))
    d.add(Line(394, 96, 406, 96, strokeColor=W, strokeWidth=1.4))
    d.add(Line(390, 90, 390, 102, strokeColor=W, strokeWidth=1.4))
    d.add(Line(400, 90, 400, 66, strokeColor=W))
    gnd_sym(d, 400, 62)
    txt(d, 410, 96, 'DS2482', 6.3)
    txt(d, 340, 40, '高电平 5 V，无对冲', 7.2, anchor='middle', c=GRN, bold=True)
    txt(d, 375, 26, '板卡引脚全程固定方向，半字节冲突同时消失',
        6.2, anchor='middle', c=GRN)
    return d

pdfmetrics.registerFont(TTFont('CN', 'C:/Windows/Fonts/msyh.ttf'))
pdfmetrics.registerFont(TTFont('CNB', 'C:/Windows/Fonts/msyhbd.ttf'))

H1 = ParagraphStyle('H1', fontName='CNB', fontSize=15, leading=21, spaceAfter=8)
H2 = ParagraphStyle('H2', fontName='CNB', fontSize=11.5, leading=17, spaceBefore=11, spaceAfter=5)
BODY = ParagraphStyle('B', fontName='CN', fontSize=9, leading=14.5, spaceAfter=4)
CELL = ParagraphStyle('C', fontName='CN', fontSize=8, leading=11.5)
CELLB = ParagraphStyle('CB', fontName='CNB', fontSize=8, leading=11.5)
MONO = ParagraphStyle('M', fontName='Courier', fontSize=7.3, leading=9.4)
NOTE = ParagraphStyle('N', fontName='CN', fontSize=8, leading=13, textColor=colors.HexColor('#444444'))


def h1(t):
    return Paragraph(t, H1)


def h2(t):
    return Paragraph(t, H2)


def p(t):
    return Paragraph(t, BODY)


def note(t):
    return Paragraph(t, NOTE)


def pre(t):
    return Preformatted(t, MONO)


def table(header, rows, widths):
    data = [[Paragraph(c, CELLB) for c in header]]
    data += [[Paragraph(str(c), CELL) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef5')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#9aa5b1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f6f8fa')]),
    ]))
    return t


S = []
S.append(h1('PCIE-1751 GPIO 模拟 I²C 验证板 · 设计说明'))
S.append(note('版本 v1.3 &nbsp;|&nbsp; 连接方式：PCL-10168 线缆 + ADAM-3968 端子台 &nbsp;|&nbsp; 目标链路：PCIE-1751 DIO → 软件模拟 I²C → DS2482-100 → 1-Wire → DS2431'))

S.append(h2('1. 设计目的'))
S.append(p('用最小电路验证一条完整链路：PCIE-1751 的三个普通 DIO 引脚（P2_6 / P2_7 / P0_2）经软件位操作模拟 I²C 主机，'
           '驱动 DS2482-100 桥接器，再经 1-Wire 总线读出 DS2431 的 64 位 ROM 与存储器内容。'
           '板卡侧沿用 H-9220 背板已在用的三个引脚，验证结论可直接迁移回背板。'))

S.append(h2('2. 设计依据与要解决的问题'))
S.append(p('<b>现有背板（H-9220 REV07）的故障</b>：SDA 总线高电平实测仅 1.9 V，通信偶尔成功但不可靠。'
           '根因是 SCL(P2_6) 与 SDA_OUT(P2_7) 同处 Port 2 高半字节，而 PCIE-1751 的方向按半字节配置，'
           '导致 SDA 无法在保持 SCL 可控的前提下切换到高阻。软件只能让 P2_7 常驻输出态、'
           '用「输出 1」代替「释放」，于是每个 ACK 位和读数据位都发生推挽输出与 DS2482 开漏下拉的正面对冲，'
           '节点被拽到 1.9 V —— 低于 DS2482 的 V<sub>IH</sub>(3.5 V)，也落在板卡输入的灰区(0.8~2.0 V)。'))
S.append(p('<b>本验证板的对策</b>：用 74HCT07 六路集电极开漏缓冲，把板卡的推挽输出转换成真正的开漏驱动。'
           '板卡侧三个引脚从此<b>全程保持固定方向</b>，不再需要任何方向切换，半字节冲突和电平对冲同时消失。'))

S.append(Spacer(1, 4))
S.append(fig_compare())
S.append(note('<b>图 1</b> &nbsp;推挽直连（现状）与开漏缓冲（本方案）的对比。'
              '推挽输出与从机的开漏下拉是两个都在主动驱动的源，只能靠分压定节点电压；'
              '换成开漏后总线上只剩「拉低」和「释放」两种动作，高电平由上拉电阻唯一决定。'))

S.append(PageBreak())
S.append(h2('3. 系统原理图'))
S.append(Spacer(1, 4))
S.append(fig_schematic())
S.append(note('<b>图 2</b> &nbsp;验证板原理图。三角形符号为 74HCT07 的开漏缓冲通道，'
              '输出端菱形表示集电极开漏。<b>导线交叉处未画实心圆点即表示不相连</b>（如 R2 与 SCL 的交叉）。'
              '去耦电容未在图中画出：C1(10 µF) + C2(0.1 µF) 置于 +5 V 入口，'
              'C3、C4(0.1 µF) 分别紧贴 U1、U2 的电源脚；电源指示 D1 + R7(1 kΩ) 接在 +5 V 与 GND 之间。'))
S.append(Spacer(1, 3))
S.append(note('74x07 为<b>非反相</b>开漏缓冲——输入 0 → 输出拉低；输入 1 → 输出高阻，由上拉电阻拉高。'
              '软件语义与直觉一致：写 0 = 占用总线，写 1 = 释放总线，无需取反。'))

S.append(h2('4. 元件清单（BOM）'))
S.append(table(
    ['位号', '型号 / 值', '封装', '说明'],
    [['U1', '74HCT07', 'DIP-14 或 SOIC-14', '六路集电极开漏缓冲，非反相。<b>必须 HCT，不可用 HC</b>'],
     ['U2', 'DS2482S-100+', 'SO-8 (150mil)', 'I²C 转 1-Wire 桥接器，2.9~5.5 V'],
     ['U3', 'DS2431+', 'TO-92（建议加插座）', '1024 位 1-Wire EEPROM，2.8~5.25 V'],
     ['R1, R2', '2.2 kΩ', '0805', 'SCL / SDA 上拉至 +5 V（与背板取值一致）'],
     ['R3, R4', '10 kΩ', '0805', 'U1 输入端上拉，防排线未插时输入悬空'],
     ['R5', '4.7 kΩ', '0805', 'U1 的 3Y 开漏输出上拉（回读通路必需）'],
     ['R6', '1 kΩ', '0805', '1-Wire 上拉，<b>留焊盘不焊（NF）</b>，见 6.5'],
     ['R7', '1 kΩ', '0805', '电源指示灯限流'],
     ['C1', '10 µF / 16 V', '0805 或钽电容', '+5 V 入口储能'],
     ['C2, C3, C4', '0.1 µF', '0805', '分别置于 +5 V 入口、U1、U2 的电源脚旁'],
     ['D1', 'LED（任意色）', '0805', '电源指示'],
     ['J1', '5 位接线端子 / 排针', '2.54 mm', '接 PCIE-1751'],
     ['J2', '4 位排针', '2.54 mm', '逻辑分析仪测试点'],
     ],
    [22 * mm, 32 * mm, 32 * mm, 78 * mm]))

S.append(h2('5. 连接表'))
S.append(p('<b>5.1 &nbsp;J1 — 与 PCIE-1751 的连接</b>'))
S.append(table(
    ['J1 脚', '信号', '端子板端子号<br/>(= SCSI-68 引脚)', 'PCIE-1751 端口位', '方向（板卡视角）'],
    [['1', '+5V', 'pin 34（或 68）', '—', '供电，两脚合计 0.5 A'],
     ['2', 'GND', 'pin 27（或 9/18/43/52/61）', '—', '共地'],
     ['3', 'SCL_OUT', 'pin 25', 'P2_6', '固定输出'],
     ['4', 'SDA_OUT', 'pin 26', 'P2_7', '固定输出'],
     ['5', 'SDA_IN', 'pin 3', 'P0_2', '固定输入'],
     ],
    [16 * mm, 24 * mm, 46 * mm, 34 * mm, 44 * mm]))
S.append(note('三个信号引脚与 H-9220 背板现有接线完全一致，验证结论可直接迁移。'
              'ADAM-3968 端子台的端子编号与 SCSI-68 引脚号一一对应，接线前请核对端子台丝印上的数字。'))

S.append(Spacer(1, 5))
S.append(p('<b>5.2 &nbsp;U1 74HCT07 — 六路开漏缓冲</b>'))
S.append(table(
    ['引脚', '名称', '连接', '说明'],
    [['1', '1A', 'J1.3 (P2_6)，并经 R3 10k 上拉至 +5V', 'SCL 驱动通道输入'],
     ['2', '1Y', 'SCL 总线，并经 R1 2.2k 上拉至 +5V', '开漏输出'],
     ['3', '2A', 'J1.4 (P2_7)，并经 R4 10k 上拉至 +5V', 'SDA 驱动通道输入'],
     ['4', '2Y', 'SDA 总线，并经 R2 2.2k 上拉至 +5V', '开漏输出'],
     ['5', '3A', 'SDA 总线', 'SDA 回读通道输入'],
     ['6', '3Y', 'J1.5 (P0_2)，并经 R5 4.7k 上拉至 +5V', '开漏输出，送回板卡'],
     ['9, 11, 13', '4A, 5A, 6A', 'GND', '未用通道，CMOS 输入不可悬空'],
     ['8, 10, 12', '4Y, 5Y, 6Y', '悬空', '未用通道输出'],
     ['7', 'GND', 'GND', '—'],
     ['14', 'VCC', '+5V，旁路 C3 0.1 µF', '—'],
     ],
    [20 * mm, 26 * mm, 68 * mm, 50 * mm]))

S.append(Spacer(1, 4))
S.append(fig_pinout())
S.append(note('<b>图 3</b> &nbsp;74HCT07 引脚使用一览（DIP-14 顶视图，缺口朝上）。'
              '蓝色为使用中的引脚，灰色为未用通道——其输入端必须接 GND，'
              'CMOS 输入悬空会导致输入级贯通电流与状态不定；未用通道的输出端保持悬空即可。'))

S.append(Spacer(1, 5))
S.append(p('<b>5.3 &nbsp;U2 DS2482-100（SO-8）与 U3 DS2431（TO-92）</b>'))
S.append(table(
    ['器件', '引脚', '名称', '连接'],
    [['U2', '1', 'VCC', '+5V，旁路 C4 0.1 µF'],
     ['U2', '2', 'IO', '1-Wire 网络 → U3.2；R6（1k 上拉）留焊盘不焊'],
     ['U2', '3', 'GND', 'GND'],
     ['U2', '4', 'SCL', 'SCL 总线'],
     ['U2', '5', 'SDA', 'SDA 总线'],
     ['U2', '6', 'PCTLZ', '悬空（不使用外部 MOSFET 强上拉）'],
     ['U2', '7', 'AD1', 'GND'],
     ['U2', '8', 'AD0', 'GND &nbsp;→ 7 位从机地址 <b>0x18</b>（写 0x30 / 读 0x31）'],
     ['U3', '1', 'GND', 'GND'],
     ['U3', '2', 'IO', '1-Wire 网络 → U2.2'],
     ['U3', '3', 'N.C.', '悬空'],
     ],
    [16 * mm, 16 * mm, 24 * mm, 108 * mm]))
S.append(note('引脚定义已核对 Maxim 数据手册：DS2482-100 SO-8 为 1=VCC、2=IO、3=GND、4=SCL、5=SDA、6=PCTLZ、7=AD1、8=AD0；'
              'DS2431 TO-92 为 1=GND、2=IO、3=N.C.。'))

S.append(h2('6. 关键设计说明'))
S.append(p('<b>6.1 &nbsp;为什么必须用 74HCT07 而不是 74HC07</b><br/>'
           'PCIE-1751 是 TTL 输出，V<sub>OH</sub> 最低仅 2.4 V。74HC 系列在 5 V 供电下要求 V<sub>IH</sub> 不低于 3.5 V，'
           '接不了；74HCT 系列是 TTL 兼容门限，V<sub>IH</sub> = 2.0 V，可以可靠识别。'))
S.append(p('<b>6.2 &nbsp;为什么用 07 而不是 05</b><br/>'
           '74x05 是反相开漏，74x07 是非反相开漏。选 07 可使软件逻辑与总线电平同相，避免取反带来的心智负担和出错。'))
S.append(p('<b>6.3 &nbsp;R3 / R4 为什么上拉到 +5 V 而不是下拉</b><br/>'
           'CMOS 输入不可悬空。上拉至 +5 V 时，排线未插或板卡未上电的情况下 U1 输出为高阻，'
           'I²C 总线被 R1/R2 拉高，正好是总线空闲态，对 DS2482 安全；若改为下拉，未插线时总线会被死死拉低。'))
S.append(p('<b>6.4 &nbsp;R5 为什么不能省</b><br/>'
           '3Y 是开漏输出，必须有上拉才能输出高电平。虽然 PCIE-1751 每个 DIO 脚内部已有 10 kΩ 上拉至 +5 V，'
           '但不应依赖该特性：本板自带 4.7 kΩ 后上升沿更快、电平更确定。二者并联约 3.2 kΩ，'
           '74HCT07 拉低时灌 1.4 mA，远低于其 4 mA 能力。'))
S.append(p('<b>6.5 &nbsp;1-Wire 线为什么不加上拉电阻</b><br/>'
           'DS2482-100 的 IO 引脚内置可编程的无源/有源上拉，其数据手册（Rev 7, 8/08）已明确'
           '「删除了典型工作电路中的 1-Wire 端接电阻」。因此 R6 默认不焊，仅保留焊盘；'
           '若实测 1-Wire 上升沿过缓或存在长线，再补焊 1 kΩ。'))
S.append(p('<b>6.6 &nbsp;74HCT07 是单向器件，为什么能驱动双向的 SDA</b><br/>'
           '74HCT07 的每一路都是单向的：输入 A、开漏输出 Y，信号只能 A → Y。本设计并不需要双向器件，'
           '因为 SDA 的双向性是用<b>两路独立的单向通道</b>拼出来的——CH2(2A→2Y) 负责「板卡驱动总线」，'
           'CH3(3A→3Y) 负责「总线送回板卡」。二者挂在同一 SDA 节点上互不干扰：'
           'CH2 是开漏输出，释放时呈高阻；CH3 是 CMOS 输入，只监听不驱动。'))
S.append(p('更本质地说，I²C 的双向性本来就由「开漏 + 上拉」的线与机制提供，而不是由缓冲器提供：'
           'SDA 上真正能主动动作的只有 CH2 的下拉管与 DS2482 的下拉管，任何一方拉低，各方都读到低电平。'
           '这个拓扑之所以成立，正是因为背板已把 SDA 拆成 SDA_OUT 与 SDA_IN 两个板卡引脚，'
           '两个方向在板卡侧本就是分开的。'))
S.append(p('只有当板卡仅用<b>一个</b> DIO 引脚收发 SDA 时，才需要 PCA9306 一类的双向器件，'
           '或带方向控制脚的 74LVC1T45（还须再占用一个 DIO 控制方向）。'
           '在 I²C 上使用自动方向检测型的双向缓冲反而有锁死或振荡的风险，因此当前的分脚拓扑配单向缓冲更简单可靠。'))
S.append(p('<b>6.7 &nbsp;电平与供电</b><br/>'
           'PCIE-1751（5 V TTL）、74HCT07（5 V）、DS2482-100（2.9~5.5 V）、DS2431（2.8~5.25 V）'
           '全部工作在 5 V，无需任何电平转换。'))

S.append(h2('7. 电流预算'))
S.append(table(
    ['项目', '电流', '说明'],
    [['74HCT07 静态', '&lt; 10 µA', 'CMOS'],
     ['DS2482-100 工作', '~1 mA 量级', '含 1-Wire 操作'],
     ['电源指示 LED', '~3 mA', 'R7 = 1 kΩ'],
     ['SCL 拉低时', '2.1 mA', '(5 - 0.4) / 2.2 kΩ'],
     ['SDA 拉低时', '2.1 mA', '(5 - 0.4) / 2.2 kΩ'],
     ['SDA_IN 回读拉低时', '1.4 mA', 'R5 4.7 kΩ 与板卡内部 10 kΩ 并联'],
     ['<b>峰值合计</b>', '<b>&lt; 10 mA</b>', '板卡 +5 V 可供 0.5 A，余量充足'],
     ],
    [46 * mm, 30 * mm, 88 * mm]))
S.append(note('对照：74HCT07 每路开漏输出的灌电流能力约 4 mA，上表中各路均在能力之内；'
              'DS2482 拉低 SDA 时只需灌 2.1 mA，相比背板现状（等效上拉 1.53 kΩ、需灌 3.0 mA）恢复了余量。'))

S.append(h2('8. 分层验证步骤'))
S.append(p('每一步都应在上一步通过后再进行，便于把故障锁定在最小范围。'))
S.append(table(
    ['步骤', '操作', '预期结果'],
    [['1) 上电', '仅接 +5V / GND，不运行软件', 'LED 亮；SCL、SDA 静态电压均 约  5 V。<b>此步即可证明 1.9 V 问题已消除</b>'],
     ['2) 输出通路', '软件将 P2_6 / P2_7 分别写 0 与 1', 'SCL、SDA 在 约 0.2 V 与 约 5 V 之间干净切换'],
     ['3) 回读通路', '手动把 SDA 短接到 GND，再松开', 'P0_2 读回相应为 0 / 1'],
     ['4) I²C 应答', '发送 START + 0x30（写地址）', 'ACK 位期间 SDA 被 DS2482 拉低，P0_2 读回 0'],
     ['5) 桥接器', '发 Device Reset (0xF0)，读状态寄存器', '状态寄存器 RST 位置 1'],
     ['6) 1-Wire 存在', '发 1-Wire Reset (0xB4)，读状态寄存器', 'PPD（存在脉冲检测）位置 1'],
     ['7) 读 ROM', '1-Wire Read ROM (0x33)，读 8 字节', '首字节为家族码 <b>0x2D</b>，末字节 CRC8 校验通过'],
     ['8) 读存储器', '1-Wire Read Memory (0xF0)，从地址 0x0000 起', '读出 128 字节数据，与写入内容一致'],
     ],
    [22 * mm, 62 * mm, 80 * mm]))

S.append(h2('9. 注意事项'))
S.append(p('<b>9.1 &nbsp;与 PCIE-1751 的连接方式（已确定：端子板）</b><br/>'
           '采用研华 PCL-10168 型 68 芯 SCSI 线缆，一端插板卡的 SCSI-68 母座，另一端插 ADAM-3968 端子台；'
           '再从端子台用 5 根导线接到本板 J1。端子台编号与 SCSI-68 引脚号一致，因此接线即为：'
           '端子 34 → J1.1(+5V)、端子 27 → J1.2(GND)、端子 25 → J1.3(SCL_OUT)、'
           '端子 26 → J1.4(SDA_OUT)、端子 3 → J1.5(SDA_IN)。'))
S.append(p('<b>9.2</b> &nbsp;端子台到验证板的导线建议 24~26 AWG 多股软线，长度尽量短（30 cm 以内），'
           '并让 SCL、SDA 两根信号线各自贴近一根 GND 走线。通信速率在 kHz 量级，对线缆本身无特殊要求，'
           '但不要与继电器、电机等强干扰线束捆在一起。'))
S.append(p('<b>9.3</b> &nbsp;U1 建议采用 DIP-14 加插座，便于在验证阶段更换或改接。'))
S.append(p('<b>9.4</b> &nbsp;U3 建议加 TO-92 插座，便于更换不同 DS2431 样品、核对各自唯一的 ROM ID。'))
S.append(p('<b>9.5</b> &nbsp;J2 测试点（SCL / SDA / 1-Wire IO / GND）务必保留，'
           '这是验证板最主要的价值——所有时序问题都要靠抓波形定位。'))
S.append(p('<b>9.6</b> &nbsp;板卡跳线 JP1 决定热复位后端口是否保持上次状态。上电默认态下 PCIE-1751 端口为输入，'
           'U1 的输入端由 R3/R4 拉高、输出保持高阻，I²C 总线处于空闲态，对 DS2482 安全。'))
S.append(p('<b>9.7</b> &nbsp;验证通过后，可将同样的 74HCT07 缓冲电路移植回 H-9220 背板 U31 与 J2 之间；'
           '背板侧 R35 / R36（2.2 kΩ）可继续沿用，无需改动 SCSI-68 的三个引脚分配。'))

out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'hardware')
os.makedirs(out_dir, exist_ok=True)
out = os.path.abspath(os.path.join(out_dir, 'PCIE-1751_I2C验证板设计说明.pdf'))
SimpleDocTemplate(out, pagesize=A4, leftMargin=17 * mm, rightMargin=15 * mm,
                  topMargin=15 * mm, bottomMargin=15 * mm,
                  title='PCIE-1751 GPIO 模拟 I2C 验证板设计说明').build(S)
print(out)
