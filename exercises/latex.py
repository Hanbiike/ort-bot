"""
LaTeX compilation utilities for mathematical task generation.

This module handles LaTeX document creation and compilation to PDF format,
with optional PNG conversion through the pdf_converter module.
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio
import aiofiles
import config
import time
import json

# Import PDF conversion functionality
try:
    from pdf_converter import convert_pdf_single_image, PDFConversionError
    PDF_CONVERSION_AVAILABLE = True
except ImportError:
    PDF_CONVERSION_AVAILABLE = False

def _load_counter() -> dict:
    """Загрузить JSON с счетчиком для тем (threads/counter.json)."""
    file_path = Path(config.COUNTER_FILE)
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    return {}

def _save_counter(data: dict) -> None:
    """Сохранить JSON с счетчиком для тем (threads/counter.json)."""
    file_path = Path(config.COUNTER_FILE)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class LaTeXCompilationError(Exception):
    """Custom exception for LaTeX compilation errors."""
    pass


async def compile_latex(latex_content: str, output_name: str = "output") -> bool:
    """
    Асинхронно компилирует LaTeX документ в PDF.
    
    Функция создает временный .tex файл, компилирует его в PDF используя
    LaTeX компилятор, и проверяет успешность создания выходного файла.
    Поддерживает множественную компиляцию для корректного создания ссылок.
    
    Args:
        latex_content (str): Содержимое LaTeX документа для компиляции
        output_name (str): Имя выходного файла без расширения (по умолчанию "output")
    
    Returns:
        bool: True если компиляция успешна, False иначе
        
    Raises:
        LaTeXCompilationError: Если компиляция не удалась по любой причине
        
    Example:
        >>> content = "\\documentclass{article}\\begin{document}Hello\\end{document}"
        >>> success = await compile_latex(content, "test_document")
        >>> print(success)  # True if compilation successful
    """
    # Создаем временную директорию для компиляции
    temp_dir = config.get_temp_dir()
    
    # Определяем пути к файлам (используем абсолютные пути для надежности)
    tex_file = temp_dir / f"{output_name}.tex"
    pdf_file = temp_dir / f"{output_name}.pdf"
    log_file = temp_dir / f"{output_name}.log"
    aux_file = temp_dir / f"{output_name}.aux"
    
    try:
        # Удаляем старые файлы для избежания конфликтов
        for old_file in [pdf_file, log_file, aux_file]:
            if old_file.exists():
                old_file.unlink()
        
        # Записываем LaTeX содержимое в файл асинхронно с UTF-8 кодировкой
        async with aiofiles.open(tex_file, 'w', encoding='utf-8', errors='replace') as f:
            await f.write(latex_content)
        
        print(f"🔄 Компилирую LaTeX документ: {tex_file}")
        
        # Проверяем что файл действительно создан
        if not tex_file.exists():
            raise LaTeXCompilationError(f"Не удалось создать файл {tex_file}")
        
        print(f"📝 LaTeX файл создан: {tex_file} ({tex_file.stat().st_size} байт)")
        
        # Получаем текущий event loop для выполнения subprocess в executor
        loop = asyncio.get_event_loop()
        
        # Компилируем PDF несколько раз для корректного создания ссылок и референсов
        success = False
        for attempt in range(config.LATEX_COMPILE_PASSES):
            print(f"   Попытка {attempt + 1}/{config.LATEX_COMPILE_PASSES}")
            
            # Формируем команду компиляции с абсолютными путями
            cmd = [
                config.LATEX_COMPILER,
                *config.LATEX_OPTIONS,
                "-output-directory", str(temp_dir.resolve()),
                str(tex_file.resolve())  # Абсолютный путь к .tex файлу
            ]
            
            print(f"   Команда: {' '.join(cmd)}")
            
            # Запускаем компиляцию асинхронно в executor для избежания блокировки
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=60,  # 60 second timeout для предотвращения зависания
                    cwd=str(temp_dir.resolve())  # Рабочая директория - temp_latex
                )
            )
            
            if result.returncode == 0:
                success = True
                print(f"   ✅ Компиляция успешна на попытке {attempt + 1}")
                # Даем время системе завершить запись файла
                await asyncio.sleep(0.5)
                break
            else:
                print(f"   ⚠️ Ошибка на попытке {attempt + 1}")
                print(f"   Return code: {result.returncode}")
                print(f"   STDOUT: {result.stdout[:500]}...")  # First 500 chars
                print(f"   STDERR: {result.stderr[:500]}...")  # First 500 chars
                
                if attempt == config.LATEX_COMPILE_PASSES - 1:  # Last attempt
                    error_msg = f"❌ {config.ERROR_MESSAGES['compilation_failed']}:\n"
                    error_msg += f"STDOUT: {result.stdout}\n"
                    error_msg += f"STDERR: {result.stderr}"
                    print(error_msg)
                    
                    # Пытаемся прочитать лог файл для дополнительной диагностики
                    if log_file.exists():
                        try:
                            async with aiofiles.open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                                log_content = await f.read()
                                print(f"LaTeX Log (последние 1000 символов):\n{log_content[-1000:]}")
                        except Exception as log_error:
                            print(f"Не удалось прочитать лог: {log_error}")
                    
                    raise LaTeXCompilationError(error_msg)
        
        # Проверяем результат компиляции
        if success and pdf_file.exists():
            # Проверяем размер PDF файла для выявления потенциальных проблем
            file_size = pdf_file.stat().st_size
            print(f"📄 PDF файл создан: {pdf_file} ({file_size} байт)")
            
            if file_size < 1024:  # Файлы меньше 1KB вероятно повреждены
                raise LaTeXCompilationError("PDF файл слишком мал - возможна ошибка компиляции")
            
            print(config.SUCCESS_MESSAGES["pdf_created"].format(path=pdf_file))
            return True
        else:
            raise LaTeXCompilationError("PDF файл не был создан после успешной компиляции")
            
    except asyncio.TimeoutError:
        error_msg = "Тайм-аут компиляции LaTeX"
        print(f"❌ {error_msg}")
        raise LaTeXCompilationError(error_msg)
    except FileNotFoundError as e:
        error_msg = f"{config.ERROR_MESSAGES['latex_missing']} - {e}"
        print(f"❌ {error_msg}")
        raise LaTeXCompilationError(error_msg)
    except Exception as e:
        error_msg = f"Ошибка компиляции: {e}"
        print(f"❌ {error_msg}")
        raise LaTeXCompilationError(error_msg)


async def compile_latex_to_png(
    latex_content: str, 
    output_name: str = "output",
    dpi: int = None
) -> Optional[str]:
    """
    Асинхронно компилирует LaTeX документ напрямую в PNG.
    
    Функция сначала компилирует LaTeX в PDF, затем конвертирует результат
    в PNG изображение с заданным разрешением. Используется для создания
    изображений математических задач.
    
    Args:
        latex_content (str): Содержимое LaTeX документа
        output_name (str): Имя выходного файла без расширения
        dpi (int): Разрешение для PNG изображения (по умолчанию из config.DEFAULT_DPI)
    
    Returns:
        Optional[str]: Путь к PNG файлу если успешно, None иначе
        
    Raises:
        LaTeXCompilationError: Если компиляция или конвертация не удалась
        
    Example:
        >>> content = "\\documentclass{article}\\begin{document}$x^2$\\end{document}"
        >>> png_path = await compile_latex_to_png(content, "math_task", dpi=300)
        >>> print(f"PNG created: {png_path}")
    """
    if not PDF_CONVERSION_AVAILABLE:
        error_msg = config.ERROR_MESSAGES["pdf2image_missing"]
        print(f"❌ {error_msg}")
        raise LaTeXCompilationError(error_msg)
    
    if dpi is None:
        dpi = config.DEFAULT_DPI
    
    # Сначала компилируем в PDF
    try:
        if await compile_latex(latex_content, output_name):
            temp_dir = config.get_temp_dir()
            pdf_file = temp_dir / f"{output_name}.pdf"
            
            # Ждем немного чтобы файл был полностью записан на диск
            await asyncio.sleep(1)
            
            # Проверяем что PDF файл существует и доступен
            if not pdf_file.exists():
                raise LaTeXCompilationError("PDF файл не найден после компиляции")
            
            # Конвертируем PDF в PNG асинхронно
            png_path = await convert_pdf_single_image(
                str(pdf_file),
                str(pdf_file.with_suffix('.png')),
                dpi=dpi
            )
            return png_path
            
    except PDFConversionError as e:
        error_msg = f"{config.ERROR_MESSAGES['conversion_failed']}: {e}"
        print(f"❌ {error_msg}")
        raise LaTeXCompilationError(error_msg)
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {e}"
        print(f"❌ {error_msg}")
        raise LaTeXCompilationError(error_msg)
    
    return None


def create_full_latex_document(subject: str, content: str, task_type: str) -> str:
    """
    Создает полный LaTeX документ с использованием класса stand.cls.
    
    Функция обертывает содержимое задачи в полноценный LaTeX документ
    с правильными опциями класса в зависимости от типа задачи.
    
    Args:
        content (str): Содержимое задачи (LaTeX команды)
        task_type (str): Тип задачи (COMPARISON или ABCDE)
    
    Returns:
        str: Полный LaTeX документ готовый к компиляции
        
    Example:
        >>> content = "\\ABCDE[What is 2+2?]{2}{3}{4}{5}{6}"
        >>> doc = create_full_latex_document(content, "ABCDE")
        >>> print(doc.startswith("\\documentclass"))  # True
    """
    document_options = config.LATEX_OPTIONS_MAP.get(task_type, "")
    counter = _load_counter()

    document = f"""\\documentclass{{{config.LATEX_DOCUMENT_CLASS}}}
{document_options}

