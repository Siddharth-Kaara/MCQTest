document.addEventListener("DOMContentLoaded", () => {
    const API_URL = "http://127.0.0.1:8001";

    const loginView = document.getElementById("login-view");
    const quizView = document.getElementById("quiz-view");
    const adminView = document.getElementById("admin-view");

    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error");

    const quizContent = document.getElementById("quiz-content");
    const timerDisplay = document.getElementById("timer");
    const submitQuizBtn = document.getElementById("submit-quiz-btn");
    const resultsBody = document.getElementById("results-body");

    let token = null;
    let timerInterval = null;
    let questions = [];
    let userAnswers = {};
    let quizStartTime = null;

    async function startQuiz() {
        try {
            const response = await fetch(`${API_URL}/questions/`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 400 && errorData.detail === "You have already completed the quiz.") {
                    quizContent.innerHTML = `<p class="info-message">You have already completed the quiz. Thank you for your participation.</p>`;
                    // Hide submit button and timer if they are visible
                    if(submitQuizBtn) submitQuizBtn.style.display = 'none';
                    if(timerDisplay) timerDisplay.style.display = 'none';
                } else {
                    throw new Error(errorData.detail || "Could not load quiz questions.");
                }
                return; // Stop further execution
            }
            
            questions = await response.json();
            renderQuestions();
            startTimer();
            quizStartTime = Date.now();
        } catch (error) {
            console.error(error);
            quizContent.innerHTML = `<p class="error-message">${error.message}</p>`;
        }
    }

    function renderQuestions() {
        quizContent.innerHTML = "";
        questions.forEach((q, index) => {
            const questionEl = document.createElement("div");
            questionEl.className = "question";
            
            const optionsHtml = q.options.split("||").map(opt => {
                // Extract letter and text, e.g., "A. Some text"
                const [letter, ...textParts] = opt.split('. ');
                const text = textParts.join('. ');
                return `<div class="option" data-question-id="${q.id}" data-answer="${letter}">${opt}</div>`;
            }).join("");

            questionEl.innerHTML = `
                <p>${index + 1}. ${q.question_text}</p>
                <div class="options">${optionsHtml}</div>
            `;
            quizContent.appendChild(questionEl);
        });
    }
    
    function startTimer() {
        let timeLeft = 20 * 60; // 20 minutes in seconds
        timerInterval = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                submitQuiz();
            }
            timeLeft--;
        }, 1000);
    }
    
    async function submitQuiz() {
        clearInterval(timerInterval);
        
        const submissionData = {
            answers: Object.entries(userAnswers).map(([question_id, selected_answer]) => ({
                question_id: parseInt(question_id),
                selected_answer,
            }))
        };

        try {
            const response = await fetch(`${API_URL}/submit`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(submissionData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Submission failed");
            }

            const result = await response.json();
            quizView.innerHTML = `
                <div class="container">
                    <h1>Quiz Complete!</h1>
                    <p>Your submission has been received.</p>
                    <p>Thank you for participating.</p>
                </div>
            `;

        } catch (error) {
            console.error("Submission error:", error);
            alert(`An error occurred during submission: ${error.message}`);
        }
    }

    async function loadAdminDashboard() {
        try {
            const response = await fetch(`${API_URL}/admin/results/`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!response.ok) throw new Error("Could not load admin data.");
            
            const results = await response.json();
            renderResults(results);

        } catch (error) {
            console.error("Admin error:", error);
            adminView.innerHTML = `<p class="error-message">${error.message}</p>`;
        }
    }

    function renderResults(results) {
        resultsBody.innerHTML = "";
        // Sort results to show students who have completed the quiz first
        results.sort((a, b) => (b.result ? 1 : 0) - (a.result ? 1 : 0));

        results.forEach(student => {
            // Skip admin user in the results table
            if (student.email === "admin@kaaratech.com") {
                return; // Skips the rest of the loop for the admin
            }
            
            const score = student.result ? student.result.score : "Not Attempted";
            const timeTaken = student.result ? student.result.time_taken : "N/A";
            
            let normalizedScoreText = "N/A";
            if (student.result) {
                const maxTime = 20 * 60;
                const timePenalty = Math.max(0, (student.result.time_taken - (maxTime * 0.25)) / (maxTime * 0.75));
                const speedScore = (1 - timePenalty) * 100;
                const academicScore = (student.cgpa * 10 + student.tenth_percentage + student.twelfth_percentage) / 3;
                const quizScore = (student.result.score / 25) * 100;
                const normalizedScore = (quizScore * 0.5) + (academicScore * 0.3) + (speedScore * 0.2);
                normalizedScoreText = normalizedScore.toFixed(2);
            }

            const row = `
                <tr>
                    <td>${student.roll_no}</td>
                    <td>${student.full_name}</td>
                    <td>${student.email}</td>
                    <td>${score}</td>
                    <td>${timeTaken}</td>
                    <td>${student.tenth_percentage || "N/A"}</td>
                    <td>${student.twelfth_percentage || "N/A"}</td>
                    <td>${student.cgpa || "N/A"}</td>
                    <td>${normalizedScoreText}</td>
                </tr>
            `;
            resultsBody.innerHTML += row;
        });
    }

    submitQuizBtn.addEventListener("click", submitQuiz);

    quizContent.addEventListener("click", (e) => {
        if (e.target.classList.contains("option")) {
            const questionId = e.target.dataset.questionId;
            const answer = e.target.dataset.answer;

            // Deselect other options for the same question
            const allOptions = quizContent.querySelectorAll(`.option[data-question-id="${questionId}"]`);
            allOptions.forEach(opt => opt.classList.remove("selected"));
            
            // Select the clicked option
            e.target.classList.add("selected");
            userAnswers[questionId] = answer;
        }
    });

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        const details = {
            'username': email,
            'password': password
        };
        const formBody = Object.keys(details).map(key => encodeURIComponent(key) + '=' + encodeURIComponent(details[key])).join('&');


        try {
            const response = await fetch(`${API_URL}/token`, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
                },
                body: formBody,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Login failed");
            }

            const data = await response.json();
            token = data.access_token;
            
            // For now, let's just hide the login and prepare for the next view
            loginView.classList.add("hidden");
            loginError.textContent = "";

            // Simple routing based on email
            if (email === "admin@kaaratech.com") {
                adminView.classList.remove("hidden");
                await loadAdminDashboard();
            } else {
                quizView.classList.remove("hidden");
                await startQuiz();
            }

        } catch (error) {
            loginError.textContent = error.message;
        }
    });
}); 