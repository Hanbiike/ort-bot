"""
OpenAI API integration for generating LaTeX tasks.

This module handles the generation of mathematical tasks using OpenAI's API
and converts them to both PDF and PNG formats for the ORT broadcaster system.
"""

from typing import Optional, Dict, Any, List
from openai import OpenAI
from pydantic import BaseModel
import config
from random_task_generator import TaskGenerator, TaskGeneratorError
from latex import compile_latex, compile_latex_to_png, create_full_latex_document, LaTeXCompilationError
from pdf_converter import convert_pdf_single_image, PDFConversionError


class TaskGenerationError(Exception):
    """Custom exception for task generation errors."""
    pass


class Comparison(BaseModel):
    """Model for comparison tasks between two quantities."""
    question: str
    column_A: str
    column_B: str
    correct_answer: str


class ABCDE(BaseModel):
    """Model for multiple choice tasks with five answer options."""
    question: str
    answer_A: str
    answer_B: str
    answer_C: str
    answer_D: str
    answer_E: str
    correct_answer: str


class TaskAPIClient:
    """Client for OpenAI API task generation."""
    
    def __init__(self, api_key: str):
        """
        Initialize the API client.
        
        Args:
            api_key (str): OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.generator = TaskGenerator()
    
    def generate_comparison_task(self, task: Dict[str, Any]) -> Comparison:
        """
        Generate a comparison task using OpenAI API.
        
        Args:
            task (Dict[str, Any]): Task configuration
            
        Returns:
            Comparison: Generated comparison task
            
        Raises:
            TaskGenerationError: If API call fails
        """
        try:
            response = self.client.responses.parse(
                model=config.OPENAI_MODEL,
                instructions="""Создай задачу, содержащую две величины, которые нужно сравнить.
                Варианты ответа: >, <, =, недостаточно данных
                Формулы пиши в LaTeX и оборачивай в $...$ в дробях кроме степеней всегда используй \dfrac{}{}.""",
                input=self.generator.get_text(task),
                text_format=Comparison
            )
            return response.output_parsed
            
        except Exception as e:
            raise TaskGenerationError(f"Ошибка генерации COMPARISON задачи: {e}")
    
    def generate_abcde_task(self, task: Dict[str, Any]) -> ABCDE:
        """
        Generate an ABCDE multiple choice task using OpenAI API.
        
        Args:
            task (Dict[str, Any]): Task configuration
            
        Returns:
            ABCDE: Generated ABCDE task
            
        Raises:
            TaskGenerationError: If API call fails
        """
        try:
            response = self.client.responses.parse(
                model=config.OPENAI_MODEL,
                instructions="""Создай задачу с 5 вариантами ответа.
                Формулы пиши в LaTeX и оборачивай в $...$ в дробях кроме степеней всегда используй \dfrac{}{}.""",
                input=self.generator.get_text(task),
                text_format=ABCDE
            )
            return response.output_parsed
            
        except Exception as e:
            raise TaskGenerationError(f"Ошибка генерации ABCDE задачи: {e}")


def generate_task_images(
    api_key: str,
    output_formats: List[str] = None,
    dpi: int = None
) -> Dict[str, Any]:
    """
    Generate mathematical tasks and export in specified formats.
    
    Args:
        api_key (str): OpenAI API key
        output_formats (List[str]): List of formats to generate ('pdf', 'png')
        dpi (int): Resolution for PNG output
        
    Returns:
        Dict[str, Any]: Results including file paths and task data
        
    Raises:
        TaskGenerationError: If task generation fails
    """
    if output_formats is None:
        output_formats = config.SUPPORTED_OUTPUT_FORMATS.copy()
    if dpi is None:
        dpi = config.DEFAULT_DPI
    
    # Validate output formats
    for fmt in output_formats:
        if fmt not in config.SUPPORTED_OUTPUT_FORMATS:
            raise TaskGenerationError(f"Неподдерживаемый формат: {fmt}")
    
    result = {
        "task_type": None,
        "task_data": None,
        "files": {},
        "success": False
    }
    
    try:
        # Initialize components
        api_client = TaskAPIClient(api_key)
        task = api_client.generator.generate_random_task()
        result["task_type"] = task["тип_задачи"]
        
        if task["тип_задачи"] == "COMPARISON":
            result.update(_generate_comparison_task(api_client, task, output_formats, dpi))
        elif task["тип_задачи"] == "ABCDE":
            result.update(_generate_abcde_task(api_client, task, output_formats, dpi))
        else:
            raise TaskGenerationError(f"Неподдерживаемый тип задачи: {task['тип_задачи']}")
            
    except (TaskGeneratorError, TaskGenerationError, LaTeXCompilationError) as e:
        result["error"] = str(e)
        print(f"❌ {e}")
    except Exception as e:
        error_msg = f"Неожиданная ошибка генерации задачи: {e}"
        result["error"] = error_msg
        print(f"❌ {error_msg}")
    
    return result


def _generate_comparison_task(
    api_client: TaskAPIClient,
    task: Dict[str, Any],
    output_formats: List[str],
    dpi: int
) -> Dict[str, Any]:
    """
    Generate a comparison task with specified output formats.
    
    Args:
        api_client (TaskAPIClient): API client instance
        task (Dict[str, Any]): Task configuration
        output_formats (List[str]): Desired output formats
        dpi (int): PNG resolution
        
    Returns:
        Dict[str, Any]: Generation results
    """
    # Generate task content
    parsed_data = api_client.generate_comparison_task(task)
    latex_content = f"\\comparison[{parsed_data.question}]{{{parsed_data.column_A}}}{{{parsed_data.column_B}}}"
    
    # Create full document
    full_document = create_full_latex_document(latex_content, "COMPARISON")
    
    # Generate outputs
    files = _generate_output_files(full_document, "comparison_task", output_formats, dpi)
    
    return {
        "task_data": parsed_data.model_dump(),
        "files": files,
        "success": bool(files),
        "latex_content": latex_content
    }


def _generate_abcde_task(
    api_client: TaskAPIClient,
    task: Dict[str, Any],
    output_formats: List[str],
    dpi: int
) -> Dict[str, Any]:
    """
    Generate an ABCDE multiple choice task with specified output formats.
    
    Args:
        api_client (TaskAPIClient): API client instance
        task (Dict[str, Any]): Task configuration
        output_formats (List[str]): Desired output formats
        dpi (int): PNG resolution
        
    Returns:
        Dict[str, Any]: Generation results
    """
    # Generate task content
    parsed_data = api_client.generate_abcde_task(task)
    latex_content = (f"\\ABCDE[{parsed_data.question}]"
                    f"{{{parsed_data.answer_A}}}{{{parsed_data.answer_B}}}"
                    f"{{{parsed_data.answer_C}}}{{{parsed_data.answer_D}}}"
                    f"{{{parsed_data.answer_E}}}")
    
    # Create full document
    full_document = create_full_latex_document(latex_content, "ABCDE")
    
    # Generate outputs
    files = _generate_output_files(full_document, "abcde_task", output_formats, dpi)
    
    return {
        "task_data": parsed_data.model_dump(),
        "files": files,
        "success": bool(files),
        "latex_content": latex_content
    }


def _generate_output_files(
    full_document: str,
    output_name: str,
    output_formats: List[str],
    dpi: int
) -> Dict[str, str]:
    """
    Generate output files in specified formats.
    
    Args:
        full_document (str): Complete LaTeX document
        output_name (str): Base name for output files
        output_formats (List[str]): Desired output formats
        dpi (int): PNG resolution
        
    Returns:
        Dict[str, str]: Mapping of format to file path
        
    Raises:
        LaTeXCompilationError: If file generation fails
    """
    files = {}
    temp_dir = config.get_temp_dir()
    
    # First, always compile to PDF
    try:
        if compile_latex(full_document, output_name):
            pdf_path = str(temp_dir / f"{output_name}.pdf")
            
            if "pdf" in output_formats:
                files["pdf"] = pdf_path
            
            # If PNG is requested, convert the PDF
            if "png" in output_formats:
                try:
                    png_path = convert_pdf_single_image(
                        pdf_path,
                        str(temp_dir / f"{output_name}.png"),
                        dpi=dpi
                    )
                    if png_path:
                        files["png"] = png_path
                        print(config.SUCCESS_MESSAGES["png_created"].format(path=png_path))
                except PDFConversionError as e:
                    print(f"⚠️ Не удалось создать PNG версию: {e}")
                    # Don't fail completely, just skip PNG
                    pass
    except LaTeXCompilationError:
        # Re-raise compilation errors
        raise
    
    return files


# Main execution
if __name__ == "__main__":
    # Example usage with API key from environment or config
    api_key = config.OPENAI_API_KEY
    try:
        # Generate task in both PDF and PNG formats
        result = generate_task_images(
            api_key=api_key,
            output_formats=["pdf", "png"], 
            dpi=300
        )
        
        if result["success"]:
            print(config.SUCCESS_MESSAGES["task_generated"].format(task_type=result['task_type']))
            for format_type, file_path in result["files"].items():
                print(f"📄 {format_type.upper()}: {file_path}")
        else:
            print("❌ Не удалось создать задачу")
            if "error" in result:
                print(f"Ошибка: {result['error']}")
                
    except TaskGenerationError as e:
        print(f"❌ Ошибка генерации: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")