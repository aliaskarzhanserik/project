
const questions = [
    {
        question: "Какой знак запрещает движение всех транспортных средств?",
        options: ["Знак \"Въезд запрещён\"", "Знак \"Движение запрещено\"", "Знак \"Остановка запрещена\"", "Знак \"Пешеходная зона\""],
        correct: 0
    },
    {
        question: "Сколько метров до пешеходного перехода должно быть установлено предупреждающее расстояние знака?",
        options: ["50-100 метров", "100-150 метров", "150-200 метров", "200-300 метров"],
        correct: 2
    },
    {
        question: "Какой знак предупреждает о неровной дороге?",
        options: ["Знак \"Тряская дорога\"", "Знак \"Неровная дорога\"", "Знак \"Выбоина\"", "Знак \"Осторожно\""],
        correct: 1
    },
    {
        question: "Разрешена ли обгон справа?",
        options: ["Да, всегда", "Нет, никогда", "Да, при наличии свободной полосы", "Только на двухполосной дороге"],
        correct: 1
    },
    {
        question: "Какой минимальный возраст для управления скутером (мопедом)?",
        options: ["14 лет", "16 лет", "18 лет", "20 лет"],
        correct: 1
    },
    {
        question: "При каком сигнале светофора запрещено переходить дорогу пешеходам?",
        options: ["Зелёный мигающий", "Зелёный", "Красный", "Жёлтый мигающий"],
        correct: 2
    },
    {
        question: "Какой знак указывает на место для парковки?",
        options: ["Знак \"Парковка\"", "Знак \"Стоянка запрещена\"", "Знак \"Место стоянки\"", "Знак \"Автостоянка\""],
        correct: 0
    },
    {
        question: "Что означает жёлтый сигнал светофора?",
        options: ["Можно двигаться", "Приготовиться к остановке", "Обязательная остановка", "Предупреждение об опасности"],
        correct: 1
    },
    {
        question: "Какой знак запрещает въезд транспортных средств с опасными грузами?",
        options: ["Знак \"Опасный груз\"", "Знак \"Проезд запрещён\"", "Знак \"Движение механических ТС запрещено\"", "Знак \"Транспортные средства с опасными грузами запрещены\""],
        correct: 3
    },
    {
        question: "Разрешено ли поворачивать направо на красный сигнал светофора?",
        options: ["Да, всегда", "Нет, никогда", "Только при наличии стрелки", "Только если нет пешеходов"],
        correct: 2
    }
];

let currentQuestion = 0;
let score = 0;
let answered = false;


function initQuiz() {
    showQuestion();
}

function showQuestion() {
    const quizContainer = document.getElementById('quiz');
    if (!quizContainer) return;

    const q = questions[currentQuestion];
    let html = `
        <div class="score-display">Вопрос ${currentQuestion + 1} из ${questions.length} | Правильных ответов: ${score}</div>
        <div class="quiz-question">
            <h3>${q.question}</h3>
        </div>
        <div class="quiz-options">
    `;

    q.options.forEach((option, index) => {
        html += `<div class="quiz-option" onclick="selectAnswer(${index})">${option}</div>`;
    });

    html += `</div>`;
    quizContainer.innerHTML = html;
}


function selectAnswer(index) {
    if (answered) return;
    answered = true;

    const options = document.querySelectorAll('.quiz-option');
    const correct = questions[currentQuestion].correct;

    options.forEach((option, i) => {
        option.style.pointerEvents = 'none';
        if (i === correct) {
            option.classList.add('correct');
        } else if (i === index && index !== correct) {
            option.classList.add('wrong');
        }
    });

    if (index === correct) {
        score++;
    }

    setTimeout(() => {
        currentQuestion++;
        answered = false;
        if (currentQuestion < questions.length) {
            showQuestion();
        } else {
            showResult();
        }
    }, 1500);
}

function showResult() {
    const quizContainer = document.getElementById('quiz');
    const percentage = Math.round((score / questions.length) * 100);
    
    let message = '';
    if (percentage >= 80) {
        message = 'Отлично! Вы хорошо знаете ПДД!';
    } else if (percentage >= 60) {
        message = 'Хорошо! Но есть что повторить.';
    } else {
        message = 'Советуем изучить ПДД внимательнее!';
    }

    quizContainer.innerHTML = `
        <div class="quiz-question">
            <h2>Тест завершён!</h2>
            <p style="font-size: 2rem; margin: 1rem 0;">${score} / ${questions.length}</p>
            <p style="font-size: 1.2rem; color: var(--secondary-color);">${message}</p>
            <button class="quiz-btn" onclick="restartQuiz()">Пройти снова</button>
        </div>
    `;
}


function restartQuiz() {
    currentQuestion = 0;
    score = 0;
    answered = false;
    showQuestion();
}


document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('nav a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    
    if (document.getElementById('quiz')) {
        initQuiz();
    }
});
