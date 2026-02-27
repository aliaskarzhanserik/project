import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import urllib.parse


app = Flask(__name__, template_folder='./templates')
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'data', 'database.db')

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

@app.route('/')
def index():
    questions = get_questions()
    return render_template('index.html', questions=questions)

@app.route('/register', methods=['GET', 'POST'])
def register():
            if request.method == 'POST':
                username = request.form['username']
                email = request.form['email']
                password = request.form['password']
            if not username or not email or not password:
                flash('Барлық өрістер толтырылуы керек')
                return redirect(url_for('register'))

            pw_hash = generate_password_hash(password, method='pbkdf2:sha256')
            conn = get_db_connection()
            
            try:
                conn.execute('INSERT INTO users (username, email, pw_hash) VALUES (?, ?, ?)',
                            (username, email, pw_hash))
                conn.commit()
                flash('Тіркелу сәтті өтті. Кіруге болады.')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Бұл электрондық пошта бұрыннан тіркелген')
                return redirect(url_for('register'))
            finally:
                conn.close()

                return render_template('register.html')

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
            flash('Қош келдіңіз, ' + user['username'])
            return redirect(url_for('dashboard'))
        else:
            flash('Қате электрондық пошта немесе пароль')
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
    return render_template('dashboard.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    default_wa = os.environ.get('WHATSAPP_LINK', 'https://wa.me/77785627501')
    message = f"Сәлем, мен премиумға жазылғым келеді. Пайдаланушы id={session['user_id']}, username={session.get('username')}"
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
        flash('40 сұрақтық тест тек премиум қолданушыларға қолжетімді. Төлеу үшін профильге өтіңіз.')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    ts = conn.execute('SELECT * FROM test_sets WHERE id = ?', (set_id,)).fetchone()
    conn.close()
    if not ts:
        flash('Тест табылмады')
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
        {'id':'learn','name':'Оқу (әр сұрақта түсініктеме көрсетіледі)'},
        {'id':'practice','name':'Практика (түсініктеме жоқ)'}
    ]
    return render_template('training_index.html', modes=modes)


@app.route('/training/<mode>')
def training_mode(mode):
   
    if mode not in ('learn','practice'):
        flash('Мәлімет жоқ')
        return redirect(url_for('training_index'))

   
    questions = get_random_questions(limit=20)
    return render_template('training.html', questions=questions, mode=mode)

@app.route('/submit', methods=['POST'])
def submit():
    answers = {}
    for key, val in request.form.items():
        if key.startswith('q_'):
            answers[key[2:]] = val

    questions = get_questions()
    score = 0
    for q in questions:
        qid = str(q['id'])
        correct = q['correct_option']
        if qid in answers and answers[qid] == correct:
            score += 1

    total_q = len(questions)
    
    if 'user_id' in session:
        conn = get_db_connection()
        conn.execute('INSERT INTO results (user_id, score, total_questions) VALUES (?, ?, ?)', (session['user_id'], score, total_q))
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

   
    analysis = 'Жетістік деңгейі тұрақты.'
    if len(percents) >= 6:
        half = len(percents)//2
        first_avg = sum(percents[half:]) / max(1, len(percents[half:]))
        second_avg = sum(percents[:half]) / max(1, len(percents[:half]))
        diff = round(second_avg - first_avg,1)
        if diff > 2:
            analysis = f'Соңғы уақытта жақсарған (орташа +{diff}%)'
        elif diff < -2:
            analysis = f'Соңғы уақытта нашарлаған (орташа {diff}%)'
        else:
            analysis = 'Жетістік деңгейі тұрақты.'

    conn.close()
    return render_template('history.html', rows=rows, stats=stats, trend=trend, analysis=analysis)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)