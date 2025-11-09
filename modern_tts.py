"""
Рефакторированное TTS приложение.
Модульная архитектура согласно принципам SOLID и DRY.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel, QProgressBar,
    QGroupBox, QStatusBar, QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut, QTextCursor, QColor
from PyQt6.QtMultimedia import QMediaPlayer
import qtawesome as qta

# Импорт наших модулей
from config import AppConfig
from settings_manager import SettingsManager
from audio_manager import TextToSpeechCore, AudioPlayer, AudioFileManager, TempFileManager
from validation import Validator, TextValidator
from style_manager import StyleManager
from ui_components import (
    ApiKeyDialog, SettingsDialog, FormatInfoDialog, 
    StyledMessageBox, FileDialogHelper
)

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, AppConfig.LOG_LEVEL),
    format=AppConfig.LOG_FORMAT,
    handlers=[
        logging.FileHandler(AppConfig.LOG_FILENAME),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModernTTSApp(QMainWindow):
    """Современное TTS приложение с модульной архитектурой."""
    
    def __init__(self):
        super().__init__()
        
        # Инициализация компонентов
        self.settings_manager = SettingsManager()
        self.temp_manager = TempFileManager()
        self.audio_player = AudioPlayer()
        
        # Состояние приложения
        self.audio_data: Optional[bytes] = None
        self.current_worker = None
        self.tts_core: Optional[TextToSpeechCore] = None
        
        # Инициализация
        self._setup_api_key()
        self._setup_window()
        self._init_ui()
        self._setup_shortcuts()
        self._apply_theme()
        self._connect_signals()
        
        logger.info("Приложение успешно инициализировано")
    
    def _setup_api_key(self):
        """Настройка API ключа."""
        api_key = self.settings_manager.load_api_key()
        
        if not api_key:
            self._show_api_key_dialog()
            return
        
        try:
            self.tts_core = TextToSpeechCore(api_key, self.settings_manager)
        except (ConnectionError, ValueError) as e:
            StyledMessageBox.show_error(
                self, "❌ Ошибка API", 
                f"Ошибка инициализации TTS: {e}",
                self.settings_manager.get_theme()
            )
            self._show_api_key_dialog()
    
    def _show_api_key_dialog(self, is_initial_setup: bool = True):
        """Показывает диалог ввода API ключа.
        Если is_initial_setup=True, приложение завершится при отмене.
        """
        dialog = ApiKeyDialog(self, self.settings_manager.get_theme())
        
        if dialog.exec() == ApiKeyDialog.DialogCode.Accepted:
            api_key = dialog.get_api_key()
            if self.settings_manager.save_api_key(api_key):
                try:
                    self.tts_core = TextToSpeechCore(api_key, self.settings_manager)
                    StyledMessageBox.show_success(
                        self, "✅ Успех", 
                        "API ключ сохранен и проверен!",
                        self.settings_manager.get_theme()
                    )
                except Exception as e:
                    StyledMessageBox.show_error(
                        self, "❌ Ошибка", 
                        f"Ошибка проверки API ключа: {e}",
                        self.settings_manager.get_theme()
                    )
                    if is_initial_setup:
                        sys.exit(1)
            else:
                StyledMessageBox.show_error(
                    self, "❌ Ошибка", 
                    "Не удалось сохранить API ключ",
                    self.settings_manager.get_theme()
                )
                if is_initial_setup:
                    sys.exit(1)
        else:
            if is_initial_setup:
                StyledMessageBox.show_error(
                    self, "❌ Ошибка", 
                    AppConfig.Messages.ERROR_API_KEY,
                    self.settings_manager.get_theme()
                )
                sys.exit(1)
            else:
                # Если не начальная настройка, просто логируем и продолжаем работу
                logger.info("Изменение API ключа отменено пользователем.")
                self.status_bar.showMessage("Изменение API ключа отменено", 2000)
    
    def _setup_window(self):
        """Настройка основного окна."""
        self.setWindowTitle(AppConfig.WINDOW_TITLE)
        self.setWindowIcon(qta.icon('fa5s.microphone', color=AppConfig.Colors.PRIMARY))
        
        # Восстанавливаем геометрию окна
        geometry = self.settings_manager.get_window_geometry()
        self.setGeometry(geometry['x'], geometry['y'], geometry['width'], geometry['height'])
        
        # Минимальный размер
        self.setMinimumSize(AppConfig.MIN_WINDOW_WIDTH, AppConfig.MIN_WINDOW_HEIGHT)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(AppConfig.Messages.READY)
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(AppConfig.Sizes.SPACING_SMALL)
        main_layout.setContentsMargins(
            AppConfig.Sizes.SPACING_MEDIUM, AppConfig.Sizes.SPACING_MEDIUM,
            AppConfig.Sizes.SPACING_MEDIUM, AppConfig.Sizes.SPACING_MEDIUM
        )

        # Заголовок
        self._create_header(main_layout)

        # Поле ввода текста (растягивается)
        text_group = self._create_text_input(main_layout)

        # Создаем контейнер для нижних элементов
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setSpacing(AppConfig.Sizes.SPACING_SMALL)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Настройки голоса
        self._create_voice_settings(bottom_layout)

        # Прогресс бар
        self._create_progress_bar(bottom_layout)

        # Кнопки управления
        self._create_control_buttons(bottom_layout)

        # Добавляем нижний контейнер в main layout
        main_layout.addWidget(bottom_container)

        # Устанавливаем stretch factors: текстовое поле (2), нижний контейнер (1)
        main_layout.setStretchFactor(text_group, 2)
        main_layout.setStretchFactor(bottom_container, 1)
    
    def _create_header(self, main_layout: QVBoxLayout):
        """Создает заголовок приложения."""
        header_layout = QHBoxLayout()

        title_label = QLabel(f"🎤 {AppConfig.APP_NAME}")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {AppConfig.Fonts.SIZE_TITLE}px;
                font-weight: {AppConfig.Fonts.WEIGHT_BOLD};
                color: {AppConfig.Colors.PRIMARY};
                margin-bottom: 0px;
            }}
        """)
        header_layout.addWidget(title_label)

        # Кнопка настроек
        settings_button = QPushButton(qta.icon('fa5s.cog', color='white'), "")
        settings_button.setFixedSize(AppConfig.Sizes.ICON_SIZE, AppConfig.Sizes.ICON_SIZE)
        settings_button.setToolTip("Настройки")
        settings_button.clicked.connect(self._show_settings)
        header_layout.addWidget(settings_button)

        main_layout.addLayout(header_layout)
    
    def _create_text_input(self, main_layout: QVBoxLayout):
        """Создает поле ввода текста."""
        text_group = QGroupBox("📝 Текст для озвучивания")
        text_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        text_layout = QVBoxLayout(text_group)
        text_layout.setSpacing(AppConfig.Sizes.SPACING_SMALL)
        text_layout.setContentsMargins(
            AppConfig.Sizes.PADDING_MEDIUM, AppConfig.Sizes.PADDING_MEDIUM,
            AppConfig.Sizes.PADDING_MEDIUM, AppConfig.Sizes.PADDING_MEDIUM
        )

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Введите текст...\n\n"
            "Используйте теги для смены голоса, например:\n"
            "[voice:Kore]Привет, я Кора.[/voice]\n"
            "[voice:Puck]А я Пак![/voice]"
        )
        self.text_input.setText(AppConfig.DEFAULT_TEXT)
        self.text_input.setMinimumHeight(250)
        self.text_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Счетчик символов
        self.char_counter = QLabel()
        self.char_counter.setStyleSheet(f"font-size: {AppConfig.Fonts.SIZE_SMALL}px;")
        self.text_input.textChanged.connect(self._on_text_changed)

        text_layout.addWidget(self.text_input)
        text_layout.addWidget(self.char_counter)
        main_layout.addWidget(text_group)

        # Обновляем счетчик
        self._update_char_counter()

        return text_group
    
    def _create_voice_settings(self, main_layout: QVBoxLayout):
        """Создает настройки голоса."""
        voice_group = QGroupBox("🎭 Настройки голоса")
        voice_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        voice_layout = QVBoxLayout(voice_group)
        voice_layout.setSpacing(AppConfig.Sizes.SPACING_SMALL)
        voice_layout.setContentsMargins(
            AppConfig.Sizes.PADDING_MEDIUM, AppConfig.Sizes.PADDING_MEDIUM,
            AppConfig.Sizes.PADDING_MEDIUM, AppConfig.Sizes.PADDING_MEDIUM
        )
        
        # Объединенная строка с выбором голоса, фильтром и статистикой
        voice_control_layout = QHBoxLayout()
        voice_control_layout.addWidget(QLabel("Голос:"))

        self.voice_combo = QComboBox()
        # Добавляем голоса с описаниями и полом
        for voice in AppConfig.VOICES:
            display_name = AppConfig.get_voice_display_name_with_gender(voice)
            self.voice_combo.addItem(display_name, voice)

        # Восстанавливаем последний выбранный голос
        last_voice = self.settings_manager.get_last_voice()
        for i in range(self.voice_combo.count()):
            if self.voice_combo.itemData(i) == last_voice:
                self.voice_combo.setCurrentIndex(i)
                break

        self.voice_combo.currentTextChanged.connect(self._on_voice_changed)
        voice_control_layout.addWidget(self.voice_combo)

        # Кнопка предварительного прослушивания
        preview_button = QPushButton(qta.icon('fa5s.headphones', color='white'), "Тест")
        preview_button.setToolTip("Прослушать образец голоса")
        preview_button.clicked.connect(self._preview_voice)
        # Устанавливаем фиксированную высоту для консистентности
        preview_button.setFixedHeight(32)
        voice_control_layout.addWidget(preview_button)

        # Кнопка вставки тега голоса (такая же высота как у кнопки "Тест")
        insert_tag_button = QPushButton(qta.icon('fa5s.tag', color='white'), "")
        insert_tag_button.setFixedSize(32, 32)  # Квадратная кнопка
        insert_tag_button.setToolTip("Вставить тег голоса в текст")
        insert_tag_button.clicked.connect(self._insert_voice_tag)
        voice_control_layout.addWidget(insert_tag_button)

        # Разделитель
        voice_control_layout.addSpacing(AppConfig.Sizes.SPACING_MEDIUM)

        # Фильтры по полу
        voice_control_layout.addWidget(QLabel("Фильтр:"))

        self.gender_filter_combo = QComboBox()
        self.gender_filter_combo.addItem("🔄 Все голоса", "all")
        self.gender_filter_combo.addItem("♂️ Мужские", "male")
        self.gender_filter_combo.addItem("♀️ Женские", "female")
        self.gender_filter_combo.currentTextChanged.connect(self._on_gender_filter_changed)
        voice_control_layout.addWidget(self.gender_filter_combo)

        # Разделитель
        voice_control_layout.addSpacing(AppConfig.Sizes.SPACING_MEDIUM)

        # Статистика голосов
        stats = AppConfig.get_voice_statistics()
        stats_label = QLabel(
            f"📊 Всего: {stats['total']} | "
            f"♂️ {stats['male']} ({stats['male_percentage']}%) | "
            f"♀️ {stats['female']} ({stats['female_percentage']}%)"
        )
        stats_label.setStyleSheet(f"color: #888888; font-size: {AppConfig.Fonts.SIZE_SMALL}px;")
        voice_control_layout.addWidget(stats_label)

        voice_control_layout.addStretch()
        voice_layout.addLayout(voice_control_layout)

        main_layout.addWidget(voice_group)
    
    def _create_progress_bar(self, main_layout: QVBoxLayout):
        """Создает прогресс бар."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.progress_bar)
    
    def _create_control_buttons(self, main_layout: QVBoxLayout):
        """Создает кнопки управления."""
        buttons_group = QGroupBox("🎮 Управление")
        buttons_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        buttons_layout = QVBoxLayout(buttons_group)
        buttons_layout.setSpacing(AppConfig.Sizes.SPACING_SMALL)
        buttons_layout.setContentsMargins(
            AppConfig.Sizes.PADDING_MEDIUM, AppConfig.Sizes.PADDING_MEDIUM,
            AppConfig.Sizes.PADDING_MEDIUM, AppConfig.Sizes.PADDING_MEDIUM
        )
        
        # Основные кнопки
        main_buttons_layout = QHBoxLayout()
        
        self.generate_button = QPushButton(qta.icon('fa5s.magic', color='white'), " Сгенерировать")
        self.generate_button.setMinimumHeight(AppConfig.Sizes.BUTTON_LARGE_HEIGHT)
        
        self.save_button = QPushButton(qta.icon('fa5s.download', color='white'), " Сохранить")
        self.info_button = QPushButton(qta.icon('fa5s.info-circle', color='white'), " Форматы")
        
        main_buttons_layout.addWidget(self.generate_button)
        main_buttons_layout.addWidget(self.save_button)
        main_buttons_layout.addWidget(self.info_button)
        
        # Кнопки воспроизведения
        playback_layout = QHBoxLayout()
        
        self.play_button = QPushButton(qta.icon('fa5s.play', color='white'), " Воспроизвести")
        self.pause_button = QPushButton(qta.icon('fa5s.pause', color='white'), " Пауза")
        self.stop_button = QPushButton(qta.icon('fa5s.stop', color='white'), " Стоп")
        
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.pause_button)
        playback_layout.addWidget(self.stop_button)
        
        buttons_layout.addLayout(main_buttons_layout)
        buttons_layout.addLayout(playback_layout)
        main_layout.addWidget(buttons_group)
        
        # Начальное состояние кнопок
        self._update_ui_state(state='idle')
    
    def _setup_shortcuts(self):
        """Настройка горячих клавиш."""
        shortcuts = [
            (AppConfig.Shortcuts.GENERATE, self._generate_speech),
            (AppConfig.Shortcuts.PLAY_PAUSE, self._toggle_playback),
            (AppConfig.Shortcuts.SAVE, self._save_speech),
            (AppConfig.Shortcuts.STOP, self._stop_speech),
            (AppConfig.Shortcuts.SETTINGS, self._show_settings),
            (AppConfig.Shortcuts.QUIT, self.close)
        ]
        
        for shortcut_key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(shortcut_key), self)
            shortcut.activated.connect(callback)
    
    def _apply_theme(self):
        """Применяет выбранную тему."""
        theme = self.settings_manager.get_theme()
        self.setStyleSheet(StyleManager.get_main_window_style(theme))
        
        # Обновляем цвета текста после смены темы
        if hasattr(self, 'text_input'):
            QTimer.singleShot(100, self._setup_text_colors)
    
    def _connect_signals(self):
        """Подключает сигналы."""
        # Кнопки
        self.generate_button.clicked.connect(self._generate_speech)
        self.play_button.clicked.connect(self._play_speech)
        self.pause_button.clicked.connect(self._pause_speech)
        self.stop_button.clicked.connect(self._stop_speech)
        self.save_button.clicked.connect(self._save_speech)
        self.info_button.clicked.connect(self._show_format_info)
        
        # Медиа плеер
        player = self.audio_player.get_player()
        player.playbackStateChanged.connect(self._on_playback_state_changed)

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_text_changed(self):
        """Обработчик изменения текста."""
        self._update_char_counter()
        self._fix_text_colors()

    def _update_char_counter(self):
        """Обновляет счетчик символов."""
        text = self.text_input.toPlainText()
        status_text, color = Validator.get_text_length_status(text)

        self.char_counter.setText(status_text)
        self.char_counter.setStyleSheet(f"color: {color}; font-size: {AppConfig.Fonts.SIZE_SMALL}px;")

    def _fix_text_colors(self):
        """Исправляет цвета текста после вставки."""
        if not hasattr(self, 'text_input'):
            return

        cursor = self.text_input.textCursor()
        current_position = cursor.position()

        # Определяем правильный цвет для текущей темы
        theme = self.settings_manager.get_theme()
        text_color = QColor(AppConfig.Colors.DARK_TEXT if theme == 'dark' else AppConfig.Colors.LIGHT_TEXT)

        # Блокируем сигналы для избежания рекурсии
        self.text_input.blockSignals(True)

        # Применяем цвет ко всему тексту
        cursor.select(QTextCursor.SelectionType.Document)
        char_format = cursor.charFormat()
        char_format.setForeground(text_color)
        cursor.setCharFormat(char_format)

        # Восстанавливаем позицию курсора
        cursor.setPosition(current_position)
        self.text_input.setTextCursor(cursor)

        # Разблокируем сигналы
        self.text_input.blockSignals(False)

    def _setup_text_colors(self):
        """Настраивает цвета текста в зависимости от темы."""
        if not hasattr(self, 'text_input'):
            return

        theme = self.settings_manager.get_theme()
        style = StyleManager.get_text_edit_style(theme)
        self.text_input.setStyleSheet(style)
        self.text_input.update()

    def _on_voice_changed(self):
        """Обработчик изменения голоса."""
        current_index = self.voice_combo.currentIndex()
        if current_index >= 0:
            voice = self.voice_combo.itemData(current_index)
            self.settings_manager.set_last_voice(voice)
            
            # Логируем информацию о голосе
            gender = AppConfig.get_voice_gender(voice)
            logger.debug(f"Выбран голос: {voice} (пол: {gender})")
    
    def _on_gender_filter_changed(self):
        """Обработчик изменения фильтра по полу."""
        current_index = self.gender_filter_combo.currentIndex()
        if current_index < 0:
            return
        
        selected_gender = self.gender_filter_combo.itemData(current_index)
        current_voice = None
        
        # Сохраняем текущий выбранный голос
        voice_index = self.voice_combo.currentIndex()
        if voice_index >= 0:
            current_voice = self.voice_combo.itemData(voice_index)
        
        # Очищаем комбобокс
        self.voice_combo.clear()
        
        # Получаем отфильтрованный список голосов
        if selected_gender == "all":
            voices_to_show = AppConfig.VOICES
        else:
            voices_to_show = AppConfig.get_voices_by_gender(selected_gender)
        
        # Заполняем комбобокс отфильтрованными голосами
        for voice in voices_to_show:
            display_name = AppConfig.get_voice_display_name_with_gender(voice)
            self.voice_combo.addItem(display_name, voice)
        
        # Пытаемся восстановить выбранный голос, если он есть в фильтре
        if current_voice and current_voice in voices_to_show:
            for i in range(self.voice_combo.count()):
                if self.voice_combo.itemData(i) == current_voice:
                    self.voice_combo.setCurrentIndex(i)
                    break
        elif self.voice_combo.count() > 0:
            # Если текущий голос не подходит под фильтр, выбираем первый доступный
            self.voice_combo.setCurrentIndex(0)
        
        logger.debug(f"Применен фильтр голосов: {selected_gender}, доступно голосов: {len(voices_to_show)}")

    def _insert_voice_tag(self):
        """Вставляет тег голоса в текущую позицию курсора."""
        current_index = self.voice_combo.currentIndex()
        if current_index < 0:
            return

        voice = self.voice_combo.itemData(current_index)

        # Получаем текущую позицию курсора
        cursor = self.text_input.textCursor()

        # Создаем тег голоса
        voice_tag = f"[voice:{voice}]...[/voice]"

        # Вставляем тег в позицию курсора
        cursor.insertText(voice_tag)

        # Позиционируем курсор между тегами (после "...")
        # Находим позицию "..." и ставим курсор туда
        cursor_position = cursor.position() - len("[/voice]")
        cursor.setPosition(cursor_position - 3)  # Перед "..."
        cursor.setPosition(cursor_position, QTextCursor.MoveMode.KeepAnchor)  # Выделяем "..."

        # Устанавливаем курсор обратно в текстовое поле
        self.text_input.setTextCursor(cursor)

        # Фокусируемся на текстовом поле
        self.text_input.setFocus()

        logger.debug(f"Вставлен тег голоса: {voice}")

    def _update_ui_state(self, state: str):
        """
        Централизованно обновляет состояние UI.
        Возможные состояния: 'idle', 'generating', 'has_audio', 'playing', 'paused'.
        """
        is_idle = state == 'idle'
        is_generating = state == 'generating'
        has_audio = state in ['has_audio', 'playing', 'paused']
        is_playing = state == 'playing'
        is_paused = state == 'paused'

        # Кнопка генерации
        self.generate_button.setEnabled(not is_generating)
        
        # Кнопки управления аудио
        self.play_button.setEnabled(has_audio and not is_playing)
        self.pause_button.setEnabled(is_playing)
        self.stop_button.setEnabled(is_playing or is_paused)
        self.save_button.setEnabled(has_audio)
        
        # Текст и иконки
        if is_paused:
            self.play_button.setText(" Продолжить")
            self.play_button.setIcon(qta.icon('fa5s.play', color='white'))
        else:
            self.play_button.setText(" Воспроизвести")
            self.play_button.setIcon(qta.icon('fa5s.play', color='white'))

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState):
        """Обработчик изменения состояния воспроизведения."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._update_ui_state('playing')
            self.status_bar.showMessage(AppConfig.Messages.PLAYING)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._update_ui_state('paused')
            self.status_bar.showMessage(AppConfig.Messages.PAUSED)
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self._update_ui_state('has_audio' if self.audio_data else 'idle')
            if self.audio_data:
                self.status_bar.showMessage("Готов к воспроизведению")

    # === ДЕЙСТВИЯ ===

    def _generate_speech(self):
        """Генерирует речь."""
        if not self.tts_core:
            StyledMessageBox.show_error(
                self, "❌ Ошибка",
                "TTS не инициализирован. Необходимо настроить API ключ.\n\n"
                "Откройте настройки и добавьте действующий API ключ.",
                self.settings_manager.get_theme()
            )
            return

        text = self.text_input.toPlainText().strip()
        current_index = self.voice_combo.currentIndex()
        voice = self.voice_combo.itemData(current_index) if current_index >= 0 else AppConfig.DEFAULT_VOICE

        # Валидация
        validation = self.tts_core.validate_request(text, voice)
        if not validation.is_valid:
            StyledMessageBox.show_error(
                self, "❌ Ошибка валидации",
                validation.message,
                self.settings_manager.get_theme()
            )
            return

        self._update_ui_state('generating')
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Создаем worker
        self.current_worker = self.tts_core.create_worker(text, voice)
        self.current_worker.finished.connect(self._on_generation_finished)
        self.current_worker.error.connect(self._on_generation_error)
        self.current_worker.progress.connect(self._on_generation_progress)
        self.current_worker.start()

        logger.info(f"Начата генерация речи: {len(text)} символов, голос {voice}")

    def _on_generation_progress(self, message: str):
        """Обработчик прогресса генерации."""
        self.status_bar.showMessage(message)
        current_value = self.progress_bar.value()
        if current_value < 90:
            self.progress_bar.setValue(current_value + 30)

    def _on_generation_finished(self, audio_data: bytes):
        """Обработчик успешной генерации."""
        self.audio_data = audio_data
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        self._update_ui_state('has_audio')
        self.status_bar.showMessage("Аудио успешно сгенерировано!", 3000)

        # Загружаем аудио в плеер
        result = self.audio_player.load_audio_data(audio_data)
        if not result.is_valid:
            StyledMessageBox.show_error(
                self, "❌ Ошибка",
                f"Ошибка загрузки аудио: {result.message}",
                self.settings_manager.get_theme()
            )

        # Сохраняем выбранный голос
        current_index = self.voice_combo.currentIndex()
        if current_index >= 0:
            voice = self.voice_combo.itemData(current_index)
            self.settings_manager.set_last_voice(voice)

        # Автовоспроизведение если включено
        if self.settings_manager.get_auto_play():
            self._play_speech()

        logger.info("Речь успешно сгенерирована")

    def _on_generation_error(self, error_message: str):
        """Обработчик ошибки генерации."""
        self.progress_bar.setVisible(False)
        self._update_ui_state('idle')

        StyledMessageBox.show_error(
            self, "❌ Ошибка генерации",
            error_message,
            self.settings_manager.get_theme()
        )
        self.status_bar.showMessage("Ошибка генерации", 3000)

    def _play_speech(self):
        """Воспроизводит аудио."""
        if not self.audio_data:
            StyledMessageBox.show_error(
                self, "❌ Ошибка",
                AppConfig.Messages.ERROR_NO_AUDIO,
                self.settings_manager.get_theme()
            )
            return

        result = self.audio_player.play()
        if not result.is_valid:
            StyledMessageBox.show_error(
                self, "❌ Ошибка воспроизведения",
                result.message,
                self.settings_manager.get_theme()
            )

    def _pause_speech(self):
        """Приостанавливает воспроизведение."""
        self.audio_player.pause()

    def _stop_speech(self):
        """Останавливает воспроизведение."""
        self.audio_player.stop()

    def _toggle_playback(self):
        """Переключает воспроизведение (пробел)."""
        player = self.audio_player.get_player()

        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._pause_speech()
        elif player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self._play_speech()
        elif self.audio_data:
            self._play_speech()

    def _save_speech(self):
        """Сохраняет сгенерированное аудио."""
        if not self.audio_data:
            StyledMessageBox.show_error(
                self, "❌ Ошибка",
                AppConfig.Messages.ERROR_NO_AUDIO,
                self.settings_manager.get_theme()
            )
            return

        # Получаем последнюю директорию сохранения
        last_directory = self.settings_manager.get_last_save_directory()

        # Показываем диалог сохранения
        file_path, _ = FileDialogHelper.get_audio_save_dialog(
            self, PYDUB_AVAILABLE, last_directory
        )

        if not file_path:
            return

        try:
            # Сохраняем директорию
            self.settings_manager.set_last_save_directory(os.path.dirname(file_path))

            # Определяем формат по расширению
            file_extension = os.path.splitext(file_path)[1].lower()

            self.status_bar.showMessage("Сохранение файла...")

            if file_extension == '.mp3':
                if not PYDUB_AVAILABLE:
                    StyledMessageBox.show_warning(
                        self, "⚠️ Предупреждение",
                        "Для сохранения в MP3 необходимо установить библиотеку pydub.\n\n"
                        "Выполните команду:\npip install pydub\n\n"
                        "Файл будет сохранен в формате WAV.",
                        self.settings_manager.get_theme()
                    )
                    # Меняем расширение на .wav
                    file_path = os.path.splitext(file_path)[0] + '.wav'
                    result = AudioFileManager.save_wav_file(file_path, self.audio_data)
                else:
                    # Создаем временный WAV файл
                    temp_wav = self.temp_manager.create_temp_file('.wav')
                    wav_result = AudioFileManager.save_wav_file(temp_wav, self.audio_data)

                    if wav_result.is_valid:
                        result = AudioFileManager.convert_to_mp3(temp_wav, file_path)
                    else:
                        result = wav_result
            else:
                # Сохраняем как WAV
                result = AudioFileManager.save_wav_file(file_path, self.audio_data)

            if result.is_valid:
                # Получаем информацию о файле
                file_info = AudioFileManager.get_audio_info(file_path)

                success_message = f"Файл сохранен: {os.path.basename(file_path)}\n\n"
                success_message += f"📁 Путь: {file_path}\n"

                if 'format' in file_info:
                    success_message += f"🎵 Формат: {file_info['format']}\n"

                if 'size' in file_info:
                    size_mb = file_info['size'] / (1024 * 1024)
                    success_message += f"📊 Размер: {size_mb:.2f} МБ\n"

                if file_extension == '.mp3':
                    success_message += f"📱 Совместим с WhatsApp"

                StyledMessageBox.show_success(
                    self, "✅ Успех",
                    success_message,
                    self.settings_manager.get_theme()
                )

                self.status_bar.showMessage(AppConfig.Messages.SAVED, 3000)
            else:
                StyledMessageBox.show_error(
                    self, "❌ Ошибка сохранения",
                    result.message,
                    self.settings_manager.get_theme()
                )

        except Exception as e:
            error_msg = f"Неожиданная ошибка при сохранении: {e}"
            logger.error(error_msg)
            StyledMessageBox.show_error(
                self, "❌ Ошибка",
                error_msg,
                self.settings_manager.get_theme()
            )

    def _preview_voice(self):
        """Предварительное прослушивание голоса."""
        if not self.tts_core:
            return

        current_index = self.voice_combo.currentIndex()
        if current_index < 0:
            return

        voice = self.voice_combo.itemData(current_index)
        preview_text = f"Привет! Меня зовут {voice}. Это образец моего голоса."

        # Создаем worker для генерации образца
        self.preview_worker = self.tts_core.create_worker(preview_text, voice)
        self.preview_worker.finished.connect(self._on_preview_finished)
        self.preview_worker.error.connect(lambda msg: StyledMessageBox.show_error(
            self, "❌ Ошибка", f"Ошибка генерации образца: {msg}", self.settings_manager.get_theme()
        ))
        self.preview_worker.start()

        self.status_bar.showMessage(f"Генерируется образец голоса {voice}...")

    def _on_preview_finished(self, audio_data: bytes):
        """Обработчик завершения генерации образца."""
        try:
            # Создаем временный плеер для образца
            temp_path = self.temp_manager.create_temp_file('.wav')
            result = AudioFileManager.save_wav_file(temp_path, audio_data)

            if result.is_valid:
                # Воспроизводим образец
                player = self.audio_player.get_player()
                player.setSource(QUrl.fromLocalFile(temp_path))
                player.play()

                self.status_bar.showMessage("Воспроизводится образец голоса", 3000)
            else:
                StyledMessageBox.show_error(
                    self, "❌ Ошибка",
                    f"Ошибка воспроизведения образца: {result.message}",
                    self.settings_manager.get_theme()
                )

        except Exception as e:
            StyledMessageBox.show_error(
                self, "❌ Ошибка",
                f"Ошибка воспроизведения образца: {e}",
                self.settings_manager.get_theme()
            )

    # === ДИАЛОГИ ===

    def _show_settings(self):
        """Показывает диалог настроек."""
        current_theme = self.settings_manager.get_theme()
        dialog = SettingsDialog(self, current_theme, self.settings_manager, self.settings_manager.get_encryption_status())

        # Подключаем сигналы для работы с API ключом
        dialog.change_api_key_requested.connect(self._handle_change_api_key_request)
        dialog.remove_api_key_requested.connect(self._handle_remove_api_key_request)

        # Устанавливаем текущие значения
        dialog.auto_play_checkbox.setChecked(self.settings_manager.get_auto_play())
        # save_window_pos_checkbox уже установлен в SettingsDialog ч��рез settings_manager

        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            # Сохраняем настройки темы и автовоспроизведения
            new_theme = dialog.get_selected_theme()
            auto_play = dialog.get_auto_play()
            save_window_pos = dialog.get_save_window_pos()

            if new_theme != current_theme:
                self.settings_manager.set_theme(new_theme)
                self._apply_theme()

            self.settings_manager.set_auto_play(auto_play)
            # Сохраняем настройку сохранения позиции окна
            # (хотя она используется только при запуске, сохраним для консистентности)
            # self.settings_manager.set_save_window_pos(save_window_pos) # Если такой метод будет добавлен

            # Сохраняем настройки разделителя голосов
            delimiter_enabled = dialog.get_delimiter_enabled()
            delimiter_string = dialog.get_delimiter_string()
            delimiter_voice_sequence = dialog.get_delimiter_voice_sequence()

            self.settings_manager.set_delimiter_enabled(delimiter_enabled)
            self.settings_manager.set_delimiter_string(delimiter_string)
            self.settings_manager.set_delimiter_voice_sequence(delimiter_voice_sequence)

            # Сохраняем настройки TTS
            use_native_multispeaker = dialog.get_use_native_multispeaker()
            self.settings_manager.set_use_native_multispeaker(use_native_multispeaker)

            self.status_bar.showMessage("Настройки сохранены", 2000)

    def _handle_change_api_key_request(self):
        """Обработчик запроса на изменение API ключа."""
        self._show_api_key_dialog(is_initial_setup=False)
        # После изменения ключа, возможно, потребуется обновить статус в диалоге настроек
        # Но так как диалог уже открыт, это может быть сложно.
        # Проще закрыть и открыть заново, или обновить только статус.
        # Пока просто переоткроем диалог настроек после закрытия диалога API ключа.
        # Это не идеальное решение, но рабочее.
        # В более сложном приложении можно было бы использовать сигналы для обновления.
        self.status_bar.showMessage("Измените API ключ", 2000)

    def _handle_remove_api_key_request(self):
        """Обработчик запроса на удаление API ключа."""
        confirm = StyledMessageBox.show_question(
            self, "Удалить API ключ?",
            "Вы уверены, что хотите удалить сохраненный API ключ?\n\n"
            "После удаления вам потребуется ввести новый ключ для работы с приложением.",
            self.settings_manager.get_theme()
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.settings_manager.remove_api_key()

            # Сбрасываем TTS core, так как ключ больше недоступен
            self.tts_core = None

            StyledMessageBox.show_success(
                self, "API ключ удален",
                "API ключ успешно удален.\n\n"
                "Для продолжения работы потребуется ввести новый API ключ.",
                self.settings_manager.get_theme()
            )

            self.status_bar.showMessage("API ключ удален. Требуется новый ключ для работы.", 5000)

            # Показываем диалог ввода нового ключа
            self._show_api_key_dialog(is_initial_setup=False)
        else:
            self.status_bar.showMessage("Удаление API ключа отменено", 2000)

    def _show_format_info(self):
        """Показывает информацию о форматах."""
        dialog = FormatInfoDialog(self, self.settings_manager.get_theme())
        dialog.exec()

    # === СОБЫТИЯ ОКНА ===

    def closeEvent(self, event):
        """Обработчик закрытия окна."""
        # Сохраняем геометрию окна
        geometry = self.geometry()
        self.settings_manager.save_window_geometry(
            geometry.x(), geometry.y(), geometry.width(), geometry.height()
        )

        # Останавливаем воспроизведение
        self.audio_player.stop()

        # Очищаем ресурсы
        self.audio_player.cleanup()
        self.temp_manager.cleanup()

        # Останавливаем worker если он работает
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait(3000)  # Ждем 3 секунды

        logger.info("Приложение закрыто")
        event.accept()


def main():
    """Главная функция приложения."""
    app = QApplication(sys.argv)

    # Настройка приложения
    app.setApplicationName(AppConfig.APP_NAME)
    app.setApplicationVersion(AppConfig.APP_VERSION)
    app.setOrganizationName(AppConfig.ORGANIZATION)

    # Создание и показ главного окна
    try:
        window = ModernTTSApp()
        window.show()

        # Запуск приложения
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске приложения: {e}")

        # Показываем сообщение об ошибке
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Критическая ошибка")
        msg.setText(f"Не удалось запустить приложение:\n\n{e}")
        msg.exec()

        sys.exit(1)


if __name__ == "__main__":
    main()
