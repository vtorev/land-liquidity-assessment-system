#!/usr/bin/env python3
"""
Скрипт для проверки зависимостей и готовности системы к запуску
"""

import sys
import subprocess
import importlib
from pathlib import Path
import json

def check_python_version():
    """Проверка версии Python"""
    print("🔍 Проверка версии Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - требуется 3.8+")
        return False

def check_package(package_name, import_name=None):
    """Проверка установленного пакета"""
    try:
        if import_name:
            importlib.import_module(import_name)
        else:
            importlib.import_module(package_name)
        print(f"✅ {package_name} - установлен")
        return True
    except ImportError:
        print(f"❌ {package_name} - не установлен")
        return False

def check_docker():
    """Проверка Docker"""
    print("🔍 Проверка Docker...")
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker - {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker не доступен")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker не найден")
        return False

def check_docker_compose():
    """Проверка Docker Compose"""
    print("🔍 Проверка Docker Compose...")
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker Compose - {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker Compose не доступен")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker Compose не найден")
        return False

def check_nodejs():
    """Проверка Node.js"""
    print("🔍 Проверка Node.js...")
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Node.js - {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js не доступен")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Node.js не найден")
        return False

def check_npm():
    """Проверка npm"""
    print("🔍 Проверка npm...")
    try:
        result = subprocess.run(['npm', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ npm - {result.stdout.strip()}")
            return True
        else:
            print("❌ npm не доступен")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ npm не найден")
        return False

def check_required_files():
    """Проверка наличия обязательных файлов"""
    print("🔍 Проверка обязательных файлов...")
    required_files = [
        'requirements.txt',
        'frontend/package.json',
        'docker-compose.yml',
        'Dockerfile.backend',
        'frontend/Dockerfile',
        'config/settings.py',
        '.env.example'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - найден")
        else:
            print(f"❌ {file_path} - отсутствует")
            all_exist = False
    
    return all_exist

def check_environment_variables():
    """Проверка переменных окружения"""
    print("🔍 Проверка переменных окружения...")
    
    # Проверяем наличие .env.example
    env_example = Path('.env.example')
    if not env_example.exists():
        print("❌ Файл .env.example не найден")
        return False
    
    # Читаем пример переменных
    with open(env_example, 'r') as f:
        content = f.read()
    
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL', 
        'CELERY_BROKER_URL',
        'SECRET_KEY'
    ]
    
    for var in required_vars:
        if var in content:
            print(f"✅ {var} - определена в .env.example")
        else:
            print(f"⚠️  {var} - не найдена в .env.example")
    
    return True

def check_python_dependencies():
    """Проверка Python зависимостей"""
    print("🔍 Проверка Python зависимостей...")
    
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('sqlalchemy', 'sqlalchemy'),
        ('alembic', 'alembic'),
        ('psycopg2-binary', 'psycopg2'),
        ('redis', 'redis'),
        ('celery', 'celery'),
        ('requests', 'requests'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('scikit-learn', 'sklearn'),
        ('catboost', 'catboost'),
        ('geoalchemy2', 'geoalchemy2'),
        ('shap', 'shap'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('python-dotenv', 'dotenv')
    ]
    
    all_installed = True
    for package_name, import_name in required_packages:
        if not check_package(package_name, import_name):
            all_installed = False
    
    return all_installed

def check_frontend_dependencies():
    """Проверка frontend зависимостей"""
    print("🔍 Проверка frontend зависимостей...")
    
    package_json = Path('frontend/package.json')
    if not package_json.exists():
        print("❌ frontend/package.json не найден")
        return False
    
    with open(package_json, 'r') as f:
        package_data = json.load(f)
    
    dependencies = package_data.get('dependencies', {})
    dev_dependencies = package_data.get('devDependencies', {})
    
    required_deps = [
        'next', 'react', 'react-dom', '@hookform/resolvers', 'zod',
        'react-hot-toast', 'recharts', 'leaflet', 'react-leaflet'
    ]
    
    all_found = True
    for dep in required_deps:
        if dep in dependencies or dep in dev_dependencies:
            print(f"✅ {dep} - найден в package.json")
        else:
            print(f"❌ {dep} - не найден в package.json")
            all_found = False
    
    return all_found

def main():
    """Основная функция проверки"""
    print("🚀 Запуск проверки зависимостей системы оценки ликвидности земельных участков")
    print("=" * 80)
    
    checks = [
        ("Python версия", check_python_version),
        ("Обязательные файлы", check_required_files),
        ("Переменные окружения", check_environment_variables),
        ("Python зависимости", check_python_dependencies),
        ("Frontend зависимости", check_frontend_dependencies),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Node.js", check_nodejs),
        ("npm", check_npm),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 40)
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 80)
    print("📊 Результаты проверки:")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        status = "✅ ПРОЙДЕНА" if result else "❌ ПРОВАЛЕНА"
        print(f"{check_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 80)
    print(f"Всего проверок: {len(results)}")
    print(f"Пройдено: {passed}")
    print(f"Провалено: {failed}")
    
    if failed == 0:
        print("\n🎉 Все проверки пройдены! Система готова к запуску.")
        print("\nДля запуска системы выполните:")
        print("1. Скопируйте .env.example в .env и настройте переменные")
        print("2. Запустите: ./scripts/start.sh")
        return True
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Пожалуйста, устраните их перед запуском.")
        print("\nРекомендуемые действия:")
        print("1. Установите недостающие зависимости: pip install -r requirements.txt")
        print("2. Установите frontend зависимости: cd frontend && npm install")
        print("3. Убедитесь, что Docker и Node.js установлены")
        print("4. Скопируйте .env.example в .env и настройте переменные")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)