import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import urllib.parse
import re
import random
import string
from datetime import datetime, timedelta


app = Flask(__name__, template_folder='./templates')
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_questions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()
    return questions

def get_random_questions(limit=40):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (limit,))
    questions = cursor.fetchall()
    conn.close()
    return questions


def admin_required():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Только для администраторов')


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))


def store_verification_code(email, code):
    conn = get_db_connection()
    expires_at = datetime.now() + timedelta(minutes=15)
    conn.execute(
        'INSERT OR REPLACE INTO email_verifications (email, code, expires_at) VALUES (?, ?, ?)',
        (email, code, expires_at.isoformat())
    )
    conn.commit()
    conn.close()


def verify_email_code(email, code):
    conn = get_db_connection()
    verification = conn.execute(
        'SELECT code, expires_at FROM email_verifications WHERE email = ? AND code = ?',
        (email, code)
    ).fetchone()
    conn.close()
    
    if not verification:
        return False
    
    expires_at = datetime.fromisoformat(verification['expires_at'])
    if datetime.now() > expires_at:
        return False
    
    return True


@app.route('/')
def index():
    questions = get_questions()
    return render_template('index.html', questions=questions)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Все поля должны быть заполнены')
            return redirect(url_for('register'))

        if len(username) < 3:
            flash('Имя пользователя должно содержать минимум 3 символа')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов')
            return redirect(url_for('register'))

        if not is_valid_email(email):
            flash('Неправильный адрес электронной почты')
            return redirect(url_for('register'))

        conn = get_db_connection()
        existing = conn.execute(
            'SELECT id FROM users WHERE email = ? OR username = ?',
            (email, username)
        ).fetchone()
        conn.close()

        if existing:
            flash('Этот адрес электронной почты или логин уже зарегистрированы')
            return redirect(url_for('register'))

        session['pending_registration'] = {
            'username': username,
            'email': email,
            'password': password
        }

        code = generate_verification_code()
        store_verification_code(email, code)

        flash(f'Код подтверждения: {code}')
        return redirect(url_for('verify_email'))

    return render_template('register.html')


