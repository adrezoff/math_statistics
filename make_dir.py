import os
import re


def clean_text(text):
    """Очищает текст: заменяет множественные пробелы на один."""
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def create_safe_name(text, max_length=30, is_folder=True):
    """
    Создает безопасное имя для папки или файла.
    Удаляет пробелы в начале и конце, а также недопустимые символы.
    """
    # Убираем пробелы в начале и конце
    text = text.strip()

    # Убираем недопустимые символы для файловой системы
    if is_folder:
        # Для папок заменяем проблемные символы
        safe_text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Убираем точки в конце имени папки (кроме первой точки после номера)
        safe_text = safe_text.rstrip('.')
        # Убираем пробелы в начале и конце снова (на случай если появились после удаления символов)
        safe_text = safe_text.strip()
        # Обрезаем до max_length символов
        if len(safe_text) > max_length:
            safe_text = safe_text[:max_length]
            # Убедимся, что после обрезки нет пробела в конце
            safe_text = safe_text.rstrip()
        return safe_text
    else:
        # Для файлов аналогично
        safe_text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Убираем точки в конце (кроме расширения)
        safe_text = safe_text.rstrip('.')
        # Убираем пробелы в начале и конце
        safe_text = safe_text.strip()
        # Обрезаем до max_length символов
        if len(safe_text) > max_length:
            safe_text = safe_text[:max_length]
            # Убедимся, что после обрезки нет пробела в конце
            safe_text = safe_text.rstrip()
        return safe_text


def extract_tickets_from_text(text):
    """Извлекает номера и тексты билетов из введенного текста."""
    tickets = []
    lines = text.strip().split('\n')

    current_ticket = None
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Ищем начало нового билета
        match = re.match(r'^(\d+)[\.\)\s]+(.+)$', line)
        if match:
            # Сохраняем предыдущий билет
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
    base_dir = "tickets"
    os.makedirs(base_dir, exist_ok=True)

    print(f"Создаю структуру в папке: {base_dir}/")
    print("-" * 50)

    for ticket_num, ticket_text in tickets:
        # Создаем название для папки (первые 30 символов)
        short_folder_name = create_safe_name(ticket_text, max_length=30, is_folder=True)
        folder_name = f"{ticket_num}. {short_folder_name}"
        # Убираем возможные пробелы в конце имени папки
        folder_name = folder_name.rstrip()

        # Создаем имя файла (первые 30 символов)
        short_file_name = create_safe_name(ticket_text, max_length=30, is_folder=False)
        file_name = f"{ticket_num}. {short_file_name}.md"
        # Убираем возможные пробелы перед .md
        file_name = file_name.replace(' .md', '.md')
        file_name = file_name.rstrip()

        # Проверяем, что имена не пустые
        if not short_folder_name or short_folder_name.isspace():
            short_folder_name = f"Билет_{ticket_num}"
            folder_name = f"{ticket_num}. {short_folder_name}"

        if not short_file_name or short_file_name.isspace():
            short_file_name = f"Билет_{ticket_num}"
            file_name = f"{ticket_num}. {short_file_name}.md"

        # Создаем папку
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Создаем полный путь к MD файлу
        file_path = os.path.join(folder_path, file_name)

        # Создаем содержимое MD файла
        md_content = f"# {ticket_num}. {ticket_text}\n\n"

        # Записываем MD файл
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"✓ Создан билет {ticket_num}:")
            print(f"  Папка: '{folder_name}/' (длина: {len(folder_name)})")
            print(f"  Файл: '{file_name}' (длина: {len(file_name)})")
            print()
        except Exception as e:
            print(f"✗ Ошибка при создании билета {ticket_num}: {e}")
            print(f"  Проблемное имя папки: '{folder_name}'")
            print(f"  Проблемное имя файла: '{file_name}'")
            print()


def main():
    print("СОЗДАНИЕ СТРУКТУРЫ БИЛЕТОВ")
    print("=" * 50)
    print("Введите текст с билетами (введите 'END' на новой строке для завершения):")
    print("Формат: номер. текст билета")
    print("-" * 50)

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
        print("\nТекст не введен!")
        return

    # Извлекаем билеты из текста
    tickets = extract_tickets_from_text(input_text)

    if not tickets:
        print("\nНе найдено билетов в тексте!")
        print("Убедитесь, что билеты начинаются с номера и точки, например:")
        print("1. Текст первого билета")
        print("2. Текст второго билета")
        return

    print(f"\nНайдено билетов: {len(tickets)}")

    # Показываем извлеченные билеты для проверки
    print("\nИзвлеченные билеты:")
    print("-" * 50)
    for num, text in tickets:
        print(f"{num}: {text[:80]}{'...' if len(text) > 80 else ''}")

    # Подтверждение
    print("\n" + "=" * 50)
    confirm = input("Создать папки и файлы? (y/n): ").strip().lower()

    if confirm in ['y', 'yes', 'да', 'д']:
        create_ticket_structure(tickets)
        print("\n" + "=" * 50)
        print("Структура создана успешно!")
        print("Примечания:")
        print("1. Папки и файлы ограничены 30 символами (без учета номера и расширения)")
        print("2. Удалены пробелы в начале и конце имен")
        print("3. Удалены недопустимые символы: < > : \" / \\ | ? *")
    else:
        print("\nСоздание отменено")


if __name__ == "__main__":
    main()