"""
OpenAI API integration for generating LaTeX tasks.

This module handles the generation of mathematical tasks using OpenAI's API
and converts them to both PDF and PNG formats for the ORT broadcaster system.
"""

from typing import Optional, Dict, Any, List, Literal
from openai import AsyncAzureOpenAI
from pydantic import BaseModel
import config
from exercises.random_task_generator import TaskGenerator, TaskGeneratorError
from exercises.latex import compile_latex, compile_latex_to_png, create_full_latex_document, LaTeXCompilationError
from exercises.pdf_converter import convert_pdf_single_image, PDFConversionError


class TaskGenerationError(Exception):
    """Custom exception for task generation errors."""
    pass


class Comparison(BaseModel):
    """Model for comparison tasks between two quantities."""
    question: Optional[str]
    column_A: str
    column_B: str
    correct_answer: Literal["А", "Б", "В", "Г"]


class ABCDE(BaseModel):
    """Model for multiple choice tasks with five answer options."""
    question: str
    answer_A: str
    answer_B: str
    answer_C: str
    answer_D: str
    answer_E: str
    correct_answer: Literal["А", "Б", "В", "Г", "Д"]


class TaskAPIClient:
    """Client for OpenAI API task generation."""

    def __init__(self, subject: str, api_key: str):
        """
        Initialize the API client.
        
        Args:
            api_key (str): OpenAI API key
        """
        self.client = AsyncAzureOpenAI(azure_deployment=config.AZURE_DEPLOYMENT, api_version=config.AZURE_API_VERSION, azure_endpoint=config.AZURE_ENDPOINT, api_key=api_key)
        self.generator = TaskGenerator(subject=subject)
    
    async def generate_comparison_task(self, task: Dict[str, Any]) -> Comparison:
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
            response = await self.client.responses.parse(
                model=config.AZURE_DEPLOYMENT,
                instructions=task["instruction"],
                input=task["prompt"],
                text_format=Comparison,
                #top_p=0.9
                #temperature=2
            )
            return response.output_parsed
            
        except Exception as e:
            raise TaskGenerationError(f"Ошибка генерации COMPARISON задачи: {e}")
    
    async def generate_abcde_task(self, task: Dict[str, Any]) -> ABCDE:
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
            response = await self.client.responses.parse(
                model=config.AZURE_DEPLOYMENT,
                instructions=task["instruction"],
                input=task["prompt"],
                text_format=ABCDE,
                #top_p=0.9
                #temperature=2
            )
            return response.output_parsed
            
        except Exception as e:
            raise TaskGenerationError(f"Ошибка генерации ABCDE задачи: {e}")


async def generate_task_images(
    subject: str,
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
        "task_meta": None,
        "task_topic": None,
        "files": {},
        "success": False
    }

    try:
        # Initialize components
        api_client = TaskAPIClient(subject=subject, api_key=api_key)
        await api_client.generator.initialize()  # Асинхронная инициализация
        task = await api_client.generator.generate_random_task()
        result["task_type"] = task["type"]
        result["task_meta"] = task["caption"]
        result["task_topic"] = task["topic"]

        if task["type"] == "COMPARISON":
            result.update(await _generate_comparison_task(subject=subject, api_client=api_client, task=task, output_formats=output_formats, dpi=dpi))
        elif task["type"] == "ABCDE":
            result.update(await _generate_abcde_task(subject=subject, api_client=api_client, task=task, output_formats=output_formats, dpi=dpi))
        else:
            raise TaskGenerationError(f"Неподдерживаемый тип задачи: {task['type']}")
            
    except (TaskGeneratorError, TaskGenerationError, LaTeXCompilationError) as e:
        result["error"] = str(e)
        print(f"❌ {e}")
    except Exception as e:
        error_msg = f"Неожиданная ошибка генерации задачи: {e}"
        result["error"] = error_msg
        print(f"❌ {error_msg}")
    
    return result


async def _generate_comparison_task(
    subject: str,
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
    parsed_data = await api_client.generate_comparison_task(task)
    latex_content = rf"\comparison[{parsed_data.question}]{{{parsed_data.column_A}}}{{{parsed_data.column_B}}}"
    
    # Create full document
    full_document = create_full_latex_document(subject=subject, content=latex_content, task_type="COMPARISON")

    # Generate outputs
    files = await _generate_output_files(full_document, "comparison_task", output_formats, dpi)
    
    return {
        "task_data": parsed_data.model_dump(),
        "files": files,
        "success": bool(files),
        "latex_content": latex_content,
        "right_answer": parsed_data.correct_answer
    }


async def _generate_abcde_task(
    subject: str,
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
    parsed_data = await api_client.generate_abcde_task(task)
    latex_content = (rf"\ABCDE[{parsed_data.question}]"
                    rf"{{{parsed_data.answer_A}}}{{{parsed_data.answer_B}}}"
                    rf"{{{parsed_data.answer_C}}}{{{parsed_data.answer_D}}}"
                    rf"{{{parsed_data.answer_E}}}")

    # Create full document
    full_document = create_full_latex_document(subject=subject, content=latex_content, task_type="ABCDE")

    # Generate outputs
    files = await _generate_output_files(full_document, "abcde_task", output_formats, dpi)
    
    return {
        "task_data": parsed_data.model_dump(),
        "files": files,
        "success": bool(files),
        "latex_content": latex_content,
        "right_answer": parsed_data.correct_answer
    }


async def _generate_output_files(
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
        if await compile_latex(full_document, output_name):
            pdf_path = str(temp_dir / f"{output_name}.pdf")
            
            if "pdf" in output_formats:
                files["pdf"] = pdf_path
            
            # If PNG is requested, convert the PDF
            if "png" in output_formats:
                try:
                    png_path = await convert_pdf_single_image(
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
    api_key = config.AZURE_OPENAI_API_KEY
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