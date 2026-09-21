#!/usr/bin/env python3
"""生成《PCIE-1751 I2C 验证板故障排查记录》PDF 到 docs/hardware/。"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)

pdfmetrics.registerFont(TTFont('CN', 'C:/Windows/Fonts/msyh.ttf'))
pdfmetrics.registerFont(TTFont('CNB', 'C:/Windows/Fonts/msyhbd.ttf'))

H1 = ParagraphStyle('H1', fontName='CNB', fontSize=15, leading=21, spaceAfter=8)
H2 = ParagraphStyle('H2', fontName='CNB', fontSize=11.5, leading=17, spaceBefore=11, spaceAfter=5)
BODY = ParagraphStyle('B', fontName='CN', fontSize=9, leading=14.5, spaceAfter=4)
CELL = ParagraphStyle('C', fontName='CN', fontSize=7.6, leading=11)
CELLB = ParagraphStyle('CB', fontName='CNB', fontSize=7.6, leading=11)
NOTE = ParagraphStyle('N', fontName='CN', fontSize=8, leading=13, textColor=colors.HexColor('#444444'))

OK = colors.HexColor('#1e8449')
NG = colors.HexColor('#c0392b')


def h1(t):
    return Paragraph(t, H1)


def h2(t):
    return Paragraph(t, H2)


def p(t):
    return Paragraph(t, BODY)


def note(t):
    return Paragraph(t, NOTE)


def table(header, rows, widths, align=None):
    data = [[Paragraph(c, CELLB) for c in header]]
    data += [[Paragraph(str(c), CELL) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef5')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#9aa5b1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f6f8fa')]),
    ]
    if align:
        style += align
    t.setStyle(TableStyle(style))
    return t


S = []
S.append(h1('PCIE-1751 I²C 验证板 · 故障排查记录'))
S.append(note('对象：I2C_PCIE1751 EVAL Board (REV01) &nbsp;|&nbsp; '
              '链路：PCIE-1751 DIO → 74HCT07 → I²C → DS2482-100 → 1-Wire → DS2431 &nbsp;|&nbsp; '
              '排查日期：2026-09-20'))

S.append(h2('1. 故障现象'))
S.append(p('板卡可正常打开、端口方向配置正确，但 <b>DS2482-100 对任何 I²C 地址均无应答</b>。'
           '对 0x08 ~ 0x77 全部 112 个 7 位地址做扫描，无一应答。现象稳定复现十余次，'
           '不随时间、速率或重新上电改变。'))
S.append(p('对照：1-Wire 侧用 USB-1Wire 适配器可正常读出 DS2431 的 ROM ID，说明 1-Wire 器件、'
           'ID 网络走线、R7 上拉与板级接地均正常。'))
S.append(note('<b>本文档记录完整排查过程。最终定性见第 8 节：U1(74HCT07) 料号不符，'
              '标称开漏的器件实为推挽输出。</b>'))

S.append(h2('2. 系统配置'))
S.append(table(
    ['信号', 'PCIE-1751', 'SCSI-68 引脚', '74HCT07 通道', 'DS2482 引脚'],
    [['SCL', 'P2_6（固定输出）', 'pin 25', 'CH1: 1A(1) → 1Y(2)', 'pin 4'],
     ['SDA_OUT', 'P2_7（固定输出）', 'pin 26', 'CH2: 2A(3) → 2Y(4)', 'pin 5'],
     ['SDA_IN', 'P0_2（固定输入）', 'pin 3', 'CH3: 3A(5) → 3Y(6)', '（回读通道）'],
     ['GND', '—', 'pin 27 等', 'pin 7', 'pin 3'],
     ],
    [22 * mm, 34 * mm, 26 * mm, 46 * mm, 36 * mm]))
S.append(note('板卡 Board ID = 1（BID#0 不存在）。验证板由 J1 独立 5V 供电（PTC + TVS），不从板卡取电。'
              'DS2482 的 AD0/AD1 接地，预期 7 位从机地址 0x18。74HCT07 为非反相开漏缓冲，'
              '板卡侧三个引脚全程固定方向。'))

S.append(h2('3. 硬件测量记录'))
S.append(table(
    ['测量项', '实测值', '理论/预期', '结论'],
    [['5V 网络电压', '5.186 V', '5 V ± 5%', '正常，在 DS2482(2.9~5.5V)与 74HCT07(4.5~5.5V)范围内'],
     ['D1 电源指示灯', '点亮', '点亮', '验证板已上电'],
     ['U2 pin1 (VCC) 对 GND', '5.186 V', '5 V', '芯片供电正常'],
     ['U2 pin3 (GND) 对板上 GND', '0.2 Ω', '≈0 Ω', '接地良好'],
     ['U2 pin4 (SCL) 方波实测', '0 / 5 V 跳变', '跳变', 'SCL 信号到达芯片引脚'],
     ['U2 pin5 (SDA) 方波实测', '0 / 5 V 跳变', '跳变', 'SDA 信号到达芯片引脚'],
     ['<b>U2 pin4 与 pin5</b>', '<b>4.38 kΩ</b>', 'R1+R2 = 4.4 kΩ', '<b>无短路，且两脚均低阻连到各自网络</b>'],
     ['<b>U2 pin5 与 SDA_OUT 焊盘</b>', '<b>12.21 kΩ</b>', 'R4+R2 = 12.2 kΩ', '<b>pin5 焊接良好，R2/R4/5V 网络均正常</b>'],
     ['U2 pin7 (AD1) 对 GND', '0.2 Ω', '≈0 Ω', '地址脚接地正常'],
     ['U2 pin8 (AD0) 对 GND', '0.2 Ω', '≈0 Ω', '地址脚接地正常，地址确为 0x18'],
     ['74HCT07 pin4(2Y) 与 pin5(3A)', '0.2 Ω', '≈0 Ω', '同一 SDA 网络，连通'],
     ['74HCT07 pin5(3A) 与 U2 pin5', '0.2 Ω', '≈0 Ω', 'ACK 回读路径连通'],
     ['SCL 方波时测 U2 pin5', '仅 ±10 mV', '不跳变', '容性串扰，SCL 与 SDA 未短路'],
     ['U2 丝印', 'DS2482', 'DS2482', '料号正确'],
     ['更换新 U2', '现象不变', '—', '排除单颗芯片偶发损坏'],
     ],
    [44 * mm, 26 * mm, 28 * mm, 66 * mm]))

S.append(PageBreak())
S.append(h2('4. 软件测量记录'))
S.append(table(
    ['测量项', '实测结果', '结论'],
    [['端口方向回读', 'Port0 = 0x00，Port2 = 0xF0', '方向配置已生效（Input / LinHout）'],
     ['总线空闲 SDA_IN', '1', '见第 6 节：此项不足以证明验证板已上电'],
     ['SDA 回环自检', '释放=1，拉低=0，再释放=1', '主机驱动与回读通道工作'],
     ['START 条件回读', '拉低 SDA 后读回 0', 'START 条件正确产生'],
     ['逐位写 / 回读（0x30）', '0/0 0/0 1/1 1/1 0/0 0/0 0/0 0/0', '八位全部一致，SDA 电平正确'],
     ['I²C 地址扫描', '0x08~0x77 共 112 个地址全无应答', '排除地址跑偏'],
     ['<b>SCL 高速翻转</b>', '<b>74553 Hz，万用表读 2.6 V</b>', '<b>5.186÷2 = 2.59V，SCL 在通信速度下确实翻转</b>'],
     ['DAQNavi 读写错误计数', '0 次', '驱动层无静默失败'],
     ['位延时 5 µs（约 50 kHz）', '无应答', '—'],
     ['位延时 1000 µs（约 325 Hz）', '无应答', '排除速率与上升沿相关问题'],
     ],
    [40 * mm, 58 * mm, 66 * mm]))
S.append(note('实测 I²C 速率：由 74553 Hz 的翻转频率反推，单次 DAQNavi WriteBit 约 1.7 µs，'
              '一个 I²C 位周期约 20 µs，即 SCL 约 50 kHz，满足标准模式 tLOW ≥ 4.7 µs / tHIGH ≥ 4.0 µs。'))

S.append(h2('5. 已排除的假设'))
S.append(table(
    ['假设', '排除依据'],
    [['验证板未上电', 'D1 点亮；U2 pin1 实测 5.186 V'],
     ['未与板卡共地', 'U2 pin3 对板上 GND 仅 0.2 Ω；1-Wire 通信正常'],
     ['SDA 驱动链路断开', 'SDA 回环自检通过；SDA 方波在 U2 pin5 上实测跳变'],
     ['SCL 驱动链路断开', 'SCL 方波在 U2 pin4 上实测跳变；高速翻转实测 2.6 V'],
     ['SCL 与 SDA 短路', 'pin4 与 pin5 实测 4.38 kΩ；SCL 方波时 pin5 仅 ±10 mV 串扰'],
     ['引脚虚焊（假焊）', 'pin4/pin5 的 4.38 kΩ 与 pin5 的 12.21 kΩ 均精确吻合理论值，'
                          '任何数 kΩ 级的接触电阻都会使读数明显偏大'],
     ['地址不是 0x18', 'AD0/AD1 均 0.2 Ω 接地；且全地址扫描无应答'],
     ['AD0/AD1 悬空导致芯片状态异常', '两脚实测 0.2 Ω 接地'],
     ['DS2482 芯片损坏', '已更换新片，现象完全相同'],
     ['DS2482 料号错误', '丝印确认为 DS2482'],
     ['速率过高 / 上升沿不足', '位延时 1000 µs（约 325 Hz）同样无应答'],
     ['容性负载（含 C3/C4）', '若为 100 nF，时间常数 = 2.2k x 100nF = 220 us，'
                              '1000 µs 延时下高电平超过 4.5 倍时间常数，足以充分上升，但仍不通。'
                              '且 PCB 上 C3/C4 位于电源脚旁，不在信号线上'],
     ['推挽输出干扰总线', '74HCT07 已将推挽隔离为开漏；总线高电平 5.186 V（对比背板直连时的 1.9 V）'],
     ['DAQNavi 写入静默失败', '已在位操作层检查返回值，实测 0 次错误'],
     ['ACK 回读路径断开', '74HCT07 pin4 与 pin5、pin5 与 U2 pin5 均 0.2 Ω'],
     ['1-Wire 侧异常', 'USB-1Wire 适配器可正常读出 DS2431 的 ID'],
     ['PCIE-1751 或上位机软件有问题', '改用独立的 USB-I2C 工具直连 DS2482 引脚，同样无应答'],
     ['DS2482 焊接或 PCB 走线缺陷', '拆除 U1 后，同一块板、同一颗芯片立即应答 0x30'],
     ['<b>U1 器件损坏</b>', '<b>更换新片后现象完全相同 —— 并非损坏，而是整批料号不符</b>'],
     ],
    [52 * mm, 112 * mm]))

S.append(PageBreak())
S.append(h2('6. 诊断方法论：每项测试的覆盖范围与盲点'))
S.append(p('本次排查中多次出现"测试通过但故障依旧"的情况，根源在于若干测试的覆盖范围'
           '比直觉上以为的要窄。以下记录供后续排查与改板时参考，可避免重复走弯路。'))
S.append(table(
    ['测试', '能够证明', '<b>不能</b>证明（盲点）'],
    [['SDA_IN 空闲读回 1',
      '回读链路未被持续拉低',
      '<b>不能证明验证板已上电</b>。PCIE-1751 的 P0_2 内部自带 10 kΩ 上拉至 +5 V，'
      '验证板完全断电时 74HCT07 输出高阻，该脚照样读到 1'],
     ['SDA 回环自检通过',
      '2A → 2Y → 3A → 3Y → P0_2 这一圈连通',
      '<b>不能证明 SDA 到达了 DS2482</b>。该回路完全不经过 U2 的 pin5'],
     ['逐位写 / 回读一致',
      '通信期间 SDA 电平正确',
      '<b>不能验证 SCL</b>。读回的是主机自己驱动的值，SCL 即使完全不动，回读同样全对'],
     ['万用表测到电压跳变',
      '该节点上存在信号',
      '<b>不能排除假焊</b>。万用表输入阻抗 10 MΩ，几十 kΩ 的假焊接触照样测得完整电压，'
      '而 I²C 拉低需要灌 2 mA 的低阻通路'],
     ['1 Hz 方波测量正常',
      '静态电平正确',
      '<b>不能证明通信速度下正常</b>。二者相差四个数量级，'
      '需用"高速翻转 + 万用表读半电源电压"来验证'],
     ['地址扫描覆盖 0x18~0x1B',
      '地址未落在这四个值上',
      '仅在 AD0/AD1 处于<b>确定电平</b>时成立。若两脚悬空，CMOS 输入浮于中间电平、'
      '芯片状态不确定，可能对任何地址都不响应'],
     ['测 SCL / SDA_OUT 测试焊盘',
      'J2 到 74HCT07 输入侧连通',
      '<b>那不是 I²C 总线</b>。这两个焊盘在 74HCT07 的输入侧，缓冲器单向，'
      'ACK 无法经此返回。用 USB-I2C 工具接这里必然得到假的"无应答"'],
     ],
    [34 * mm, 46 * mm, 84 * mm]))

S.append(h2('7. 两个一次顶多次的电阻测量'))
S.append(p('排查中有两个读数因为精确吻合理论值，一次性确认了多个环节，值得记录方法：'))
S.append(p('<b>U2 pin5 与 SDA_OUT 焊盘 = 12.21 kΩ</b><br/>'
           '路径为 SDA_OUT 焊盘 → R4(10k) → 5V 网络 → R2(2.2k) → SDA 总线 → U2 pin5，'
           '理论 12.2 kΩ，误差不到 0.1%。一次确认：R4 焊接良好、R2 焊接良好、5V 网络连通、'
           'U2 的 pin5 低阻连在 SDA 总线上（若有假焊，读数会明显偏大）。'))
S.append(p('<b>U2 pin4 与 pin5 = 4.38 kΩ</b><br/>'
           '路径为 pin4 → R1(2.2k) → 5V → R2(2.2k) → pin5，理论 4.4 kΩ。'
           '一次确认：两脚未短路（短路则为 0 Ω）、两脚分别低阻连到 SCL 与 SDA 网络、R1/R2 阻值正确。'))
S.append(note('通用方法：在有上拉电阻的网络之间测电阻，读数应等于两只上拉之和。'
              '该值对接触电阻非常敏感，比单纯测电压更能反映焊接质量。'))

S.append(h2('8. 最终结论'))
S.append(p('<b>根因：U1 的料号不符。</b>板上标称 74HCT07（集电极开漏）的器件，'
           '实测输出为推挽结构，使 I²C 总线失去"线与"特性，从机无法拉低 SDA，'
           '每一个 ACK 位均被判为 NACK。详细机理与验证数据见'
           '《74HCT07 干扰机理分析》。'))
S.append(table(
    ['阶段', '关键实验', '结果'],
    [['引入独立主机', '改用 USB-I2C 工具（JTool）直连 U2 的 pin4 / pin5，拔掉 SCSI 线',
      '仍无应答 —— 排除 PCIE-1751 与上位机软件'],
     ['分离芯片与 PCB', 'DS2482 脱离 PCB，飞线接 JTool',
      '<b>立即扫到 0x30</b> —— DS2482 本身完好'],
     ['芯片焊回', '同一颗芯片焊回板上，JTool 直连',
      '恢复无应答 —— 干扰源在 PCB 上'],
     ['<b>移除 U1</b>', '拆除 74HCT07，不更换任何其它器件，JTool 直连',
      '<b>立即扫到 0x30</b> —— 干扰源定位为 U1'],
     ['更换新片', '焊接新 74HCT07，先供电再插 PCIE-1751',
      '仍不通 —— 推翻"器件损坏"，指向整批料'],
     ['<b>脱离 PCB 独立验证</b>',
      'VCC = 5 V、GND 接地、其余输入接地、1A 接 5 V、1Y 经 1 kΩ 接地',
      '<b>实测 4.960 V（真开漏应约 0 V），输出阻抗约 44 Ω，确认为推挽</b>'],
     ],
    [26 * mm, 70 * mm, 68 * mm]))
S.append(note('问题批次：ST 标记「74HCT07 / 0AA709」。同批剩料应全部隔离。'
              '来料检验方法见《74HCT07 干扰机理分析》第 8 节。'))
S.append(p('<b>附带发现</b>：REV01 中 U1 由 J1 独立供电、输入却来自 PCIE-1751，'
           '构成双电源域。若先开工控机、后给验证板供电，输入端会在 VCC 缺失时'
           '经 ESD 保护二极管倒灌电流。本次故障与之无关，但建议在 REV02 中一并消除。'))

S.append(h2('9. 配套的软件诊断工具'))
S.append(p('上位机程序（software/desktop/PCIe-GPIO-I2C）已内置以下诊断功能，'
           '均可在"打开设备"后独立使用，不依赖 DS2482 是否应答：'))
S.append(table(
    ['功能', '用途'],
    [['测试 DS2482', '最小 I²C 链路验证：Device Reset + 读状态 + 写配置，不涉及 1-Wire'],
     ['扫描 I2C 地址', '遍历 0x08~0x77，区分"芯片无响应"与"地址不符"'],
     ['SDA 回环自检', '验证 P2_7 → CH2 → SDA → CH3 → P0_2 链路（注意其盲点，见第 6 节）'],
     ['SCL 方波（5 秒）', '1 Hz 方波，供万用表测量 SCL 通路'],
     ['SDA 方波（5 秒）', '1 Hz 方波，供万用表在 U2 pin5 上测量（回环自检不覆盖此段）'],
     ['SCL 高速翻转', '以通信速度连续翻转并报告实测频率，万用表应读到约半个电源电压'],
     ['SDA 外部拉低测试', '释放 SDA 并监视，由操作者手动短接 SDA 到 GND，'
                           '验证"外部器件拉低总线 → 主机可感知"，即 ACK 检测路径'],
     ['日志级别 Error/Info/Debug/Trace', 'Debug 记录 DS2482 命令与状态寄存器逐位解析；'
                                          'Trace 记录每个 I²C 字节及逐位写/回读对照'],
     ['位延时可调（1~1000 µs）', '运行时改变 I²C 速率，用于排查速率相关问题'],
     ],
    [40 * mm, 124 * mm]))
S.append(note('日志文件位于程序目录下 Log/DS2431_yyyyMMdd.log，按天追加。'
              'Trace 级会输出每个字节的"写入值/回读值"对照，写 0 却回读 1 即表示 SDA 拉不低。'))

out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'hardware')
os.makedirs(out_dir, exist_ok=True)
out = os.path.abspath(os.path.join(out_dir, 'PCIE-1751_I2C验证板故障排查记录.pdf'))
SimpleDocTemplate(out, pagesize=A4, leftMargin=16 * mm, rightMargin=14 * mm,
                  topMargin=15 * mm, bottomMargin=15 * mm,
                  title='PCIE-1751 I2C 验证板故障排查记录').build(S)
print(out)
