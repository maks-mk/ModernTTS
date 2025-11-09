"""
Конфигурация приложения TTS.
Содержит все константы, настройки и конфигурационные параметры.
"""

from pathlib import Path


class AppConfig:
    """Центральная конфигурация приложения."""
    
    # === ОСНОВНЫЕ КОНСТАНТЫ ===
    APP_NAME = "Modern TTS"
    APP_VERSION = "2.0.0"
    ORGANIZATION = "TTSApp"
    
    # === НАСТРОЙКИ ОКНА ===
    WINDOW_TITLE = "🎤 Modern TTS - Text to Speech"
    MIN_WINDOW_WIDTH = 700
    MIN_WINDOW_HEIGHT = 650
    DEFAULT_WINDOW_WIDTH = 900
    DEFAULT_WINDOW_HEIGHT = 750
    DEFAULT_WINDOW_X = 100
    DEFAULT_WINDOW_Y = 100
    
    # === НАСТРОЙКИ ТЕКСТА ===
    DEFAULT_VOICE = 'Kore'
    DEFAULT_TEXT = """[voice:Kore]Привет! Меня зовут Кора, и я женский голос.[/voice] [voice:Puck]А я Пак - энергичный мужской голос![/voice] [voice:Zephyr]Я Зефир, яркий женский голос.[/voice] [voice:Charon]И я Харон - информативный мужской голос. Вместе мы демонстрируем возможности многоголосового синтеза речи![/voice]"""
    MAX_TEXT_LENGTH = 5000
    TEXT_WARNING_LENGTH = 4500

    # === НАСТРОЙКИ РАЗДЕЛИТЕЛЯ ГОЛОСОВ ===
    DEFAULT_VOICE_DELIMITER = "---"
    MAX_DELIMITER_LENGTH = 10
    
    # === НАСТРОЙКИ API ===
    MIN_API_KEY_LENGTH = 30
    GEMINI_MODEL = "gemini-2.5-flash-preview-tts"
    
    # === НАСТРОЙКИ АУДИО ===
    AUDIO_SAMPLE_RATE = 24000
    AUDIO_CHANNELS = 1
    AUDIO_SAMPLE_WIDTH = 2
    
    # === НАСТРОЙКИ MP3 ===
    MP3_BITRATE = "128k"
    MP3_SAMPLE_RATE = 44100
    MP3_CHANNELS = 1
    
    # === ФАЙЛЫ ===
    OUTPUT_FILENAME_WAV = "out.wav"
    OUTPUT_FILENAME_MP3 = "out.mp3"
    LOG_FILENAME = "tts_app.log"
    CONFIG_FILENAME = ".tts_app_config.json"
    
    # === ПУТИ ===
    HOME_DIR = Path.home()
    CONFIG_FILE_PATH = HOME_DIR / CONFIG_FILENAME
    
    # === НАСТРОЙКИ ЛОГИРОВАНИЯ ===
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # === ТЕМЫ ===
    DEFAULT_THEME = "dark"
    AVAILABLE_THEMES = ["dark", "light"]
    
    # === ГОЛОСА ===
    # Список доступных голосов (поддерживаемые Gemini TTS API)
    VOICES = [
        'Zephyr', 'Puck', 'Charon', 'Kore', 'Fenrir', 'Leda', 'Orus', 'Aoede',
        'Callirrhoe', 'Autonoe', 'Enceladus', 'Iapetus', 'Umbriel', 'Algieba',
        'Despina', 'Erinome', 'Algenib', 'Rasalgethi', 'Laomedeia', 'Achernar',
        'Alnilam', 'Schedar', 'Gacrux', 'Pulcherrima', 'Achird', 'Zubenelgenubi',
        'Vindemiatrix', 'Sadachbia', 'Sadaltager', 'Sulafat'
    ]
    
    # === ОПИСАНИЯ ГОЛОСОВ ===
    VOICE_DESCRIPTIONS = {
        'Zephyr': 'Яркий',
        'Puck': 'Бодрый',
        'Charon': 'Информативный',
        'Kore': 'Твердый',
        'Fenrir': 'Сильный',
        'Leda': 'Молодой',
        'Orus': 'Твердый',
        'Aoede': 'Легкий',
        'Callirrhoe': 'Непринужденный',
        'Autonoe': 'Яркий',
        'Enceladus': 'Дышащий',
        'Iapetus': 'Четкий',
        'Umbriel': 'Непринужденный',
        'Algieba': 'Гладкий',
        'Despina': 'Гладкий',
        'Erinome': 'Четкий',
        'Algenib': 'Каменистый',
        'Rasalgethi': 'Информативный',
        'Laomedeia': 'Бодрый',
        'Achernar': 'Мягкий',
        'Alnilam': 'Твердый',
        'Schedar': 'Ровный',
        'Gacrux': 'Взрослый',
        'Pulcherrima': 'Передовой',
        'Achird': 'Дружелюбный',
        'Zubenelgenubi': 'Обычный',
        'Vindemiatrix': 'Нежный',
        'Sadachbia': 'Живой',
        'Sadaltager': 'Знающий',
        'Sulafat': 'Теплый'
    }
    
    # === ПОЛ ГОЛОСОВ ===
    # Основано на данных Google Cloud TTS API и анализе имен голосов
    # Источник: https://cloud.google.com/text-to-speech/docs/voices
    VOICE_GENDERS = {
        # Женские голоса
        'Zephyr': 'female',        # Зефир - в мифологии женское божество ветра
        'Aoede': 'female',         # Аэда - одна из муз в греческой мифологии
        'Callirrhoe': 'female',    # Каллироя - нимфа в греческой мифологии
        'Autonoe': 'female',       # Автоноя - женское имя в греческой мифологии
        'Leda': 'female',          # Леда - женское имя в греческой мифологии
        'Kore': 'female',          # Кора - женское имя (Персефона)
        'Despina': 'female',       # Деспина - женское имя
        'Erinome': 'female',       # Эриноме - женское имя в мифологии
        'Gacrux': 'female',        # Гакрукс - звезда, в TTS API помечена как female
        'Laomedeia': 'female',     # Лаомедея - женское имя в мифологии
        'Pulcherrima': 'female',   # Пульхеррима - женское имя (лат. "красивейшая")
        'Vindemiatrix': 'female',  # Виндемиатрикс - звезда, традиционно женского рода
        'Sulafat': 'female',       # Сулафат - звезда, в TTS API помечена как female
        'Achernar': 'female',      # Ахернар - в некоторых источниках female
        
        # Мужские голоса
        'Puck': 'male',            # Пак - мужской персонаж из "Сна в летнюю ночь"
        'Charon': 'male',          # Харон - мужское божество в греческой мифологии
        'Fenrir': 'male',          # Фенрир - мужской волк в скандинавской мифологии
        'Orus': 'male',            # Орус - мужское имя
        'Enceladus': 'male',       # Энцелад - мужской титан в греческой мифологии
        'Iapetus': 'male',         # Япет - мужской титан в греческой мифологии
        'Umbriel': 'male',         # Умбриэль - мужской персонаж из "Похищения локона"
        'Algieba': 'male',         # ��льгиеба - звезда, в TTS API помечена как male
        'Algenib': 'male',         # Альгениб - звезда, традиционно мужского рода
        'Rasalgethi': 'male',      # Расальгети - звезда, в TTS API помечена как male
        'Alnilam': 'male',         # Альнилам - звезда в созвездии Ориона
        'Schedar': 'male',         # Шедар - звезда, в TTS API помечена как male
        'Achird': 'male',          # Ахирд - звезда, традиционно мужского рода
        'Zubenelgenubi': 'male',   # Зубенельгенуби - звезда, в TTS API помечена как male
        'Sadachbia': 'male',       # Садахбия - звезда, в TTS API помечена как male
        'Sadaltager': 'male',      # Садальтагер - звезда, в TTS API помечена как male
    }
    
    # === КАТЕГОРИИ ГОЛОСОВ ===
    VOICE_CATEGORIES = {
        'male': [voice for voice, gender in VOICE_GENDERS.items() if gender == 'male'],
        'female': [voice for voice, gender in VOICE_GENDERS.items() if gender == 'female'],
        'all': list(VOICE_GENDERS.keys())
    }
    
    # === ЦВЕТА ===
    class Colors:
        """Цветовая палитра приложения."""
        PRIMARY = "#1e88e5"
        PRIMARY_HOVER = "#2196f3"
        PRIMARY_PRESSED = "#1976d2"

        SUCCESS = "#00c853"
        SUCCESS_HOVER = "#00e676"

        WARNING = "#ffab00"
        DANGER = "#ff3d00"
        DANGER_HOVER = "#ff5252"

        # Темная тема - профессиональная
        DARK_BG = "#121212"
        DARK_BG_SECONDARY = "#1e1e1e"
        DARK_WIDGET_BG = "#2d2d2d"
        DARK_BORDER = "#444444"
        DARK_TEXT = "#e0e0e0"
        DARK_TEXT_SECONDARY = "#b0b0b0"
        DARK_TEXT_MUTED = "#707070"

        # Светлая тема - чистая
        LIGHT_BG = "#fafafa"
        LIGHT_BG_SECONDARY = "#f0f0f0"
        LIGHT_WIDGET_BG = "#ffffff"
        LIGHT_BORDER = "#dddddd"
        LIGHT_TEXT = "#212121"
        LIGHT_TEXT_SECONDARY = "#424242"
        LIGHT_TEXT_MUTED = "#757575"
    
    # === РАЗМЕРЫ ===
    class Sizes:
        """Размеры элементов интерфейса."""
        BUTTON_MIN_HEIGHT = 24
        BUTTON_LARGE_HEIGHT = 32
        ICON_SIZE = 32
        BORDER_RADIUS = 4
        BORDER_RADIUS_LARGE = 6
        SPACING_SMALL = 6
        SPACING_MEDIUM = 10
        SPACING_LARGE = 15
        PADDING_SMALL = 4
        PADDING_MEDIUM = 6
        PADDING_LARGE = 8
    
    # === ШРИФТЫ ===
    class Fonts:
        """Настройки шрифтов."""
        SIZE_SMALL = 10
        SIZE_NORMAL = 11
        SIZE_MEDIUM = 12
        SIZE_LARGE = 13
        SIZE_TITLE = 14
        SIZE_HEADER = 20

        WEIGHT_NORMAL = "normal"
        WEIGHT_BOLD = "bold"
    
    # === АНИМАЦИИ ===
    class Animation:
        """Настройки анимаций."""
        DURATION_FAST = 100
        DURATION_NORMAL = 200
        DURATION_SLOW = 300
    
    # === ГОРЯЧИЕ КЛАВИШИ ===
    class Shortcuts:
        """Горячие клавиши."""
        GENERATE = "Ctrl+G"
        PLAY_PAUSE = "Space"
        SAVE = "Ctrl+S"
        STOP = "Escape"
        SETTINGS = "Ctrl+,"
        QUIT = "Ctrl+Q"
    
    # === СООБЩЕНИЯ ===
    class Messages:
        """Текстовые сообщения."""
        READY = "Готов к работе"
        GENERATING = "Генерация речи..."
        PLAYING = "Воспроизведение..."
        PAUSED = "Воспроизведение приостановлено"
        STOPPED = "Воспроизведение остановлено"
        SAVED = "Файл сохранен"
        ERROR_NO_AUDIO = "Сначала сгенерируйте аудио"
        ERROR_EMPTY_TEXT = "Текст пустой или слишком длинный"
        ERROR_INVALID_VOICE = "Неподдерживаемый голос"
        ERROR_API_KEY = "API ключ обязателен для работы приложения"
        ERROR_API_KEY_SHORT = "API ключ кажется слишком коротким"
    
    @classmethod
    def get_voice_display_name(cls, voice: str) -> str:
        """Возвращает отображаемое имя голос�� с описанием."""
        description = cls.VOICE_DESCRIPTIONS.get(voice, "")
        if description:
            return f"{voice} ({description})"
        return voice
    
    @classmethod
    def get_voice_display_name_with_gender(cls, voice: str) -> str:
        """Возвращает отображаемое имя голоса с описанием и полом."""
        description = cls.VOICE_DESCRIPTIONS.get(voice, "")
        gender = cls.get_voice_gender(voice)
        
        gender_icon = "♂️" if gender == "male" else "♀️" if gender == "female" else "⚪"
        gender_text = "муж." if gender == "male" else "жен." if gender == "female" else "неизв."
        
        if description:
            return f"{gender_icon} {voice} ({description}, {gender_text})"
        else:
            return f"{gender_icon} {voice} ({gender_text})"
    
    @classmethod
    def get_voice_gender(cls, voice: str) -> str:
        """Возвращает пол голоса (male/female/unknown)."""
        return cls.VOICE_GENDERS.get(voice, "unknown")
    
    @classmethod
    def get_voices_by_gender(cls, gender: str) -> list:
        """Возвращает список голосов определенного пола."""
        if gender in cls.VOICE_CATEGORIES:
            return cls.VOICE_CATEGORIES[gender]
        return []
    
    @classmethod
    def get_male_voices(cls) -> list:
        """Возвращает список мужских голосов."""
        return cls.get_voices_by_gender('male')
    
    @classmethod
    def get_female_voices(cls) -> list:
        """Возвращает список женских голосов."""
        return cls.get_voices_by_gender('female')
    
    @classmethod
    def is_male_voice(cls, voice: str) -> bool:
        """Проверяет, является ли голос мужским."""
        return cls.get_voice_gender(voice) == "male"
    
    @classmethod
    def is_female_voice(cls, voice: str) -> bool:
        """Проверяет, является ли голос женским."""
        return cls.get_voice_gender(voice) == "female"
    
    @classmethod
    def get_voice_statistics(cls) -> dict:
        """Возвращает статистику по голосам."""
        male_count = len(cls.get_male_voices())
        female_count = len(cls.get_female_voices())
        total_count = len(cls.VOICES)
        
        return {
            'total': total_count,
            'male': male_count,
            'female': female_count,
            'unknown': total_count - male_count - female_count,
            'male_percentage': round((male_count / total_count) * 100, 1) if total_count > 0 else 0,
            'female_percentage': round((female_count / total_count) * 100, 1) if total_count > 0 else 0
        }
    
    @classmethod
    def validate_theme(cls, theme: str) -> str:
        """Валидирует и возвращает корректную тему."""
        return theme if theme in cls.AVAILABLE_THEMES else cls.DEFAULT_THEME
    
    @classmethod
    def validate_voice(cls, voice: str) -> str:
        """Валидирует и возвращает корректный голос."""
        return voice if voice in cls.VOICES else cls.DEFAULT_VOICE
