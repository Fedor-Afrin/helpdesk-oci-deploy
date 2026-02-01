import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret')

# Получаем URL бэкенда
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
        except Exception as e:
            flash(f'Backend unavailable: {str(e)}', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard') # В Flask используется @app.route, а не @router.get
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Подготавливаем параметры для бэкенда
    params = {
        'user_id': session['user_id'],
        'is_admin': str(session.get('is_admin', False)).lower(),
        'is_staff': str(session.get('is_staff', False)).lower()
    }
    
    try:
        # Вызываем бэкенд
        resp = requests.get(f"{BACKEND_URL}/tickets/", params=params, timeout=5)
        tickets = resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"Error: {e}")
        tickets = []
        
    return render_template('dashboard.html', tickets=tickets, user=session)
# --- Создание тикета ---
@app.route('/create_ticket', methods=['POST'])
def create_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    
    data = {
        "title": title,
        "description": description,
        "creator_id": session['user_id']
    }
    
    try:
        requests.post(f"{BACKEND_URL}/tickets/", json=data)
        flash('Ticket created!', 'success')
    except:
        flash('Error creating ticket', 'error')
        
    return redirect(url_for('dashboard'))

# --- Удаление тикета ---
@app.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
def delete_ticket(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    try:
        # Для удаления тоже нужно передавать, кто удаляет (админ)
        params = {'user_id': session['user_id'], 'is_admin': session['is_admin']}
        requests.delete(f"{BACKEND_URL}/tickets/{ticket_id}", params=params)
        flash('Ticket deleted', 'success')
    except:
        flash('Error deleting ticket', 'error')
        
    return redirect(url_for('dashboard'))

# --- Обновление статуса тикета (ИСПРАВЛЕНО) ---
@app.route('/ticket/<int:ticket_id>/update', methods=['POST'])
def update_ticket(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    status = request.form.get('status')
    
    # ВАЖНО: Передаем user_id в параметрах, иначе Бэкенд вернет ошибку 422
    params = {
        'user_id': session['user_id'],
        'is_admin': session['is_admin'],
        'is_staff': session.get('is_staff', False)
    }
    
    try:
        resp = requests.put(f"{BACKEND_URL}/tickets/{ticket_id}", json={"status": status}, params=params)
        if resp.status_code == 200:
            flash('Status updated', 'success')
        else:
            flash(f'Error updating status: {resp.text}', 'error')
    except:
        flash('Network error updating status', 'error')
        
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))
# -----------------------------------------

@app.route('/ticket/<int:ticket_id>')
def ticket_detail(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        t_resp = requests.get(f"{BACKEND_URL}/tickets/{ticket_id}")
        r_resp = requests.get(f"{BACKEND_URL}/tickets/{ticket_id}/reports")
        
        if t_resp.status_code != 200:
            return "Ticket Not Found", 404
            
        return render_template('ticket_detail.html', ticket=t_resp.json(), reports=r_resp.json())
    except Exception as e:
        # Если ты увидишь этот текст на экране, значит код ОБНОВИЛСЯ успешно
        return f"Frontend Error (v7): {str(e)}", 500

@app.route('/ticket/<int:ticket_id>/add_report', methods=['POST'])
def add_report(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    comment = request.form.get('comment')
    file = request.files.get('file')
    
    files = {'file': (file.filename, file.read())} if file and file.filename else None
    data = {'comment': comment}
    
    try:
        requests.post(f"{BACKEND_URL}/tickets/{ticket_id}/reports", data=data, files=files)
        flash('Report added', 'success')
    except:
        flash('Error adding report', 'error')
        
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))


    
# Исправленный блок функции admin в frontend-app/app.py
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # ПРАВИЛЬНЫЙ СПОСОБ получения галочек из твоего HTML
        # Если галочка стоит, придет 'on', если нет - None
        is_admin = True if request.form.get('is_admin') == 'on' else False
        is_staff = True if request.form.get('is_staff') == 'on' else False

        try:
            resp = requests.post(f"{BACKEND_URL}/auth/users", json={
                "username": username,
                "password": password,
                "is_admin": is_admin,
                "is_staff": is_staff
            }, timeout=5)
            
            if resp.status_code == 200:
                flash(f'User {username} created successfully!', 'success')
            else:
                flash(f'Error: {resp.text}', 'error')
        except Exception as e:
            flash(f'Connection error: {str(e)}', 'error')

    return render_template('admin.html')

@app.route('/media/<path:filename>')
def serve_media(filename):
    if 'user_id' not in session:
        return "Unauthorized", 401
    
    namespace = os.getenv('OCI_NAMESPACE')
    bucket_name = os.getenv('OCI_BUCKET_NAME')
    region = os.getenv('OCI_REGION', 'il-jerusalem-1')

    if not namespace or not bucket_name:
        return "Error: Cloud storage configuration is missing", 500
    
    oci_url = f"https://objectstorage.{region}.oraclecloud.com/n/{namespace}/b/{bucket_name}/o/{filename}"
    return redirect(oci_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)