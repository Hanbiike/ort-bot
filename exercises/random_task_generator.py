#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор случайных задач по разным предметам
Выбирает случайным образом: subject, domain, topic, subtopic, сложность и тип задачи
"""

import json
import random
from typing import Dict, List, Any, Optional
from pathlib import Path
import config


class TaskGeneratorError(Exception):
    """Custom exception for task generation errors."""
    pass


class TaskGenerator:
    """Генератор случайных задач по предметам"""
    
    def __init__(self, subject: str, domains_file: Optional[str] = None):
        """
        Инициализация генератора
        
        Args:
            subject (str): предмет (например: 'math', 'chemistry', 'biology')
            domains_file: путь к файлу с данными о доменах и темах
        """
        self.subject = subject
        self.domains_file = domains_file or config.SUBJECT_FILES.get(subject)
        if not self.domains_file:
            raise TaskGeneratorError(f"Нет JSON файла для предмета: {subject}")
        
        self.domains_data = self._load_domains_data()
        
        # Настройки типов задач и стилей для каждого предмета
        self.task_types = config.SUBJECT_TASK_TYPES.get(subject, [])
        self.task_styles = config.SUBJECT_TASK_STYLES.get(subject, [])
        if not self.task_types or not self.task_styles:
            raise TaskGeneratorError(f"Не заданы task types или styles для предмета {subject}")
    
    def _load_domains_data(self) -> Dict[str, Any]:
        """Загрузка данных о доменах и темах из JSON файла"""
        domains_path = Path(self.domains_file)
        
        try:
            with open(domains_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    raise TaskGeneratorError("Файл с данными пуст")
                return data
                
        except FileNotFoundError:
            raise TaskGeneratorError(f"Файл не найден: {self.domains_file}")
        except json.JSONDecodeError as e:
            raise TaskGeneratorError(f"Некорректный JSON в {self.domains_file}: {e}")
    
    def get_available_domains(self) -> List[str]:
        return list(self.domains_data.keys())
    
    def get_available_topics(self, domain: str) -> List[str]:
        return list(self.domains_data.get(domain, {}).keys())
    
    def get_available_subtopics(self, domain: str, topic: str) -> List[str]:
        return self.domains_data.get(domain, {}).get(topic, [])
    
    def get_random_domain(self) -> str:
        domains = self.get_available_domains()
        if not domains:
            raise TaskGeneratorError("Нет доступных доменов")
        return random.choice(domains)
    
    def get_random_topic(self, domain: str) -> str:
        topics = self.get_available_topics(domain)
        if not topics:
            raise TaskGeneratorError(f"Нет доступных тем для домена {domain}")
        return random.choice(topics)
    
    def get_random_subtopic(self, domain: str, topic: str) -> str:
        subtopics = self.get_available_subtopics(domain, topic)
        if not subtopics:
            raise TaskGeneratorError(f"Нет доступных подтем для {domain}, {topic}")
        return random.choice(subtopics)
    
    def get_random_difficulty(self, min_difficulty: Optional[int] = None, max_difficulty: Optional[int] = None) -> str:
        difficulty_levels = ["Легкая", "Средняя", "Сложная"]
        return random.choice(difficulty_levels)
    
    def get_random_task_type(self, task_types: Optional[List[str]] = None) -> str:
        types = task_types or self.task_types
        if not types:
            raise TaskGeneratorError("Список типов задач пуст")
        return random.choice(types)

    def get_random_task_style(self, task_styles: Optional[List[str]] = None) -> str:
        styles = task_styles or self.task_styles
        if not styles:
            raise TaskGeneratorError("Список стилей задач пуст")
        return random.choice(styles)

    def generate_random_task(self,
                             task_types: Optional[List[str]] = None,
                             min_difficulty: Optional[int] = None,
                             max_difficulty: Optional[int] = None) -> Dict[str, Any]:
        """Генерация случайной задачи"""
        domain = self.get_random_domain()
        topic = self.get_random_topic(domain)
        subtopic = self.get_random_subtopic(domain, topic)
        difficulty = self.get_random_difficulty(min_difficulty, max_difficulty)
        task_type = self.get_random_task_type(task_types)
        task_style = self.get_random_task_style()

        return {
            "subject": self.subject,
            "domain": domain,
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "type": task_type,
            "style": task_style,
            "instruction": config.SUBJECT_PROMPTS[self.subject]["ABCDE"] if self.subject != "Математика ОРТ" else config.SUBJECT_PROMPTS["Математика ОРТ"][task_type],
            "prompt" : f"""
                    Предмет: {self.subject}
                    Тема: {topic}
                    Подтема: {subtopic}
                    Сложность: {difficulty}
                    Тип задачи: {task_type}
                    Стиль задачи: {task_style}
                    """,
            "caption": f"Тема: {topic} - {subtopic}, сложность {difficulty}"
        }
