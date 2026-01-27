import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret')

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            resp = requests.post(f"{BACKEND_URL}/auth/login", json={"username": username, "password": password})
            if resp.status_code == 200:
                user = resp.json()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                session['is_staff'] = user.get('is_staff', False)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials', 'error')
        except:
            flash('Backend unavailable', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    params = {
        'user_id': session['user_id'],
        'is_admin': session['is_admin'],
        'is_staff': session.get('is_staff', False)
    }
    resp = requests.get(f"{BACKEND_URL}/tickets/", params=params)
    tickets = resp.json() if resp.status_code == 200 else []
    return render_template('dashboard.html', tickets=tickets, user=session)

@app.route('/ticket/<int:ticket_id>')
def ticket_detail(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    t_resp = requests.get(f"{BACKEND_URL}/tickets/{ticket_id}")
    r_resp = requests.get(f"{BACKEND_URL}/tickets/{ticket_id}/reports")
    if t_resp.status_code != 200:
        return "Not Found", 404
    return render_template('ticket_detail.html', ticket=t_resp.json(), reports=r_resp.json())

@app.route('/ticket/<int:ticket_id>/add_report', methods=['POST'])
def add_report(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    comment = request.form.get('comment')
    file = request.files.get('file')
    # Фронтенд просто пересылает файл в бэкенд, а тот загрузит в S3
    files = {'file': (file.filename, file.read())} if file and file.filename else None
    data = {'comment': comment}
    requests.post(f"{BACKEND_URL}/tickets/{ticket_id}/reports", data=data, files=files)
    flash('Report added', 'success')
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route('/media/<path:filename>')
def serve_media(filename):
    if 'user_id' not in session:
        return "Unauthorized", 401
    
    # Читаем настройки Object Storage из переменных окружения
    namespace = os.getenv('OCI_NAMESPACE')
    bucket_name = os.getenv('OCI_BUCKET_NAME')
    region = os.getenv('OCI_REGION', 'il-jerusalem-1')

    # Если переменных нет — значит что-то пошло не так с конфигом
    if not namespace or not bucket_name:
        return "Cloud storage configuration missing", 500
    
    # Формируем публичную ссылку на файл в облаке Oracle
    # Пример: https://objectstorage.il-jerusalem-1.oraclecloud.com/n/axm70tntbzcm/b/helpdesk-storage/o/tickets/1/image.png
    oci_url = f"https://objectstorage.{region}.oraclecloud.com/n/{namespace}/b/{bucket_name}/o/{filename}"
    
    # Перенаправляем пользователя (Redirect 302) прямо на картинку
    return redirect(oci_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
