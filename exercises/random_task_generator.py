#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор случайных задач по разным предметам
Выбирает случайным образом: subject, domain, topic, subtopic, сложность и тип задачи
"""

import json
import random
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import asyncio
import aiofiles
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
        
        self.domains_data = None
        
        # Настройки типов задач и стилей для каждого предмета
        self.task_types = config.SUBJECT_TASK_TYPES.get(subject, [])
        self.task_styles = config.SUBJECT_TASK_STYLES.get(subject, [])
        if not self.task_types or not self.task_styles:
            raise TaskGeneratorError(f"Не заданы task types или styles для предмета {subject}")
    
    async def _load_domains_data(self) -> Union[Dict[str, Any], List[Any]]:
        """Загрузка данных о доменах и темах из JSON файла"""
        domains_path = Path(self.domains_file)
        
        try:
            async with aiofiles.open(domains_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                if not data:
                    raise TaskGeneratorError("Файл с данными пуст")
                return data
                
        except FileNotFoundError:
            raise TaskGeneratorError(f"Файл не найден: {self.domains_file}")
        except json.JSONDecodeError as e:
            raise TaskGeneratorError(f"Некорректный JSON в {self.domains_file}: {e}")
    
    def _normalize_data_structure(self, data: Union[Dict[str, Any], List[Any]]) -> Dict[str, Dict[str, List[str]]]:
        """
        Нормализация структуры данных к ожидаемому формату.
        
        Args:
            data: Данные из JSON файла (могут быть списком или словарем)
            
        Returns:
            Dict[str, Dict[str, List[str]]]: Нормализованная структура данных
        """
        if isinstance(data, list):
            # Если данные - это список тем/подтем, создаем простую структуру
            normalized = {"Общие темы": {}}
            for item in data:
                if isinstance(item, str):
                    normalized["Общие темы"][item] = [item]  # Тема совпадает с подтемой
                elif isinstance(item, dict):
                    # Если элемент - словарь, извлекаем ключи и значения
                    for key, value in item.items():
                        if isinstance(value, list):
                            normalized["Общие темы"][key] = value
                        else:
                            normalized["Общие темы"][key] = [str(value)]
            return normalized
            
        elif isinstance(data, dict):
            # Проверяем, что структура соответствует ожидаемой
            normalized = {}
            for domain_key, domain_value in data.items():
                if isinstance(domain_value, dict):
                    # Структура domain -> topic -> subtopics
                    normalized[domain_key] = {}
                    for topic_key, topic_value in domain_value.items():
                        if isinstance(topic_value, list):
                            normalized[domain_key][topic_key] = topic_value
                        else:
                            # Если не список, преобразуем в список
                            normalized[domain_key][topic_key] = [str(topic_value)]
                elif isinstance(domain_value, list):
                    # Структура domain -> list of topics/subtopics
                    normalized[domain_key] = {}
                    for item in domain_value:
                        if isinstance(item, str):
                            normalized[domain_key][item] = [item]
                        elif isinstance(item, dict):
                            normalized[domain_key].update(item)
                else:
                    # Простое значение
                    normalized[domain_key] = {"Общее": [str(domain_value)]}
            return normalized
        else:
            raise TaskGeneratorError(f"Неожиданный тип данных: {type(data)}")
    
    async def initialize(self) -> None:
        """Асинхронная инициализация - загрузка данных из файла"""
        raw_data = await self._load_domains_data()
        self.domains_data = self._normalize_data_structure(raw_data)
    
    def get_available_domains(self) -> List[str]:
        """
        Получить список всех доступных доменов.
        
        Returns:
            List[str]: Список названий доменов
            
        Raises:
            TaskGeneratorError: Если данные не загружены
        """
        if not self.domains_data:
            raise TaskGeneratorError("Данные не загружены. Вызовите initialize() сначала.")
        return list(self.domains_data.keys())
    
    def get_available_topics(self, domain: str) -> List[str]:
        """
        Получить список доступных тем для домена.
        
        Args:
            domain (str): Название домена
            
        Returns:
            List[str]: Список тем
        """
        domain_data = self.domains_data.get(domain, {})
        return list(domain_data.keys())
    
    def get_available_subtopics(self, domain: str, topic: str) -> List[str]:
        """
        Получить список доступных подтем для темы в домене.
        
        Args:
            domain (str): Название домена
            topic (str): Название темы
            
        Returns:
            List[str]: Список подтем
        """
        return self.domains_data.get(domain, {}).get(topic, [])
    
    def get_random_domain(self) -> str:
        """Получить случайный домен."""
        domains = self.get_available_domains()
        if not domains:
            raise TaskGeneratorError("Нет доступных доменов")
        return random.choice(domains)
    
    def get_random_topic(self, domain: str) -> str:
        """Получить случайную тему для указанного домена."""
        topics = self.get_available_topics(domain)
        if not topics:
            raise TaskGeneratorError(f"Нет доступных тем для домена {domain}")
        return random.choice(topics)
    
    def get_random_subtopic(self, domain: str, topic: str) -> str:
        """Получить случайную подтему для указанной темы и домена."""
        subtopics = self.get_available_subtopics(domain, topic)
        if not subtopics:
            raise TaskGeneratorError(f"Нет доступных подтем для {domain}, {topic}")
        return random.choice(subtopics)
    
    def get_random_difficulty(self, min_difficulty: Optional[int] = None, 
                            max_difficulty: Optional[int] = None) -> str:
        """Получить случайный уровень сложности."""
        difficulty_levels = ["Легкая", "Средняя", "Сложная"]
        return random.choice(difficulty_levels)
    
    def get_random_task_type(self, task_types: Optional[List[str]] = None) -> str:
        """Получить случайный тип задачи."""
        types = task_types or self.task_types
        if not types:
            raise TaskGeneratorError("Список типов задач пуст")
        return random.choice(types)

    def get_random_task_style(self, task_styles: Optional[List[str]] = None) -> str:
        """Получить случайный стиль задачи."""
        styles = task_styles or self.task_styles
        if not styles:
            raise TaskGeneratorError("Список стилей задач пуст")
        return random.choice(styles)

    async def generate_random_task(self,
                                 task_types: Optional[List[str]] = None,
                                 min_difficulty: Optional[int] = None,
                                 max_difficulty: Optional[int] = None) -> Dict[str, Any]:
        """
        Генерация случайной задачи.
        
        Args:
            task_types: Список допустимых типов задач (по умолчанию все)
            min_difficulty: Минимальная сложность (не используется)
            max_difficulty: Максимальная сложность (не используется)
            
        Returns:
            Dict[str, Any]: Словарь с параметрами сгенерированной задачи
        """
        if not self.domains_data:
            await self.initialize()
            
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
            "prompt": f"""
                    Предмет: {self.subject}
                    Тема: {topic}
                    Подтема: {subtopic}
                    Сложность: {difficulty}
                    Тип задачи: {task_type}
                    Стиль задачи: {task_style}
                    """,
            "caption": f"""Тема: {topic} - {subtopic}\nСложность: {difficulty}"""
        }
