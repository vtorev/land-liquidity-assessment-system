#!/usr/bin/env python3
"""
Скрипт для автоматической загрузки системы на GitHub
"""

import os
import subprocess
import sys
from pathlib import Path


class GitHubUploader:
    def __init__(self, repo_url: str, project_root: str = "."):
        self.repo_url = repo_url
        self.project_root = Path(project_root)
        self.git_commands = []
        
    def check_git_installed(self) -> bool:
        """Проверка установки Git"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Git установлен: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git не установлен. Установите Git и добавьте в PATH.")
            return False
    
    def check_git_config(self) -> bool:
        """Проверка настройки Git"""
        try:
            # Проверка имени пользователя
            result = subprocess.run(['git', 'config', 'user.name'], 
                                  capture_output=True, text=True, check=True)
            username = result.stdout.strip()
            
            # Проверка email
            result = subprocess.run(['git', 'config', 'user.email'], 
                                  capture_output=True, text=True, check=True)
            email = result.stdout.strip()
            
            print(f"✅ Git настроен: {username} <{email}>")
            return True
        except subprocess.CalledProcessError:
            print("❌ Git не настроен. Выполните:")
            print("  git config --global user.name 'Ваше Имя'")
            print("  git config --global user.email 'ваш@email.com'")
            return False
    
    def init_git_repo(self) -> bool:
        """Инициализация Git репозитория"""
        try:
            if (self.project_root / ".git").exists():
                print("✅ Git репозиторий уже инициализирован")
                return True
            
            subprocess.run(['git', 'init'], cwd=self.project_root, check=True)
            print("✅ Git репозиторий инициализирован")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка инициализации Git: {e}")
            return False
    
    def add_files_to_git(self) -> bool:
        """Добавление файлов в Git"""
        try:
            # Проверка .gitignore
            if not (self.project_root / ".gitignore").exists():
                print("⚠️  Предупреждение: .gitignore не найден")
            
            subprocess.run(['git', 'add', '.'], cwd=self.project_root, check=True)
            print("✅ Файлы добавлены в Git")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка добавления файлов: {e}")
            return False
    
    def create_initial_commit(self) -> bool:
        """Создание первого коммита"""
        try:
            commit_message = """Initial commit: Land liquidity assessment system with ML models and Telegram bot

Features:
- Backend API (Python/FastAPI) with ML models (CatBoost, Random Forest)
- Frontend application (React) with interactive maps and visualization
- Telegram bot for convenient access
- Docker containerization for all services
- Celery for asynchronous tasks
- PostgreSQL database
- Redis for caching
- CI/CD with GitHub Actions
- Complete documentation and deployment guides
"""
            
            subprocess.run(['git', 'commit', '-m', commit_message], 
                         cwd=self.project_root, check=True)
            print("✅ Первый коммит создан")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания коммита: {e}")
            return False
    
    def add_remote_repo(self) -> bool:
        """Добавление удаленного репозитория"""
        try:
            subprocess.run(['git', 'remote', 'add', 'origin', self.repo_url], 
                         cwd=self.project_root, check=True)
            print(f"✅ Удаленный репозиторий добавлен: {self.repo_url}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка добавления удаленного репозитория: {e}")
            return False
    
    def push_to_github(self) -> bool:
        """Загрузка на GitHub"""
        try:
            # Создание ветки main и push
            subprocess.run(['git', 'branch', '-M', 'main'], 
                         cwd=self.project_root, check=True)
            
            result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                                  cwd=self.project_root, check=True)
            
            print("✅ Код успешно загружен на GitHub!")
            print(f"🌐 Репозиторий: {self.repo_url}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка загрузки на GitHub: {e}")
            print("💡 Возможно, потребуется аутентификация через GitHub CLI или Personal Access Token")
            return False
    
    def check_repo_status(self) -> bool:
        """Проверка статуса репозитория"""
        try:
            result = subprocess.run(['git', 'status'], 
                                  cwd=self.project_root, 
                                  capture_output=True, text=True, check=True)
            print("📊 Статус репозитория:")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка проверки статуса: {e}")
            return False
    
    def run_full_upload(self) -> bool:
        """Запуск полной загрузки"""
        print("🚀 Начинаем загрузку системы на GitHub...")
        print("=" * 60)
        
        steps = [
            ("Проверка Git", self.check_git_installed),
            ("Проверка конфигурации Git", self.check_git_config),
            ("Инициализация репозитория", self.init_git_repo),
            ("Добавление файлов", self.add_files_to_git),
            ("Создание коммита", self.create_initial_commit),
            ("Добавление удаленного репозитория", self.add_remote_repo),
            ("Загрузка на GitHub", self.push_to_github),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Шаг '{step_name}' не выполнен")
                return False
            print(f"✅ Шаг '{step_name}' завершен")
        
        print("\n" + "=" * 60)
        print("🎉 Загрузка на GitHub завершена успешно!")
        print(f"🌐 Ваш репозиторий: {self.repo_url}")
        print("\n💡 Дальнейшие шаги:")
        print("1. Перейдите на GitHub и проверьте репозиторий")
        print("2. Настройте GitHub Actions (если нужно)")
        print("3. Пригласите команду в репозиторий")
        print("4. Начните разработку!")
        
        return True


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python upload_to_github.py <URL_репозитория>")
        print("Пример: python upload_to_github.py https://github.com/username/repo.git")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    project_root = "."
    
    print(f"🎯 Целевой репозиторий: {repo_url}")
    print(f"📁 Рабочая директория: {project_root}")
    print()
    
    uploader = GitHubUploader(repo_url, project_root)
    
    # Проверка существования директории
    if not Path(project_root).exists():
        print(f"❌ Директория {project_root} не существует")
        sys.exit(1)
    
    # Запуск загрузки
    if uploader.run_full_upload():
        print("\n✅ Загрузка завершена успешно!")
        sys.exit(0)
    else:
        print("\n❌ Загрузка не удалась")
        sys.exit(1)


if __name__ == "__main__":
    main()