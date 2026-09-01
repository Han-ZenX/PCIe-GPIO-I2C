#!/usr/bin/env python3
"""
中文 Markdown 转 PDF 工具（用于 docs/ 下的硬件设计文档）

用法: python md2pdf.py docs/hardware/xxx.md docs/hardware/xxx.pdf --subtitle "CORE 项目"

依赖: reportlab, fonttools
字体: 思源黑体 (Noto Sans SC)，SIL Open Font License，可自由嵌入分发。
      系统装的是可变字体，默认权重 100 (Thin) 过细，首次运行会自动实例化出
      400/700 两个静态字重并缓存到 ~/.cache/core-docs-fonts/。

支持的 Markdown 语法: 标题(#~###)、表格、代码块(```)、引用(>)、
有序/无序列表、水平分割线(---)、行内 **粗体** 与 `代码`。
插图: 单独一行写 `@fig:名称 图题`，由 figures.py 生成矢量示意图。
不支持: 外部图片文件、嵌套列表、脚注、超链接。
"""

import argparse
import os
import re
import sys

import figures

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, PageTemplate,
                                Paragraph, Preformatted, Spacer, Table, TableStyle)

VF = r'C:\Windows\Fonts\NotoSansSC-VF.ttf'
CACHE = os.path.join(os.path.expanduser('~'), '.cache', 'core-docs-fonts')

FONT, BOLD, MONO = 'NotoSC', 'NotoSC-Bold', 'Courier'

ACCENT = colors.HexColor('#1a5f9c')
DARK = colors.HexColor('#1a1a1a')
GREY = colors.HexColor('#555555')
CODEBG = colors.HexColor('#f2f4f6')

PAGE_W = A4[0] - 40 * mm

S = {
    'title': ParagraphStyle('title', fontName=BOLD, fontSize=19, leading=26,
                            textColor=ACCENT, spaceAfter=2),
    'sub': ParagraphStyle('sub', fontName=FONT, fontSize=9, leading=13,
                          textColor=GREY, spaceAfter=12),
    'h1': ParagraphStyle('h1', fontName=BOLD, fontSize=13.5, leading=19,
                         textColor=ACCENT, spaceBefore=13, spaceAfter=5),
    'h2': ParagraphStyle('h2', fontName=BOLD, fontSize=11, leading=16,
                         textColor=DARK, spaceBefore=9, spaceAfter=4),
    'body': ParagraphStyle('body', fontName=FONT, fontSize=9.5, leading=15.5,
                           textColor=DARK, spaceAfter=5),
    'quote': ParagraphStyle('quote', fontName=FONT, fontSize=9, leading=14.5,
                            textColor=colors.HexColor('#7a4a00'), spaceAfter=8,
                            backColor=colors.HexColor('#fdf6e6'),
                            borderPadding=(6, 8, 6, 8)),
    'li': ParagraphStyle('li', fontName=FONT, fontSize=9.5, leading=15.5,
                         textColor=DARK, leftIndent=14, bulletIndent=3,
                         spaceAfter=3),
    'code': ParagraphStyle('code', fontName=MONO, fontSize=8, leading=11.5,
                           textColor=colors.HexColor('#22333f'),
                           backColor=CODEBG, borderPadding=(6, 7, 6, 7),
                           spaceBefore=4, spaceAfter=8),
    'cell': ParagraphStyle('cell', fontName=FONT, fontSize=8.5, leading=12.5,
                           textColor=DARK),
    'cellh': ParagraphStyle('cellh', fontName=BOLD, fontSize=8.5, leading=12.5,
                            textColor=colors.white),
}


def ensure_fonts():
    """确保字重 400/700 的静态 TTF 存在，返回两者路径。"""
    paths = [os.path.join(CACHE, n)
             for n in ('NotoSansSC-Regular.ttf', 'NotoSansSC-Bold.ttf')]
    if all(os.path.exists(p) for p in paths):
        return paths
    if not os.path.exists(VF):
        sys.exit('[ERROR] 找不到思源黑体可变字体: %s\n'
                 '        请安装 Noto Sans SC，或修改脚本顶部的 VF 路径。' % VF)
    from fontTools.ttLib import TTFont as FTFont
    from fontTools.varLib import instancer
    os.makedirs(CACHE, exist_ok=True)
    for path, weight, style in zip(paths, (400, 700), ('Regular', 'Bold')):
        if os.path.exists(path):
            continue
        f = FTFont(VF)
        instancer.instantiateVariableFont(f, {'wght': weight}, inplace=True)
        # 实例化不更新 name 表，否则 PDF 里会显示成 VF 的默认名 Thin
        nm = f['name']
        for nid in (1, 2, 4, 6, 16, 17):
            nm.removeNames(nameID=nid)
        for nid, val in ((1, 'Noto Sans SC'), (2, style),
                         (4, 'Noto Sans SC ' + style),
                         (6, 'NotoSansSC-' + style)):
            nm.setName(val, nid, 3, 1, 0x409)
        f.save(path)
        print('[FONT] 已生成字体缓存: %s' % path)
    return paths


