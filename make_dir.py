import os
import re


def clean_text(text):
    """Очищает текст: заменяет множественные пробелы на один."""
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def create_safe_name(text, max_length=30, is_folder=True):
    """
    Создает безопасное имя для папки или файла.
    Для папок: [номер]. [первые max_length символов]
    Для файлов: [номер]. [первые max_length символов].md
    """
    # Убираем недопустимые символы для файловой системы
    if is_folder:
        # Для папок заменяем проблемные символы
        safe_text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Обрезаем до max_length символов
        if len(safe_text) > max_length:
            safe_text = safe_text[:max_length]
        return safe_text
    else:
        # Для файлов аналогично
        safe_text = re.sub(r'[<>:"/\\|?*]', '', text)
        if len(safe_text) > max_length:
            safe_text = safe_text[:max_length]
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

    for ticket_num, ticket_text in tickets:
        # Создаем название для папки (первые 30 символов)
        short_folder_name = create_safe_name(ticket_text, max_length=30, is_folder=True)
        folder_name = f"{ticket_num}. {short_folder_name}"

        # Создаем имя файла (первые 30 символов)
        short_file_name = create_safe_name(ticket_text, max_length=30, is_folder=False)
        file_name = f"{ticket_num}. {short_file_name}.md"

        # Создаем папку
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Создаем полный путь к MD файлу
        file_path = os.path.join(folder_path, file_name)

        # Создаем содержимое MD файла
        md_content = f"# {ticket_num}. {ticket_text}\n\n"

        # Записываем MD файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"Создан билет {ticket_num}:")
        print(f"  Папка: {folder_name}/")
        print(f"  Файл: {file_name}")
        print()


def main():
    print("СОЗДАНИЕ СТРУКТУРЫ БИЛЕТОВ")
    print("Введите текст с билетами (введите 'END' на новой строке для завершения):")
    print("Формат: номер. текст билета")

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
        print("Текст не введен!")
        return

    # Извлекаем билеты из текста
    tickets = extract_tickets_from_text(input_text)

    if not tickets:
        print("Не найдено билетов в тексте!")
        print("Убедитесь, что билеты начинаются с номера и точки, например:")
        print("1. Текст первого билета")
        print("2. Текст второго билета")
        return

    print(f"Найдено билетов: {len(tickets)}")

    # Показываем извлеченные билеты для проверки
    print("Извлеченные билеты:")
    for num, text in tickets:
        print(f"{num}: {text}")

    # Подтверждение
    confirm = input("Создать папки и файлы? (y/n): ").strip().lower()

    if confirm in ['y', 'yes', 'да', 'д']:
        create_ticket_structure(tickets)
        print("Структура создана успешно!")
        print(f"Папки и файлы ограничены 30 символами (без учета номера и расширения)")
    else:
        print("Создание отменено")


if __name__ == "__main__":
    main()