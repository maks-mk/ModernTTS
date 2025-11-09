"""
Менеджер аудио для TTS приложения.
Управляет генерацией, воспроизведением и сохранением аудио.
"""
import sys
import os
import wave
import tempfile
import logging
import re
import subprocess
from io import BytesIO
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from google import genai
from google.genai import types

from config import AppConfig
from validation import Validator, ValidationResult

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger(__name__)

# Настройка для скрытия консоли ffmpeg/ffprobe в Windows
if os.name == 'nt':  # Windows
    # Сохраняем оригинальный Popen
    original_popen = subprocess.Popen

    def silent_popen(*args, **kwargs):
        """Обертка для subprocess.Popen, которая скрывает консоль в Windows."""
        # Добавляем флаги для скрытия консоли
        if 'startupinfo' not in kwargs:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo

        # Добавляем флаг создания процесса без консоли
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW

        return original_popen(*args, **kwargs)

    # Заменяем subprocess.Popen на нашу обертку
    subprocess.Popen = silent_popen
    logger.info("Настроена скрытая работа ffmpeg/ffprobe (без консоли)")

if PYDUB_AVAILABLE:
    # Определяем базовый путь для поиска ffmpeg/ffprobe
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Если приложение запущено из PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        # Если приложение запущено в режиме разработки
        base_path = Path(os.getcwd())

    ffmpeg_path = base_path / "ffmpeg.exe"
    ffprobe_path = base_path / "ffprobe.exe"

    if ffmpeg_path.exists():
        AudioSegment.converter = str(ffmpeg_path)
        logger.info(f"Найден ffmpeg: {ffmpeg_path}")
    else:
        logger.warning(f"ffmpeg.exe не найден по пути: {ffmpeg_path}. "
                       "Для работы с MP3 и склейки аудио он должен быть доступен.")

    if ffprobe_path.exists():
        AudioSegment.ffprobe = str(ffprobe_path)
        logger.info(f"Найден ffprobe: {ffprobe_path}")
    else:
        logger.warning(f"ffprobe.exe не найден по пути: {ffprobe_path}. "
                       "Для получения информации об аудио он должен быть доступен.")


class TextParser:
    """Парсер текста для разделения на сегменты с разными голосами."""
    
    @staticmethod
    def parse(text: str, default_voice: str,
              delimiter_enabled: bool = False,
              delimiter_string: str = AppConfig.DEFAULT_VOICE_DELIMITER,
              delimiter_voice_sequence: list[str] = None) -> list[tuple[str, str]]:
        """
        Парсит текст и возвращает список сегментов (голос, текст).
        Приоритет: теги [voice:VOICE_NAME]...[/voice] имеют приоритет над разделителями.
        """
        segments = []

        # Проверяем наличие тегов голосов (приоритет)
        if TextParser.has_voice_tags(text):
            # Режим с тегами [voice:...] (приоритет над разделителями)
            pattern = r'\[voice:(\w+)\](.*?)\[/voice\]'
            last_end = 0

            for match in re.finditer(pattern, text, re.DOTALL):
                start, end = match.span()

                # Добавляем текст перед тегом
                if start > last_end:
                    segments.append((default_voice, text[last_end:start].strip()))

                # Добавляем текст внутри тега
                voice_name = match.group(1)
                segment_text = match.group(2).strip()

                # Валидируем голос
                if Validator.validate_voice(voice_name).is_valid:
                    segments.append((voice_name, segment_text))
                else:
                    logger.warning(f"Невалидный голос '{voice_name}' в теге, используется голос по умолчанию.")
                    segments.append((default_voice, segment_text))

                last_end = end

            # Добавляем оставшийся текст
            if last_end < len(text):
                segments.append((default_voice, text[last_end:].strip()))

        elif delimiter_enabled and delimiter_string:
            # Режим переключения по разделителю
            if not delimiter_voice_sequence:
                delimiter_voice_sequence = [default_voice]
            
            parts = text.split(delimiter_string)
            voice_index = 0
            for part in parts:
                stripped_part = part.strip()
                if stripped_part:
                    current_voice = delimiter_voice_sequence[voice_index % len(delimiter_voice_sequence)]
                    segments.append((current_voice, stripped_part))
                    voice_index += 1
        else:
            # Обычный текст без тегов и разделителей
            segments.append((default_voice, text.strip()))
        
        # Фильтруем пустые сегменты
        return [(v, t) for v, t in segments if t]

    @staticmethod
    def has_voice_tags(text: str) -> bool:
        """Проверяет, есть ли в тексте теги голосов."""
        return '[voice:' in text


