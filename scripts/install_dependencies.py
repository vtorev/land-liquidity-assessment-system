#!/usr/bin/env python3
"""
Скрипт для автоматической установки зависимостей системы
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Выполнить команду и вывести результат"""
    print(f"🔧 {description}")
    print(f"Команда: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - УСПЕШНО")
            if result.stdout.strip():
                print(f"Вывод: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - ОШИБКА")
            print(f"Ошибка: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - ТАЙМАУТ")
        return False
    except Exception as e:
        print(f"💥 {description} - ИСКЛЮЧЕНИЕ: {e}")
        return False

def install_python_dependencies():
    """Установка Python зависимостей"""
    print("🐍 Установка Python зависимостей...")
    
    # Проверяем наличие requirements.txt
    if not Path('requirements.txt').exists():
        print("❌ Файл requirements.txt не найден")
        return False
    
    # Устанавливаем зависимости
    success = run_command(
        "pip install -r requirements.txt",
        "Установка Python зависимостей"
    )
    
    if success:
        print("✅ Python зависимости установлены")
    else:
        print("❌ Не удалось установить Python зависимости")
    
    return success

def install_frontend_dependencies():
    """Установка frontend зависимостей"""
    print("📦 Установка frontend зависимостей...")
    
    # Проверяем наличие frontend директории
    if not Path('frontend').exists():
        print("❌ Директория frontend не найдена")
        return False
    
    # Проверяем наличие package.json
    if not Path('frontend/package.json').exists():
        print("❌ Файл frontend/package.json не найден")
        return False
    
    # Переходим в frontend директорию и устанавливаем зависимости
    os.chdir('frontend')
    
    success = run_command(
        "npm install",
        "Установка frontend зависимостей"
    )
    
    # Возвращаемся в корневую директорию
    os.chdir('..')
    
    if success:
        print("✅ Frontend зависимости установлены")
    else:
        print("❌ Не удалось установить frontend зависимости")
    
    return success

def check_docker():
    """Проверка Docker"""
    print("🐳 Проверка Docker...")
    
    success = run_command(
        "docker --version",
        "Проверка Docker"
    )
    
    if success:
        print("✅ Docker доступен")
    else:
        print("⚠️  Docker не найден. Рекомендуется установить Docker для контейнеризации.")
    
    return success

def check_nodejs():
    """Проверка Node.js"""
    print("🟢 Проверка Node.js...")
    
    success = run_command(
        "node --version",
        "Проверка Node.js"
    )
    
    if success:
        print("✅ Node.js доступен")
    else:
        print("⚠️  Node.js не найден. Рекомендуется установить Node.js для frontend разработки.")
    
    return success

def check_npm():
    """Проверка npm"""
    print("📦 Проверка npm...")
    
    success = run_command(
        "npm --version",
        "Проверка npm"
    )
    
    if success:
        print("✅ npm доступен")
    else:
        print("⚠️  npm не найден.")
    
    return success

def main():
    """Основная функция"""
    print("🚀 Автоматическая установка зависимостей системы оценки ликвидности земельных участков")
    print("=" * 80)
    
    # Проверяем текущую директорию
    if not Path('requirements.txt').exists():
        print("❌ Требуется запуск из корневой директории проекта")
        return False
    
    results = []
    
    # Устанавливаем Python зависимости
    results.append(("Python зависимости", install_python_dependencies()))
    
    # Проверяем Node.js и npm
    results.append(("Node.js", check_nodejs()))
    results.append(("npm", check_npm()))
    
    # Устанавливаем frontend зависимости (если npm доступен)
    if check_npm():
        results.append(("Frontend зависимости", install_frontend_dependencies()))
    else:
        print("⚠️  Пропуск установки frontend зависимостей (npm недоступен)")
        results.append(("Frontend зависимости", False))
    
    # Проверяем Docker
    results.append(("Docker", check_docker()))
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 Результаты установки:")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        status = "✅ УСПЕШНО" if result else "❌ ПРОВАЛЕНО"
        print(f"{check_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 80)
    print(f"Всего проверок: {len(results)}")
    print(f"Успешно: {passed}")
    print(f"Провалено: {failed}")
    
    if failed == 0:
        print("\n🎉 Все зависимости установлены успешно!")
        print("\nСледующие шаги:")
        print("1. Скопируйте .env.example в .env и настройте переменные")
        print("2. Запустите: ./scripts/start.sh")
    elif failed <= 2:
        print(f"\n⚠️  Установлено с {failed} предупреждениями")
        print("Система может работать, но рекомендуется установить недостающие компоненты")
    else:
        print(f"\n❌ Критические ошибки: {failed}")
        print("Рекомендуется установить недостающие зависимости вручную")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)