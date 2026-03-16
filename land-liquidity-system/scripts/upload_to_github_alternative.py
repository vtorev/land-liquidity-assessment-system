#!/usr/bin/env python3
"""
Альтернативный скрипт для загрузки системы на GitHub без необходимости установки Git
"""

import os
import subprocess
import sys
import zipfile
import tempfile
import shutil
from pathlib import Path
import requests
import json


class GitHubUploaderAlternative:
    def __init__(self, repo_url: str, project_root: str = "."):
        self.repo_url = repo_url
        self.project_root = Path(project_root)
        self.repo_name = repo_url.split('/')[-1].replace('.git', '')
        self.username = repo_url.split('/')[-2]
        
    def check_github_cli(self) -> bool:
        """Проверка установки GitHub CLI"""
        try:
            result = subprocess.run(['gh', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ GitHub CLI установлен: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ GitHub CLI не установлен")
            return False
    
    def install_github_cli(self) -> bool:
        """Инструкция по установке GitHub CLI"""
        print("💡 Инструкция по установке GitHub CLI:")
        print("1. Скачайте с https://cli.github.com/")
        print("2. Установите GitHub CLI")
        print("3. Выполните: gh auth login")
        print("4. Повторите загрузку")
        return False
    
    def create_zip_archive(self) -> str:
        """Создание ZIP архива с проектом"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                temp_path = temp_file.name
            
            print("📦 Создание архива проекта...")
            
            # Создаем архив
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.project_root):
                    # Пропускаем системные директории
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                    
                    for file in files:
                        if file.startswith('.') and file != '.gitignore':
                            continue
                        
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.project_root)
                        zipf.write(file_path, arcname)
            
            print(f"✅ Архив создан: {temp_path}")
            return temp_path
        except Exception as e:
            print(f"❌ Ошибка создания архива: {e}")
            return ""
    
    def upload_via_github_cli(self, zip_path: str) -> bool:
        """Загрузка через GitHub CLI"""
        try:
            # Создание релиза через GitHub CLI
            tag_name = f"v1.0.0-{int(os.path.getmtime(zip_path))}"
            release_name = "Initial Release"
            release_body = """Initial commit: Land liquidity assessment system with ML models and Telegram bot

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
            
            # Создание релиза
            cmd = [
                'gh', 'release', 'create', tag_name,
                '--repo', f"{self.username}/{self.repo_name}",
                '--title', release_name,
                '--notes', release_body,
                zip_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✅ Релиз создан через GitHub CLI")
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания релиза: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
    
    def upload_via_api(self, zip_path: str) -> bool:
        """Загрузка через GitHub API (требует токен)"""
        print("💡 Для загрузки через API нужен Personal Access Token")
        print("1. Создайте токен на GitHub: Settings → Developer settings → Personal access tokens")
        print("2. Выберите scopes: repo")
        print("3. Скопируйте токен")
        
        token = input("Введите ваш GitHub Personal Access Token: ")
        
        if not token:
            print("❌ Токен не введен")
            return False
        
        try:
            # Создание релиза через API
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Создание релиза
            release_data = {
                'tag_name': f'v1.0.0-{int(os.path.getmtime(zip_path))}',
                'name': 'Initial Release',
                'body': """Initial commit: Land liquidity assessment system with ML models and Telegram bot

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
""",
                'draft': False,
                'prerelease': False
            }
            
            create_release_url = f"https://api.github.com/repos/{self.username}/{self.repo_name}/releases"
            response = requests.post(create_release_url, headers=headers, json=release_data)
            
            if response.status_code == 201:
                release = response.json()
                upload_url = release['upload_url'].replace('{?name,label}', f'?name=land-liquidity-system.zip')
                
                # Загрузка архива
                with open(zip_path, 'rb') as f:
                    headers['Content-Type'] = 'application/zip'
                    upload_response = requests.post(upload_url, headers=headers, data=f)
                
                if upload_response.status_code == 201:
                    print("✅ Архив загружен через GitHub API")
                    print(f"🌐 Релиз: {release['html_url']}")
                    return True
                else:
                    print(f"❌ Ошибка загрузки архива: {upload_response.status_code}")
                    print(upload_response.text)
                    return False
            else:
                print(f"❌ Ошибка создания релиза: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Ошибка загрузки через API: {e}")
            return False
    
    def manual_upload_instructions(self, zip_path: str) -> bool:
        """Инструкции для ручной загрузки"""
        print("\n" + "=" * 60)
        print("📋 Инструкция для ручной загрузки:")
        print("=" * 60)
        print(f"📁 Архив создан: {zip_path}")
        print(f"🌐 Репозиторий: {self.repo_url}")
        print("\n💡 Ручная загрузка:")
        print("1. Перейдите на GitHub: https://github.com/vtorev/land-liquidity-assessment-system")
        print("2. Нажмите 'Add file' → 'Upload files'")
        print("3. Перетащите архив или выберите файл")
        print("4. Распакуйте архив и загрузите файлы")
        print("5. Создайте коммит с сообщением:")
        print("   'Initial commit: Land liquidity assessment system'")
        print("\n✅ Архив готов к ручной загрузке!")
        return True
    
    def run_upload(self) -> bool:
        """Запуск загрузки"""
        print("🚀 Начинаем альтернативную загрузку системы на GitHub...")
        print("=" * 60)
        
        # Создание архива
        zip_path = self.create_zip_archive()
        if not zip_path:
            return False
        
        # Проверка GitHub CLI
        if self.check_github_cli():
            print("\n📋 Попытка загрузки через GitHub CLI...")
            if self.upload_via_github_cli(zip_path):
                print("\n✅ Загрузка через GitHub CLI завершена!")
                return True
            else:
                print("❌ Загрузка через GitHub CLI не удалась")
        
        # Попытка загрузки через API
        print("\n📋 Попытка загрузки через GitHub API...")
        if self.upload_via_api(zip_path):
            print("\n✅ Загрузка через GitHub API завершена!")
            return True
        else:
            print("❌ Загрузка через API не удалась")
        
        # Ручная загрузка
        print("\n📋 Подготовка инструкций для ручной загрузки...")
        self.manual_upload_instructions(zip_path)
        
        # Очистка временного файла
        try:
            os.unlink(zip_path)
            print("🧹 Временный файл удален")
        except:
            print("⚠️  Не удалось удалить временный файл")
        
        return True


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python upload_to_github_alternative.py <URL_репозитория>")
        print("Пример: python upload_to_github_alternative.py https://github.com/username/repo.git")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    project_root = "."
    
    print(f"🎯 Целевой репозиторий: {repo_url}")
    print(f"📁 Рабочая директория: {project_root}")
    print()
    
    uploader = GitHubUploaderAlternative(repo_url, project_root)
    
    # Проверка существования директории
    if not Path(project_root).exists():
        print(f"❌ Директория {project_root} не существует")
        sys.exit(1)
    
    # Запуск загрузки
    if uploader.run_upload():
        print("\n✅ Загрузка завершена!")
        sys.exit(0)
    else:
        print("\n❌ Загрузка не удалась")
        sys.exit(1)


if __name__ == "__main__":
    main()