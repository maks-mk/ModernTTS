"""
UI компоненты для TTS приложения.
Содержит переиспользуемые диалоги и виджеты.
"""

import os
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QRadioButton, QDialogButtonBox, QMessageBox,
    QFileDialog, QTextEdit, QGroupBox, QCheckBox, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import qtawesome as qta

from config import AppConfig
from style_manager import StyleManager
from validation import Validator, ValidationResult


class BaseDialog(QDialog):
    """Базовый класс для всех диалогов."""
    
    def __init__(self, parent=None, title: str = "", theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self.setup_dialog(title)
    
    def setup_dialog(self, title: str):
        """Настройка базового диалога."""
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 700)
        self.setStyleSheet(StyleManager.get_dialog_style(self.theme))
    
    def create_button_layout(self, ok_text: str = "OK", cancel_text: str = "Отмена") -> QHBoxLayout:
        """Создает стандартную раскладку кнопок."""
        layout = QHBoxLayout()
        
        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button = QPushButton(ok_text)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.ok_button)
        
        return layout


class ApiKeyDialog(BaseDialog):
    """Диалог для ввода API ключа."""
    
    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent, "🔑 Настройка API ключа", theme)
        self.api_key = ""
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса диалога."""
        layout = QVBoxLayout(self)
        layout.setSpacing(AppConfig.Sizes.SPACING_MEDIUM)
        layout.setContentsMargins(
            AppConfig.Sizes.SPACING_LARGE, AppConfig.Sizes.SPACING_LARGE,
            AppConfig.Sizes.SPACING_LARGE, AppConfig.Sizes.SPACING_LARGE
        )
        
        # Заголовок
        title_label = QLabel("🔑 Настройка Gemini API ключа")
        title_label.setStyleSheet(f"""
            font-size: {AppConfig.Fonts.SIZE_TITLE}px; 
            font-weight: {AppConfig.Fonts.WEIGHT_BOLD}; 
            color: {AppConfig.Colors.PRIMARY}; 
            margin-bottom: {AppConfig.Sizes.SPACING_SMALL}px;
        """)
        layout.addWidget(title_label)
        
        # Описание
        desc_text = (
            "Для работы приложения необходим API ключ от Google Gemini.\n\n"
            "📋 Как получить API ключ:\n"
            "1. Перейдите на сайт: https://aistudio.google.com/app/apikey\n"
            "2. Войдите в свой Google аккаунт\n"
            "3. Нажмите 'Create API Key'\n"
            "4. Скопируйте полученный ключ\n\n"
            "🔒 Ваш ключ будет сохранен безопасно в настройках приложения."
        )
        
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {AppConfig.Colors.DARK_TEXT_SECONDARY if self.theme == 'dark' else AppConfig.Colors.LIGHT_TEXT_SECONDARY}; 
            font-size: {AppConfig.Fonts.SIZE_SMALL}px; 
            line-height: 1.5;
        """)
        layout.addWidget(desc_label)
        
        # Поле ввода
        input_label = QLabel("Введите ваш API ключ:")
        layout.addWidget(input_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("AIzaSy...")
        self.api_key_input.textChanged.connect(self.validate_input)
        layout.addWidget(self.api_key_input)
        
        # Статус валидации
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet(f"font-size: {AppConfig.Fonts.SIZE_SMALL}px;")
        layout.addWidget(self.validation_label)
        
        # Кнопки
        buttons_layout = self.create_button_layout("✅ Сохранить", "❌ Отмена")
        layout.addLayout(buttons_layout)
        
        # Изначально кнопка OK отключена
        self.ok_button.setEnabled(False)
    
    def validate_input(self):
        """Валидирует введенный API ключ."""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            self.validation_label.setText("")
            self.ok_button.setEnabled(False)
            return
        
        validation = Validator.validate_api_key(api_key)
        
        if validation.is_valid:
            self.validation_label.setText("✅ API ключ корректен")
            self.validation_label.setStyleSheet(f"color: {AppConfig.Colors.SUCCESS}; font-size: {AppConfig.Fonts.SIZE_SMALL}px;")
            self.ok_button.setEnabled(True)
        else:
            self.validation_label.setText(f"❌ {validation.message}")
            self.validation_label.setStyleSheet(f"color: {AppConfig.Colors.DANGER}; font-size: {AppConfig.Fonts.SIZE_SMALL}px;")
            self.ok_button.setEnabled(False)
    
    def get_api_key(self) -> str:
        """Возвращает введенный API ключ."""
        return self.api_key_input.text().strip()


class SettingsDialog(BaseDialog):
    """Диалог настроек приложения."""
    
    # Сигнал для запроса изменения API ключа
    change_api_key_requested = pyqtSignal()
    remove_api_key_requested = pyqtSignal()

    def __init__(self, parent=None, current_theme: str = "dark", settings_manager=None, encryption_status: dict = None):
        super().__init__(parent, "⚙️ Настройки", current_theme)
        self.current_theme = current_theme
        self.settings_manager = settings_manager
        self.encryption_status = encryption_status or {}
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса диалога."""
        # Создаем основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем прокручиваемую область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Применяем стили к прокручиваемой области
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {AppConfig.Colors.DARK_BG if self.current_theme == 'dark' else AppConfig.Colors.LIGHT_BG};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {AppConfig.Colors.DARK_WIDGET_BG if self.current_theme == 'dark' else AppConfig.Colors.LIGHT_WIDGET_BG};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {AppConfig.Colors.DARK_TEXT_SECONDARY if self.current_theme == 'dark' else AppConfig.Colors.LIGHT_TEXT_SECONDARY};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {AppConfig.Colors.DARK_TEXT if self.current_theme == 'dark' else AppConfig.Colors.LIGHT_TEXT};
            }}
        """)

        # Создаем виджет для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {AppConfig.Colors.DARK_BG if self.current_theme == 'dark' else AppConfig.Colors.LIGHT_BG};
            }}
        """)

        layout = QVBoxLayout(content_widget)
        layout.setSpacing(AppConfig.Sizes.SPACING_MEDIUM)
        layout.setContentsMargins(
            AppConfig.Sizes.SPACING_LARGE, AppConfig.Sizes.SPACING_LARGE,
            AppConfig.Sizes.SPACING_LARGE, AppConfig.Sizes.SPACING_LARGE
        )
        
        # Выбор темы
        theme_group = QGroupBox("🎨 Тема оформления")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(AppConfig.Sizes.SPACING_SMALL)
        
        self.dark_theme_radio = QRadioButton("🌙 Темная тема")
        self.light_theme_radio = QRadioButton("☀️ Светлая тема")
        
        if self.current_theme == 'dark':
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)
        
        theme_layout.addWidget(self.dark_theme_radio)
        theme_layout.addWidget(self.light_theme_radio)
        layout.addWidget(theme_group)
        
        # Управление API ключом
        api_group = QGroupBox("🔑 Управление API ключом")
        api_layout = QVBoxLayout(api_group)
        api_layout.setSpacing(AppConfig.Sizes.SPACING_SMALL)
        
        if self.encryption_status.get('has_saved_key'):
            status_text = "✅ API ключ сохранен"
            status_color = AppConfig.Colors.SUCCESS
        else:
            status_text = "❌ API ключ не настроен"
            status_color = AppConfig.Colors.DANGER
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: {AppConfig.Fonts.SIZE_NORMAL}px;")
        api_layout.addWidget(status_label)
        
        api_buttons_layout = QHBoxLayout()
        
        change_key_button = QPushButton("🔄 Изменить ключ")
        change_key_button.clicked.connect(self.change_api_key_requested.emit)
        change_key_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppConfig.Colors.PRIMARY};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-height: {AppConfig.Sizes.BUTTON_MIN_HEIGHT}px;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {AppConfig.Colors.PRIMARY_PRESSED};
            }}
        """)
        api_buttons_layout.addWidget(change_key_button)
        
        if self.encryption_status.get('has_saved_key'):
            remove_key_button = QPushButton("🗑️ Удалить ключ")
            remove_key_button.clicked.connect(self.remove_api_key_requested.emit)
            remove_key_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {AppConfig.Colors.DANGER};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                    min-height: {AppConfig.Sizes.BUTTON_MIN_HEIGHT}px;
                }}
                QPushButton:hover {{
                    background-color: {AppConfig.Colors.DANGER_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: #c82333;
                }}
            """)
            api_buttons_layout.addWidget(remove_key_button)
        
        api_layout.addLayout(api_buttons_layout)
        
        crypto_info = f"🔒 Шифрование: {'Включено' if self.encryption_status.get('encryption_enabled') else 'Отключено'}"
        if not self.encryption_status.get('crypto_available'):
            crypto_info += "\n⚠️ Для повышения безопасности установите: pip install cryptography"
        
        crypto_label = QLabel(crypto_info)
        crypto_label.setStyleSheet(f"""
            color: {AppConfig.Colors.DARK_TEXT_SECONDARY if self.current_theme == 'dark' else AppConfig.Colors.LIGHT_TEXT_SECONDARY}; 
            font-size: {AppConfig.Fonts.SIZE_SMALL}px; 
            font-style: italic;
        """)
        api_layout.addWidget(crypto_label)
        
        layout.addWidget(api_group)
        
        # Дополнительные настройки
        additional_group = QGroupBox("🔧 Дополнительные настройки")
        additional_layout = QVBoxLayout(additional_group)

        self.auto_play_checkbox = QCheckBox("🎵 Автовоспроизведение после генерации")
        self.save_window_pos_checkbox = QCheckBox("💾 Сохранять позицию окна")
        self.save_window_pos_checkbox.setChecked(True)

        if self.current_theme == 'dark':
            checkbox_style = "color: white;"
        else:
            checkbox_style = "color: black;"
        self.auto_play_checkbox.setStyleSheet(checkbox_style)
        self.save_window_pos_checkbox.setStyleSheet(checkbox_style)

        additional_layout.addWidget(self.auto_play_checkbox)
        additional_layout.addWidget(self.save_window_pos_checkbox)
        layout.addWidget(additional_group)

        # Настройки разделителя голосов
        delimiter_group = QGroupBox("💬 Разделитель голосов")
        delimiter_layout = QVBoxLayout(delimiter_group)

        self.delimiter_enabled_checkbox = QCheckBox("Включить переключение голосов по разделителю")
        if self.settings_manager:
            self.delimiter_enabled_checkbox.setChecked(self.settings_manager.get_delimiter_enabled())
        self.delimiter_enabled_checkbox.setStyleSheet(checkbox_style)
        delimiter_layout.addWidget(self.delimiter_enabled_checkbox)

        delimiter_string_layout = QHBoxLayout()
        delimiter_string_layout.addWidget(QLabel("Строка-разделитель:"))
        self.delimiter_string_input = QLineEdit()
        self.delimiter_string_input.setPlaceholderText(AppConfig.DEFAULT_VOICE_DELIMITER)
        if self.settings_manager:
            self.delimiter_string_input.setText(self.settings_manager.get_delimiter_string())
        delimiter_string_layout.addWidget(self.delimiter_string_input)
        delimiter_layout.addLayout(delimiter_string_layout)

        delimiter_voices_layout = QHBoxLayout()
        delimiter_voices_layout.addWidget(QLabel("Последовательность голосов (через запятую):"))
        self.delimiter_voices_input = QLineEdit()
        self.delimiter_voices_input.setPlaceholderText("Kore, Puck, Nova")
        if self.settings_manager:
            self.delimiter_voices_input.setText(", ".join(self.settings_manager.get_delimiter_voice_sequence()))
        delimiter_voices_layout.addWidget(self.delimiter_voices_input)
        delimiter_layout.addLayout(delimiter_voices_layout)

        layout.addWidget(delimiter_group)

        # Настройки TTS
        tts_group = QGroupBox("🎙️ Настройки TTS")
        tts_layout = QVBoxLayout(tts_group)

        self.native_multispeaker_checkbox = QCheckBox("Нативная генерация (только 2 голоса)")
        self.native_multispeaker_checkbox.setToolTip(
            "Использует встроенную поддержку мультиспикеров Gemini API.\n"
            "• Быстрее и качественнее для 2 спикеров\n"
            "• При ошибке автоматически переключается на обычную генерацию\n"
            "• Работает только с тегами голосов [voice:Name]...[/voice]"
        )
        if self.settings_manager:
            self.native_multispeaker_checkbox.setChecked(self.settings_manager.get_use_native_multispeaker())
        self.native_multispeaker_checkbox.setStyleSheet(checkbox_style)
        tts_layout.addWidget(self.native_multispeaker_checkbox)

        layout.addWidget(tts_group)

        info_label = QLabel("💡 Изменения применятся сразу после нажатия OK")
        info_label.setStyleSheet(f"""
            color: {AppConfig.Colors.DARK_TEXT_SECONDARY if self.current_theme == 'dark' else AppConfig.Colors.LIGHT_TEXT_SECONDARY}; 
            font-size: {AppConfig.Fonts.SIZE_SMALL}px; 
            font-style: italic;
        """)
        layout.addWidget(info_label)

        # Устанавливаем содержимое в прокручиваемую область
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Добавляем кнопки вне прокручиваемой области
        buttons_layout = self.create_button_layout()
        main_layout.addLayout(buttons_layout)

        # Устанавливаем максимальную высоту окна
        self.setMaximumHeight(600)  # Ограничиваем высоту окна
    
    def get_selected_theme(self) -> str:
        return "dark" if self.dark_theme_radio.isChecked() else "light"
    
    def get_auto_play(self) -> bool:
        return self.auto_play_checkbox.isChecked()
    
    def get_save_window_pos(self) -> bool:
        return self.save_window_pos_checkbox.isChecked()

    def get_delimiter_enabled(self) -> bool:
        return self.delimiter_enabled_checkbox.isChecked()

    def get_delimiter_string(self) -> str:
        return self.delimiter_string_input.text().strip()

    def get_delimiter_voice_sequence(self) -> list[str]:
        voices_str = self.delimiter_voices_input.text().strip()
        if voices_str:
            return [v.strip() for v in voices_str.split(',') if v.strip()]
        return []

    def get_use_native_multispeaker(self) -> bool:
        return self.native_multispeaker_checkbox.isChecked()


class FormatInfoDialog(BaseDialog):
    """Диалог с информацией о форматах."""
    
    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent, "📄 Информация о форматах", theme)
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса диалога."""
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(AppConfig.Sizes.SPACING_MEDIUM)
        layout.setContentsMargins(
            AppConfig.Sizes.SPACING_LARGE, AppConfig.Sizes.SPACING_LARGE,
            AppConfig.Sizes.SPACING_LARGE, AppConfig.Sizes.SPACING_LARGE
        )
        
        # Заголовок
        title_label = QLabel("📄 Поддерживаемые форматы аудио")
        title_label.setStyleSheet(f"""
            font-size: {AppConfig.Fonts.SIZE_TITLE}px; 
            font-weight: {AppConfig.Fonts.WEIGHT_BOLD}; 
            color: {AppConfig.Colors.PRIMARY}; 
            margin-bottom: {AppConfig.Sizes.SPACING_SMALL}px;
        """)
        layout.addWidget(title_label)
        
        # Информация о форматах
        format_info = """
<h3>🎵 WAV (Waveform Audio File Format)</h3>
<ul>
<li><b>Качество:</b> Без потерь, максимальное качество</li>
<li><b>Размер:</b> Большой размер файла</li>
<li><b>Совместимость:</b> Универсальная поддержка</li>
<li><b>Рекомендуется:</b> Для архивирования и профессионального использования</li>
</ul>

<h3>🎶 MP3 (MPEG Audio Layer III)</h3>
<ul>
<li><b>Качество:</b> Сжатие с потерями, хорошее качество</li>
<li><b>Размер:</b> Компактный размер (в ~10 раз меньше WAV)</li>
<li><b>Совместимость:</b> Поддерживается всеми устройствами</li>
<li><b>Настройки:</b> 128 kbps, 44.1 kHz, моно</li>
<li><b>Рекомендуется:</b> Для WhatsApp, Telegram и повседневного использования</li>
</ul>

<h3>📱 Совместимость с мессенджерами</h3>
<ul>
<li><b>WhatsApp:</b> MP3 (оптимизированные настройки)</li>
<li><b>Telegram:</b> MP3, WAV</li>
<li><b>Discord:</b> MP3, WAV</li>
</ul>

<h3>💡 Рекомендации</h3>
<ul>
<li>Для отправки в мессенджеры используйте <b>MP3</b></li>
<li>Для сохранения на компьютере используйте <b>WAV</b></li>
<li>MP3 файлы автоматически оптимизируются для мобильных устройств</li>
</ul>
        """
        
        info_text = QTextEdit()
        info_text.setHtml(format_info)
        info_text.setReadOnly(True)
        layout.addWidget(info_text)
        
        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


class StyledMessageBox:
    """Стилизованные сообщения."""
    
    @staticmethod
    def show_info(parent, title: str, message: str, theme: str = "dark"):
        """Показывает информационное сообщение."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStyleSheet(StyleManager.get_dialog_style(theme))
        return msg_box.exec()
    
    @staticmethod
    def show_warning(parent, title: str, message: str, theme: str = "dark"):
        """Показывает предупреждение."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStyleSheet(StyleManager.get_dialog_style(theme))
        return msg_box.exec()

    @staticmethod
    def show_question(parent, title: str, message: str, theme: str = "dark"):
        """Показывает вопрос с кнопками Да/Нет."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)  # По умолчанию "Нет" для безопасности
        msg_box.setStyleSheet(StyleManager.get_dialog_style(theme))
        return msg_box.exec()
    
    @staticmethod
    def show_error(parent, title: str, message: str, theme: str = "dark"):
        """Показывает сообщение об ошибке."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setStyleSheet(StyleManager.get_dialog_style(theme))
        return msg_box.exec()
    
    @staticmethod
    def show_success(parent, title: str, message: str, theme: str = "dark"):
        """Показывает сообщение об успехе."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        # Кастомная иконка для успеха
        msg_box.setIconPixmap(qta.icon('fa5s.check-circle', color=AppConfig.Colors.SUCCESS).pixmap(64, 64))
        msg_box.setStyleSheet(StyleManager.get_dialog_style(theme))
        return msg_box.exec()


class FileDialogHelper:
    """Помощник для работы с диалогами файлов."""
    
    @staticmethod
    def get_save_file_dialog(parent, title: str, default_filename: str, 
                           file_filter: str, last_directory: str = "") -> tuple:
        """Показывает диалог сохранения файла."""
        if not last_directory:
            last_directory = str(AppConfig.HOME_DIR)
        
        default_path = os.path.join(last_directory, default_filename)
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent, title, default_path, file_filter
        )
        
        return file_path, selected_filter
    
    @staticmethod
    def get_audio_save_dialog(parent, has_pydub: bool = True, 
                            last_directory: str = "") -> tuple:
        """Показывает диалог сохранения аудио файла."""
        if has_pydub:
            file_filter = "MP3 Files (*.mp3);;WAV Files (*.wav);;All Files (*.*)"
            default_filename = AppConfig.OUTPUT_FILENAME_MP3
        else:
            file_filter = "WAV Files (*.wav);;All Files (*.*)"
            default_filename = AppConfig.OUTPUT_FILENAME_WAV
        
        return FileDialogHelper.get_save_file_dialog(
            parent, "💾 Сохранить аудио файл", default_filename, 
            file_filter, last_directory
        )
