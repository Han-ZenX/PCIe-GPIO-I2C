#!/usr/bin/env python3
"""生成《74HCT07 干扰机理分析》PDF 到 docs/hardware/。"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)
from reportlab.graphics.shapes import Drawing, Line, Rect, String, Circle, Polygon, PolyLine

pdfmetrics.registerFont(TTFont('CN', 'C:/Windows/Fonts/msyh.ttf'))
pdfmetrics.registerFont(TTFont('CNB', 'C:/Windows/Fonts/msyhbd.ttf'))

H1 = ParagraphStyle('H1', fontName='CNB', fontSize=15, leading=21, spaceAfter=8)
H2 = ParagraphStyle('H2', fontName='CNB', fontSize=11.5, leading=17, spaceBefore=11, spaceAfter=5)
BODY = ParagraphStyle('B', fontName='CN', fontSize=9, leading=14.5, spaceAfter=4)
CELL = ParagraphStyle('C', fontName='CN', fontSize=7.8, leading=11.2)
CELLB = ParagraphStyle('CB', fontName='CNB', fontSize=7.8, leading=11.2)
NOTE = ParagraphStyle('N', fontName='CN', fontSize=8, leading=13, textColor=colors.HexColor('#444444'))

INK = colors.HexColor('#1a2430')
W = colors.HexColor('#20406a')
RED = colors.HexColor('#c0392b')
GRN = colors.HexColor('#1e8449')
GRY = colors.HexColor('#8895a4')
FILL = colors.HexColor('#eef3f9')


def h1(t):
    return Paragraph(t, H1)


def h2(t):
    return Paragraph(t, H2)


def p(t):
    return Paragraph(t, BODY)


def note(t):
    return Paragraph(t, NOTE)


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


# ------------------------------------------------------------------ 绘图工具
def txt(d, x, y, s, size=6.8, c=INK, anchor='start', bold=False):
    d.add(String(x, y, s, fontName='CNB' if bold else 'CN',
                 fontSize=size, fillColor=c, textAnchor=anchor))


def wire(d, pts, c=W, w=1.0, dash=None):
    pl = PolyLine(pts, strokeColor=c, strokeWidth=w)
    if dash:
        pl.strokeDashArray = dash
    d.add(pl)


def dot(d, x, y, c=W):
    d.add(Circle(x, y, 2.2, fillColor=c, strokeColor=c))


def nmos(d, x, y, c=W, label=''):
    """简化 NMOS：栅极竖线 + 沟道 + 漏源引线。(x,y) 为器件中心"""
    d.add(Line(x - 10, y, x - 5, y, strokeColor=c, strokeWidth=1))       # 栅引线
    d.add(Line(x - 5, y - 7, x - 5, y + 7, strokeColor=c, strokeWidth=1.3))
    d.add(Line(x - 1, y - 7, x - 1, y + 7, strokeColor=c, strokeWidth=1.3))
    d.add(Line(x - 1, y + 5, x + 8, y + 5, strokeColor=c, strokeWidth=1))  # 漏
    d.add(Line(x + 8, y + 5, x + 8, y + 14, strokeColor=c, strokeWidth=1))
    d.add(Line(x - 1, y - 5, x + 8, y - 5, strokeColor=c, strokeWidth=1))  # 源
    d.add(Line(x + 8, y - 5, x + 8, y - 14, strokeColor=c, strokeWidth=1))
    if label:
        txt(d, x - 12, y - 3, label, 6.2, anchor='end', c=c)


def res_v(d, x, ytop, ybot, label, c=W):
    ym = (ytop + ybot) / 2.0
    d.add(Line(x, ytop, x, ym + 8, strokeColor=c))
    d.add(Rect(x - 3.2, ym - 8, 6.4, 16, fillColor=colors.white, strokeColor=c, strokeWidth=0.9))
    d.add(Line(x, ym - 8, x, ybot, strokeColor=c))
    txt(d, x + 6, ym - 2, label, 6.2, c=c)


def gnd(d, x, y, c=W):
    d.add(Line(x - 6, y, x + 6, y, strokeColor=c, strokeWidth=1.1))
    d.add(Line(x - 3.5, y - 2.5, x + 3.5, y - 2.5, strokeColor=c, strokeWidth=1.1))
    d.add(Line(x - 1.3, y - 5, x + 1.3, y - 5, strokeColor=c, strokeWidth=1.1))


def fig_output_stage():
    """图 1：正常开漏输出 与 损坏成驱动高 的对比"""
    d = Drawing(500, 235)
    for x0, title, tc in ((4, '正常：集电极开漏', GRN), (256, '损坏：输出主动驱动高', RED)):
        d.add(Rect(x0, 6, 240, 222, fillColor=None, strokeColor=tc,
                   strokeWidth=0.8, strokeDashArray=[3, 2]))
        txt(d, x0 + 120, 214, title, 7.6, anchor='middle', c=tc, bold=True)

    for base, broken in ((4, False), (256, True)):
        vcc_y, gnd_y = 196, 30
        xout = base + 150
        # VCC 与 GND 轨
        d.add(Line(base + 30, vcc_y, base + 210, vcc_y, strokeColor=W, strokeWidth=1.2))
        txt(d, base + 30, vcc_y + 5, 'VCC', 6.5, c=W, bold=True)
        d.add(Line(base + 30, gnd_y, base + 210, gnd_y, strokeColor=W, strokeWidth=1.2))
        txt(d, base + 30, gnd_y - 9, 'GND', 6.5, c=W, bold=True)

        # 外部上拉
        res_v(d, base + 60, vcc_y, 120, 'R 上拉')
        wire(d, [base + 60, 120, xout, 120])
        dot(d, base + 60, vcc_y)

        # 下拉 NMOS
        nmos(d, base + 150, 78, label='输入')
        d.add(Line(base + 158, 92, base + 158, 120, strokeColor=W))
        d.add(Line(base + 158, 64, base + 158, gnd_y, strokeColor=W))
        dot(d, base + 158, gnd_y)
        dot(d, base + 158, 120)

        # 输出引出
        d.add(Line(base + 158, 120, base + 205, 120, strokeColor=W, strokeWidth=1.2))
        txt(d, base + 207, 117, '输出', 6.5, c=W, bold=True)

        if broken:
            # 损坏：寄生上拉通路
            wire(d, [base + 158, 150, base + 120, 150, base + 120, vcc_y],
                 c=RED, w=1.3, dash=[3, 2])
            dot(d, base + 158, 150, c=RED)
            dot(d, base + 120, vcc_y, c=RED)
            txt(d, base + 139, 156, '寄生/损坏通路', 6.2, c=RED, anchor='middle')
            d.add(Line(base + 158, 120, base + 158, 150, strokeColor=RED, strokeWidth=1.3))
            txt(d, base + 30, 52, '输入 = 1 时输出仍被拉向 VCC', 6.5, c=RED)
            txt(d, base + 30, 42, '总线不再是"线与"，外部器件拉不低', 6.5, c=RED)
        else:
            txt(d, base + 30, 52, '输入 = 1 时 NMOS 关断，输出呈高阻', 6.5, c=GRN)
            txt(d, base + 30, 42, '电平完全由外部上拉与其它器件决定', 6.5, c=GRN)
    return d


def fig_ack_conflict():
    """图 2：ACK 时刻的对冲"""
    d = Drawing(500, 172)
    y = 92
    txt(d, 6, 156, 'ACK 时刻：主机释放 SDA，DS2482 拉低以示应答', 7.6, c=INK, bold=True)

    # 上拉
    d.add(Line(150, 130, 330, 130, strokeColor=W, strokeWidth=1.1))
    txt(d, 150, 134, 'VCC', 6.4, c=W, bold=True)
    res_v(d, 200, 130, y, 'R2 2.2k')
    dot(d, 200, y)

    # SDA 总线
    d.add(Line(90, y, 400, y, strokeColor=W, strokeWidth=1.4))
    txt(d, 128, y + 6, 'SDA', 7, c=W, bold=True)

    # 左：74HCT07 的 2Y（损坏，驱动高）
    d.add(Rect(30, y - 22, 58, 44, fillColor=FILL, strokeColor=RED, strokeWidth=1.1))
    txt(d, 59, y + 6, '74HCT07', 6.4, anchor='middle', c=RED, bold=True)
    txt(d, 59, y - 4, '2Y 损坏', 6.4, anchor='middle', c=RED)
    txt(d, 59, y - 14, '驱动高', 6.4, anchor='middle', c=RED)
    d.add(Line(88, y, 90, y, strokeColor=RED, strokeWidth=1.4))

    # 右：DS2482 的下拉
    nmos(d, 360, y - 30, c=GRN, label='')
    d.add(Line(368, y - 16, 368, y, strokeColor=GRN, strokeWidth=1.2))
    dot(d, 368, y, c=GRN)
    d.add(Line(368, y - 44, 368, 34, strokeColor=GRN))
    gnd(d, 368, 34, c=GRN)
    txt(d, 386, y - 34, 'DS2482 拉低(ACK)', 6.4, c=GRN)

    # 冲突标记
    d.add(Circle(258, y, 13, fillColor=None, strokeColor=RED, strokeWidth=1.3))
    txt(d, 258, y + 22, '对冲', 7, anchor='middle', c=RED, bold=True)
    txt(d, 258, 44, 'SDA 被撑在高电平，主机读到 1 = NACK', 7.2, anchor='middle', c=RED, bold=True)
    txt(d, 258, 32, '每一个 ACK 位、每一个读数据位都会这样失败', 6.4, anchor='middle', c=GRY)
    return d


def fig_bisect():
    """图 3：三次对照实验的证据链"""
    d = Drawing(500, 168)
    cases = [
        (8, '① 芯片脱离 PCB', 'DS2482 飞线 + JTool', '扫到 0x30', GRN),
        (172, '② 芯片焊回 PCB', 'JTool 直连 pin4/pin5', '无应答', RED),
        (336, '③ 拆掉 74HCT07', '同板同芯片 + JTool', '扫到 0x30', GRN),
    ]
    for x0, title, cond, result, c in cases:
        d.add(Rect(x0, 46, 156, 108, fillColor=None, strokeColor=c, strokeWidth=1))
        txt(d, x0 + 78, 138, title, 7.4, anchor='middle', c=INK, bold=True)
        txt(d, x0 + 78, 120, cond, 6.6, anchor='middle', c=GRY)
        d.add(Rect(x0 + 24, 74, 108, 26, fillColor=FILL, strokeColor=c, strokeWidth=0.9))
        txt(d, x0 + 78, 84, result, 8.4, anchor='middle', c=c, bold=True)
        txt(d, x0 + 78, 56, '芯片相同 / 板子相同' if x0 > 8 else '基准：芯片本身正常',
            6.2, anchor='middle', c=GRY)

    txt(d, 250, 26, '① 与 ② 对比：问题在 PCB 上，不在芯片',
        7, anchor='middle', c=INK)
    txt(d, 250, 12, '② 与 ③ 对比：PCB 上的干扰源就是 74HCT07',
        7.4, anchor='middle', c=RED, bold=True)
    return d


S = []
S.append(h1('74HCT07 干扰机理分析'))
S.append(note('对象：I2C_PCIE1751 EVAL Board (REV01) 的 U1 &nbsp;|&nbsp; '
              '故障：DS2482-100 对全部 112 个 I²C 地址无应答 &nbsp;|&nbsp; 日期：2026-09-20'))

S.append(h2('1. 结论摘要'))
S.append(p('<b>根因：U1 的料号不符。</b>板上标称 74HCT07（集电极开漏）的器件，'
           '实测输出为推挽结构。开漏总线因此失去"线与"特性，从机无法拉低 SDA，'
           '导致每一个 ACK 位都被判为 NACK。'))
S.append(table(
    ['结论', '依据'],
    [['拆除 U1 后，同一块板、同一颗 DS2482 立即应答 0x30',
      '实验证实'],
     ['<b>U1 的输出为推挽，而非开漏</b>',
      '<b>脱离 PCB 的面包板独立验证：输入置高、输出经 1 kΩ 接地，'
      '实测 4.960 V（真开漏应为约 0 V），反推输出阻抗约 44 Ω</b>'],
     ['推挽输出在 ACK 时刻与 DS2482 的下拉对冲，使从机无法拉低 SDA',
      '机理与全部现象一致，见第 3 节'],
     ['更换新片无效',
      '两片同批，行为一致 —— 并非器件损坏，而是整批料不对'],
     ],
    [64 * mm, 100 * mm]))
S.append(note('排查前期曾推断为"器件损坏"，后被新片替换实验推翻。'
              '最终定性为料号不符，验证数据见第 5 节。'))

S.append(h2('2. 定位过程：三次对照实验'))
S.append(Spacer(1, 3))
S.append(fig_bisect())
S.append(note('<b>图 1</b> &nbsp;三次实验只改变一个变量。实验 ① 证明 DS2482 本身完好；'
              '② 证明把它放回 PCB 就失效；③ 在不更换任何器件的前提下仅移除 U1，故障立即消失。'
              '三者构成完整的因果链，定位到 U1。'))

S.append(h2('3. 干扰机理'))
S.append(p('74x07 属于集电极开漏（open-drain）缓冲器，其输出级<b>只有一只下拉 NMOS，没有上拉管</b>。'
           '正常情况下输入为 1 时 NMOS 关断，输出呈高阻，总线电平完全交给外部上拉电阻和总线上的其它器件决定——'
           '这正是 I²C "线与" 机制的前提。'))
S.append(Spacer(1, 3))
S.append(fig_output_stage())
S.append(note('<b>图 2</b> &nbsp;左为正常的开漏输出级；右为损坏后出现寄生上拉通路的情形。'
              '一旦输出在"应当高阻"时仍被拉向 VCC，该引脚就从"开漏"退化成了"推挽"，'
              '总线失去线与特性。'))

S.append(PageBreak())
S.append(p('对 I²C 通信而言，这一退化只在<b>特定时刻</b>才暴露出来：'))
S.append(table(
    ['时刻', '正常的 74HCT07', '损坏后（输出驱动高）'],
    [['主机发送数据位 0（2Y 拉低）', '2Y 拉低，SDA = 0', '2Y 拉低，SDA = 0 &nbsp;<b>（无差别）</b>'],
     ['主机发送数据位 1（2Y 释放）', '高阻，上拉使 SDA = 1', '驱动高，SDA = 1 &nbsp;<b>（无差别）</b>'],
     ['<b>ACK 时刻：主机释放，从机拉低</b>',
      '<b>高阻，DS2482 顺利把 SDA 拉低，主机读到 0 = ACK</b>',
      '<b>驱动高与 DS2482 的下拉对冲，SDA 被撑住，主机读到 1 = NACK</b>'],
     ['读数据位（从机驱动 SDA）', '从机可自由控制 SDA', '从机无法拉低，读出恒为 0xFF'],
     ],
    [40 * mm, 60 * mm, 64 * mm]))
S.append(Spacer(1, 4))
S.append(fig_ack_conflict())
S.append(note('<b>图 3</b> &nbsp;ACK 时刻的对冲。前两行动作因为方向一致而看不出任何异常，'
              '只有当"总线需要由别人拉低"时故障才显现——而这恰恰是 I²C 协议中每个字节都要发生一次的动作。'))

S.append(h2('4. 为何此前所有测试都未能发现'))
S.append(p('这是本次排查耗时最长的原因：<b>"输出驱动高"与"输出高阻"在静态测量下完全一致</b>。'))
S.append(table(
    ['已做过的测试', '当时的结论', '为何漏掉了这个故障'],
    [['SDA 回环自检（释放=1 / 拉低=0 / 再释放=1）', '通过',
      '拉低是 2Y 自己完成的，不存在冲突；释放读到 1——<b>驱动高读到的同样是 1</b>'],
     ['万用表测 SCL / SDA 空闲电平 = 5 V', '正常',
      '上拉到 VCC 是 5 V，<b>被驱动到 VCC 也是 5 V</b>，两者无法区分'],
     ['SCL / SDA 方波，在 U2 引脚实测跳变', '通路正常',
      '主机自己驱动的波形，不涉及"被外部器件拉低"'],
     ['SCL 高速翻转 74553 Hz，读到半电源电压', '通信速度下正常',
      '同上，仍是主机单向驱动'],
     ['U2 pin4 与 pin5 = 4.38 kΩ、pin5 与 SDA_OUT = 12.21 kΩ', '焊接与网络均正常',
      '断电测量，无法反映有源器件的行为'],
     ['逐位写 / 回读全部一致', 'SDA 电平正确',
      '读回的是主机自己驱动的值'],
     ],
    [52 * mm, 26 * mm, 86 * mm]))
S.append(note('共同点：<b>所有测试中都没有"由第三方器件拉低总线、再观察主机能否感知"这一步</b>，'
              '而这正是 ACK 的本质。排查后期加入的「SDA 外部拉低测试」正是为封堵此盲点而设计。'))

S.append(PageBreak())
S.append(h2('5. 验证过程与结果'))
S.append(table(
    ['验证项', '条件', '结果'],
    [['新片替换',
      '焊接新的 74HCT07，J1 先供 5 V 再插 PCIE-1751（规避上电顺序风险）',
      '<b>仍不通</b>。推翻"器件损坏"假设，指向整批料的问题'],
     ['<b>在板电阻分压</b>',
      '拔掉 SCSI 线（1A/2A 由 R3/R4 上拉至 5.18 V），1 kΩ 自 SCL 接地',
      '<b>实测 4.95 V</b>（若输出高阻，仅 R1 分压应为 1.62 V）'],
     ['<b>脱离 PCB 独立验证</b>',
      'VCC = 5 V、GND 接地、其余输入接地、1A 接 5 V、1Y 经 1 kΩ 接地',
      '<b>实测 4.960 V</b>，输出阻抗约 44 Ω，确认为推挽输出'],
     ],
    [30 * mm, 74 * mm, 60 * mm]))
S.append(note('<b>验证方法的关键在于输出端不接上拉。</b>只有在没有上拉的条件下，'
              '"高阻"与"驱动高"才会表现出约 0 V 与约 5 V 的巨大差别。'
              '这正是本次排查长期未能区分二者的原因 —— 板上始终有 R1/R2 上拉存在，'
              '两种状态下测得的电压完全相同。'))
S.append(p('<b>关于 GND 的提醒</b>：独立验证时若遗漏芯片的 GND 引脚，'
           '电流会经"VCC → 芯片内部 → 输出 → 负载电阻 → 地"形成寄生回路，'
           '读到约 3.3 V 的中间值，该读数无任何意义。本次验证中曾出现此情况，'
           '补接 GND 后方得到有效数据。'))

S.append(h2('6. 附带发现的设计隐患：双电源域上电顺序'))
S.append(p('本次故障的根因是料号不符，与下述问题无关。但排查过程中发现 REV01 存在一处'
           '独立的设计隐患，应在 REV02 中一并解决。'))
S.append(p('REV01 中 U1 由 <b>J1 独立 5 V 供电</b>，而它的输入（1A / 2A）来自 <b>PCIE-1751</b>，'
           '二者属于两个互相独立的电源域。当出现下述上电顺序时会形成风险：'))
S.append(table(
    ['步骤', '状态', '后果'],
    [['先开启工控机', 'PCIE-1751 上电，P2_6 / P2_7 输出 0 或 5 V', '—'],
     ['此时 J1 尚未供电', 'U1 的 VCC = 0 V，而输入脚上存在 5 V',
      '输入端 ESD 保护二极管正偏导通'],
     ['电流路径', '输入脚 → 保护二极管 → VCC 网络 → 负载',
      '<b>轻则器件异常，重则闩锁或永久损伤</b>'],
     ],
    [30 * mm, 66 * mm, 68 * mm]))
S.append(note('这属于典型的 partial power-down 问题。由于每次"先开机、后给验证板供电"都会重演一次，'
              '损伤具有累积性且不易察觉。本次虽未造成实际故障，仍建议在 REV02 中消除。'))

S.append(h2('7. REV02 改进建议'))
S.append(table(
    ['措施', '说明', '推荐度'],
    [['<b>U1 输入端串 100 Ω ~ 1 kΩ 限流电阻</b>',
      '将 VCC 缺失时经保护二极管灌入的电流限制在安全范围。改动最小，'
      '对 kHz 级的 I²C 时序无任何影响',
      '★★★'],
     ['<b>改用具备 I_off 特性的器件</b>',
      '如 74LVC1G07 等，掉电时输入呈高阻，专为混合电源域设计。需核对电平与封装',
      '★★☆'],
     ['<b>取消独立供电，统一由板卡取电</b>',
      '从根本上消除双电源域。需核算 PCIE-1751 的 +5 V 余量'
      '（pin 34/68 合计 0.5 A，本板峰值约 10 mA，余量充足）',
      '★★☆'],
     ['为 SCL 增加回读通道',
      '现设计中 SCL 无回读，软件无法自检，只能依赖万用表。'
      '若 74HCT07 尚有空闲通道，可再用一路把 SCL 引回板卡的一个输入脚',
      '★☆☆'],
     ],
    [44 * mm, 100 * mm, 20 * mm]))

S.append(h2('8. 来料检验方法（针对本次根因）'))
S.append(p('开漏 / 集电极开路器件的输出类型无法从外观、丝印或万用表的常规测量中识别，'
           '必须用下述方法逐批抽检。成本几乎为零，但正是本次踩坑的直接对策。'))
S.append(table(
    ['步骤', '接法'],
    [['1. 供电', 'VCC 接 5 V，<b>GND 必须接地</b>（遗漏会读到无意义的中间值）'],
     ['2. 未用引脚', '所有未用<b>输入</b>脚接 GND，避免 CMOS 输入悬空'],
     ['3. 被测通道', '输入脚接 <b>5 V</b>（即"释放"状态）'],
     ['4. 负载', '输出脚经 <b>1 kΩ 接 GND</b>，<b>不得加任何上拉</b>'],
     ['5. 判读', '<b>输出约 0 V = 真开漏，合格；输出约 5 V = 推挽，退货</b>'],
     ],
    [30 * mm, 134 * mm]))
S.append(note('采购时应确认数据手册明确标注 open-drain / open-collector output，'
             '并优先选择 TI、NXP、Toshiba、Diodes 等厂商的正规代理渠道。'
             '本次问题批次标记为 ST「74HCT07 / 0AA709」，同批剩料应全部隔离，'
             '不得用于其它产品。'))

S.append(h2('9. 经验沉淀'))
S.append(p('<b>对开漏总线而言，"能拉低"与"能释放"必须分别验证。</b>'
           '本次所有测试都只覆盖了前者，导致一个输出级损坏的缓冲器在长达数十项测量中始终"表现正常"。'))
S.append(p('可迁移的检验方法：<b>在被测器件输出端不接上拉的条件下，输入置为"释放"，'
           '用一只下拉电阻观察输出电压。</b>该方法可用于所有开漏 / 集电极开路器件的来料与故障检验，'
           '成本极低但判别力极强。'))

out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'hardware')
os.makedirs(out_dir, exist_ok=True)
out = os.path.abspath(os.path.join(out_dir, '74HCT07干扰机理分析.pdf'))
SimpleDocTemplate(out, pagesize=A4, leftMargin=16 * mm, rightMargin=14 * mm,
                  topMargin=15 * mm, bottomMargin=15 * mm,
                  title='74HCT07 干扰机理分析').build(S)
print(out)
