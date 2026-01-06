import os
import re
import glob
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import sys


def get_sorted_pdf_files():
    """Находит все PDF файлы и сортирует их по номеру в имени или папке."""
    pdf_files = []

    # Ищем все PDF файлы рекурсивно
    for pdf_path in Path('.').rglob('*.pdf'):
        # Пропускаем итоговый файл, если он уже существует
        if pdf_path.name.lower() in ['объединенный.pdf', 'combined.pdf', 'result.pdf', 'output.pdf']:
            continue

        # Извлекаем номер из пути
        number = extract_number_from_path(pdf_path)

        if number is not None:
            pdf_files.append({
                'number': number,
                'path': pdf_path,
                'dir': pdf_path.parent
            })

    # Сортируем по номеру
    pdf_files.sort(key=lambda x: x['number'])
    return pdf_files


def extract_number_from_path(path):
    """Извлекает номер из пути к файлу."""
    # Пробуем из имени файла
    filename = path.stem  # Без расширения
    match = re.search(r'^(\d+)', filename)
    if match:
        return int(match.group(1))

    # Пробуем из имени папки
    dir_name = path.parent.name
    match = re.search(r'^(\d+)', dir_name)
    if match:
        return int(match.group(1))

    return None


def find_md_file_for_pdf(pdf_file_info):
    """Находит MD файл для соответствующего PDF."""
    pdf_dir = pdf_file_info['dir']
    pdf_name = pdf_file_info['path'].stem  # Имя PDF без расширения

    # Варианты имен MD файлов
    possible_md_names = [
        f"{pdf_name}.md",
        "README.md",
        "readme.md",
        f"{pdf_file_info['number']}.md",
        f"{pdf_file_info['number']}. билет.md",
    ]

    for md_name in possible_md_names:
        md_path = pdf_dir / md_name
        if md_path.exists():
            return md_path

    # Ищем любой MD файл в той же директории
    for md_path in pdf_dir.glob('*.md'):
        return md_path

    return None


def get_title_from_md(md_path):
    """Извлекает заголовок из первой строки MD файла."""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

            # Если строка начинается с #, убираем маркер заголовка
            if first_line.startswith('#'):
                # Убираем все # в начале и пробелы
                title = first_line.lstrip('#').strip()
            else:
                title = first_line

            # Если заголовок слишком длинный, обрезаем
            if len(title) > 150:
                title = title[:147] + "..."

            return title if title else f"Билет {md_path.stem}"

    except Exception as e:
        print(f"  Ошибка чтения {md_path}: {e}")
        return f"Билет {pdf_file_info['number']}"


def create_bookmarks(pdf_writer, pdf_files, titles):
    """Создает закладки (оглавление) в PDF."""
    bookmark_list = []

    current_page = 0

    for i, (pdf_info, title) in enumerate(zip(pdf_files, titles)):
        # Открываем каждый PDF файл для получения количества страниц
        try:
            pdf_reader = PdfReader(str(pdf_info['path']))
            num_pages = len(pdf_reader.pages)

            # Создаем закладку на первую страницу этого билета
            if current_page < len(pdf_writer.pages):
                bookmark = pdf_writer.add_outline_item(
                    title=f"{pdf_info['number']}. {title}",
                    page_number=current_page
                )
                bookmark_list.append(bookmark)

            current_page += num_pages

        except Exception as e:
            print(f"  Ошибка при обработке {pdf_info['path'].name}: {e}")
            continue

    return bookmark_list


def merge_pdfs_with_toc(pdf_files, output_filename='объединенный.pdf'):
    """Объединяет PDF файлы и добавляет оглавление."""
    print(f"\nОбъединение PDF файлов в: {output_filename}")

    # Используем PdfMerger для объединения
    merger = PdfMerger()

    # Собираем заголовки для оглавления
    titles = []

    print("\nОбработка файлов:")
    print("-" * 60)

    for i, pdf_info in enumerate(pdf_files, 1):
        pdf_path = pdf_info['path']

        # Находим соответствующий MD файл
        md_path = find_md_file_for_pdf(pdf_info)

        if md_path:
            title = get_title_from_md(md_path)
            print(f"{i:3d}. {pdf_path.name:50} -> {title[:50]}...")
        else:
            title = f"Билет {pdf_info['number']}"
            print(f"{i:3d}. {pdf_path.name:50} -> {title} (MD файл не найден)")

        titles.append(title)

        # Добавляем PDF в объединение
        try:
            merger.append(str(pdf_path))
        except Exception as e:
            print(f"  Ошибка при добавлении {pdf_path.name}: {e}")

    # Создаем оглавление (закладки)
    print("\nСоздание оглавления...")

    # Добавляем закладки
    for i, (pdf_info, title) in enumerate(zip(pdf_files, titles)):
        try:
            # Определяем страницу, на которой начинается этот PDF
            start_page = 0
            for j in range(i):
                try:
                    reader = PdfReader(str(pdf_files[j]['path']))
                    start_page += len(reader.pages)
                except:
                    pass

            # Добавляем закладку
            merger.add_outline_item(
                title=f"{pdf_info['number']}. {title}",
                page_number=start_page,
                parent=None
            )
        except Exception as e:
            print(f"  Ошибка при создании закладки для {pdf_info['path'].name}: {e}")

    # Сохраняем объединенный PDF
    try:
        merger.write(output_filename)
        merger.close()

        # Проверяем размер файла
        file_size = os.path.getsize(output_filename) / (1024 * 1024)  # в МБ
        print(f"\n✅ Готово! PDF сохранен как: {output_filename}")
        print(f"📊 Размер файла: {file_size:.2f} MB")
        print(f"📄 Количество исходных файлов: {len(pdf_files)}")

        return True

    except Exception as e:
        print(f"\n❌ Ошибка при сохранении PDF: {e}")
        return False