class TempFileManager:
    """Менеджер для безопасной работы с временными файлами."""
    
    def __init__(self):
        self.temp_files: list[str] = []
    
    def create_temp_file(self, suffix: str = '.wav') -> str:
        """Создает безопасный временный файл."""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = temp_file.name
            temp_file.close()
            self.temp_files.append(temp_path)
            logger.debug(f"Создан временный файл: {temp_path}")
            return temp_path
        except Exception as e:
            logger.error(f"Ошибка создания временного файла: {e}")
            raise IOError(f"Не удалось создать временный файл: {e}")
    
    def cleanup(self):
        """Очищает все временные файлы."""
        for temp_path in self.temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"Удален временный файл: {temp_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}")
        self.temp_files.clear()
    
    def __del__(self):
        """Автоматическая очистка при удалении объекта."""
        self.cleanup()


class TTSWorker(QThread):
    """Асинхронный worker для генерации речи."""
    
    # Сигналы для коммуникации с UI
    finished = pyqtSignal(bytes)  # Успешная генерация
    error = pyqtSignal(str)       # Ошибка
    progress = pyqtSignal(str)    # Прогресс
    
    def __init__(self, api_key: str, text: str, voice: str):
        super().__init__()
        self.api_key = api_key
        self.text = text
        self.voice = voice
    
    def run(self):
        """Выполняет генерацию речи в отдельном потоке."""
        try:
            # Валидация входных данных
            api_validation = Validator.validate_api_key(self.api_key)
            if not api_validation.is_valid:
                self.error.emit(f"Ошибка API ключа: {api_validation.message}")
                return
            
            text_validation = Validator.validate_text(self.text)
            if not text_validation.is_valid:
                self.error.emit(f"Ошибка текста: {text_validation.message}")
                return
            
            voice_validation = Validator.validate_voice(self.voice)
            if not voice_validation.is_valid:
                self.error.emit(f"Ошибка голоса: {voice_validation.message}")
                return
            
            self.progress.emit("Инициализация TTS клиента...")
            logger.info(f"Начало генерации речи: голос={self.voice}, длина текста={len(self.text)}")
            
            client = genai.Client(api_key=self.api_key)
            
            self.progress.emit("Отправка запроса к API...")
            
            response = client.models.generate_content(
                model=AppConfig.GEMINI_MODEL,
                contents=self.text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice,
                            )
                        )
                    ),
                )
            )
            
            self.progress.emit("Обработка ответа...")
            
            if not response.candidates or not response.candidates[0].content.parts:
                self.error.emit("Пустой ответ от API")
                return
            
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            if not audio_data:
                self.error.emit("Не удалось получить аудио данные")
                return
            
            logger.info("Речь успешно сгенерирована")
            self.finished.emit(audio_data)
            
        except Exception as e:
            error_msg = f"Ошибка при генерации речи: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)


