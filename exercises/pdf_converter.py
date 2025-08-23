"""
PDF to PNG conversion utilities.

This module provides functions to convert PDF files to PNG images
using the pdf2image library, which is a Python wrapper for poppler.
"""

from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import os
import subprocess
import sys
import asyncio

try:
    from pdf2image import convert_from_path
    from PIL import Image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# Add missing import
import config


class PDFConversionError(Exception):
    """Custom exception for PDF conversion errors."""
    pass


def install_pdf2image() -> bool:
    """
    Install pdf2image library and provide setup instructions.
    
    pdf2image requires poppler-utils to be installed on the system.
    This function provides installation instructions for different platforms.
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    print("Устанавливаю pdf2image...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 'pdf2image', 'pillow'
        ])
        print("✅ pdf2image успешно установлен!")
        
        # Provide platform-specific poppler installation instructions
        print("\n📋 Дополнительно требуется установить poppler:")
        print("На macOS: brew install poppler")
        print("На Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("На Windows: скачайте poppler с официального сайта")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки: {e}")
        return False


async def convert_pdf_to_png(
    pdf_path: str, 
    output_dir: Optional[str] = None,
    dpi: int = 500,
    output_format: str = 'PNG',
    page_numbers: Optional[List[int]] = None
) -> List[str]:
    """
    Convert PDF file to PNG images.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_dir (Optional[str]): Directory for output PNG files. 
                                   If None, uses same directory as PDF
        dpi (int): Resolution for output images (default: 300)
        output_format (str): Output image format (default: 'PNG')
        page_numbers (Optional[List[int]]): Specific pages to convert.
                                          If None, converts all pages
    
    Returns:
        List[str]: List of paths to generated PNG files
        
    Raises:
        PDFConversionError: If conversion fails
        FileNotFoundError: If PDF file doesn't exist
    """
    if not PDF2IMAGE_AVAILABLE:
        raise PDFConversionError(
            "pdf2image не установлен. "
            "Установите: pip install pdf2image pillow"
        )
    
    # Validate input file
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF файл не найден: {pdf_path}")
    
    # Set output directory
    if output_dir is None:
        output_dir = pdf_file.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run conversion in executor to avoid blocking
        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(
            None,
            lambda: convert_from_path(pdf_path, dpi=dpi) if not page_numbers
            else convert_from_path(
                pdf_path, 
                dpi=dpi, 
                first_page=min(page_numbers),
                last_page=max(page_numbers)
            )
        )
        
        # Filter to requested pages if needed
        if page_numbers and len(images) > 1:
            images = [
                img for i, img in enumerate(images, start=min(page_numbers) if page_numbers else 1)
                if i in page_numbers
            ]
        
        # Save images as PNG files
        output_files = []
        base_name = pdf_file.stem
        
        for i, image in enumerate(images):
            if page_numbers:
                page_num = page_numbers[i]
            else:
                page_num = i + 1
                
            output_filename = f"{base_name}_page_{page_num:03d}.png"
            output_path = output_dir / output_filename
            
            # Save with high quality in executor
            await loop.run_in_executor(
                None,
                lambda: image.save(output_path, output_format, optimize=True, quality=95)
            )
            output_files.append(str(output_path))
            
        print(f"✅ Конвертировано {len(images)} страниц в PNG")
        return output_files
        
    except Exception as e:
        raise PDFConversionError(f"Ошибка конвертации: {e}")


async def validate_pdf_file(pdf_path: str) -> bool:
    """
    Validate if PDF file is readable and not corrupted.
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        bool: True if PDF is valid, False otherwise
    """
    try:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return False
            
        # Check file size - empty or very small files are likely corrupted
        if pdf_file.stat().st_size < 1024:  # Less than 1KB
            print(f"⚠️ PDF файл слишком мал: {pdf_file.stat().st_size} байт")
            return False
            
        # Try to read PDF header asynchronously
        loop = asyncio.get_event_loop()
        header = await loop.run_in_executor(
            None,
            lambda: open(pdf_path, 'rb').read(8)
        )
        
        if not header.startswith(b'%PDF-'):
            print("⚠️ PDF файл не имеет корректного заголовка")
            return False
                
        return True
        
    except Exception as e:
        print(f"⚠️ Ошибка валидации PDF: {e}")
        return False


async def convert_pdf_single_image(
    pdf_path: str,
    output_path: Optional[str] = None,
    dpi: int = None,
    combine_pages: bool = False
) -> str:
    """
    Convert PDF to a single PNG image.
    
    Args:
        pdf_path (str): Path to input PDF file
        output_path (Optional[str]): Path for output PNG file
        dpi (int): Resolution for output image
        combine_pages (bool): If True and PDF has multiple pages,
                             combine them vertically into one image
    
    Returns:
        str: Path to generated PNG file
        
    Raises:
        PDFConversionError: If conversion fails
        FileNotFoundError: If PDF file doesn't exist
    """
    if not PDF2IMAGE_AVAILABLE:
        raise PDFConversionError("pdf2image не установлен")
    
    if dpi is None:
        dpi = config.DEFAULT_DPI
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF файл не найден: {pdf_path}")
    
    # Validate PDF file before conversion
    if not await validate_pdf_file(pdf_path):
        raise PDFConversionError(f"PDF файл поврежден или некорректен: {pdf_path}")
    
    # Set default output path
    if output_path is None:
        output_path = pdf_file.with_suffix('.png')
    
    try:
        # Add timeout and error handling for pdf2image
        print(f"🔄 Конвертирую PDF в PNG (DPI: {dpi})...")
        
        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(
            None,
            lambda: convert_from_path(
                pdf_path, 
                dpi=dpi,
                fmt='png',
                thread_count=1,  # Use single thread for stability
                timeout=30       # 30 second timeout
            )
        )
        
        if not images:
            raise PDFConversionError("Не удалось извлечь страницы из PDF")
        
        if len(images) == 1 or not combine_pages:
            # Save first page only
            await loop.run_in_executor(
                None,
                lambda: images[0].save(output_path, 'PNG', optimize=config.PNG_OPTIMIZE, quality=config.PNG_QUALITY)
            )
            
        else:
            # Combine multiple pages vertically
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)
            
            combined_image = Image.new('RGB', (max_width, total_height), 'white')
            
            y_offset = 0
            for img in images:
                # Center image horizontally if needed
                x_offset = (max_width - img.width) // 2
                combined_image.paste(img, (x_offset, y_offset))
                y_offset += img.height
            
            await loop.run_in_executor(
                None,
                lambda: combined_image.save(output_path, 'PNG', optimize=config.PNG_OPTIMIZE, quality=config.PNG_QUALITY)
            )
        
        print(f"✅ PDF конвертирован в PNG: {output_path}")
        return str(output_path)
        
    except Exception as e:
        # More detailed error information
        error_msg = f"Ошибка конвертации: {e}"
        if "Unable to get page count" in str(e):
            error_msg += "\n💡 Возможно PDF файл поврежден. Проверьте компиляцию LaTeX."
        raise PDFConversionError(error_msg)


async def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
    """
    Get information about PDF file.
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        Dict[str, Any]: PDF information including page count
    """
    if not PDF2IMAGE_AVAILABLE:
        return {"error": "pdf2image не установлен"}
    
    try:
        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(
            None,
            lambda: convert_from_path(pdf_path, dpi=72)  # Low DPI for info only
        )
        return {
            "page_count": len(images),
            "file_size": os.path.getsize(pdf_path),
            "file_name": Path(pdf_path).name
        }
    except Exception as e:
        return {"error": str(e)}


# Example usage and testing
if __name__ == "__main__":
    if not PDF2IMAGE_AVAILABLE:
        print("pdf2image не установлен. Запускаю установку...")
        install_pdf2image()
    else:
        # Example: Convert a PDF to PNG
        pdf_file = "temp_latex/comparison_task.pdf"
        
        if Path(pdf_file).exists():
            try:
                # Convert all pages
                png_files = convert_pdf_to_png(pdf_file, dpi=300)
                print(f"Созданы файлы: {png_files}")
                
                # Or convert to single image
                single_png = convert_pdf_single_image(pdf_file, dpi=300)
                print(f"Создан файл: {single_png}")
                
            except (PDFConversionError, FileNotFoundError) as e:
                print(f"Ошибка: {e}")
        else:
            print(f"PDF файл не найден: {pdf_file}")
