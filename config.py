import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot settings - load from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # Get this from @BotFather
API_TOKEN = BOT_TOKEN  # Alias for consistency

# OpenAI API settings - load from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT", "")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "")

# Database settings (if you need them in future)
DB_HOST = "localhost"
DB_NAME = "database_name"
DB_USER = "user"
DB_PASS = "password"

# Other settings
ADMIN_IDS = [  # List of admin user IDs
    123456789,
    987654321
]

# Debug mode
DEBUG = False

# Custom settings
HAN_ID = 631573859
CHANNEL_ID = -1001180087578
HAN_USER_ID = HAN_ID
MAX_SCORE = 245

# File settings
GROUPS_FILE = 'groups.txt'

# Bot and group settings
OWNER_ID = 631573859
GROUP_ID = -1001932954655
DATA_FILE = 'schedule.json'

SCANNER_WEBAPP_URL = "https://example.com/scanner"
QUIZ_WEBAPP_BASE_URL = "https://hanbiike.github.io/ort-bot/"

"""
Configuration settings for the ORT broadcaster system.
"""

# File paths and directories
GRADES_FILE = "biology.json"
TEMP_LATEX_DIR = Path("temp_latex")
OUTPUT_DIR = Path("output")

TASK_CREATION_INTERVAL = 300

# LaTeX compilation settings
LATEX_COMPILER = "pdflatex"
LATEX_OPTIONS = [
    "-interaction=nonstopmode",
    "-halt-on-error",
    "-file-line-error"
]

# Multiple compilation passes for better PDF generation
LATEX_COMPILE_PASSES = 2

# PDF to PNG conversion settings
DEFAULT_DPI = 300
PNG_QUALITY = 95
PNG_OPTIMIZE = True

COUNTER_FILE = "threads/counter.json"

LOGGING_GROUP = {
    "chat_id": -1002542011959,
    "path": "threads/logs.json"
}

SUBJECT_GROUPS = {
    "Математика ОРТ": -1002040877762,
    "Химия": -1002002915357,
    "Биология": -1003015910302
}

THREADS_FILES = {
    "Математика ОРТ": "threads/math.json",
    "Химия": "threads/chemistry.json",
    "Биология": "threads/biology.json"
}

# Файлы с предметами
SUBJECT_FILES = {
    "Математика ОРТ": "subjects/math.json",
    "Химия": "subjects/chemistry.json",
    "Биология": "subjects/biology.json"
}

# Типы задач по предметам
SUBJECT_TASK_TYPES = {
    "Математика ОРТ": ["COMPARISON", "ABCDE"],
    "Химия": ["ABCDE"],
    "Биология": ["ABCDE"]
}

# Стили задач по предметам
SUBJECT_TASK_STYLES = {
    "Математика ОРТ": ["Строгий", "Прикладной", "Сюжетный", "Максимальная креативность"],
    "Химия": ["Строгий"],
    "Биология": ["Строгий"]
}

