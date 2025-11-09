"""
Менеджер стилей для TTS приложения.
Централизованное управление CSS стилями для устранения дублирования.
"""

from config import AppConfig


class StyleManager:
    """Менеджер стилей приложения."""
    
    @staticmethod
    def get_button_style(color_type: str = "primary", size: str = "normal") -> str:
        """Возвращает стиль для кнопок."""
        colors = AppConfig.Colors
        sizes = AppConfig.Sizes
        
        if color_type == "primary":
            bg_color = f"stop:0 {colors.PRIMARY}, stop:1 {colors.PRIMARY_PRESSED}"
            hover_color = f"stop:0 {colors.PRIMARY_HOVER}, stop:1 {colors.PRIMARY}"
            pressed_color = f"stop:0 {colors.PRIMARY_PRESSED}, stop:1 #2a6aa3"
        elif color_type == "success":
            bg_color = f"stop:0 {colors.SUCCESS}, stop:1 #1e7e34"
            hover_color = f"stop:0 {colors.SUCCESS_HOVER}, stop:1 {colors.SUCCESS}"
            pressed_color = f"stop:0 #1e7e34, stop:1 #155724"
        elif color_type == "danger":
            bg_color = f"stop:0 {colors.DANGER}, stop:1 #c82333"
            hover_color = f"stop:0 {colors.DANGER_HOVER}, stop:1 {colors.DANGER}"
            pressed_color = f"stop:0 #c82333, stop:1 #bd2130"
        else:
            bg_color = f"stop:0 {colors.PRIMARY}, stop:1 {colors.PRIMARY_PRESSED}"
            hover_color = f"stop:0 {colors.PRIMARY_HOVER}, stop:1 {colors.PRIMARY}"
            pressed_color = f"stop:0 {colors.PRIMARY_PRESSED}, stop:1 #2a6aa3"
        
        height = sizes.BUTTON_LARGE_HEIGHT if size == "large" else sizes.BUTTON_MIN_HEIGHT
        
        return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {bg_color});
            border: none;
            border-radius: {sizes.BORDER_RADIUS}px;
            padding: {sizes.PADDING_MEDIUM}px {sizes.PADDING_LARGE * 2}px;
            font-size: {AppConfig.Fonts.SIZE_MEDIUM}px;
            font-weight: {AppConfig.Fonts.WEIGHT_BOLD};
            color: white;
            min-height: {height}px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {hover_color});
        }}
        
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {pressed_color});
        }}
        
        QPushButton:disabled {{
            background-color: #555555;
            color: #888888;
        }}
        """
    
    @staticmethod
    def get_text_edit_style(theme: str = "dark") -> str:
        """Возвращает стиль для текстовых полей."""
        colors = AppConfig.Colors
        sizes = AppConfig.Sizes

        if theme == "dark":
            bg_color = colors.DARK_WIDGET_BG
            border_color = colors.DARK_BORDER
            text_color = colors.DARK_TEXT
            scroll_color = colors.DARK_BORDER
            scroll_handle = colors.DARK_TEXT_SECONDARY
        else:
            bg_color = colors.LIGHT_WIDGET_BG
            border_color = colors.LIGHT_BORDER
            text_color = colors.LIGHT_TEXT
            scroll_color = colors.LIGHT_BORDER
            scroll_handle = colors.LIGHT_TEXT_SECONDARY

        return f"""
        QTextEdit {{
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: {sizes.BORDER_RADIUS_LARGE}px;
            padding: {sizes.PADDING_LARGE}px;
            font-size: {AppConfig.Fonts.SIZE_LARGE}px;
            color: {text_color};
            selection-background-color: {colors.PRIMARY};
        }}

        QTextEdit:focus {{
            border: 2px solid {colors.PRIMARY};
        }}

        QTextEdit QScrollBar:vertical {{
            border: none;
            background: {bg_color};
            width: 10px;
            border-radius: 5px;
            margin: 0px;
        }}

        QTextEdit QScrollBar::handle:vertical {{
            background: {scroll_handle};
            min-height: 20px;
            border-radius: 4px;
        }}

        QTextEdit QScrollBar::handle:vertical:hover {{
            background: {scroll_color};
        }}

        QTextEdit QScrollBar::add-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}

        QTextEdit QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        """
    
    @staticmethod
    def get_combo_box_style(theme: str = "dark") -> str:
        """Возвращает стиль для комбо-боксов."""
        colors = AppConfig.Colors
        sizes = AppConfig.Sizes
        
        if theme == "dark":
            bg_color = colors.DARK_WIDGET_BG
            border_color = colors.DARK_BORDER
            text_color = colors.DARK_TEXT
        else:
            bg_color = colors.LIGHT_WIDGET_BG
            border_color = colors.LIGHT_BORDER
            text_color = colors.LIGHT_TEXT
        
        return f"""
        QComboBox {{
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: {sizes.BORDER_RADIUS}px;
            padding: {sizes.PADDING_SMALL}px {sizes.PADDING_LARGE}px;
            font-size: {AppConfig.Fonts.SIZE_MEDIUM}px;
            color: {text_color};
            min-height: 25px;
        }}
        
        QComboBox:focus {{
            border: 2px solid {colors.PRIMARY};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {text_color};
        }}
        """
    
    @staticmethod
    def get_dialog_style(theme: str = "dark") -> str:
        """Возвращает стиль для диалогов."""
        colors = AppConfig.Colors
        sizes = AppConfig.Sizes
        
        if theme == "dark":
            bg_color = colors.DARK_BG
            text_color = colors.DARK_TEXT
            secondary_text = colors.DARK_TEXT_SECONDARY
            widget_bg = colors.DARK_WIDGET_BG
            border_color = colors.DARK_BORDER
        else:
            bg_color = colors.LIGHT_BG
            text_color = colors.LIGHT_TEXT
            secondary_text = colors.LIGHT_TEXT_SECONDARY
            widget_bg = colors.LIGHT_WIDGET_BG
            border_color = colors.LIGHT_BORDER
        
        button_style = StyleManager.get_button_style("primary")
        
        return f"""
        QDialog {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        QLabel {{
            color: {text_color};
            font-size: {AppConfig.Fonts.SIZE_MEDIUM}px;
            line-height: 1.4;
        }}
        
        QLineEdit {{
            background-color: {widget_bg};
            border: 2px solid {border_color};
            border-radius: {sizes.BORDER_RADIUS}px;
            padding: {sizes.PADDING_MEDIUM}px;
            font-size: {AppConfig.Fonts.SIZE_MEDIUM}px;
            color: {text_color};
            min-height: 25px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {colors.PRIMARY};
        }}
        
        QGroupBox {{
            font-size: {AppConfig.Fonts.SIZE_LARGE}px;
            font-weight: {AppConfig.Fonts.WEIGHT_BOLD};
            color: {text_color};
            border: 2px solid {border_color};
            border-radius: {sizes.BORDER_RADIUS_LARGE}px;
            margin-top: {sizes.SPACING_SMALL}px;
            padding-top: {sizes.SPACING_SMALL}px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {sizes.SPACING_SMALL}px;
            padding: 0 {sizes.PADDING_SMALL}px 0 {sizes.PADDING_SMALL}px;
            color: {text_color};
        }}
        
        QRadioButton {{
            color: {text_color};
            font-size: {AppConfig.Fonts.SIZE_MEDIUM}px;
            spacing: {sizes.PADDING_MEDIUM}px;
        }}
        
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}
        
        QRadioButton::indicator:unchecked {{
            border: 2px solid {border_color};
            border-radius: 8px;
            background-color: {widget_bg};
        }}
        
        QRadioButton::indicator:checked {{
            border: 2px solid {colors.PRIMARY};
            border-radius: 8px;
            background-color: {colors.PRIMARY};
        }}
        
        {button_style}
        """
    
    @staticmethod
    def get_main_window_style(theme: str = "dark") -> str:
        """Возвращает основной стиль для главного окна."""
        colors = AppConfig.Colors
        sizes = AppConfig.Sizes
        
        if theme == "dark":
            bg_gradient = f"stop:0 {colors.DARK_BG}, stop:1 {colors.DARK_BG_SECONDARY}"
            text_color = colors.DARK_TEXT
            border_color = colors.DARK_BORDER
            widget_bg = colors.DARK_WIDGET_BG
            muted_text = colors.DARK_TEXT_MUTED
        else:
            bg_gradient = f"stop:0 {colors.LIGHT_BG}, stop:1 {colors.LIGHT_BG_SECONDARY}"
            text_color = colors.LIGHT_TEXT
            border_color = colors.LIGHT_BORDER
            widget_bg = colors.LIGHT_WIDGET_BG
            muted_text = colors.LIGHT_TEXT_MUTED
        
        text_edit_style = StyleManager.get_text_edit_style(theme)
        button_style = StyleManager.get_button_style("primary")
        combo_style = StyleManager.get_combo_box_style(theme)
        
        return f"""
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {bg_gradient});
            color: {text_color};
        }}
        
        {text_edit_style}
        {button_style}
        {combo_style}
        
        QLabel {{
            color: {text_color};
            font-size: {AppConfig.Fonts.SIZE_MEDIUM}px;
            font-weight: {AppConfig.Fonts.WEIGHT_BOLD};
        }}
        
        QProgressBar {{
            border: 2px solid {border_color};
            border-radius: {sizes.BORDER_RADIUS}px;
            background-color: {widget_bg};
            text-align: center;
            font-size: {AppConfig.Fonts.SIZE_SMALL}px;
            color: {text_color};
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {colors.PRIMARY}, stop:1 {colors.PRIMARY_PRESSED});
            border-radius: 4px;
        }}
        
        QGroupBox {{
            font-size: {AppConfig.Fonts.SIZE_LARGE}px;
            font-weight: {AppConfig.Fonts.WEIGHT_BOLD};
            color: {text_color};
            border: 2px solid {border_color};
            border-radius: {sizes.BORDER_RADIUS_LARGE}px;
            margin-top: {sizes.SPACING_SMALL}px;
            padding-top: {sizes.SPACING_SMALL}px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {sizes.SPACING_SMALL}px;
            padding: 0 {sizes.PADDING_SMALL}px 0 {sizes.PADDING_SMALL}px;
        }}
        
        QStatusBar {{
            background-color: {colors.DARK_BG if theme == 'dark' else colors.LIGHT_BG};
            color: {text_color};
            border-top: 1px solid {border_color};
        }}
        """
