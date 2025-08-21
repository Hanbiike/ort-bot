"""
LaTeX compilation utilities for mathematical task generation.

This module handles LaTeX document creation and compilation to PDF format,
with optional PNG conversion through the pdf_converter module.
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import config
import time

# Import PDF conversion functionality
try:
    from pdf_converter import convert_pdf_single_image, PDFConversionError
    PDF_CONVERSION_AVAILABLE = True
except ImportError:
    PDF_CONVERSION_AVAILABLE = False


class LaTeXCompilationError(Exception):
    """Custom exception for LaTeX compilation errors."""
    pass


def compile_latex(latex_content: str, output_name: str = "output") -> bool:
    """
    Компилирует LaTeX документ в PDF.
    
    Args:
        latex_content (str): Содержимое LaTeX документа
        output_name (str): Имя выходного файла без расширения
    
    Returns:
        bool: True если компиляция успешна, False иначе
        
    Raises:
        LaTeXCompilationError: If compilation fails
    """
    # Создаем временную директорию для компиляции
    temp_dir = config.get_temp_dir()
    
    # Путь к файлам (используем абсолютные пути)
    tex_file = temp_dir / f"{output_name}.tex"
    pdf_file = temp_dir / f"{output_name}.pdf"
    log_file = temp_dir / f"{output_name}.log"
    aux_file = temp_dir / f"{output_name}.aux"
    
    try:
        # Удаляем старые файлы
        for old_file in [pdf_file, log_file, aux_file]:
            if old_file.exists():
                old_file.unlink()
        
        # Записываем LaTeX содержимое в файл
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"🔄 Компилирую LaTeX документ: {tex_file}")
        
        # Проверяем что файл действительно создан
        if not tex_file.exists():
            raise LaTeXCompilationError(f"Не удалось создать файл {tex_file}")
        
        print(f"📝 LaTeX файл создан: {tex_file} ({tex_file.stat().st_size} байт)")
        
        # Компилируем PDF несколько раз для корректного создания ссылок
        success = False
        for attempt in range(config.LATEX_COMPILE_PASSES):
            print(f"   Попытка {attempt + 1}/{config.LATEX_COMPILE_PASSES}")
            
            # Используем абсолютные пути и правильную рабочую директорию
            cmd = [
                config.LATEX_COMPILER,
                *config.LATEX_OPTIONS,
                "-output-directory", str(temp_dir.resolve()),
                str(tex_file.resolve())  # Абсолютный путь к .tex файлу
            ]
            
            print(f"   Команда: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=60,  # 60 second timeout
                cwd=str(temp_dir.resolve())  # Рабочая директория - temp_latex
            )
            
            if result.returncode == 0:
                success = True
                print(f"   ✅ Компиляция успешна на попытке {attempt + 1}")
                # Даем время системе завершить запись файла
                time.sleep(0.5)
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
                    
                    # Also try to read log file for more details
                    if log_file.exists():
                        try:
                            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                log_content = f.read()
                                print(f"LaTeX Log (последние 1000 символов):\n{log_content[-1000:]}")
                        except Exception as log_error:
                            print(f"Не удалось прочитать лог: {log_error}")
                    
                    raise LaTeXCompilationError(error_msg)
        
        if success and pdf_file.exists():
            # Проверяем размер PDF файла
            file_size = pdf_file.stat().st_size
            print(f"📄 PDF файл создан: {pdf_file} ({file_size} байт)")
            
            if file_size < 1024:  # Less than 1KB
                raise LaTeXCompilationError("PDF файл слишком мал - возможна ошибка компиляции")
            
            print(config.SUCCESS_MESSAGES["pdf_created"].format(path=pdf_file))
            return True
        else:
            raise LaTeXCompilationError("PDF файл не был создан после успешной компиляции")
            
    except subprocess.TimeoutExpired:
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


def compile_latex_to_png(
    latex_content: str, 
    output_name: str = "output",
    dpi: int = None
) -> Optional[str]:
    """
    Компилирует LaTeX документ напрямую в PNG.
    
    Args:
        latex_content (str): Содержимое LaTeX документа
        output_name (str): Имя выходного файла без расширения
        dpi (int): Разрешение для PNG изображения
    
    Returns:
        Optional[str]: Путь к PNG файлу если успешно, None иначе
        
    Raises:
        LaTeXCompilationError: If compilation or conversion fails
    """
    if not PDF_CONVERSION_AVAILABLE:
        error_msg = config.ERROR_MESSAGES["pdf2image_missing"]
        print(f"❌ {error_msg}")
        raise LaTeXCompilationError(error_msg)
    
    if dpi is None:
        dpi = config.DEFAULT_DPI
    
    # Сначала компилируем в PDF
    try:
        if compile_latex(latex_content, output_name):
            temp_dir = config.get_temp_dir()
            pdf_file = temp_dir / f"{output_name}.pdf"
            
            # Ждем немного чтобы файл был полностью записан
            time.sleep(1)
            
            # Проверяем что PDF файл существует и валиден
            if not pdf_file.exists():
                raise LaTeXCompilationError("PDF файл не найден после компиляции")
            
            # Конвертируем PDF в PNG
            png_path = convert_pdf_single_image(
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


def create_full_latex_document(content: str, task_type: str) -> str:
    """
    Создает полный LaTeX документ с использованием класса stand.cls.
    
    Args:
        content (str): Содержимое задачи
        task_type (str): Тип задачи (COMPARISON или ABCDE)
    
    Returns:
        str: Полный LaTeX документ
    """
    document_options = config.LATEX_OPTIONS_MAP.get(task_type, "")
    
    document = f"""\\documentclass{{{config.LATEX_DOCUMENT_CLASS}}}
{document_options}

\\begin{{document}}

{content}

\\end{{document}}"""
    
    return document


def validate_latex_installation() -> bool:
    """
    Check if LaTeX is properly installed and available.
    
    Returns:
        bool: True if LaTeX is available, False otherwise
    """
    try:
        result = subprocess.run(
            [config.LATEX_COMPILER, "--version"], 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_compilation_log(output_name: str) -> Optional[str]:
    """
    Get LaTeX compilation log for debugging.
    
    Args:
        output_name (str): Name of the output file
        
    Returns:
        Optional[str]: Log content if available, None otherwise
    """
    temp_dir = config.get_temp_dir()
    log_file = temp_dir / f"{output_name}.log"
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None