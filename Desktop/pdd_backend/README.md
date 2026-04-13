# ПДД TEST - Kazakh Road Rules Testing System

Қазақ ПДД (жол ережелері) бойынша онлайн тестілеу жүйесі. 

## 🚀 Ерекшеліктер

- ✅ Қазақ & Орыс тілінде толық қолдау
- ✅ Ақ/Қара режимі теме айни
- 📊 Статистика және рейтинг панелі
- 🔐 Электрондық пошта растау арқылы қарсылықсыз тіркелу
- 📱 Мобиль-дружественныый дизайн
- ⚡ REST API түпнұсқалары
- 🛠️ Администратор панелі
- 💾 Автосохранение тест сыналмаларының

## 📋 Талаптар

- Python 3.8+
- Flask 2.0+
- SQLite3
- pip (Python пакет менеджері)

## 🔧 Орнату

### 1. Репозиторийін клондау

```bash
git clone https://github.com/yourusername/pdd_backend.git
cd pdd_backend
```

### 2. Виртуаль ортасын құру

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# немесе Windows үшін:
# venv\Scripts\activate
```

### 3. Тәуелділіктерді орнату

```bash
cd app
pip install -r requirements.txt
```

### 4. Деректер базасын інициализациялау

```bash
python3 init_db.py
```

## 🚀 Қолдану

### Әдеттің сервері қосу

```bash
./start_site.sh
# немесе тура:
python3 app.py
```

Сайтына өтіңіз: `http://localhost:5000`

### Flask ортасын құру (өндіктіліктегі)

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 app.py
```

## 📡 REST API

### Аутентификация керек

#### Dashboard статистикасы
```
GET /api/dashboard/stats
```
**Жауап:**
```json
{
  "username": "student_name",
  "total_attempts": 10,
  "avg_percent": 82.5,
  "best_percent": 95.0,
  "excellent": 6,
  "good": 3,
  "needs_improvement": 1,
  "is_premium": false
}
```

#### Тест нәтижелері
```
GET /api/results
```

#### Пайдаланушы профилі
```
GET /api/user/profile
```

#### Рейтинг
```
GET /api/leaderboard
```

#### Тест сұрақтарын алу
```
GET /api/test/questions/<test_id>
```

#### Тест жарттарын жіберу
```
POST /api/test/submit
Content-Type: application/json

{
  "answers": {
    "1": "a",
    "2": "b",
    "3": "c"
  },
  "test_id": 1
}
```

## 📊 Деректер базасы

### Кестелер

- **users** - Пайдаланушы аккаунттары
- **email_verifications** - Электрондық пошта растау кодтары (15 минут)
- **tests** - Тест жиынтықтары
- **questions** - Сұрақтар
- **test_sets** - Сынақ топтары
- **results** - Сынақ нәтижелері
- **autosaves** - Автосохраненные сынақ деректері

## 🎨 Дизайн

- **Түсіндігі:** Түріндегі голубой (#0f73ff) және зеленый (#1eb980)
- **Фон:** Светлое и темное режимы с плавной инверсией
- **Шрифт:** Inter, Segoe UI
- **Адаптив:** Мобильді өндіктілік оңтайлау

## 🔐 Аутентификация

### Тіркелу ағыны
1. Email мекенжайын және пароль енгізіңіз
2. Электрондық поштаға 6 цифрлі коды алыңыз
3. Кодты растау беттесінде енгізіңіз
4. Аккаунт құрылды, пайдалана аласыз

### Пароль талаптары
- Міндетті түрде 6 таңба немесе одан көп
- Email форматы дұрыс болуы керек

## 📁 Папка құрылымы

```
pdd_backend/
├── app/
│   ├── app.py                 # Flask қосымшасының негізі
│   ├── init_db.py            # Деректер базасын инициализациялау
│   ├── schema.sql            # Деректер базасының схемасы
│   ├── seed.sql              # Демо деректер
│   ├── requirements.txt       # Python пакеттері
│   ├── data/
│   │   └── database.db       # SQLite деректер базасы
│   ├── static/
│   │   └── style.css         # CSS стильдері
│   └── templates/            # Jinja2 шаблондары
│       ├── base.html
│       ├── dashboard.html
│       ├── test.html
│       ├── login.html
│       ├── register.html
│       ├── verify_email.html
│       └── ...
├── start_site.sh             # Сервисті қосу скрипті
└── README.md                 # Бұл файл
```

## ⚙️ Конфигурация

Ортамды айнымалыларын `.env` файлында орнатыңыз:

```bash
FLASK_ENV=production
FLASK_SECRET=your-secret-key-here
WHATSAPP_LINK=https://wa.me/77785627501
```

## 🐛 Мәсақттарды шешу

### SQL қатесі деректер базасында
```bash
cd app
python3 init_db.py  # Деректер базасын қайта құру
```

### Flask портісі қолданыста
```bash
python3 app.py --port 5001
```

MIT License - бай пайдала құрылысы бойынша исіменді құрайды.

## 👥 Қатысушылар

- @zhanserikaliaskar - Негіз құрастырушы

## 📞 қолдау

WhatsApp: https://wa.me/77785627501
Instagram: https://www.instagram.com/pddala.kz
Email: support@pdd.kz

---

**Соңғы өңдеу:** 10 апреля 2026
