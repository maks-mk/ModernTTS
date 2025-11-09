"""
Модуль валидации для TTS приложения.
Содержит все функции проверки данных.
"""

import re
from typing import Tuple, Optional
from config import AppConfig


class ValidationResult:
    """Результат валидации."""
    
    def __init__(self, is_valid: bool, message: str = ""):
        self.is_valid = is_valid
        self.message = message
    
    def __bool__(self) -> bool:
        return self.is_valid


class Validator:
    """Класс для валидации различных данных."""
    
    @staticmethod
    def validate_text(text: str) -> ValidationResult:
        """Валидирует входной текст для TTS."""
        if not text or not text.strip():
            return ValidationResult(False, "Текст не может быть пустым")
        
        text_length = len(text.strip())
        
        if text_length > AppConfig.MAX_TEXT_LENGTH:
            return ValidationResult(
                False, 
                f"Текст слишком длинный. Максимум {AppConfig.MAX_TEXT_LENGTH} символов, "
                f"введено {text_length}"
            )
        
        # Проверка на подозрительные символы. Разрешаем буквы, цифры, пробелы и основные знаки препинания,
        # а также символы, необходимые для тегов голоса: [], : /
        if re.search(r'[^/\w\s\.,!?;:\-\(\)\"\'«»\n\r\[\]]', text, re.UNICODE):
            return ValidationResult(
                False,
                "Текст содержит недопустимые символы. Используйте только буквы, цифры и знаки препинания."
            )
        
        return ValidationResult(True, "Текст корректен")
    
    @staticmethod
    def validate_voice(voice_name: str) -> ValidationResult:
        """Валидирует имя голоса."""
        if not voice_name:
            return ValidationResult(False, "Голос не выбран")
        
        if voice_name not in AppConfig.VOICES:
            return ValidationResult(
                False, 
                f"Неподдерживаемый голос: {voice_name}. "
                f"Доступные голоса: {', '.join(AppConfig.VOICES[:5])}..."
            )
        
        return ValidationResult(True, f"Голос {voice_name} поддерживается")
    
    @staticmethod
    def validate_api_key(api_key: str) -> ValidationResult:
        """Валидирует API ключ."""
        if not api_key:
            return ValidationResult(False, "API ключ не может быть пустым")
        
        api_key = api_key.strip()
        
        if len(api_key) < AppConfig.MIN_API_KEY_LENGTH:
            return ValidationResult(
                False,
                f"API ключ слишком короткий. Минимум {AppConfig.MIN_API_KEY_LENGTH} символов, "
                f"введено {len(api_key)}"
            )
        
        # Базовая проверка формата Google API ключа
        if not api_key.startswith('AIza'):
            return ValidationResult(
                False,
                "API ключ должен начинаться с 'AIza'. Проверьте правильность ключа."
            )
        
        # Проверка на допустимые символы
        if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
            return ValidationResult(
                False,
                "API ключ содержит недопустимые символы. "
                "Используйте только буквы, цифры, дефисы и подчеркивания."
            )
        
        return ValidationResult(True, "API ключ корректен")
    
    @staticmethod
    def validate_file_path(file_path: str, allowed_extensions: list = None) -> ValidationResult:
        """Валидирует путь к файлу."""
        if not file_path:
            return ValidationResult(False, "Путь к файлу не указан")
        
        if allowed_extensions:
            file_extension = file_path.lower().split('.')[-1]
            if file_extension not in [ext.lower().lstrip('.') for ext in allowed_extensions]:
                return ValidationResult(
                    False,
                    f"Неподдерживаемый формат файла. "
                    f"Разрешенные форматы: {', '.join(allowed_extensions)}"
                )
        
        # Проверка на недопустимые символы в имени файла
        import os
        filename = os.path.basename(file_path)
        if re.search(r'[<>:"|?*]', filename):
            return ValidationResult(
                False,
                "Имя файла содержит недопустимые символы: < > : \" | ? *"
            )
        
        return ValidationResult(True, "Путь к файлу корректен")
    
    @staticmethod
    def validate_theme(theme: str) -> ValidationResult:
        """Валидирует тему оформления."""
        if not theme:
            return ValidationResult(False, "Тема не указана")
        
        if theme not in AppConfig.AVAILABLE_THEMES:
            return ValidationResult(
                False,
                f"Неподдерживаемая тема: {theme}. "
                f"Доступные темы: {', '.join(AppConfig.AVAILABLE_THEMES)}"
            )
        
        return ValidationResult(True, f"Тема {theme} поддерживается")
    
    @staticmethod
    def validate_audio_format(format_name: str) -> ValidationResult:
        """Валидирует формат аудио."""
        supported_formats = ['wav', 'mp3']
        
        if not format_name:
            return ValidationResult(False, "Формат аудио не указан")
        
        format_name = format_name.lower().lstrip('.')
        
        if format_name not in supported_formats:
            return ValidationResult(
                False,
                f"Неподдерживаемый формат аудио: {format_name}. "
                f"Поддерживаемые форматы: {', '.join(supported_formats)}"
            )
        
        return ValidationResult(True, f"Формат {format_name} поддерживается")
    
    @staticmethod
    def get_text_length_status(text: str) -> Tuple[str, str]:
        """Возвращает статус длины текста и соответствующий цвет."""
        if not text:
            return "Текст пустой", AppConfig.Colors.DARK_TEXT_MUTED
        
        length = len(text)
        
        if length > AppConfig.MAX_TEXT_LENGTH:
            return f"Превышен лимит: {length}/{AppConfig.MAX_TEXT_LENGTH}", AppConfig.Colors.DANGER
        elif length > AppConfig.TEXT_WARNING_LENGTH:
            return f"Близко к лимиту: {length}/{AppConfig.MAX_TEXT_LENGTH}", AppConfig.Colors.WARNING
        else:
            return f"Символов: {length}", AppConfig.Colors.DARK_TEXT_MUTED
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Очищает имя файла от недопустимых символов."""
        # Удаляем недопустимые символы
        sanitized = re.sub(r'[<>:"|?*]', '_', filename)
        
        # Удаляем множественные пробелы и подчеркивания
        sanitized = re.sub(r'[_\s]+', '_', sanitized)
        
        # Убираем подчеркивания в начале и конце
        sanitized = sanitized.strip('_')
        
        # Если имя стало пустым, используем значение по умолчанию
        if not sanitized:
            sanitized = "audio_file"
        
        return sanitized
    
    @staticmethod
    def validate_window_geometry(x: int, y: int, width: int, height: int) -> ValidationResult:
        """Валидирует геометрию окна."""
        if width < AppConfig.MIN_WINDOW_WIDTH or height < AppConfig.MIN_WINDOW_HEIGHT:
            return ValidationResult(
                False,
                f"Размер окна слишком мал. Минимум: "
                f"{AppConfig.MIN_WINDOW_WIDTH}x{AppConfig.MIN_WINDOW_HEIGHT}"
            )
        
        # Проверяем, что окно не выходит за пределы экрана (базовая проверка)
        if x < -width or y < -height:
            return ValidationResult(
                False,
                "Окно находится за пределами экрана"
            )
        
        return ValidationResult(True, "Геометрия окна корректна")


class TextValidator:
    """Специализированный валидатор для текста."""
    
    @staticmethod
    def check_encoding(text: str) -> ValidationResult:
        """Проверяет кодировку текста."""
        try:
            # Пытаемся закодировать в UTF-8
            text.encode('utf-8')
            return ValidationResult(True, "Кодировка корректна")
        except UnicodeEncodeError as e:
            return ValidationResult(
                False,
                f"Ошибка кодировки: {e}. Используйте только UTF-8 совместимые символы."
            )
    
    @staticmethod
    def check_language_support(text: str) -> ValidationResult:
        """Проверяет поддержку языка."""
        # Проверяем наличие кириллицы (основной язык приложения - русский)
        has_cyrillic = bool(re.search(r'[а-яё]', text.lower()))
        has_latin = bool(re.search(r'[a-z]', text.lower()))
        
        if not has_cyrillic and not has_latin:
            return ValidationResult(
                False,
                "Текст должен содержать буквы (русские или английские)"
            )
        
        return ValidationResult(True, "Язык поддерживается")
    
    @staticmethod
    def suggest_improvements(text: str) -> list:
        """Предлагает улучшения для текста."""
        suggestions = []
        
        # Проверка на слишком длинные предложения
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if len(sentence.strip()) > 200:
                suggestions.append("Рассмотрите разбиение длинных предложений на более короткие")
                break
        
        # Проверка на повторяющиеся слова
        words = text.lower().split()
        word_count = {}
        for word in words:
            if len(word) > 3:  # Игнорируем короткие слова
                word_count[word] = word_count.get(word, 0) + 1
        
        repeated_words = [word for word, count in word_count.items() if count > 5]
        if repeated_words:
            suggestions.append(f"Часто повторяющиеся слова: {', '.join(repeated_words[:3])}")
        
        # Проверка на отсутствие знаков препинания
        if not re.search(r'[.!?]', text):
            suggestions.append("Добавьте знаки препинания для лучшей интонации")
        
        return suggestions
