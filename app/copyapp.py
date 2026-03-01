from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3, os

# --- Настройка Flask с указанием путей ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, '../templates'),
    static_folder=os.path.join(BASE_DIR, '../static')
)
app.secret_key = "supersecretkey"

# --- Путь к базе данных ---
DB_PATH = os.path.join(BASE_DIR, 'users.db')

# --- Инициализация базы ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    c.execute('DELETE FROM users')
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'supersecret'))
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('user', '1234'))
    conn.commit()
    conn.close()

# --- SQL Injection Levels — Теория и Ситуации ---
sql_levels = [
    {
        "id": 1,
        "title": "Level 1: Basic Authentication Bypass",
        "theory": "SQL-инъекция позволяет вмешиваться в запросы к базе данных. Пример: ' OR '1'='1.",
        "situation": "Нужно обойти авторизацию в логин-форме."
    },
    {
        "id": 2,
        "title": "Level 2: Bypassing Login with Comments",
        "theory": "Используем SQL-комментарии (`--`) для игнорирования части запроса.",
        "situation": "Форма усилена, используйте комментарии, чтобы отключить проверку пароля."
    },
    {
        "id": 3,
        "title": "Level 3: Time-Based Blind Injection",
        "theory": "Сервер не отображает результат напрямую. Можно использовать `SLEEP()` для проверки.",
        "situation": "Нужно замедлить сервер и понять, прошла ли авторизация."
    },
    {
        "id": 4,
        "title": "Level 4: Extracting Data with UNION",
        "theory": "Команда `UNION SELECT` позволяет извлечь данные из других таблиц.",
        "situation": "Попробуйте узнать имена пользователей с помощью UNION SELECT."
    },
    {
        "id": 5,
        "title": "Level 5: Advanced Extraction with Subqueries",
        "theory": "Подзапросы (`SELECT (...)`) помогают получить конкретные значения.",
        "situation": "Узнайте пароль админа с помощью подзапроса и фильтрации по ID."
    }
]

# --- Главная страница ---
@app.route('/')
def home():
    return render_template("home.html")

# --- Панель с прогрессом ---
@app.route('/dashboard')
def dashboard():
    session.setdefault('xss_count', 0)
    session.setdefault('sql_count', 0)
    session.setdefault('balance', 500) # Даем стартовый капитал "на подъем"
    session.setdefault('xp', 0) 
    session.setdefault('achievements', [])
    

    xss_max, sql_max = 5, 5
    xss_progress = min(int(session['xss_count'] / xss_max * 100), 100)
    sql_progress = min(int(session['sql_count'] / sql_max * 100), 100)

    xss_level = session['xss_count'] // 2 + 1
    sql_level = session['sql_count'] // 2 + 1
    overall_progress = int((xss_progress + sql_progress) / 2)
    overall_level = (xss_level + sql_level) // 2

    xp = session.get('xp', 0)
    xp_percent = int((xp % (overall_level * 100 or 100)) / (overall_level * 100 or 100) * 100)

    return render_template("index.html",
                           xss_progress=xss_progress,
                           sql_progress=sql_progress,
                           overall_progress=overall_progress,
                           xss_level=xss_level,
                           sql_level=sql_level,
                           overall_level=overall_level,
                           xp=xp,
                           xp_percent=xp_percent,
                           balance=session['balance'])

# --- Страница достижений ---
@app.route('/achievements')
def achievements():
    # Если в сессии еще нет списка, создаем пустой
    user_achievements = session.get('achievements', [])
    return render_template("achievements.html", achievements=user_achievements)

# --- SQL Injection: Список уровней ---
@app.route('/sql-injection/levels')
def sql_levels_page():
    return render_template("sql_levels.html", levels=sql_levels)

@app.route('/sql-injection/level/<int:level_id>', methods=['GET', 'POST'])
def sql_level(level_id):
    level_data = next((lvl for lvl in sql_levels if lvl["id"] == level_id), None)
    if not level_data: return "Level not found", 404

    session.setdefault('balance', 500)
    session.setdefault('fail_sql', 0)
    session.setdefault('achievements', [])
    message, hint, solution = '', '', ''

    # --- СИСТЕМА ПОКУПКИ (GET) ---
    buy_type = request.args.get('buy')
    if buy_type == 'hint':
        if session['balance'] >= 50:
            session['balance'] -= 50
            hint = "Информатор шепчет: попробуйте ' OR '1'='1 в поле пароля."
        else:
            message = "❌ Недостаточно средств для подсказки!"
    elif buy_type == 'solution':
        if session['balance'] >= 150:
            session['balance'] -= 150
            solution = "Полный эксплойт: admin / ' OR '1'='1'"
        else:
            message = "❌ Недостаточно средств для решения!"

    # --- ЛОГИКА ВЗЛОМА (POST) ---
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Уязвимая f-строка для обучения
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

        try:
            c.execute(query)
            result = c.fetchone()
            
            if result:
                reward = 200
                session['balance'] += reward
                session['sql_count'] += 1
                session['fail_sql'] = 0
                session['xp'] = session.get('xp', 0) + 10
                
                message = f"✅ Доступ получен! Добро пожаловать, {username}. Вы заработали ${reward}!"
                
                # Добавляем ачивку, если её еще нет
                if "SQL Apprentice" not in session['achievements']:
                    session['achievements'].append("SQL Apprentice")
                    session.modified = True # Явно говорим Flask, что список в сессии изменился
            else:
                session['fail_sql'] += 1
                message = "❌ Ошибка авторизации. Система заблокировала запрос."

        except sqlite3.OperationalError as e:
            # Обработка ошибки синтаксиса (когда кавычки ломают запрос)
            message = f"⚠️ Ошибка базы данных: {e}. Твоя инъекция сломала синтаксис!"
            session['fail_sql'] += 1
        finally:
            conn.close()
                
    return render_template("sql_level_detail.html",
                           level=level_data,
                           message=message,
                           hint=hint,
                           solution=solution,
                           balance=session['balance'],
                           fail_count=session['fail_sql'])

# --- XSS Lab ---
@app.route('/XSS', methods=['GET', 'POST'])
def XSS():
    message = ''
    hint = ''
    solution = ''
    description = "Вы нашли поле ввода комментария. Возможно, оно не фильтрует теги."

    level = session.get('xss_count', 0) // 2 + 1
    session.setdefault('fail_xss', 0)

    if request.method == 'POST':
        user_input = request.form['user_input']
        if "<script>" in user_input:
            message = f"XSS Detected! {user_input}"
            session['xss_count'] += 1
            session['fail_xss'] = 0
            session['xp'] = session.get('xp', 0) + 10

            if "XSS Beginner" not in session['achievements']:
                session['achievements'].append("XSS Beginner")
        else:
            message = "Try inserting a script tag!"
            session['fail_xss'] += 1

            if session['fail_xss'] >= 3:
                hint = "Попробуйте <script>alert('XSS')</script>"

            if session['fail_xss'] >= 10:
                solution = "<script>alert('XSS')</script>"

    return render_template("xss.html",
                           message=message,
                           hint=hint,
                           solution=solution,
                           description=description,
                           level=level)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