@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if 'pending_registration' not in session:
        flash('Сеанс регистрации истёк. Начните заново.')
        return redirect(url_for('register'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        email = session['pending_registration']['email']

        if not code:
            flash('Введите код подтверждения')
            return redirect(url_for('verify_email'))

        if not verify_email_code(email, code):
            flash('Код подтверждения неверный или истёк. Зарегистрируйтесь снова.')
            return redirect(url_for('register'))

        reg_data = session['pending_registration']
        username = reg_data['username']
        password = reg_data['password']
        pw_hash = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        try:
            existing_count = conn.execute('SELECT COUNT(*) as cnt FROM users').fetchone()['cnt']
            is_admin = 1 if existing_count == 0 else 0
            
            conn.execute(
                'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                (username, email, pw_hash, is_admin)
            )
            conn.commit()

            conn.execute('DELETE FROM email_verifications WHERE email = ?', (email,))
            conn.commit()
            conn.close()

            session.pop('pending_registration', None)

            if is_admin:
                flash('Регистрация успешна! Этот аккаунт добавлен как администратор.')
            else:
                flash('Регистрация успешна! Вы можете войти.')
            
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Произошла ошибка при дублировании данных. Зарегистрируйтесь снова.')
            return redirect(url_for('register'))
        finally:
            conn.close()

    return render_template('verify_email.html', email=session['pending_registration']['email'])
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['premium'] = bool(user['premium'])
            session['is_admin'] = bool(user['is_admin'])
            flash('Добро пожаловать, ' + user['username'])
            return redirect(url_for('dashboard'))
        else:
            flash('Неверная электронная почта или пароль')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    rows = conn.execute(
        'SELECT score, total_questions, test_date, test_id FROM results WHERE user_id = ? ORDER BY test_date DESC LIMIT 10',
        (session['user_id'],)
    ).fetchall()

    conn.close()

    total_attempts = len(rows)
    percents = []
    for r in rows:
        total_q = r['total_questions'] or 40
        percents.append(round((r['score'] / total_q) * 100, 1))

    avg_percent = round((sum(percents) / total_attempts), 1) if total_attempts else 0
    best_percent = max(percents) if percents else 0

    excellent = sum(1 for p in percents if p >= 85)
    good = sum(1 for p in percents if 65 <= p < 85)
    needs_improvement = total_attempts - excellent - good
    chart_total = total_attempts if total_attempts else 1
    
    excellent_angle = round((excellent / chart_total) * 360, 1)
    good_angle = round((good / chart_total) * 360, 1)
    
    chart_angles = {
        'excellent': excellent_angle,
        'good': good_angle,
        'excellent_end': excellent_angle,
        'good_start': excellent_angle,
        'good_end': excellent_angle + good_angle,
        'need_start': excellent_angle + good_angle,
    }

    return render_template(
        'dashboard.html',
        total_attempts=total_attempts,
        avg_percent=avg_percent,
        best_percent=best_percent,
        excellent=excellent,
        good=good,
        needs_improvement=needs_improvement,
        chart_angles=chart_angles,
        recent_results=rows
    )

@app.route('/admin')
def admin_panel():
    if not admin_required():
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    questions = conn.execute('SELECT q.*, t.title as test_title FROM questions q LEFT JOIN tests t ON q.test_id = t.id ORDER BY q.id DESC').fetchall()
    test_sets = conn.execute('SELECT * FROM test_sets ORDER BY id DESC').fetchall()
    stats = {
        'users': conn.execute('SELECT COUNT(*) as cnt FROM users').fetchone()['cnt'],
        'questions': conn.execute('SELECT COUNT(*) as cnt FROM questions').fetchone()['cnt'],
        'test_sets': conn.execute('SELECT COUNT(*) as cnt FROM test_sets').fetchone()['cnt']
    }
    conn.close()

    return render_template('admin.html', users=users, questions=questions, test_sets=test_sets, stats=stats)


@app.route('/admin/users/toggle_premium/<int:user_id>', methods=['POST'])
def admin_toggle_premium(user_id):
    if not admin_required():
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    user = conn.execute('SELECT premium FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        new_val = 0 if user['premium'] else 1
        conn.execute('UPDATE users SET premium = ? WHERE id = ?', (new_val, user_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/users/toggle_admin/<int:user_id>', methods=['POST'])
def admin_toggle_admin(user_id):
    if not admin_required():
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        new_val = 0 if user['is_admin'] else 1
        conn.execute('UPDATE users SET is_admin = ? WHERE id = ?', (new_val, user_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/questions/add', methods=['POST'])
def admin_add_question():
    if not admin_required():
        return redirect(url_for('dashboard'))

    test_id = request.form.get('test_id') or 1
    question_text = request.form.get('question_text', '').strip()
    option_a = request.form.get('option_a', '').strip()
    option_b = request.form.get('option_b', '').strip()
    option_c = request.form.get('option_c', '').strip()
    option_d = request.form.get('option_d', '').strip()
    correct_option = request.form.get('correct_option', '').upper().strip()
    explanation = request.form.get('explanation', '').strip()
    category = request.form.get('category', '').strip()
    difficulty = request.form.get('difficulty', 'normal').strip()

    if not question_text or not option_a or not option_b or not option_c or not option_d or correct_option not in ('A', 'B', 'C', 'D'):
        flash('Заполните все поля вопроса правильно')
        return redirect(url_for('admin_panel'))

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO questions (test_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, category, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (test_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, category, difficulty)
    )
    conn.commit()
    conn.close()
    flash('Вопрос добавлен')
    return redirect(url_for('admin_panel'))


@app.route('/admin/questions/delete/<int:question_id>', methods=['POST'])
def admin_delete_question(question_id):
    if not admin_required():
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()
    flash('Вопрос удален')
    return redirect(url_for('admin_panel'))


@app.route('/admin/questions/import', methods=['POST'])
def admin_import_questions():
    if not admin_required():
        return redirect(url_for('dashboard'))

    upload = request.files.get('csv_file')
    if not upload or upload.filename == '':
        flash('Выберите CSV файл')
        return redirect(url_for('admin_panel'))

    try:
        import csv, io
        stream = io.TextIOWrapper(upload.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        rows = []
        for row in reader:
            if not row.get('question_text') or not row.get('option_a') or not row.get('option_b') or not row.get('option_c') or not row.get('option_d') or not row.get('correct_option'):
                continue
            correct = row.get('correct_option','').strip().upper()
            if correct not in ('A','B','C','D'):
                continue
            rows.append((
                int(row.get('test_id') or 1),
                row['question_text'].strip(),
                row['option_a'].strip(),
                row['option_b'].strip(),
                row['option_c'].strip(),
                row['option_d'].strip(),
                correct,
                row.get('explanation','').strip(),
                row.get('category','').strip(),
                row.get('difficulty','normal').strip()
            ))

        conn = get_db_connection()
        conn.executemany('INSERT INTO questions (test_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, category, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', rows)
        conn.commit()
        conn.close()
        flash(f'Импортировано: {len(rows)} вопросов')
    except Exception as e:
        flash('Ошибка при импорте: ' + str(e))

    return redirect(url_for('admin_panel'))


@app.route('/admin/test_sets/add', methods=['POST'])
def admin_add_test_set():
    if not admin_required():
        return redirect(url_for('dashboard'))

    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'all').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Введите название теста')
        return redirect(url_for('admin_panel'))

    conn = get_db_connection()
    conn.execute('INSERT INTO test_sets (name, category, description) VALUES (?, ?, ?)', (name, category, description))
    conn.commit()
    conn.close()
    flash('Набор тестов добавлен')
    return redirect(url_for('admin_panel'))


@app.route('/admin/test_sets/delete/<int:set_id>', methods=['POST'])
def admin_delete_test_set(set_id):
    if not admin_required():
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    conn.execute('DELETE FROM test_sets WHERE id = ?', (set_id,))
    conn.commit()
    conn.close()
    flash('Набор тестов удален')
    return redirect(url_for('admin_panel'))


@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    default_wa = os.environ.get('WHATSAPP_LINK', 'https://wa.me/77785627501')
    message = f"Привет, я хочу подписаться на премиум. Пользователь id={session['user_id']}, username={session.get('username')}"
    encoded = urllib.parse.quote_plus(message)
    if default_wa.startswith('https://wa.me/'):
        if '?text=' in default_wa:
            wa_link = default_wa + '&' + f'text={encoded}'
        else:
            wa_link = default_wa + f'?text={encoded}'
    else:
        safe_number = ''.join(ch for ch in default_wa if ch.isdigit())
        wa_link = f'https://wa.me/{safe_number}?text={encoded}'

    return redirect(wa_link)

@app.route('/course')
def course():
    return render_template('course.html')


@app.route('/tests')
def tests_list():
    conn = get_db_connection()
    sets = conn.execute('SELECT * FROM test_sets').fetchall()
    conn.close()
    return render_template('tests_list.html', sets=sets)


@app.route('/start_test/<int:set_id>')
def start_test(set_id):
    if not session.get('premium'):
        flash('40-вопросный тест доступен только премиум-пользователям. Перейдите в профиль для оплаты.')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    ts = conn.execute('SELECT * FROM test_sets WHERE id = ?', (set_id,)).fetchone()
    conn.close()
    if not ts:
        flash('Тест не найден')
        return redirect(url_for('tests_list'))

    cat = ts['category'] if ts['category'] else 'all'
    if cat == 'all':
        questions = get_random_questions(limit=40)
    else:
       
        conn = get_db_connection()
        q = conn.execute('SELECT * FROM questions WHERE category = ? ORDER BY RANDOM() LIMIT ?', (cat, 40)).fetchall()
        conn.close()
        if len(q) < 40:
            questions = get_random_questions(limit=40)
        else:
            questions = q

    return render_template('test.html', questions=questions, test_set=ts)


@app.route('/training')
def training_index():

    modes = [
        {'id':'learn','name':'Обучение (в каждом вопросе показано объяснение)'},
        {'id':'practice','name':'Практика (без объяснения)'},
        {'id':'video','name':'Видео уроки'},
        {'id':'animation','name':'Анимированные примеры'}
    ]
    return render_template('training_index.html', modes=modes)


@app.route('/training/<mode>')
def training_mode(mode):
   
    if mode not in ('learn','practice','video','animation'):
        flash('Нет данных')
        return redirect(url_for('training_index'))

    if mode in ('learn', 'practice'):
        questions = get_random_questions(limit=20)
        return render_template('training.html', questions=questions, mode=mode)
    elif mode == 'video':
        return render_template('training_video.html')
    elif mode == 'animation':
        return render_template('training_animation.html')

@app.route('/submit', methods=['POST'])
def submit():
    answers = {}
    for key, val in request.form.items():
        if key.startswith('q_'):
            answers[key[2:]] = val

    if not answers:
        flash('Вы не дали никаких ответов')
        return redirect(url_for('dashboard'))

    question_ids = tuple(int(qid) for qid in answers.keys() if qid.isdigit())
    if not question_ids:
        flash('ID вопроса не найден')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    query = f"SELECT id, correct_option FROM questions WHERE id IN ({','.join(['?']*len(question_ids))})"
    fetched = conn.execute(query, question_ids).fetchall()

    score = 0
    for q in fetched:
        qid = str(q['id'])
        if qid in answers and answers[qid] == q['correct_option']:
            score += 1

    total_q = len(fetched)
    if total_q == 0:
        conn.close()
        return "Ошибка: вопросы не найдены в базе данных!"

    test_id = request.form.get('test_id')
    try:
        test_id_val = int(test_id) if test_id and test_id.isdigit() else None
    except ValueError:
        test_id_val = None

    if 'user_id' in session:
        conn.execute('INSERT INTO results (user_id, test_id, score, total_questions) VALUES (?, ?, ?, ?)',
                     (session['user_id'], test_id_val, score, total_q))
        conn.commit()
    conn.close()

    return render_template('result.html', score=score, total=total_q)


@app.route('/autosave', methods=['POST'])
def autosave():
    if 'user_id' not in session:
        return ('', 401)

    data = None
    if request.is_json:
        data = json.dumps(request.get_json())
    else:
      
        data = json.dumps(request.form.to_dict())

    conn = get_db_connection()
    conn.execute('INSERT INTO autosaves (user_id, data) VALUES (?, ?)', (session['user_id'], data))
    conn.commit()
    conn.close()
    return ('', 204)



@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT score, total_questions, test_date, test_id FROM results WHERE user_id = ? ORDER BY test_date DESC LIMIT 10',
        (session['user_id'],)
    ).fetchall()
    conn.close()

    total_attempts = len(rows)
    percents = []
    for r in rows:
        total_q = r['total_questions'] or 40
        percents.append(round((r['score'] / total_q) * 100, 1))

    avg_percent = round((sum(percents) / total_attempts), 1) if total_attempts else 0
    best_percent = max(percents) if percents else 0

    excellent = sum(1 for p in percents if p >= 85)
    good = sum(1 for p in percents if 65 <= p < 85)
    needs_improvement = total_attempts - excellent - good

    return jsonify({
        'username': session.get('username'),
        'total_attempts': total_attempts,
        'avg_percent': avg_percent,
        'best_percent': best_percent,
        'excellent': excellent,
        'good': good,
        'needs_improvement': needs_improvement,
        'is_premium': session.get('premium', False)
    })


@app.route('/api/results')
def api_results():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT id, score, total_questions, test_date, test_id FROM results WHERE user_id = ? ORDER BY test_date DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        total_q = r['total_questions'] or 40
        percent = round((r['score'] / total_q) * 100, 1)
        results.append({
            'id': r['id'],
            'score': r['score'],
            'total_questions': total_q,
            'percent': percent,
            'test_date': r['test_date'],
            'test_id': r['test_id']
        })

    return jsonify(results)


@app.route('/api/user/profile')
def api_user_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, email, is_admin, premium FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'is_admin': bool(user['is_admin']),
        'is_premium': bool(user['premium'])
    })


@app.route('/api/leaderboard')
def api_leaderboard():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT u.username, MAX(r.score) as best_score, ROUND(AVG(r.score),2) as avg_score, COUNT(r.id) as attempts, MAX(r.test_date) as last_test, u.id as user_id
        FROM results r JOIN users u ON u.id = r.user_id
        GROUP BY u.id
        ORDER BY best_score DESC, avg_score DESC
        LIMIT 100
        """
    ).fetchall()

    leaderboard = []
    for idx, row in enumerate(rows, start=1):
        leaderboard.append({
            'rank': idx,
            'username': row['username'],
            'best_score': row['best_score'],
            'avg_score': row['avg_score'],
            'attempts': row['attempts'],
            'last_test': row['last_test']
        })

    user_rank = None
    if 'user_id' in session:
        users_best = conn.execute('SELECT user_id, MAX(score) as best FROM results GROUP BY user_id ORDER BY best DESC').fetchall()
        for idx, ub in enumerate(users_best, start=1):
            if ub['user_id'] == session['user_id']:
                user_rank = idx
                break

    conn.close()
    
    return jsonify({
        'leaderboard': leaderboard,
        'user_rank': user_rank
    })


@app.route('/api/test/questions/<int:test_id>')
def api_test_questions(test_id):
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT id, question_text, option_a, option_b, option_c, option_d, correct_option FROM questions WHERE test_id = ?',
        (test_id,)
    ).fetchall()
    conn.close()

    questions = []
    for row in rows:
        questions.append({
            'id': row['id'],
            'question': row['question'],
            'options': {
                'a': row['option_a'],
                'b': row['option_b'],
                'c': row['option_c'],
                'd': row['option_d']
            }
        })

    return jsonify({'questions': questions, 'count': len(questions)})


@app.route('/api/test/submit', methods=['POST'])
def api_test_submit():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() if request.is_json else request.form.to_dict()
    answers = data.get('answers', {})
    test_id = data.get('test_id')

    if not answers:
        return jsonify({'error': 'No answers provided'}), 400

    question_ids = tuple(int(qid) for qid in answers.keys() if str(qid).isdigit())
    if not question_ids:
        return jsonify({'error': 'Invalid question IDs'}), 400

    conn = get_db_connection()
    query = f"SELECT id, correct_option FROM questions WHERE id IN ({','.join(['?']*len(question_ids))})"
    fetched = conn.execute(query, question_ids).fetchall()

    score = 0
    for q in fetched:
        qid = str(q['id'])
        if qid in answers and answers[qid] == q['correct_option']:
            score += 1

    total_q = len(fetched)
    if total_q == 0:
        conn.close()
        return jsonify({'error': 'No questions found'}), 404

    try:
        test_id_val = int(test_id) if test_id and str(test_id).isdigit() else None
    except (ValueError, TypeError):
        test_id_val = None

    conn.execute('INSERT INTO results (user_id, test_id, score, total_questions) VALUES (?, ?, ?, ?)',
                 (session['user_id'], test_id_val, score, total_q))
    conn.commit()
    conn.close()

    percent = round((score / total_q) * 100, 1)
    return jsonify({
        'score': score,
        'total': total_q,
        'percent': percent,
        'success': True
    })


@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT u.username, MAX(r.score) as best_score, ROUND(AVG(r.score),2) as avg_score, COUNT(r.id) as attempts, MAX(r.test_date) as last_test, u.id as user_id
        FROM results r JOIN users u ON u.id = r.user_id
        GROUP BY u.id
        ORDER BY best_score DESC, avg_score DESC
        LIMIT 100
        """
    ).fetchall()

    user_rank = None
    user_best = None
    if 'user_id' in session:
       
        users_best = conn.execute('SELECT user_id, MAX(score) as best FROM results GROUP BY user_id ORDER BY best DESC').fetchall()
        rank = None
        for idx, ub in enumerate(users_best, start=1):
            if ub['user_id'] == session['user_id']:
                rank = idx
                break
        user_rank = rank
        b = conn.execute('SELECT MAX(score) as best FROM results WHERE user_id = ?', (session['user_id'],)).fetchone()
        user_best = b['best'] if b else None

    conn.close()
    return render_template('leaderboard.html', rows=rows, user_rank=user_rank, user_best=user_best)


@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    rows = conn.execute('SELECT score, total_questions, test_date FROM results WHERE user_id = ? ORDER BY test_date DESC', (session['user_id'],)).fetchall()

    
    percents = []
    for r in rows:
        total_q = r['total_questions'] if r['total_questions'] else 40
        perc = (r['score'] / total_q) * 100 if total_q > 0 else 0
        percents.append(round(perc,1))

    stats = {
        'total_attempts': len(rows),
        'avg_percent': round((sum(percents)/len(percents)),1) if percents else 0,
        'best_percent': max(percents) if percents else 0
    }

    
    trend = list(reversed(percents[:10])) if percents else []

   
    analysis = 'Уровень успеха стабилен.'
    if len(percents) >= 6:
        half = len(percents)//2
        first_avg = sum(percents[half:]) / max(1, len(percents[half:]))
        second_avg = sum(percents[:half]) / max(1, len(percents[:half]))
        diff = round(second_avg - first_avg,1)
        if diff > 2:
            analysis = f'Недавно улучшилось (среднее +{diff}%)'
        elif diff < -2:
            analysis = f'Недавно ухудшилось (среднее {diff}%)'
        else:
            analysis = 'Уровень успеха стабилен.'

    conn.close()
    return render_template('history.html', rows=rows, stats=stats, trend=trend, analysis=analysis)
@app.route('/penalties')
def penalties():
    return render_template('penalties.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
