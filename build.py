# -*- coding: utf-8 -*-
"""
Скрипт для сборки рефакторированного приложения ModernTTS в один исполняемый файл (.exe)
с помощью PyInstaller.

Этот скрипт настроен для работы с модульной архитектурой приложения,
включая все необходимые модули и зависимости.

Требования:
- PyInstaller: pip install pyinstaller
- Все зависимости проекта должны быть установлены

Для сборки запустите этот скрипт:
python build.py

Собранный файл будет находиться в папке 'dist'.
"""

import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

# --- НАСТРОЙКИ СБОРКИ ---

# Имя приложения (будет использовано для .exe и .spec файла)
APP_NAME = 'ModernTTS'

# Главный файл приложения (в текущей директории)
SCRIPT_FILE = 'modern_tts.py'

# Модули приложения, которые нужно включить в сборку
APP_MODULES = [
    'config.py',
    'settings_manager.py', 
    'audio_manager.py',
    'validation.py',
    'style_manager.py',
    'ui_components.py'
]

# Дополнительные файлы для включения в сборку
ADDITIONAL_FILES = [
    '.env.example',  # Пример файла конфигурации
    'ffmpeg.exe',    # Добавляем FFmpeg
    'ffprobe.exe',   # Добавляем FFprobe
]

# Иконка для .exe файла (должна быть в формате .ico)
ICON_FILE = ''  # 'app.ico' если есть иконка

# --- ПРОВЕРКИ ---
def check_files():
    """Проверяет наличие всех необходимых файлов."""
    missing_files = []
    
    # Проверяем главный скрипт
    if not os.path.exists(SCRIPT_FILE):
        missing_files.append(SCRIPT_FILE)
    
    # Проверяем модули приложения
    for module in APP_MODULES:
        if not os.path.exists(module):
            missing_files.append(module)
    
    if missing_files:
        print("❌ ОШИБКА: Не найдены следующие файлы:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nУбедитесь, что:")
        print("1. Скрипт build.py находится в той же папке, что и файлы приложения")
        print("2. Все модули приложения присутствуют в текущей директории")
        print("3. Файл modern_tts.py существует")
        return False
    
    return True

def get_pyinstaller_params():
    """Формирует параметры для PyInstaller."""
    params = [
        '--name=%s' % APP_NAME,
        '--onefile',                    # Один исполняемый файл
        '--windowed',                   # Без консольного окна (включая ffmpeg/ffprobe)
        '--clean',                      # Очистка кэша
        '--log-level=INFO',             # Уровень логирования
        '--noconfirm',                  # Не спрашивать подтверждения
    ]
    
    # Добавляем иконку, если она указана и существует
    if ICON_FILE and os.path.exists(ICON_FILE):
        params.append('--icon=%s' % ICON_FILE)
        print(f"✅ Используется иконка: {ICON_FILE}")
    elif ICON_FILE:
        print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Файл иконки не найден: {ICON_FILE}")
    
    # Скрытые импорты - библиотеки, которые PyInstaller может не обнаружить автоматически
    hidden_imports = [
        # PyQt6 модули
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtMultimedia',
        
        # Иконки и стили
        'qtawesome',
        'qtawesome.iconic_font',
        
        # Google API
        'google.genai',
        'google.genai.types',
        'google.api_core',
        'google.auth',
        'google.oauth2',
        'google.protobuf',
        
        # Аудио обработка
        'pydub',
        'pydub.utils',
        'wave',
        'tempfile',
        
        # Криптография и безопасность
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        
        # Конфигурация
        'dotenv',
        'python-dotenv',
        
        # Системные модули
        'pathlib',
        'logging',
        'json',
        'typing',
        
        # Дополнительные модули
        'pkg_resources',
        'pkg_resources.py2_warn',
        'requests',
        'urllib3',
        'certifi',
    ]
    
    # Добавляем скрытые импорты
    for hidden_import in hidden_imports:
        params.append('--hidden-import=%s' % hidden_import)
    
    # Добавляем дополнительные файлы
    for additional_file in ADDITIONAL_FILES:
        if os.path.exists(additional_file):
            # Для ffmpeg.exe и ffprobe.exe используем --add-binary, чтобы они были в корне
            if additional_file in ['ffmpeg.exe', 'ffprobe.exe']:
                params.append('--add-binary=%s;.' % additional_file)
                print(f"✅ Добавлен бинарный файл: {additional_file}")
            else:
                params.append('--add-data=%s;.' % additional_file)
                print(f"✅ Добавлен файл данных: {additional_file}")
    
    # Исключаем ненужные модули для уменьшения размера
    exclude_modules = [
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
    ]
    
    for exclude_module in exclude_modules:
        params.append('--exclude-module=%s' % exclude_module)
    
    # Добавляем основной скрипт в конец
    params.append(SCRIPT_FILE)
    
    return params

def print_build_info():
    """Выводит информацию о сборке."""
    print("=" * 70)
    print(f"🚀 СБОРКА ПРИЛОЖЕНИЯ '{APP_NAME}'")
    print("=" * 70)
    print(f"📁 Текущая директория: {os.getcwd()}")
    print(f"📄 Главный скрипт: {SCRIPT_FILE}")
    print(f"🔧 Модули приложения:")
    for module in APP_MODULES:
        status = "✅" if os.path.exists(module) else "❌"
        print(f"   {status} {module}")
    print("=" * 70)

def cleanup_build_artifacts():
    """Очищает артефакты предыдущих сборок."""
    artifacts = ['build', 'dist', f'{APP_NAME}.spec']
    
    for artifact in artifacts:
        if os.path.exists(artifact):
            if os.path.isdir(artifact):
                shutil.rmtree(artifact)
                print(f"🗑️ Удалена папка: {artifact}")
            else:
                os.remove(artifact)
                print(f"🗑️ Удален файл: {artifact}")

def main():
    """Главная функция сборки."""
    print_build_info()
    
    # Проверяем наличие файлов
    if not check_files():
        sys.exit(1)
    
    # Очищаем артефакты предыдущих сборок
    cleanup_build_artifacts()
    
    # Получаем параметры для PyInstaller
    params = get_pyinstaller_params()
    
    print("\n🔨 Начинается процесс сборки...")
    print("⏳ Это может занять несколько минут...")
    
    try:
        # Запускаем PyInstaller
        PyInstaller.__main__.run(params)
        
        # Проверяем результат
        exe_path = os.path.join('dist', f'{APP_NAME}.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # Размер в МБ
            print("\n" + "=" * 70)
            print("✅ СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
            print("=" * 70)
            print(f"📦 Исполняемый файл: {exe_path}")
            print(f"📊 Размер файла: {file_size:.1f} МБ")
            print(f"🎯 Готов к распространению!")
            print("=" * 70)
        else:
            print("\n❌ ОШИБКА: Исполняемый файл не был создан!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ОШИБКА СБОРКИ: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()