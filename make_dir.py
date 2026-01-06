import os
import re


def clean_text(text):
    """Очищает текст: заменяет множественные пробелы на один."""
    # Заменяем все пробельные символы (включая табы, переносы) на один пробел
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def truncate_filename(name, max_length=150, keep_extension=True):
    """Обрезает имя файла до max_length символов, добавляя '...' если нужно."""
    if len(name) <= max_length:
        return name

    # Если нужно сохранить расширение
    if keep_extension and '.' in name:
        name_without_ext, extension = name.rsplit('.', 1)
        # Учитываем расширение в максимальной длине
        max_name_length = max_length - len(extension) - 1  # -1 для точки

        if len(name_without_ext) <= max_name_length:
            return name

        # Обрезаем основную часть имени
        truncated = name_without_ext[:max_name_length - 3]  # -3 для '...'
        # Обрезаем до последнего полного слова
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]

        return f"{truncated}... .{extension}"

    # Без расширения
    truncated = name[:max_length - 3]
    # Обрезаем до последнего полного слова
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + '...'


def extract_tickets_from_text(text):
    """Извлекает номера и тексты билетов из введенного текста."""
    tickets = []

    # Разбиваем текст на строки
    lines = text.strip().split('\n')

    current_ticket = None
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Ищем начало нового билета (номер с точкой или цифра в начале строки)
        match = re.match(r'^(\d+)[\.\)\s]+(.+)$', line)
        if match:
            # Если есть предыдущий билет, сохраняем его
            if current_ticket is not None:
                ticket_text = ' '.join(current_text)
                tickets.append((current_ticket, clean_text(ticket_text)))

            # Начинаем новый билет
            current_ticket = int(match.group(1))
            current_text = [match.group(2).strip()]
        elif current_ticket is not None:
            # Продолжение текста текущего билета
            current_text.append(line)

    # Добавляем последний билет
    if current_ticket is not None:
        ticket_text = ' '.join(current_text)
        tickets.append((current_ticket, clean_text(ticket_text)))

    return tickets


def create_ticket_structure(tickets):
    """Создает папки и MD файлы для каждого билета."""
    # Создаем корневую директорию для билетов
    base_dir = "tickets"
    os.makedirs(base_dir, exist_ok=True)

    print(f"\nСоздаю структуру в папке: {base_dir}/")
    print("-" * 50)

    for ticket_num, ticket_text in tickets:
        # Создаем название для папки
        folder_name = f"{ticket_num}. {ticket_text}"

        # Обрезаем слишком длинные названия папок (без расширения)
        folder_name = truncate_filename(folder_name, keep_extension=False)

        # Создаем имя файла
        file_name = f"{ticket_num}. {ticket_text}.md"

        # Обрезаем слишком длинные имена файлов (сохраняя расширение .md)
        file_name = truncate_filename(file_name, max_length=150, keep_extension=True)

        # Создаем папку
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Создаем полный путь к MD файлу
        file_path = os.path.join(folder_path, file_name)

        # Создаем содержимое MD файла
        md_content = f"## {ticket_num}. {ticket_text}\n\n"

        # Записываем MD файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"✓ Создан билет {ticket_num}:")
        print(f"  Папка: {folder_name}/")
        print(f"  Файл: {file_name}")
        print()

    # Показать итоговую структуру
    print("\nСозданная структура:")
    print("-" * 50)
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/" if level > 0 else f"{root}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")


def main():
    print("=" * 60)
    print("СОЗДАНИЕ СТРУКТУРЫ БИЛЕТОВ")
    print("=" * 60)
    print("\nВведите текст с билетами (введите 'END' на новой строке для завершения):")
    print("Формат: номер. текст билета")
    print("-" * 60)

    # Собираем многострочный ввод
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break

    # Объединяем строки
    input_text = '\n'.join(lines)

    if not input_text.strip():
        print("\n⚠  Текст не введен!")
        return

    # Извлекаем билеты из текста
    tickets = extract_tickets_from_text(input_text)

    if not tickets:
        print("\n⚠  Не найдено билетов в тексте!")
        print("Убедитесь, что билеты начинаются с номера и точки, например:")
        print("1. Текст первого билета")
        print("2. Текст второго билета")
        return

    print(f"\n✅ Найдено билетов: {len(tickets)}")

    # Показываем извлеченные билеты для проверки
    print("\nИзвлеченные билеты:")
    print("-" * 50)
    for i, (num, text) in enumerate(tickets, 1):
        print(f"{num}: {text[:80]}...")

    # Подтверждение
    print("\n" + "=" * 50)
    confirm = input("Создать папки и файлы? (y/n): ").strip().lower()

    if confirm in ['y', 'yes', 'да', 'д']:
        create_ticket_structure(tickets)

        print("\n✅ Структура создана успешно!")
        print("\nДополнительные команды:")
        print("1. Для объединения в PDF используйте скрипт make_pdf.py")
        print("2. Для редактирования MD файлов используйте любой текстовый редактор")
    else:
        print("\n❌ Создание отменено")


if __name__ == "__main__":
    main()