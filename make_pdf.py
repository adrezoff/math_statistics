import os
import re
from pathlib import Path
from PyPDF2 import PdfReader, PdfMerger
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from datetime import datetime

# ---------- Настройки ----------
FONT_FILE = "./DejaVuLGCSans.ttf"  # Положи шрифт рядом со скриптом
OUTPUT_PDF = "math_statistics.pdf"
PAGE_SIZE = A4
MARGIN = 20
LINE_HEIGHT = 20

# ---------- Получаем PDF файлы ----------
def get_sorted_pdf_files():
    pdf_files = []
    for pdf_path in Path('.').rglob('*.pdf'):
        if pdf_path.name.lower() in [OUTPUT_PDF.lower(), "объединенный.pdf", "combined.pdf"]:
            continue
        match = re.match(r'^(\d+)', pdf_path.stem)
        number = int(match.group(1)) if match else None
        if number:
            pdf_files.append({"number": number, "path": pdf_path, "dir": pdf_path.parent})
    pdf_files.sort(key=lambda x: x["number"])
    return pdf_files

# ---------- Находим заголовки из MD ----------
def find_md_file_for_pdf(pdf_info):
    pdf_dir = pdf_info['dir']
    pdf_name = pdf_info['path'].stem
    for fname in [f"{pdf_name}.md", f"{pdf_info['number']}.md", "README.md"]:
        fpath = pdf_dir / fname
        if fpath.exists():
            return fpath
    for ext in ['*.md', '*.txt']:
        for fpath in pdf_dir.glob(ext):
            if 'merge' not in fpath.name.lower() and 'combine' not in fpath.name.lower():
                return fpath
    return None

def get_title_from_md(md_path, pdf_info):
    try:
        with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(5):
                line = f.readline()
                if line and len(line.strip()) > 3:
                    line = re.sub(r'^#+\s*', '', line.strip())
                    return line[:150]
    except:
        pass
    return f"Билет {pdf_info['number']}"

# ---------- Создание оглавления ----------
def create_toc_page(pdf_files, titles):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=PAGE_SIZE)
    width, height = PAGE_SIZE

    # ---------- Шрифт ----------
    if not os.path.exists(FONT_FILE):
        raise RuntimeError(f"Шрифт {FONT_FILE} не найден!")
    pdfmetrics.registerFont(TTFont("MAIN_FONT", FONT_FILE))
    FONT_NAME = "MAIN_FONT"

    # ---------- Заголовок ----------
    current_y = height - MARGIN - 50
    c.setFont(FONT_NAME, 16)
    c.drawString(MARGIN, current_y, "ОГЛАВЛЕНИЕ")
    current_y -= 30

    # ---------- Таблица оглавления ----------
    page_counter = 2
    outline_entries = []

    for pdf_info, title in zip(pdf_files, titles):
        try:
            reader = PdfReader(str(pdf_info['path']))
            num_pages = len(reader.pages)

            # Убираем дублирование номера
            title_display = title[:60] + "..." if len(title) > 60 else title

            c.setFont(FONT_NAME, 12)
            c.drawString(MARGIN, current_y, title_display)

            # Номер страниц справа
            page_info = f"{page_counter}-{page_counter + num_pages - 1}"
            c.drawRightString(width - MARGIN, current_y, page_info)

            outline_entries.append({"title": title_display, "page": page_counter - 1})  # page 0-based

            current_y -= LINE_HEIGHT
            page_counter += num_pages

            if current_y < MARGIN + 50:
                c.showPage()
                current_y = height - MARGIN - 50

        except:
            continue

    c.save()
    packet.seek(0)
    return packet, outline_entries

# ---------- Объединение PDF с оглавлением и ссылками ----------
def merge_pdfs_with_toc(pdf_files):
    titles = []
    for pdf_info in pdf_files:
        md_path = find_md_file_for_pdf(pdf_info)
        title = get_title_from_md(md_path, pdf_info) if md_path else f"Билет {pdf_info['number']}"
        titles.append(title)

    toc_packet, outline_entries = create_toc_page(pdf_files, titles)
    toc_reader = PdfReader(toc_packet)

    merger = PdfMerger()
    merger.append(toc_reader)

    page_counter = 1  # начинаем считать страницы после оглавления
    for pdf_info in pdf_files:
        merger.append(str(pdf_info['path']))
        page_counter += len(PdfReader(str(pdf_info['path'])).pages)

    # ---------- Добавляем кликабельное оглавление ----------
    for entry in outline_entries:
        merger.add_outline_item(entry['title'], entry['page'])

    merger.write(OUTPUT_PDF)
    merger.close()

# ---------- MAIN ----------
def main():
    pdf_files = get_sorted_pdf_files()
    if not pdf_files:
        return
    merge_pdfs_with_toc(pdf_files)

if __name__ == "__main__":
    main()