class MultiVoiceTTSWorker(QThread):
    """Worker для генерации речи из нескольких сегментов с разными голосами."""

    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, api_key: str, segments: list[tuple[str, str]], use_native_multispeaker: bool = True):
        super().__init__()
        self.api_key = api_key
        self.segments = segments
        self.use_native_multispeaker = use_native_multispeaker
    
    def run(self):
        """Выполняет генерацию мультиголосового аудио."""
        # Пытаемся использовать нативную мультиспикерную генерацию
        if self.use_native_multispeaker and self._can_use_native_multispeaker():
            self._generate_native_multispeaker()
        else:
            self._generate_sequential()

    def _can_use_native_multispeaker(self) -> bool:
        """Проверяет, можно ли использовать нативную мультиспикерную генерацию."""
        # Нативная поддержка работает только с тегами голосов, не с разделителями
        # И только если есть именованные спикеры
        unique_speakers = set(voice for voice, _ in self.segments)
        return len(unique_speakers) > 1 and len(unique_speakers) <= 2  # Gemini поддерживает до 2 спикеров

    def _generate_native_multispeaker(self):
        """Генерирует аудио используя нативную мультиспикерную поддержку Gemini."""
        try:
            logger.info(f"Использование нативной мультиспикерной генерации: {len(self.segments)} сегментов")

            # Формируем prompt для мультиспикера
            prompt_parts = []
            unique_voices = list(set(voice for voice, _ in self.segments))

            for voice, text in self.segments:
                prompt_parts.append(f"{voice}: {text}")

            full_prompt = "TTS the following conversation:\n" + "\n".join(prompt_parts)

            self.progress.emit("Генерация мультиспикерного аудио...")
            logger.info(f"Prompt: {full_prompt[:200]}...")

            client = genai.Client(api_key=self.api_key)

            # Создаем конфигурацию для мультиспикера
            speaker_configs = []
            for voice in unique_voices:
                speaker_configs.append(
                    types.SpeakerVoiceConfig(
                        speaker=voice,
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    )
                )

            response = client.models.generate_content(
                model=AppConfig.GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_configs
                        )
                    ),
                )
            )

            if not response.candidates or not response.candidates[0].content.parts:
                raise Exception("Пустой ответ от API")

            audio_data = response.candidates[0].content.parts[0].inline_data.data

            if not audio_data:
                raise Exception("Не удалось получить аудио данные")

            logger.info("Нативная мультиспикерная речь успешно сгенерирована")
            self.finished.emit(audio_data)

        except Exception as e:
            logger.warning(f"Ошибка нативной мультиспикерной генерации: {e}")
            logger.info("Переключение на последовательную генерацию")
            self._generate_sequential()

    def _generate_sequential(self):
        """Выполняет последовательную генерацию и склейку аудио."""
        if not PYDUB_AVAILABLE:
            self.error.emit("Для работы с несколькими голосами нужна библиотека pydub.")
            return

        try:
            logger.info(f"Начало генерации мультиголосового аудио: {len(self.segments)} сегментов")
            for i, (voice, text) in enumerate(self.segments):
                logger.info(f"Сегмент {i+1}: голос={voice}, текст='{text[:50]}{'...' if len(text) > 50 else ''}'")

            client = genai.Client(api_key=self.api_key)
            combined_audio = AudioSegment.empty()
            total_segments = len(self.segments)

            for i, (voice, text) in enumerate(self.segments):
                self.progress.emit(f"Генерация сегмента {i+1}/{total_segments} (голос: {voice})...")
                logger.info(f"Генерация сегмента {i+1}/{total_segments}: голос={voice}")

                response = client.models.generate_content(
                    model=AppConfig.GEMINI_MODEL,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=voice,
                                )
                            )
                        ),
                    )
                )
                
                if not response.candidates or not response.candidates[0].content.parts:
                    raise ValueError(f"Пустой ответ от API для сегмента {i+1}")
                
                audio_data = response.candidates[0].content.parts[0].inline_data.data
                
                # Загружаем аудио сегмент в pydub из сырых данных
                segment_audio = AudioSegment.from_raw(
                    BytesIO(audio_data),
                    sample_width=AppConfig.AUDIO_SAMPLE_WIDTH,
                    frame_rate=AppConfig.AUDIO_SAMPLE_RATE,
                    channels=AppConfig.AUDIO_CHANNELS
                )
                combined_audio += segment_audio
            
            # Экспортируем финальное ауд��о в байты
            final_audio_io = BytesIO()
            combined_audio.export(final_audio_io, format="wav")
            
            self.finished.emit(final_audio_io.getvalue())
            
        except Exception as e:
            error_msg = f"Ошибка при генерации речи из нескольких сегментов: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)


