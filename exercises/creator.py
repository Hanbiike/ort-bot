from api import *
import config

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