def create_text_toc(pdf_files, titles, output_filename='оглавление.txt'):
    """Создает текстовое оглавление."""
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("ОГЛАВЛЕНИЕ\n")
        f.write("=" * 80 + "\n\n")

        current_page = 1

        for i, (pdf_info, title) in enumerate(zip(pdf_files, titles)):
            # Получаем количество страниц в текущем PDF
            try:
                pdf_reader = PdfReader(str(pdf_info['path']))
                num_pages = len(pdf_reader.pages)

                f.write(f"{pdf_info['number']:3d}. {title}\n")
                f.write(f"     Страницы: {current_page}-{current_page + num_pages - 1}\n")
                f.write(f"     Файл: {pdf_info['path'].name}\n\n")

                current_page += num_pages

            except Exception as e:
                f.write(f"{pdf_info['number']:3d}. {title} (ошибка: {e})\n\n")

        f.write(f"\nВсего страниц: {current_page - 1}\n")

    print(f"✓ Текстовое оглавление сохранено как: {output_filename}")
    return output_filename


def main():
    """Основная функция."""
    print("=" * 60)
    print("СБОРКА PDF ФАЙЛОВ С ОГЛАВЛЕНИЕМ")
    print("=" * 60)

    # Проверяем PyPDF2
    try:
        from PyPDF2 import PdfReader, PdfWriter, PdfMerger
    except ImportError:
        print("\n❌ Не установлена библиотека PyPDF2")
        print("Установите её командой: pip install PyPDF2")
        sys.exit(1)

    # Ищем PDF файлы
    print("\nПоиск PDF файлов...")
    pdf_files = get_sorted_pdf_files()

    if not pdf_files:
        print("❌ Не найдено PDF файлов!")
        print("\nУбедитесь, что:")
        print("1. PDF файлы существуют в текущей директории или поддиректориях")
        print("2. Имена файлов или папок начинаются с номера (1., 2., и т.д.)")
        print("3. Файлы имеют расширение .pdf")
        return

    print(f"✅ Найдено PDF файлов: {len(pdf_files)}")

    # Показываем найденные файлы
    print("\nНайденные файлы (отсортированы по номеру):")
    print("-" * 60)

    for i, pdf_info in enumerate(pdf_files, 1):
        print(f"{i:3d}. {pdf_info['path'].name:40} (папка: {pdf_info['dir'].name})")

    # Подтверждение
    print("\n" + "=" * 60)
    confirm = input("Продолжить объединение? (y/n): ").strip().lower()

    if confirm not in ['y', 'yes', 'да', 'д']:
        print("❌ Отменено пользователем")
        return

    # Объединяем PDF
    output_pdf = 'объединенный.pdf'

    # Проверяем, не существует ли уже файл
    if os.path.exists(output_pdf):
        print(f"\n⚠  Файл {output_pdf} уже существует!")
        overwrite = input("Перезаписать? (y/n): ").strip().lower()
        if overwrite not in ['y', 'yes', 'да', 'д']:
            # Предлагаем новое имя
            new_name = input("Введите новое имя файла (без .pdf): ").strip()
            if new_name:
                output_pdf = f"{new_name}.pdf"
            else:
                output_pdf = f"объединенный_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # Объединяем PDF файлы
    success = merge_pdfs_with_toc(pdf_files, output_pdf)

    if success:
        # Создаем текстовое оглавление
        # Сначала соберем все заголовки
        titles = []
        for pdf_info in pdf_files:
            md_path = find_md_file_for_pdf(pdf_info)
            if md_path:
                title = get_title_from_md(md_path)
            else:
                title = f"Билет {pdf_info['number']}"
            titles.append(title)

        create_text_toc(pdf_files, titles)

        print("\n" + "=" * 60)
        print("🎉 ОБЪЕДИНЕНИЕ ЗАВЕРШЕНО!")
        print("=" * 60)
        print(f"\nСозданные файлы:")
        print(f"1. {output_pdf} - Объединенный PDF с оглавлением")
        print(f"2. оглавление.txt - Текстовое оглавление")

        print("\n📋 Оглавление содержит:")
        for i, (pdf_info, title) in enumerate(zip(pdf_files, titles), 1):
            print(f"   {pdf_info['number']:2d}. {title[:60]}...")

    else:
        print("\n❌ Не удалось создать объединенный PDF")


if __name__ == "__main__":
    from datetime import datetime

    main()