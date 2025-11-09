"""
Менеджер настроек для TTS приложения.
Управляет сохранением и загрузкой настроек пользователя.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtCore import QSettings

from config import AppConfig
from validation import Validator

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecureKeyManager:
    """Менеджер для безопасной работы с API ключами."""
    
    def __init__(self):
        self.encryption_key_file = Path.home() / '.tts_app_key'
        self._encryption_key = self._get_or_create_encryption_key()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Получает или создает ключ шифрования."""
        if not CRYPTO_AVAILABLE:
            logger.warning("Библиотека cryptography недоступна. Ключи будут храниться без шифрования.")
            return b'dummy_key_for_fallback'
        
        try:
            if self.encryption_key_file.exists():
                with open(self.encryption_key_file, 'rb') as f:
                    return f.read()
            else:
                # Создаем новый ключ шифрования
                key = Fernet.generate_key()
                with open(self.encryption_key_file, 'wb') as f:
                    f.write(key)
                # Устанавливаем права доступа только для владельца
                self.encryption_key_file.chmod(0o600)
                logger.info("Создан новый ключ шифрования")
                return key
        except Exception as e:
            logger.error(f"Ошибка при работе с ключом шифрования: {e}")
            return Fernet.generate_key()
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Шифрует API ключ."""
        if not CRYPTO_AVAILABLE:
            logger.warning("Шифрование недоступно, ключ сохраняется в открытом виде")
            return api_key
        
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_key = fernet.encrypt(api_key.encode())
            return encrypted_key.decode()
        except Exception as e:
            logger.error(f"Ошибка шифрования API к��юча: {e}")
            return api_key
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Расшифровывает API ключ."""
        if not CRYPTO_AVAILABLE:
            return encrypted_key
        
        try:
            fernet = Fernet(self._encryption_key)
            decrypted_key = fernet.decrypt(encrypted_key.encode())
            return decrypted_key.decode()
        except Exception as e:
            logger.error(f"Ошибка расшифровки API ключа: {e}")
            return encrypted_key


from ui_components import ApiKeyDialog