class AudioFileManager:
    """Менеджер для работы с аудио файлами."""
    
    @staticmethod
    def save_wav_file(filename: str, pcm_data: bytes, 
                     channels: int = AppConfig.AUDIO_CHANNELS,
                     rate: int = AppConfig.AUDIO_SAMPLE_RATE,
                     sample_width: int = AppConfig.AUDIO_SAMPLE_WIDTH) -> ValidationResult:
        """Сохраняет PCM данные в WAV файл."""
        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm_data)
            
            logger.debug(f"WAV файл сохранен: {filename}")
            return ValidationResult(True, f"WAV файл успешно сохранен: {filename}")
            
        except Exception as e:
            error_msg = f"Ошибка при сохранении WAV файла {filename}: {e}"
            logger.error(error_msg)
            return ValidationResult(False, error_msg)
    
    @staticmethod
    def convert_to_mp3(wav_path: str, mp3_path: str, 
                      bitrate: str = AppConfig.MP3_BITRATE) -> ValidationResult:
        """Конвертирует WAV файл в MP3 формат, совместимый с WhatsApp."""
        if not PYDUB_AVAILABLE:
            return ValidationResult(
                False, 
                "Библиотека pydub не установлена. Установите её командой: pip install pydub"
            )
        
        temp_manager = TempFileManager()
        temp_wav = temp_manager.create_temp_file('.wav')
        
        try:
            logger.info(f"Конвертация WAV в MP3: {wav_path} -> {mp3_path}")
            
            # Проверяем существование исходного файла
            if not os.path.exists(wav_path):
                return ValidationResult(False, f"Исходный WAV файл не найден: {wav_path}")
            
            # Загружаем WAV файл
            audio = AudioSegment.from_wav(wav_path)
            
            # Настройки для совместимости с WhatsApp Android:
            # - Битрейт: 128 kbps (оптимальный для качества/размера)
            # - Частота дискретизации: 44100 Hz (стандарт для MP3)
            # - Каналы: моно (экономит место, WhatsApp поддерживает)
            audio = audio.set_frame_rate(AppConfig.MP3_SAMPLE_RATE).set_channels(AppConfig.MP3_CHANNELS)
            
            # Экспортируем в MP3 с оптимальными настройками для WhatsApp
            audio.export(
                mp3_path,
                format="mp3",
                bitrate=bitrate
            )
            
            logger.info(f"MP3 файл успешно создан: {mp3_path}")
            return ValidationResult(True, f"MP3 файл успешно создан: {mp3_path}")
            
        except Exception as e:
            error_msg = f"Ошибка при конвертации в MP3: {e}"
            logger.error(error_msg)
            return ValidationResult(False, error_msg)
        finally:
            # Гарантированно удаляем временный файл
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                    logger.debug(f"Временный WAV файл удален: {temp_wav}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный WAV файл: {e}")
    
    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """Получает информацию об аудио файле."""
        try:
            if file_path.lower().endswith('.wav'):
                with wave.open(file_path, 'rb') as wf:
                    return {
                        'format': 'WAV',
                        'channels': wf.getnchannels(),
                        'sample_rate': wf.getframerate(),
                        'sample_width': wf.getsampwidth(),
                        'duration': wf.getnframes() / wf.getframerate(),
                        'size': os.path.getsize(file_path)
                    }
            elif file_path.lower().endswith('.mp3') and PYDUB_AVAILABLE:
                audio = AudioSegment.from_mp3(file_path)
                return {
                    'format': 'MP3',
                    'channels': audio.channels,
                    'sample_rate': audio.frame_rate,
                    'duration': len(audio) / 1000.0,
                    'size': os.path.getsize(file_path)
                }
            else:
                return {
                    'format': 'Unknown',
                    'size': os.path.getsize(file_path)
                }
        except Exception as e:
            logger.error(f"Ошибка получения информации об аудио файле: {e}")
            return {'error': str(e)}