\\begin{{document}}
\\setcounter{{comparisoncounter}}{{{counter[subject] if subject in counter else 0}}}
{content}

\\end{{document}}"""
    counter[subject] = counter.get(subject, 0) + 1
    _save_counter(counter)
    return document


async def validate_latex_installation() -> bool:
    """
    Асинхронно проверяет, что LaTeX установлен и доступен.
    
    Функция запускает LaTeX компилятор с флагом --version для
    проверки его доступности в системе.
    
    Returns:
        bool: True если LaTeX доступен, False иначе
        
    Example:
        >>> is_available = await validate_latex_installation()
        >>> if is_available:
        ...     print("LaTeX ready to use")
        ... else:
        ...     print("LaTeX not found")
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                [config.LATEX_COMPILER, "--version"], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10  # Quick timeout for version check
            )
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


async def get_compilation_log(output_name: str) -> Optional[str]:
    """
    Асинхронно получает лог компиляции LaTeX для отладки.
    
    Функция читает .log файл созданный LaTeX компилятором для
    диагностики ошибок компиляции.
    
    Args:
        output_name (str): Имя выходного файла (без расширения)
        
    Returns:
        Optional[str]: Содержимое лог файла если доступно, None иначе
        
    Example:
        >>> log_content = await get_compilation_log("my_document")
        >>> if log_content:
        ...     print("Compilation errors found in log")
    """
    temp_dir = config.get_temp_dir()
    log_file = temp_dir / f"{output_name}.log"
    
    try:
        async with aiofiles.open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            return await f.read()
    except FileNotFoundError:
        return None


async def cleanup_temp_files(output_name: str, keep_pdf: bool = True) -> None:
    """
    Асинхронно очищает временные файлы после компиляции.
    
    Удаляет вспомогательные файлы (.aux, .log, .toc и т.д.)
    созданные во время компиляции LaTeX, оставляя только нужные файлы.
    
    Args:
        output_name (str): Имя выходного файла (без расширения)
        keep_pdf (bool): Сохранить ли PDF файл (по умолчанию True)
        
    Example:
        >>> await cleanup_temp_files("my_document", keep_pdf=False)
        >>> # Removes all temporary files including PDF
    """
    temp_dir = config.get_temp_dir()
    
    # Список расширений временных файлов LaTeX
    temp_extensions = ['.aux', '.log', '.toc', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
    
    if not keep_pdf:
        temp_extensions.append('.pdf')
    
    # Удаляем каждый временный файл если он существует
    for ext in temp_extensions:
        temp_file = temp_dir / f"{output_name}{ext}"
        if temp_file.exists():
            try:
                temp_file.unlink()
                print(f"🗑️ Удален временный файл: {temp_file}")
            except OSError as e:
                print(f"⚠️ Не удалось удалить {temp_file}: {e}")