def inline(t):
    """Markdown 行内语法 -> reportlab 标记。"""
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\*(.+?)\*', r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`',
               r'<font face="%s" size="8.5" color="#b5451b">\1</font>' % MONO, t)
    return t


def make_table(rows):
    ncol = len(rows[0])
    # 按各列最宽单元格的文本宽度加权分配列宽
    w = []
    for i in range(ncol):
        cells = [r[i] for r in rows if i < len(r)]
        w.append(max(stringWidth(re.sub(r'[`*]', '', c), FONT, 8.5)
                     for c in cells) + 14)
    total = sum(w)
    if total > PAGE_W:
        w = [x * PAGE_W / total for x in w]
    data = [[Paragraph(inline(c), S['cellh']) for c in rows[0]]]
    data += [[Paragraph(inline(c), S['cell']) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=w, hAlign='LEFT', repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#f4f7fa')]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#c9d6e2')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
    ]))
    return t


def parse(lines, subtitle=''):
    story, buf, tbl, code = [], [], [], None

    def flush_para():
        if buf:
            story.append(Paragraph(inline(' '.join(buf)), S['body']))
            buf.clear()

    def flush_table():
        if tbl:
            story.append(make_table(list(tbl)))
            story.append(Spacer(1, 6))
            tbl.clear()

    for raw in lines:
        line = raw.rstrip('\n')
        stripped = line.strip()

        if code is not None:
            if stripped.startswith('```'):
                story.append(Preformatted('\n'.join(code), S['code']))
                code = None
            else:
                code.append(line)
            continue
        if stripped.startswith('```'):
            flush_para(); flush_table()
            code = []
            continue

        if stripped.startswith('|'):
            flush_para()
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                tbl.append(cells)
            continue
        flush_table()

        if not stripped:
            flush_para()
        elif stripped in ('---', '***', '___'):
            flush_para()
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width='100%', thickness=0.6,
                                    color=colors.HexColor('#d5dee7')))
            story.append(Spacer(1, 2))
        elif stripped.startswith('#'):
            flush_para()
            level = len(stripped) - len(stripped.lstrip('#'))
            text = stripped.lstrip('#').strip()
            if level == 1:
                story.append(Paragraph(inline(text), S['title']))
                if subtitle:
                    story.append(Paragraph(subtitle, S['sub']))
            else:
                story.append(Paragraph(inline(text), S['h1' if level == 2 else 'h2']))
        elif stripped.startswith('@fig:'):
            flush_para()
            name, _, caption = stripped[5:].strip().partition(' ')
            story.extend(figures.make(name, caption.strip()))
        elif stripped.startswith('> '):
            flush_para()
            story.append(Paragraph(inline(stripped[2:]), S['quote']))
        elif re.match(r'^[-*] ', stripped):
            flush_para()
            story.append(Paragraph(inline(stripped[2:]), S['li'], bulletText='•'))
        elif re.match(r'^\d+\. ', stripped):
            flush_para()
            n, text = stripped.split('. ', 1)
            story.append(Paragraph(inline(text), S['li'], bulletText=n + '.'))
        else:
            buf.append(stripped)

    flush_para(); flush_table()
    return story


def on_page(canv, doc):
    canv.saveState()
    canv.setFont(FONT, 8)
    canv.setFillColor(GREY)
    canv.drawString(20 * mm, 12 * mm, 'CORE 项目 · 硬件设计文档')
    canv.drawRightString(A4[0] - 20 * mm, 12 * mm,
                         '第 %d 页' % canv.getPageNumber())
    canv.setStrokeColor(colors.HexColor('#d5dee7'))
    canv.setLineWidth(0.4)
    canv.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)
    canv.restoreState()


def main():
    parser = argparse.ArgumentParser(description='中文 Markdown 转 PDF')
    parser.add_argument('input', help='输入的 .md 文件')
    parser.add_argument('output', help='输出的 .pdf 文件')
    parser.add_argument('--subtitle', default='', help='标题下方的副标题行')
    args = parser.parse_args()

    reg, bold = ensure_fonts()
    pdfmetrics.registerFont(TTFont(FONT, reg))
    pdfmetrics.registerFont(TTFont(BOLD, bold))
    pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD,
                                  italic=FONT, boldItalic=BOLD)

    with open(args.input, encoding='utf-8') as f:
        story = parse(f.readlines(), args.subtitle)

    title = os.path.splitext(os.path.basename(args.input))[0]
    doc = BaseDocTemplate(
        args.output, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title=title, author='CORE 项目')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='n')
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=on_page)])
    doc.build(story)

    print('[DONE] %s -> %s' % (args.input, args.output))


if __name__ == '__main__':
    main()