class AudioPlayer:
    """Менеджер воспроизведения аудио."""
    
    def __init__(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.temp_manager = TempFileManager()
        self.current_audio_data: Optional[bytes] = None
        self.current_temp_file: Optional[str] = None
    
    def load_audio_data(self, audio_data: bytes) -> ValidationResult:
        """Загружает аудио данные для воспроизведения."""
        try:
            self.current_audio_data = audio_data
            
            # Создаем временный файл
            temp_path = self.temp_manager.create_temp_file('.wav')
            result = AudioFileManager.save_wav_file(temp_path, audio_data)
            
            if not result.is_valid:
                return result
            
            self.current_temp_file = temp_path
            self.player.setSource(QUrl.fromLocalFile(temp_path))
            
            logger.debug("Аудио данные загружены для воспроизведения")
            return ValidationResult(True, "Аудио готово к воспроизведению")
            
        except Exception as e:
            error_msg = f"Ошибка загрузки аудио данных: {e}"
            logger.error(error_msg)
            return ValidationResult(False, error_msg)
    
    def play(self) -> ValidationResult:
        """Начинает воспроизведение."""
        if not self.current_audio_data:
            return ValidationResult(False, "Нет загруженных аудио данных")
        
        try:
            self.player.play()
            logger.debug("Воспроизведение начато")
            return ValidationResult(True, "Воспроизведение начато")
        except Exception as e:
            error_msg = f"Ошибка воспроизведения: {e}"
            logger.error(error_msg)
            return ValidationResult(False, error_msg)
    
    def pause(self) -> ValidationResult:
        """Приостанавливает воспроизведение."""
        try:
            self.player.pause()
            logger.debug("Воспроизведение приостановлено")
            return ValidationResult(True, "Воспроизведение приостановлено")
        except Exception as e:
            error_msg = f"Ошибка паузы: {e}"
            logger.error(error_msg)
            return ValidationResult(False, error_msg)
    
    def stop(self) -> ValidationResult:
        """Останавливает воспроизведение."""
        try:
            self.player.stop()
            logger.debug("Воспроизведение остановлено")
            return ValidationResult(True, "Воспроизведение остановлено")
        except Exception as e:
            error_msg = f"Ошибка остановки: {e}"
            logger.error(error_msg)
            return ValidationResult(False, error_msg)
    
    def get_player(self) -> QMediaPlayer:
        """Возвращает объект медиа плеера для подключения сигналов."""
        return self.player
    
    def cleanup(self):
        """Очищает ресурсы."""
        self.stop()
        self.temp_manager.cleanup()
        self.current_audio_data = None
        self.current_temp_file = None


class TextToSpeechCore:
    """Основной класс для работы с TTS."""
    
    def __init__(self, api_key: str, settings_manager):
        validation = Validator.validate_api_key(api_key)
        if not validation.is_valid:
            raise ValueError(f"Невалидный API ключ: {validation.message}")
        
        try:
            self.client = genai.Client(api_key=api_key)
            self.api_key = api_key
            self.settings_manager = settings_manager
            logger.info("TTS клиент успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации TTS клиента: {e}")
            raise ConnectionError(f"Ошибка инициализации клиента API: {e}")
    
    def create_worker(self, text: str, voice: str) -> QThread:
        """
        Создает worker для асинхронной генерации речи.
        Автоматически выбирает MultiVoiceTTSWorker, если в тексте есть теги или включен разделитель.
        """
        delimiter_enabled = self.settings_manager.get_delimiter_enabled()
        delimiter_string = self.settings_manager.get_delimiter_string()
        delimiter_voice_sequence = self.settings_manager.get_delimiter_voice_sequence()

        logger.info(f"Создание worker'а: delimiter_enabled={delimiter_enabled}, has_voice_tags={TextParser.has_voice_tags(text)}")

        if delimiter_enabled or TextParser.has_voice_tags(text):
            segments = TextParser.parse(
                text, voice,
                delimiter_enabled=delimiter_enabled,
                delimiter_string=delimiter_string,
                delimiter_voice_sequence=delimiter_voice_sequence
            )
            use_native = self.settings_manager.get_use_native_multispeaker()
            logger.info(f"Создается MultiVoiceTTSWorker с {len(segments)} сегментами (нативная генерация: {use_native})")
            return MultiVoiceTTSWorker(self.api_key, segments, use_native)
        else:
            logger.info(f"Создается TTSWorker с голосом {voice}")
            return TTSWorker(self.api_key, text, voice)
    
    def validate_request(self, text: str, voice: str) -> ValidationResult:
        """Валидирует запрос на генерацию речи."""
        text_validation = Validator.validate_text(text)
        if not text_validation.is_valid:
            return text_validation
        
        voice_validation = Validator.validate_voice(voice)
        if not voice_validation.is_valid:
            return voice_validation
        
        return ValidationResult(True, "Запрос валиден")
    
    def get_available_voices(self) -> list[str]:
        """Возвращает список доступных голосов."""
        return AppConfig.VOICES.copy()
    
    def get_voice_description(self, voice: str) -> str:
        """Возвращает описание голоса."""
        return AppConfig.VOICE_DESCRIPTIONS.get(voice, "Описание недоступно")