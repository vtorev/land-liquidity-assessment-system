#!/usr/bin/env python3
"""
Упрощенный скрипт для загрузки системы на GitHub через API
"""

import os
import sys
import zipfile
import tempfile
import requests
import json
from pathlib import Path


def create_zip_archive(project_root: str = ".") -> str:
    """Создание ZIP архива с проектом"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_path = temp_file.name
        
        print("Creating project archive...")
        
        # Создаем архив
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_root):
                # Пропускаем системные директории
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                for file in files:
                    if file.startswith('.') and file != '.gitignore':
                        continue
                    
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(project_root)
                    zipf.write(file_path, arcname)
        
        print(f"Archive created: {temp_path}")
        return temp_path
    except Exception as e:
        print(f"Error creating archive: {e}")
        return ""


def upload_to_github(repo_url: str, zip_path: str, token: str) -> bool:
    """Загрузка через GitHub API"""
    try:
        # Извлечение username и repo_name из URL
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        username = repo_url.split('/')[-2]
        
        print(f"Uploading to GitHub: {username}/{repo_name}")
        
        # Заголовки для API
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Данные для создания релиза
        release_data = {
            'tag_name': f'v1.0.0-{int(os.path.getmtime(zip_path))}',
            'name': 'Initial Release',
            'body': '''Initial commit: Land liquidity assessment system with ML models and Telegram bot

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
''',
            'draft': False,
            'prerelease': False
        }
        
        # Создание релиза
        create_release_url = f"https://api.github.com/repos/{username}/{repo_name}/releases"
        print("Creating release...")
        response = requests.post(create_release_url, headers=headers, json=release_data)
        
        if response.status_code == 201:
            release = response.json()
            upload_url = release['upload_url'].replace('{?name,label}', f'?name=land-liquidity-system.zip')
            
            print("Uploading archive...")
            # Загрузка архива
            with open(zip_path, 'rb') as f:
                headers['Content-Type'] = 'application/zip'
                upload_response = requests.post(upload_url, headers=headers, data=f)
            
            if upload_response.status_code == 201:
                print("Archive uploaded successfully!")
                print(f"Release URL: {release['html_url']}")
                return True
            else:
                print(f"Error uploading archive: {upload_response.status_code}")
                print(upload_response.text)
                return False
        else:
            print(f"Error creating release: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Error uploading to GitHub: {e}")
        return False


def main():
    """Главная функция"""
    if len(sys.argv) < 3:
        print("Usage: python upload_to_github_simple.py <repo_url> <token>")
        print("Example: python upload_to_github_simple.py https://github.com/username/repo.git ghp_xxx")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    token = sys.argv[2]
    project_root = "."
    
    print(f"Target repository: {repo_url}")
    print(f"Project directory: {project_root}")
    print()
    
    # Проверка существования директории
    if not Path(project_root).exists():
        print(f"Error: Directory {project_root} does not exist")
        sys.exit(1)
    
    # Создание архива
    zip_path = create_zip_archive(project_root)
    if not zip_path:
        print("Failed to create archive")
        sys.exit(1)
    
    # Загрузка на GitHub
    try:
        if upload_to_github(repo_url, zip_path, token):
            print("\nUpload completed successfully!")
            print("Note: This uploaded the project as a release. To create a proper Git repository,")
            print("you'll need to clone the repo and push the files manually.")
        else:
            print("\nUpload failed")
            sys.exit(1)
    finally:
        # Очистка временного файла
        try:
            os.unlink(zip_path)
            print("Temporary file cleaned up")
        except:
            print("Warning: Could not clean up temporary file")


if __name__ == "__main__":
    main()