class SettingsManager:
    """Менеджер настроек приложения."""
    
    def __init__(self):
        """Инициализация менеджера настроек."""
        self.qt_settings = QSettings(AppConfig.ORGANIZATION, AppConfig.APP_NAME)
        self.config_file = AppConfig.CONFIG_FILE_PATH
        self.key_manager = SecureKeyManager()
        self._ensure_config_directory()
    
    def _ensure_config_directory(self):
        """Создает директорию для конфигурации, если она не существует."""
        config_dir = self.config_file.parent
        config_dir.mkdir(parents=True, exist_ok=True)
    
    # === API КЛЮЧ ===
    
    def setup_api_key_from_dialog(self, parent_widget) -> Optional[str]:
        """Показывает диалог и настраивает API ключ."""
        dialog = ApiKeyDialog(parent_widget, self.get_theme())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            api_key = dialog.get_api_key()
            if self.save_api_key(api_key):
                return api_key
        return None
        
    def load_api_key(self) -> Optional[str]:
        """Безопасная загрузка API ключа из различных источников."""
        # Проверяем, был ли ключ явно удален пользователем
        manually_removed = self.qt_settings.value('api_key_manually_removed', False, type=bool)
        if manually_removed:
            logger.debug("API ключ был явно удален пользователем, пропускаем автозагрузку")
            return None

        # 1. Сначала проверяем .env файл и переменные окружения (приоритет)
        if DOTENV_AVAILABLE:
            try:
                load_dotenv()
                logger.debug("Файл .env загружен")
            except Exception as e:
                logger.warning(f"Ошибка загрузки .env файла: {e}")

        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            validation = Validator.validate_api_key(api_key)
            if validation.is_valid:
                logger.info("API ключ загружен из переменных окружения/.env")
                return api_key
            else:
                logger.warning(f"API ключ из переменных окружения невалиден: {validation.message}")

        # 2. Затем проверяем сохраненные пользователем ключи
        # Проверяем настройки Qt (с расшифровкой)
        stored_key = self.qt_settings.value('api_key_encrypted', '')
        if stored_key:
            try:
                decrypted_key = self.key_manager.decrypt_api_key(stored_key)
                validation = Validator.validate_api_key(decrypted_key)
                if validation.is_valid:
                    logger.info("API ключ загружен из настроек Qt")
                    return decrypted_key
                else:
                    logger.warning(f"API ключ из настроек Qt невалиден: {validation.message}")
                    # Удаляем невалидный ключ
                    self.qt_settings.remove('api_key_encrypted')
            except Exception as e:
                logger.error(f"Ошибка расшифровки API ключа из Qt настроек: {e}")
                self.qt_settings.remove('api_key_encrypted')
        
        # 4. Проверяем JSON конфигурацию
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_key = config.get('api_key_encrypted', '')
                    if api_key:
                        validation = Validator.validate_api_key(api_key)
                        if validation.is_valid:
                            logger.info("API ключ загружен из JSON конфигурации")
                            return api_key
                        else:
                            logger.warning(f"API ключ из JSON конфигурации невалиден: {validation.message}")
        except Exception as e:
            logger.error(f"Ошибка чтения JSON конфигурации: {e}")

        logger.warning("API ключ не найден ни в одном из источников")
        return None
    
    def save_api_key(self, api_key: str) -> bool:
        """Сохраняет API ключ в настройки."""
        validation = Validator.validate_api_key(api_key)
        if not validation.is_valid:
            logger.error(f"Попытка сохранить невалидный API ключ: {validation.message}")
            return False
        
        try:
            # Шифруем ключ перед сохранением
            encrypted_key = self.key_manager.encrypt_api_key(api_key)
            
            # Сохраняем в Qt настройки
            self.qt_settings.setValue('api_key_encrypted', encrypted_key)
            # Сбрасываем флаг ручного удаления при сохранении нового ключа
            self.qt_settings.setValue('api_key_manually_removed', False)
            self.qt_settings.sync()  # Принудительная синхронизация

            # Сохраняем в JSON файл как резервную копию
            config = self._load_json_config()
            config['api_key_encrypted'] = encrypted_key
            config['api_key_manually_removed'] = False
            self._save_json_config(config)
            
            # Проверяем, что ключ действительно сохранился
            if self.qt_settings.value('api_key_encrypted'):
                logger.info("API ключ успешно сохранен с шифрованием")
                return True
            else:
                logger.error("Не удалось сохранить API ключ")
                return False
        except Exception as e:
            logger.error(f"Ошибка сохранения API ключа: {e}")
            return False
    
    def remove_api_key(self):
        """Удаляет сохраненный API ключ."""
        try:
            self.qt_settings.remove('api_key_encrypted')
            # Устанавливаем флаг, что пользователь явно удалил ключ
            self.qt_settings.setValue('api_key_manually_removed', True)
            self.qt_settings.sync()

            config = self._load_json_config()
            config.pop('api_key_encrypted', None)
            config['api_key_manually_removed'] = True
            self._save_json_config(config)

            logger.info("API ключ удален")
        except Exception as e:
            logger.error(f"Ошибка удаления API ключа: {e}")
    
    def has_saved_api_key(self) -> bool:
        """Проверяет, есть ли сохраненный API ключ."""
        return bool(self.qt_settings.value('api_key_encrypted', ''))
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Возвращает информацию о статусе шифрования."""
        return {
            'crypto_available': CRYPTO_AVAILABLE,
            'encryption_enabled': CRYPTO_AVAILABLE,
            'has_saved_key': self.has_saved_api_key(),
            'encryption_key_exists': self.key_manager.encryption_key_file.exists() if CRYPTO_AVAILABLE else False
        }
    
    # === ТЕМА ===
    
    def get_theme(self) -> str:
        """Получает текущую тему."""
        theme = self.qt_settings.value('theme', AppConfig.DEFAULT_THEME)
        return AppConfig.validate_theme(theme)
    
    def set_theme(self, theme: str) -> bool:
        """Устанавливает тему."""
        validation = Validator.validate_theme(theme)
        if not validation.is_valid:
            logger.error(f"Попытка установить невалидную тему: {validation.message}")
            return False
        
        try:
            self.qt_settings.setValue('theme', theme)
            logger.info(f"Тема изменена на: {theme}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения темы: {e}")
            return False
    
    # === ГОЛОС ===
    
    def get_last_voice(self) -> str:
        """Получает последний использованный голос."""
        voice = self.qt_settings.value('last_voice', AppConfig.DEFAULT_VOICE)
        return AppConfig.validate_voice(voice)
    
    def set_last_voice(self, voice: str) -> bool:
        """Сохраняет последний использованный голос."""
        validation = Validator.validate_voice(voice)
        if not validation.is_valid:
            logger.error(f"Попытка сохранить невалидный голос: {validation.message}")
            return False
        
        try:
            self.qt_settings.setValue('last_voice', voice)
            logger.debug(f"Последний голос сохранен: {voice}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения голоса: {e}")
            return False
    
    # === ГЕОМЕТРИЯ ОКНА ===
    
    def get_window_geometry(self) -> Dict[str, int]:
        """Получает геометрию окна."""
        geometry = {
            'x': self.qt_settings.value('window_x', AppConfig.DEFAULT_WINDOW_X, type=int),
            'y': self.qt_settings.value('window_y', AppConfig.DEFAULT_WINDOW_Y, type=int),
            'width': self.qt_settings.value('window_width', AppConfig.DEFAULT_WINDOW_WIDTH, type=int),
            'height': self.qt_settings.value('window_height', AppConfig.DEFAULT_WINDOW_HEIGHT, type=int)
        }
        
        # Валидируем геометрию
        validation = Validator.validate_window_geometry(
            geometry['x'], geometry['y'], geometry['width'], geometry['height']
        )
        
        if not validation.is_valid:
            logger.warning(f"Невалидная геометрия окна: {validation.message}. Используем значения по умолчанию.")
            return {
                'x': AppConfig.DEFAULT_WINDOW_X,
                'y': AppConfig.DEFAULT_WINDOW_Y,
                'width': AppConfig.DEFAULT_WINDOW_WIDTH,
                'height': AppConfig.DEFAULT_WINDOW_HEIGHT
            }
        
        return geometry
    
    def save_window_geometry(self, x: int, y: int, width: int, height: int) -> bool:
        """Сохраняет геометрию окна."""
        validation = Validator.validate_window_geometry(x, y, width, height)
        if not validation.is_valid:
            logger.error(f"Попытка сохранить невалидную геометрию окна: {validation.message}")
            return False
        
        try:
            self.qt_settings.setValue('window_x', x)
            self.qt_settings.setValue('window_y', y)
            self.qt_settings.setValue('window_width', width)
            self.qt_settings.setValue('window_height', height)
            logger.debug(f"Геометрия окна сохранена: {x}x{y} {width}x{height}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения геометрии окна: {e}")
            return False
    
    # === ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ===
    
    def get_last_save_directory(self) -> str:
        """Получает последнюю директорию сохранения."""
        return self.qt_settings.value('last_save_directory', str(Path.home()))
    
    def set_last_save_directory(self, directory: str):
        """Сохраняет последнюю директорию сохранения."""
        if Path(directory).exists():
            self.qt_settings.setValue('last_save_directory', directory)
            logger.debug(f"Последняя директория сохранения: {directory}")
    
    def get_auto_play(self) -> bool:
        """Получает настройку автовоспроизведения."""
        return self.qt_settings.value('auto_play', False, type=bool)
    
    def set_auto_play(self, enabled: bool):
        """Устанавливает настройку автовоспроизведения."""
        self.qt_settings.setValue('auto_play', enabled)
        logger.debug(f"Автовоспроизведение: {enabled}")
    
    def get_default_format(self) -> str:
        """Получает формат сохранения по умолчанию."""
        return self.qt_settings.value('default_format', 'mp3')
    
    def set_default_format(self, format_name: str):
        """Устанавливает формат сохранения по умолчанию."""
        validation = Validator.validate_audio_format(format_name)
        if validation.is_valid:
            self.qt_settings.setValue('default_format', format_name)
            logger.debug(f"Формат по умолчанию: {format_name}")

    # === НАСТРОЙКИ РАЗДЕЛИТЕЛЯ ГОЛОСОВ ===

    def get_delimiter_enabled(self) -> bool:
        """Получает настройку включения разделителя голосов."""
        return self.qt_settings.value('delimiter_enabled', False, type=bool)

    def set_delimiter_enabled(self, enabled: bool):
        """Устанавливает настройку включения разделителя голосов."""
        self.qt_settings.setValue('delimiter_enabled', enabled)
        logger.debug(f"Разделитель голосов включен: {enabled}")

    def get_delimiter_string(self) -> str:
        """Получает строку-разделитель для голосов."""
        return self.qt_settings.value('delimiter_string', AppConfig.DEFAULT_VOICE_DELIMITER)

    def set_delimiter_string(self, delimiter: str):
        """Устанавливает строку-разделитель для голосов."""
        if delimiter and len(delimiter) <= AppConfig.MAX_DELIMITER_LENGTH:
            self.qt_settings.setValue('delimiter_string', delimiter)
            logger.debug(f"Строка-разделитель установлена: '{delimiter}'")
        else:
            logger.warning(f"Невалидная строка-разделитель: '{delimiter}'. Используется по умолчанию.")

    def get_delimiter_voice_sequence(self) -> list[str]:
        """Получает последовательность голосов для разделителя."""
        # QSettings сохраняет списки как строки, разделенные запятыми
        voices_str = self.qt_settings.value('delimiter_voice_sequence', '')
        if voices_str:
            voices = [v.strip() for v in voices_str.split(',') if v.strip()]
            # Валидируем голоса из сохраненной последовательности
            valid_voices = [v for v in voices if Validator.validate_voice(v).is_valid]
            if len(valid_voices) != len(voices):
                logger.warning("Некоторые голоса в последовательности разделителя невалидны и будут проигнорированы.")
            return valid_voices if valid_voices else [AppConfig.DEFAULT_VOICE]
        return [AppConfig.DEFAULT_VOICE]

    def set_delimiter_voice_sequence(self, voices: list[str]):
        """Устанавливает последовательность голосов для разделителя."""
        # Валидируем все голоса перед сохранением
        valid_voices = [v for v in voices if Validator.validate_voice(v).is_valid]
        if valid_voices:
            self.qt_settings.setValue('delimiter_voice_sequence', ','.join(valid_voices))
            logger.debug(f"Последовательность голосов для разделителя установлена: {valid_voices}")
        else:
            logger.warning("Попытка установить пустую или невалидную последовательность г��лосов для разделителя. Используется голос по умолчанию.")
            self.qt_settings.setValue('delimiter_voice_sequence', AppConfig.DEFAULT_VOICE)

    # === НАСТРОЙКИ МУЛЬТИСПИКЕРНОЙ ГЕНЕРАЦИИ ===

    def get_use_native_multispeaker(self) -> bool:
        """Получает настройку использования нативной мультиспикерной генерации."""
        return self.qt_settings.value('use_native_multispeaker', False, type=bool)

    def set_use_native_multispeaker(self, enabled: bool):
        """Устанавливает настройку использования нативной мультиспикерной генерации."""
        self.qt_settings.setValue('use_native_multispeaker', enabled)
        logger.debug(f"Нативная мультиспикерная генерация: {enabled}")

    # === JSON КОНФИГУРАЦИЯ ===
    
    def _load_json_config(self) -> Dict[str, Any]:
        """Загружает JSON конфигурацию."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки JSON конфигурации: {e}")
        
        return {}
    
    def _save_json_config(self, config: Dict[str, Any]):
        """Сохраняет JSON конфигурацию."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения JSON конфигурации: {e}")
    
    # === ЭКСПОРТ/ИМПОРТ НАСТРОЕК ===
    
    def export_settings(self, file_path: str) -> bool:
        """Экспортирует настройки в файл."""
        try:
            settings_data = {
                'theme': self.get_theme(),
                'last_voice': self.get_last_voice(),
                'window_geometry': self.get_window_geometry(),
                'last_save_directory': self.get_last_save_directory(),
                'auto_play': self.get_auto_play(),
                'default_format': self.get_default_format(),
                'app_version': AppConfig.APP_VERSION,
                'export_timestamp': str(Path().cwd())  # Используем текущее время
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Настройки экспортированы в: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка экспорта настроек: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Импортирует настройки из файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            
            # Импортируем только валидные настройки
            if 'theme' in settings_data:
                self.set_theme(settings_data['theme'])
            
            if 'last_voice' in settings_data:
                self.set_last_voice(settings_data['last_voice'])
            
            if 'window_geometry' in settings_data:
                geom = settings_data['window_geometry']
                self.save_window_geometry(geom['x'], geom['y'], geom['width'], geom['height'])
            
            if 'last_save_directory' in settings_data:
                self.set_last_save_directory(settings_data['last_save_directory'])
            
            if 'auto_play' in settings_data:
                self.set_auto_play(settings_data['auto_play'])
            
            if 'default_format' in settings_data:
                self.set_default_format(settings_data['default_format'])
            
            logger.info(f"Настройки импортированы из: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка импорта настроек: {e}")
            return False
    
    def reset_to_defaults(self):
        """Сбрасывает все настройки к значениям по умолчанию."""
        try:
            self.qt_settings.clear()
            if self.config_file.exists():
                self.config_file.unlink()
            logger.info("Настройки сброшены к значениям по умолчанию")
        except Exception as e:
            logger.error(f"Ошибка сброса настроек: {e}")