SUBJECT_PROMPTS = {
    "Математика ОРТ": {
        "COMPARISON": """
Ты — генератор тестовых заданий для подготовки к Общереспубликанскому тестированию (ОРТ) в Кыргызстане, который похож на SAT. 
Сгенерируй ОДНУ задачу в формате теста, содержащий две величины, которые нужно сравнить. В тесте 4 варианта ответа: А - больше, Б - меньше, В - равно, Г - недостаточно данных.

Правила:
1. Тест не должен выходить за рамки школьной программы. 
2. Формулы пиши в LaTeX и оборачивай в $...$, в дробях кроме степеней всегда используй \dfrac{}{}, проценты - \%, используй символы только из utf-8.
3. Формат ответа строго такой:
[Условие задачи (опционально)]
[Величина А (короткий текст)]
[Величина Б (короткий текст)]
А) >  
Б) <  
В) =  
Г) недостаточно данных  
Правильный ответ: [буква]
4. Если формула общеизвестна, то не нужно писать ее.
5. Вопрос не должен дополнительно напоминать, что величины нужно сравнивать. Не пиши "Сравните величины", "Условие задачи:", "Величина А:", "Величина Б:".

Пример с вопросом:  
N - количество ребер в четырехугольной призме
N
10
А) >  
Б) <  
В) =  
Г) недостаточно данных   
Правильный ответ: А

Пример без вопроса:
2(c + 2)
2c
А) >  
Б) <  
В) =  
Г) недостаточно данных   
Правильный ответ: А
            """,

        "ABCDE": """
Ты — генератор тестовых заданий для подготовки к Общереспубликанскому тестированию (ОРТ) в Кыргызстане, который похож на SAT. 
Сгенерируй ОДНУ задачу в формате теста. В тесте 5 вариантов ответа: А, Б, В, Г, Д, где лишь один вариант правильный.

Правила:
1. Тест не должен выходить за рамки школьной программы. 
2. Формулы пиши в LaTeX и оборачивай в $...$, в дробях кроме степеней всегда используй \dfrac{}{}, проценты - \%, используй символы только из utf-8.
3. Формат ответа строго такой:
[Условие задачи]
А) [текст и/или выражение]
Б) [текст и/или выражение]
В) [текст и/или выражение]
Г) [текст и/или выражение]
Д) [текст и/или выражение]
Правильный ответ: [буква]
4. Если формула общеизвестна, то не нужно писать ее.
5. Вопрос не должен дополнительно напоминать, что нужно выбрать правильный ответ.

Пример:  
Сколько ребер в четырехугольной призме?
А) В призме нет ребер
Б) 8
В) 12
Г) 16
Д) недостаточно данных
Правильный ответ: В
            """
    },
    "Химия": {
        "ABCDE": """
Ты — генератор тестовых заданий для подготовки к Общереспубликанскому тестированию (ОРТ) в Кыргызстане, который похож на SAT. 
Сгенерируй ОДНУ задачу в формате теста. В тесте 5 вариантов ответа: А, Б, В, Г, Д, где лишь один вариант правильный.

Правила:
1. Тест не должен выходить за рамки школьной программы. 
2. Формулы пиши в LaTeX и оборачивай в $...$, в дробях кроме степеней всегда используй \dfrac{}{}, проценты - \%, используй символы только из utf-8.
3. Формат ответа строго такой:
[Условие задачи]
А) [текст и/или выражение]
Б) [текст и/или выражение]
В) [текст и/или выражение]
Г) [текст и/или выражение]
Д) [текст и/или выражение]
Правильный ответ: [буква]
4. Если формула общеизвестна, то не нужно писать ее.
5. Вопрос не должен дополнительно напоминать, что нужно выбрать правильный ответ.

Пример:  
Сколько ребер в четырехугольной призме?
А) В призме нет ребер
Б) 8
В) 12
Г) 16
Д) недостаточно данных
Правильный ответ: В
                
Какие задания НЕ ВКЛЮЧАЮТСЯ в тест по химии?
Задания на проверку знаний и определение терминов. Например: «Гибридизация – это...»
Задания на простое припоминание фактов. Например: «Кем был открыт закон...», или «Сколько электронов содержит атом аргона?»
            """                
    },
    "Биология": {
        "ABCDE": """
Ты — генератор тестовых заданий для подготовки к Общереспубликанскому тестированию (ОРТ) в Кыргызстане, который похож на SAT. 
Сгенерируй ОДНУ задачу в формате теста. В тесте 5 вариантов ответа: А, Б, В, Г, Д, где лишь один вариант правильный.

Правила:
1. Тест не должен выходить за рамки школьной программы. 
2. Формулы пиши в LaTeX и оборачивай в $...$, в дробях кроме степеней всегда используй \dfrac{}{}, проценты - \%, используй символы только из utf-8.
3. Формат ответа строго такой:
[Условие задачи]
А) [текст и/или выражение]
Б) [текст и/или выражение]
В) [текст и/или выражение]
Г) [текст и/или выражение]
Д) [текст и/или выражение]
Правильный ответ: [буква]
4. Если формула общеизвестна, то не нужно писать ее.
5. Вопрос не должен дополнительно напоминать, что нужно выбрать правильный ответ.

Пример:  
Сколько ребер в четырехугольной призме?
А) В призме нет ребер
Б) 8
В) 12
Г) 16
Д) недостаточно данных
Правильный ответ: В
                
Какие задания НЕ ВКЛЮЧАЮТСЯ в тест по химии?
Задания, требующие простого воспроизведения материала, типа: «Кем был открыт биогенетический закон?» или «Сколько ребер у человека?»
        """
    }
}

DEFAULT_DIFFICULTY_RANGE = (1, 10)


# OpenAI API settings
OPENAI_MODEL = "gpt-5"
OPENAI_MAX_TOKENS = 2000
OPENAI_TEMPERATURE = 0.7

# LaTeX document settings
LATEX_DOCUMENT_CLASS = "stand"
LATEX_OPTIONS_MAP = {
    "COMPARISON": "\\shownumbering",
    "ABCDE": "\\shownumbering"
}

# File extensions
SUPPORTED_OUTPUT_FORMATS = ["pdf", "png"]

# Error messages
ERROR_MESSAGES = {
    "pdf2image_missing": "pdf2image не установлен. Установите: pip install pdf2image pillow",
    "latex_missing": "pdflatex не найден. Установите LaTeX дистрибутив",
    "file_not_found": "Файл не найден: {path}",
    "compilation_failed": "Ошибка компиляции LaTeX",
    "conversion_failed": "Ошибка конвертации PDF в PNG",
    "invalid_pdf": "PDF файл поврежден или некорректен"
}

# Success messages  
SUCCESS_MESSAGES = {
    "pdf_created": "✅ PDF успешно создан: {path}",
    "png_created": "✅ PNG версия создана: {path}",
    "task_generated": "🎉 Задача типа {task_type} успешно создана!",
    "conversion_complete": "✅ Конвертировано {count} страниц в PNG"
}

def get_temp_dir() -> Path:
    """
    Get temporary directory path, creating it if necessary.
    
    Returns:
        Path: Temporary directory path
    """
    TEMP_LATEX_DIR.mkdir(exist_ok=True)
    return TEMP_LATEX_DIR

def get_output_dir() -> Path:
    """
    Get output directory path, creating it if necessary.
    
    Returns:
        Path: Output directory path
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


