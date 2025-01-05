from flask import Flask, render_template, request, redirect, url_for
import os
import requests
from requests.exceptions import RequestException
import webbrowser
import base64
from urllib.parse import quote

# Константы
GITLAB_URL = "https://gitlab.com/api/v4"
GITHUB_URL = "https://api.github.com"
GITLAB_PAT_URL = "https://gitlab.com/-/user_settings/personal_access_tokens"
GITHUB_PAT_URL = "https://github.com/settings/tokens"

app = Flask(__name__)

# Переменные для хранения данных
platform = "gitlab"
access_token = ""
project_id = ""
repo_name = ""
folder_path = ""
branch = "main"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/select_platform", methods=["POST"])
def select_platform():
    global platform
    platform = request.form.get("platform")
    return redirect(url_for("home"))

@app.route("/upload", methods=["POST"])
def upload():
    global access_token, project_id, repo_name, folder_path, branch
    access_token = request.form.get("access_token")
    project_id = request.form.get("project_id")
    folder_path = request.form.get("folder_path")
    branch = request.form.get("branch")

    if not access_token:
        return "Ошибка: Введите Personal Access Token."

    if not os.path.isdir(folder_path):
        return f"Ошибка: Папка {folder_path} не существует."

    if platform == "gitlab":
        if not project_id:
            return "Ошибка: Введите ID проекта для GitLab."
        upload_folder_to_gitlab(project_id, folder_path, branch, access_token)
    else:
        if not project_id:
            return "Ошибка: Введите имя репозитория для GitHub."
        upload_folder_to_github(project_id, folder_path, branch, access_token)

    return "Загрузка завершена!"

def upload_file_to_gitlab(project_id, file_path, relative_path, branch, access_token):
    """Загружает один файл в GitLab."""
    encoded_path = quote(relative_path, safe='')
    url = f"{GITLAB_URL}/projects/{project_id}/repository/files/{encoded_path}"

    headers = {
        "PRIVATE-TOKEN": access_token,
        "Content-Type": "application/json"
    }

    try:
        with open(file_path, "rb") as file:
            content = file.read()
            content_base64 = base64.b64encode(content).decode('utf-8')

        data = {
            "branch": branch,
            "content": content_base64,
            "encoding": "base64",
            "commit_message": f"Add {relative_path}"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            print(f"✅ Файл {relative_path} успешно загружен в GitLab.")
        else:
            print(f"❌ Ошибка при загрузке файла {relative_path}:")
            print(f"Статус: {response.status_code}")
            print(f"Ответ: {response.text}")

        response.raise_for_status()

    except Exception as e:
        print(f"❌ Ошибка при загрузке файла {relative_path} в GitLab: {str(e)}")

def upload_folder_to_gitlab(project_id, folder_path, branch, access_token):
    """Рекурсивно загружает папку в GitLab."""
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, folder_path)
            upload_file_to_gitlab(project_id, file_path, relative_path, branch, access_token)

def upload_file_to_github(repo_name, file_path, relative_path, branch, access_token):
    """Загружает один файл в GitHub."""
    url = f"{GITHUB_URL}/repos/{repo_name}/contents/{relative_path}"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        with open(file_path, "rb") as file:
            content = file.read()
            content_base64 = base64.b64encode(content).decode('utf-8')

        data = {
            "message": f"Add {relative_path}",
            "content": content_base64,
            "branch": branch
        }

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 201:
            print(f"✅ Файл {relative_path} успешно загружен в GitHub.")
        else:
            print(f"❌ Ошибка при загрузке файла {relative_path}:")
            print(f"Статус: {response.status_code}")
            print(f"Ответ: {response.text}")

        response.raise_for_status()

    except Exception as e:
        print(f"❌ Ошибка при загрузке файла {relative_path} в GitHub: {str(e)}")

def upload_folder_to_github(repo_name, folder_path, branch, access_token):
    """Рекурсивно загружает папку в GitHub."""
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, folder_path)
            upload_file_to_github(repo_name, file_path, relative_path, branch, access_token)

if __name__ == "__main__":
    app.run(debug=True)