#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор случайных математических задач
Выбирает случайным образом: класс, тему, подтему, сложность и тип задачи
"""

import json
import random
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import config


class TaskGeneratorError(Exception):
    """Custom exception for task generation errors."""
    pass


class TaskGenerator:
    """Генератор случайных математических задач"""
    
    def __init__(self, grades_file: Optional[str] = None):
        """
        Инициализация генератора
        
        Args:
            grades_file: путь к файлу с данными о классах и темах
        """
        self.grades_file = grades_file or config.GRADES_FILE
        self.grades_data = self._load_grades_data()
        
        # Типы задач по умолчанию (можно изменить через параметры)
        self.default_task_types = config.DEFAULT_TASK_TYPES.copy()
    
    def _load_grades_data(self) -> Dict[str, Any]:
        """
        Загрузка данных о классах и темах из JSON файла
        
        Returns:
            Dict[str, Any]: Данные о классах и темах
            
        Raises:
            TaskGeneratorError: If file loading fails
        """
        grades_path = Path(self.grades_file)
        
        try:
            with open(grades_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    raise TaskGeneratorError("Файл с данными о классах пуст")
                return data
                
        except FileNotFoundError:
            error_msg = config.ERROR_MESSAGES["file_not_found"].format(path=self.grades_file)
            print(f"❌ {error_msg}")
            raise TaskGeneratorError(error_msg)
            
        except json.JSONDecodeError as e:
            error_msg = f"Некорректный JSON в файле {self.grades_file}: {e}"
            print(f"❌ {error_msg}")
            raise TaskGeneratorError(error_msg)
    
    def get_available_grades(self) -> List[str]:
        """
        Получить список доступных классов
        
        Returns:
            List[str]: Список названий классов
        """
        return list(self.grades_data.keys())
    
    def get_available_topics(self, grade: str) -> List[str]:
        """
        Получить список доступных тем для класса
        
        Args:
            grade (str): Название класса
            
        Returns:
            List[str]: Список названий тем
        """
        return list(self.grades_data.get(grade, {}).keys())
    
    def get_available_subtopics(self, grade: str, topic: str) -> List[str]:
        """
        Получить список доступных подтем для класса и темы
        
        Args:
            grade (str): Название класса
            topic (str): Название темы
            
        Returns:
            List[str]: Список названий подтем
        """
        return self.grades_data.get(grade, {}).get(topic, [])
    
    def get_random_grade(self) -> str:
        """
        Случайный выбор класса
        
        Returns:
            str: Название класса
            
        Raises:
            TaskGeneratorError: If no grades available
        """
        available_grades = self.get_available_grades()
        if not available_grades:
            raise TaskGeneratorError("Нет доступных классов")
        return random.choice(available_grades)
    
    def get_random_topic(self, grade: str) -> str:
        """
        Случайный выбор темы для данного класса
        
        Args:
            grade (str): Название класса
            
        Returns:
            str: Название темы
            
        Raises:
            TaskGeneratorError: If no topics available for grade
        """
        available_topics = self.get_available_topics(grade)
        if not available_topics:
            raise TaskGeneratorError(f"Нет доступных тем для класса {grade}")
        return random.choice(available_topics)
    
    def get_random_subtopic(self, grade: str, topic: str) -> str:
        """
        Случайный выбор подтемы для данного класса и темы
        
        Args:
            grade (str): Название класса
            topic (str): Название темы
            
        Returns:
            str: Название подтемы
            
        Raises:
            TaskGeneratorError: If no subtopics available
        """
        available_subtopics = self.get_available_subtopics(grade, topic)
        if not available_subtopics:
            raise TaskGeneratorError(f"Нет доступных подтем для {grade}, {topic}")
        return random.choice(available_subtopics)
    
    def get_random_difficulty(self, min_difficulty: int = None, max_difficulty: int = None) -> int:
        """
        Случайный выбор сложности от min_difficulty до max_difficulty включительно
        
        Args:
            min_difficulty (int): Минимальная сложность
            max_difficulty (int): Максимальная сложность
            
        Returns:
            int: Уровень сложности
        """
        if min_difficulty is None:
            min_difficulty = config.DEFAULT_DIFFICULTY_RANGE[0]
        if max_difficulty is None:
            max_difficulty = config.DEFAULT_DIFFICULTY_RANGE[1]
            
        return random.randint(min_difficulty, max_difficulty)
    
    def get_random_task_type(self, task_types: Optional[List[str]] = None) -> str:
        """
        Случайный выбор типа задачи из предоставленного списка
        
        Args:
            task_types (Optional[List[str]]): Список типов задач
            
        Returns:
            str: Тип задачи
        """
        if task_types is None:
            task_types = self.default_task_types
        if not task_types:
            raise TaskGeneratorError("Список типов задач пуст")
        return random.choice(task_types)
    
    def generate_random_task(self, 
                           task_types: Optional[List[str]] = None, 
                           min_difficulty: Optional[int] = None, 
                           max_difficulty: Optional[int] = None) -> Dict[str, Any]:
        """
        Генерация случайной задачи
        
        Args:
            task_types: список типов задач для выбора
            min_difficulty: минимальная сложность
            max_difficulty: максимальная сложность
            
        Returns:
            Dict[str, Any]: Словарь с параметрами задачи
            
        Raises:
            TaskGeneratorError: If task generation fails
        """
        try:
            # 1. Случайно выбираем класс
            grade = self.get_random_grade()
            
            # 2. Случайно выбираем тему
            topic = self.get_random_topic(grade)
            
            # 3. Случайно выбираем подтему
            subtopic = self.get_random_subtopic(grade, topic)
            
            # 4. Случайно выбираем сложность
            difficulty = self.get_random_difficulty(min_difficulty, max_difficulty)
            
            # 5. Случайно выбираем тип задачи
            task_type = self.get_random_task_type(task_types)
            
            return {
                "класс": grade,
                "тема": topic,
                "подтема": subtopic,
                "сложность": difficulty,
                "тип_задачи": task_type
            }
            
        except TaskGeneratorError:
            raise
        except Exception as e:
            raise TaskGeneratorError(f"Ошибка генерации задачи: {e}")
    
    def print_task(self, task_data: Dict[str, Any]) -> None:
        """
        Красивый вывод информации о задаче
        
        Args:
            task_data (Dict[str, Any]): Данные задачи
        """
        if "error" in task_data:
            print(f"❌ {task_data['error']}")
            return
        
        print("🎲 Случайно сгенерированная задача:")
        print("=" * 50)
        print(f"📚 Класс:      {task_data['класс']}")
        print(f"📖 Тема:       {task_data['тема']}")
        print(f"📝 Подтема:    {task_data['подтема']}")
        print(f"⭐ Сложность:  {task_data['сложность']}/10")
        print(f"🔨 Тип задачи: {task_data['тип_задачи']}")
        print("=" * 50)

    def get_text(self, task_data: Dict[str, Any]) -> str:
        """
        Получение текстового представления задачи
        
        Args:
            task_data (Dict[str, Any]): Данные задачи
            
        Returns:
            str: Текстовое представление задачи
        """
        if "error" in task_data:
            return f"❌ {task_data['error']}"
        
        lines = [
            f"📚 Класс:      {task_data['класс']}",
            f"📖 Тема:       {task_data['тема']}",
            f"📝 Подтема:    {task_data['подтема']}",
            f"⭐ Сложность:  {task_data['сложность']}/10"
        ]
        return "\n".join(lines)


def main() -> None:
    """Главная функция - демонстрация работы генератора"""
    
    print("🎯 Генератор случайных математических задач")
    print()
    
    try:
        # Создаем экземпляр генератора
        generator = TaskGenerator()
        
        # Пример 1: Генерация с типами задач по умолчанию
        print("📋 Пример 1: Генерация с типами задач по умолчанию")
        task = generator.generate_random_task()
        generator.print_task(task)
        print()
        
        # Пример 2: Генерация с пользовательскими типами задач
        print("📋 Пример 2: Генерация с пользовательскими типами задач")
        custom_task_types = [
            "Контрольная работа",
            "Самостоятельная работа", 
            "Домашнее задание",
            "Олимпиадная задача",
            "ЕГЭ задача"
        ]
        task = generator.generate_random_task(task_types=custom_task_types)
        generator.print_task(task)
        print()
        
        # Пример 3: Генерация с ограничением сложности
        print("📋 Пример 3: Генерация с ограниченной сложностью (3-7)")
        task = generator.generate_random_task(min_difficulty=3, max_difficulty=7)
        generator.print_task(task)
        print()
        
        # Интерактивный режим
        print("🎮 Интерактивный режим (нажмите Enter для генерации новой задачи, 'q' для выхода)")
        while True:
            user_input = input("\nНажмите Enter для генерации новой задачи (или 'q' для выхода): ").strip()
            if user_input.lower() == 'q':
                print("👋 До свидания!")
                break
            
            task = generator.generate_random_task()
            print()
            generator.print_task(task)
    
    except TaskGeneratorError as e:
        print(f"❌ Ошибка инициализации генератора: {e}")
        return
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return


if __name__ == "__main__":
    main()
