import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, Loader2, AlertCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import kaaraLogo from '../kaara.svg';
import ConfirmationModal from './ConfirmationModal';
import { 
  getQuestions, 
  submitQuiz, 
  parseOptions, 
  hasMultipleAnswers, 
  removeAuthToken,
  type Question as APIQuestion,
  type Answer,
  type QuizState,
  getQuizStatus // Added getQuizStatus
} from '../api/mcqAPI';

// Enhanced logging utility for MCQScreen
const createLogger = (component: string) => ({
  info: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${component}] INFO: ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] [${component}] ERROR: ${message}`, error || '');
  },
  warn: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.warn(`[${timestamp}] [${component}] WARN: ${message}`, data || '');
  },
  debug: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${component}] DEBUG: ${message}`, data || '');
  }
});

const logger = createLogger('MCQScreen');

interface Question extends APIQuestion {
  selectedAnswers: string[]; // Support multiple answers for Question 6
}

const MCQScreen: React.FC = () => {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<number | null>(null); // Will be calculated from server
  const [isQuizFinished, setIsQuizFinished] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isAlreadyCompleted, setIsAlreadyCompleted] = useState(false);
  const [showTimeUpModal, setShowTimeUpModal] = useState(false);

  // Refs to prevent re-entry and race conditions
  const startTimeRef = React.useRef<Date | null>(null);
  const timeUpStartedRef = React.useRef(false);

  // Answer persistence functions
  const saveAnswersToStorage = (questions: Question[]) => {
    try {
      const answersData = questions.map(q => ({
        questionId: q.id,
        selectedAnswers: q.selectedAnswers
      }));
      localStorage.setItem('mcq_answers', JSON.stringify(answersData));
      logger.debug('Answers saved to localStorage', { answerCount: answersData.length });
    } catch (error) {
      logger.error('Failed to save answers to localStorage', error);
    }
  };

  const loadAnswersFromStorage = (): Record<number, string[]> => {
    try {
      const savedAnswers = localStorage.getItem('mcq_answers');
      if (savedAnswers) {
        const answersData = JSON.parse(savedAnswers);
        const answersMap: Record<number, string[]> = {};
        answersData.forEach((item: any) => {
          answersMap[item.questionId] = item.selectedAnswers;
        });
        logger.debug('Answers loaded from localStorage', { answerCount: answersData.length });
        return answersMap;
      }
    } catch (error) {
      logger.error('Failed to load answers from localStorage', error);
    }
    return {};
  };

  const clearAnswersFromStorage = () => {
    try {
      localStorage.removeItem('mcq_answers');
      logger.debug('Answers cleared from localStorage');
    } catch (error) {
      logger.error('Failed to clear answers from localStorage', error);
    }
  };

  // Load questions on component mount
  useEffect(() => {
    logger.info('MCQScreen component mounted - starting quiz session');
    
    const loadQuestions = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        logger.info('QUIZ START: Fetching questions from backend...');
        const startTime = performance.now();
        
        const quizState: QuizState = await getQuestions();
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        logger.info('QUIZ START SUCCESS: Questions loaded', {
          duration: `${duration.toFixed(2)}ms`,
          questionCount: quizState.questions.length,
          quizStartedAt: quizState.quiz_started_at
        });
        
        // Load saved answers from localStorage
        const savedAnswers = loadAnswersFromStorage();
        
        // Transform API questions to include selectedAnswers (restore from storage if available)
        const transformedQuestions: Question[] = quizState.questions.map(q => ({
          ...q,
          selectedAnswers: savedAnswers[q.id] || []
        }));
        
        setQuestions(transformedQuestions);
        
        logger.info('Questions loaded with saved answers', {
          questionCount: transformedQuestions.length,
          savedAnswerCount: Object.keys(savedAnswers).length,
          questionsWithAnswers: transformedQuestions.filter(q => q.selectedAnswers.length > 0).length
        });
        
        // Calculate time left based on start time - FIXED: More accurate calculation
        const startTime_quiz = new Date(quizState.quiz_started_at);
        const now = new Date();
        
        // Ensure both times are in the same timezone context
        const elapsedSeconds = Math.floor((now.getTime() - startTime_quiz.getTime()) / 1000);
        const remainingTime = Math.max(0, (20 * 60) - elapsedSeconds);
        
        logger.info('Timer calculated - FIXED', {
          quizStartTime: startTime_quiz.toISOString(),
          currentTime: now.toISOString(),
          elapsedSeconds: elapsedSeconds,
          remainingTimeSeconds: remainingTime,
          remainingTimeMinutes: Math.floor(remainingTime / 60),
          timezoneOffset: startTime_quiz.getTimezoneOffset()
        });
        
        // Save quiz start time to localStorage for continuous timer calculation
        localStorage.setItem('quiz_start_time', quizState.quiz_started_at);
        
        setTimeLeft(remainingTime);
        
        // If time has already expired, auto-submit after a short delay to ensure component is ready
        if (remainingTime <= 0) {
          logger.warn('Quiz time already expired - auto-submitting after delay');
          setTimeout(() => {
          handleTimeUp();
          }, 1000); // 1 second delay to ensure component is fully mounted
        }
        
      } catch (error: any) {
        logger.error('QUIZ START FAILED: Failed to load questions', error);
        
        // Check for "already completed" error in the correct property
        const errorDetail = error.response?.data?.detail || error.message || '';
        
        if (errorDetail.includes('already completed')) {
          setError('You have already completed this quiz.');
          logger.warn('Quiz already completed by user', { errorDetail });
          setIsAlreadyCompleted(true);
        } else if (error.response?.status === 401 || errorDetail.includes('401')) {
          logger.error('Authentication failed - redirecting to login');
          removeAuthToken();
          navigate('/login');
        } else {
          setError('Failed to load quiz questions. Please try again.');
          logger.error('Unknown error loading quiz', { 
            status: error.response?.status,
            statusText: error.response?.statusText,
            errorDetail,
            fullError: error 
          });
        }
      } finally {
        setIsLoading(false);
        logger.debug('Quiz loading process completed');
      }
    };

    loadQuestions();
  }, [navigate]);

  // Unified, Drift-Free Timer and Auto-Submission Logic
  useEffect(() => {
    // Initialize the timer only once when timeLeft is first set from the initial API call.
    if (timeLeft !== null && !startTimeRef.current) {
      // Reconstruct the start time based on the initial remaining time.
      const quizStartTime = new Date(Date.now() - ((20 * 60) - timeLeft) * 1000);
      startTimeRef.current = quizStartTime;
      logger.info("TIMER: Authoritative start time established.", { startTime: quizStartTime });
    }

    // Timer should not run if the quiz is finished or start time isn't set.
    if (isQuizFinished || !startTimeRef.current) {
      return;
    }

    let syncCount = 0;
    const timerId = setInterval(async () => {
      if (!startTimeRef.current) return;
      
      // 1. Recalculate time from scratch on every tick to prevent drift.
      const now = new Date();
      const elapsedSeconds = Math.floor((now.getTime() - startTimeRef.current.getTime()) / 1000);
      const newTimeLeft = Math.max(0, (20 * 60) - elapsedSeconds);
      setTimeLeft(newTimeLeft);

      if (newTimeLeft <= 0) {
        // The effect below will handle the submission logic.
        // This interval's only job is to update the time.
      }
      
      syncCount++;

      // 2. Periodic Server Sync (every 30 seconds for external validation)
      if (syncCount >= 30) {
        syncCount = 0; // Reset counter
        logger.info('TIMER SYNC: Checking with server...');
        try {
          const status = await getQuizStatus();
          if (status.submitted_at) {
            logger.warn('TIMER SYNC: Quiz already submitted. Ending session.');
            setIsQuizFinished(true);
            return;
          }
          // Optional: We could add a drift correction here, but the primary calculation is now local.
        } catch (error) {
          logger.error('TIMER SYNC: Failed to sync with server.', error);
        }
      }
    }, 1000);

    // Cleanup function
    return () => {
      clearInterval(timerId);
    };
  }, [timeLeft, isQuizFinished, navigate]);

  // Effect to trigger auto-submission exactly once when time runs out.
  // This is kept separate from the timer interval to prevent race conditions.
  useEffect(() => {
    if (timeLeft !== null && timeLeft <= 0 && !isQuizFinished && !isSubmitting) {
      // Use a ref to ensure the submission process is only ever initiated once.
      if (timeUpStartedRef.current) {
        return;
      }
      timeUpStartedRef.current = true;
      
      logger.info('Time is up. Triggering auto-submission modal.');
      
      setShowTimeUpModal(true);
      setTimeout(() => {
        setShowTimeUpModal(false);
        logger.info('Auto-submitting quiz now...');
        handleSubmitQuiz(true);
      }, 3000);
    }
  }, [timeLeft, isQuizFinished, isSubmitting]);

  // Copy protection and page unload handling
  useEffect(() => {
    const preventCopy = (e: Event) => {
      e.preventDefault();
      return false;
    };

    const preventContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      return false;
    };

    const preventKeyboardShortcuts = (e: KeyboardEvent) => {
      // Prevent Ctrl+C, Ctrl+A, Ctrl+X, Ctrl+V, Ctrl+Z, Ctrl+Y, F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U
      if (
        (e.ctrlKey && (e.key === 'c' || e.key === 'a' || e.key === 'x' || e.key === 'v' || e.key === 'z' || e.key === 'y')) ||
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J')) ||
        (e.ctrlKey && e.key === 'u')
      ) {
        e.preventDefault();
        return false;
      }
    };

    // Save answers when page is about to unload
    const handleBeforeUnload = () => {
      if (questions.length > 0 && !isQuizFinished) {
        saveAnswersToStorage(questions);
        logger.info('Answers saved before page unload');
      }
    };

    // Add event listeners
    document.addEventListener('copy', preventCopy);
    document.addEventListener('cut', preventCopy);
    document.addEventListener('paste', preventCopy);
    document.addEventListener('contextmenu', preventContextMenu);
    document.addEventListener('keydown', preventKeyboardShortcuts);
    document.addEventListener('selectstart', preventCopy);
    document.addEventListener('dragstart', preventCopy);
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup on unmount
    return () => {
      document.removeEventListener('copy', preventCopy);
      document.removeEventListener('cut', preventCopy);
      document.removeEventListener('paste', preventCopy);
      document.removeEventListener('contextmenu', preventContextMenu);
      document.removeEventListener('keydown', preventKeyboardShortcuts);
      document.removeEventListener('selectstart', preventCopy);
      document.removeEventListener('dragstart', preventCopy);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [questions, isQuizFinished]);

  const handleTimeUp = () => {
    // This function is now only for manual calls if needed, but is not used by the timer.
    if (isQuizFinished || isSubmitting || timeUpStartedRef.current) {
      return;
    }
    timeUpStartedRef.current = true;
    logger.info('Manual time-up triggered...');
    setShowTimeUpModal(true);
    setTimeout(() => {
        setShowTimeUpModal(false);
        handleSubmitQuiz(true);
    }, 3000);
  };

  const handleAnswerChange = (questionId: number, selectedAnswer: string) => {
    setQuestions(prev => {
      const updatedQuestions = prev.map(q => {
      if (q.id === questionId) {
        if (hasMultipleAnswers(q)) {
          // For questions with multiple answers (like Question 6)
          const currentAnswers = q.selectedAnswers || [];
          const newAnswers = currentAnswers.includes(selectedAnswer)
            ? currentAnswers.filter(ans => ans !== selectedAnswer) // Remove if already selected
            : [...currentAnswers, selectedAnswer]; // Add if not selected
          
          return { ...q, selectedAnswers: newAnswers };
        } else {
          // For single answer questions
          return { ...q, selectedAnswers: [selectedAnswer] };
        }
      }
      return q;
      });
      
      // Save answers to localStorage after each change
      saveAnswersToStorage(updatedQuestions);
      
      return updatedQuestions;
    });
  };

  const handleSubmitQuiz = async (autoSubmit = false) => {
    if (isSubmitting) {
      logger.warn('Submit quiz called while already submitting');
      return;
    }
    
    logger.info('Starting quiz submission', { autoSubmit });
    
    try {
      setIsSubmitting(true);
      setError(null);

      // Prepare answers for submission
      const answers: Answer[] = questions
        .filter(q => q.selectedAnswers && q.selectedAnswers.length > 0)
        .flatMap(q => 
          q.selectedAnswers.map(answer => ({
            question_id: q.id,
            selected_answer: answer
          }))
        );

      logger.info('Submitting answers', { 
        answerCount: answers.length,
        autoSubmit,
        timeLeft
      });

      // If auto-submitting with no answers, submit with score 0
      if (autoSubmit && answers.length === 0) {
        logger.warn('Auto-submitting with no answers selected - will submit with score 0');
        // Continue with submission - backend will calculate score 0
      }

      const result = await submitQuiz({ answers });
      
      // On SUCCESS, permanently finish the quiz
      setScore(result.score);
      setIsQuizFinished(true);
      setShowConfirmModal(false);
      clearAnswersFromStorage();
      localStorage.removeItem('quiz_start_time');

      logger.info('Quiz submitted successfully', { 
        score: result.score,
        autoSubmit 
      });
      
    } catch (error: any) {
      logger.error('Failed to submit quiz', { 
        error: error.message,
        response: error.response?.data,
        status: error.response?.status,
        autoSubmit 
      });
      
      const errorMessage = error.response?.data?.detail || error.message || 'An unknown error occurred.';
      
      // For unrecoverable errors, end the quiz.
      if (errorMessage.includes('Time limit exceeded') || errorMessage.includes('already completed')) {
        logger.warn('Unrecoverable submission error. Ending quiz.', { errorMessage });
        setError(`Your quiz could not be submitted: ${errorMessage}`);
        setIsQuizFinished(true); // Lock the quiz
        clearAnswersFromStorage();
        localStorage.removeItem('quiz_start_time');
      } else {
        // For recoverable errors (e.g., network issue), just show the error and allow retry.
        logger.error('Recoverable submission error. Allowing user to retry.', { errorMessage });
        setError(`Submission failed: ${errorMessage}. Please check your connection and try again.`);
      }

    } finally {
      setIsSubmitting(false);
      logger.debug('Quiz submission process completed');
    }
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getTimeColor = (): string => {
    if (timeLeft === null) return 'text-green-600';
    if (timeLeft <= 60) return 'text-red-600'; // Last minute
    if (timeLeft <= 300) return 'text-yellow-600'; // Last 5 minutes
    return 'text-green-600';
  };

  const goToQuestion = (index: number) => {
    if (index >= 0 && index < questions.length) {
      setCurrentQuestionIndex(index);
    }
  };

  const getAnsweredQuestionsCount = (): number => {
    return questions.filter(q => q.selectedAnswers && q.selectedAnswers.length > 0).length;
  };

  const getUnansweredQuestions = (): number[] => {
    return questions
      .map((q, index) => ({ q, index }))
      .filter(({ q }) => !q.selectedAnswers || q.selectedAnswers.length === 0)
      .map(({ index }) => index + 1);
  };

  const handleSubmitClick = () => {
    const unanswered = getUnansweredQuestions();
    if (unanswered.length > 0) {
      setShowConfirmModal(true);
    } else {
      handleSubmitQuiz();
    }
  };

  const currentQuestion = questions[currentQuestionIndex];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-red-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading quiz...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          {isAlreadyCompleted ? (
            <>
              <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Quiz Already Completed</h2>
              <p className="text-gray-600 mb-4">
                You have already submitted your responses for this quiz. Thank you for your participation!
              </p>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Return to Login
              </button>
            </>
          ) : (
            <>
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <div className="space-x-4">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Back to Login
            </button>
          </div>
            </>
          )}
        </div>
      </div>
    );
  }

  if (isQuizFinished) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
          <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Quiz Completed!</h2>
          {score !== null ? (
            <p className="text-lg text-gray-600 mb-4">
              Your Score: <span className="font-semibold text-green-600">{score.toFixed(1)}/25</span>
            </p>
          ) : (
            <p className="text-lg text-gray-600 mb-4">Your quiz has been submitted successfully.</p>
          )}
          <p className="text-gray-500 mb-6">
            Thank you for taking the quiz. You may now close this window.
          </p>
          <button
            onClick={() => {
              removeAuthToken();
              navigate('/login');
            }}
            className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No questions available.</p>
        </div>
      </div>
    );
  }

  const options = parseOptions(currentQuestion.options);
  const isMultipleChoice = hasMultipleAnswers(currentQuestion);

  // This should be the main return, wrapping the quiz screen
  // with potential overlays for submitting states.
  return (
    <>
      {isSubmitting && (
        <div className="fixed inset-0 bg-white bg-opacity-80 flex items-center justify-center z-50">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-red-600 mx-auto mb-4" />
            <p className="text-xl font-semibold text-gray-700">Submitting your answers...</p>
            <p className="text-gray-500">Please do not close this window.</p>
          </div>
        </div>
      )}

      {showTimeUpModal && (
        <div className="fixed inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50">
          <div className="text-center p-8">
            <Clock className="h-16 w-16 text-red-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Time's Up!</h2>
            <p className="text-lg text-gray-600">Your quiz will be submitted automatically now.</p>
          </div>
        </div>
      )}
      
      {/* The main quiz screen content */}
      <div className={`min-h-screen bg-gray-50 flex flex-col items-center justify-start py-8 px-4 relative ${isSubmitting ? 'blur-sm' : ''}`}>
      {/* Header */}
        <header className="w-full max-w-4xl mx-auto flex justify-between items-center mb-6">
            <div className="flex items-center space-x-4">
            <img src={kaaraLogo} alt="Kaara" className="h-6 select-none pointer-events-none" />
            <span className="text-lg font-semibold text-gray-900 select-none pointer-events-none">MCQ Assessment</span>
            </div>
            <div className="flex items-center space-x-6">
            <div className="text-sm text-gray-600 select-none pointer-events-none">
                Question {currentQuestionIndex + 1} of {questions.length}
              </div>
            <div className={`flex items-center space-x-2 text-sm font-medium ${getTimeColor()} select-none pointer-events-none`}>
                <Clock className="h-4 w-4" />
              <span>{timeLeft !== null ? formatTime(timeLeft) : '--:--'}</span>
            </div>
          </div>
        </header>

        <main className="w-full max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Question Navigation Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3 select-none pointer-events-none">Progress</h3>
                <div className="text-xs text-gray-600 mb-4 select-none pointer-events-none">
                {getAnsweredQuestionsCount()} of {questions.length} answered
              </div>
              <div className="grid grid-cols-5 gap-2">
                {questions.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => goToQuestion(index)}
                    className={`h-8 w-8 text-xs rounded flex items-center justify-center border transition-colors ${
                      index === currentQuestionIndex
                        ? 'bg-red-600 text-white border-red-600'
                        : questions[index].selectedAnswers && questions[index].selectedAnswers.length > 0
                        ? 'bg-green-100 text-green-800 border-green-300'
                        : 'bg-gray-50 text-gray-600 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <button
                  onClick={handleSubmitClick}
                  disabled={isSubmitting}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      <span>Submit Quiz</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Main Question Area */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Question {currentQuestionIndex + 1}
                  </h2>
                  {isMultipleChoice && (
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      Multiple Answers
                    </span>
                  )}
                </div>
                  <p className="text-gray-700 leading-relaxed select-none pointer-events-none">
                  {currentQuestion.question_text}
                </p>
              </div>

              <div className="space-y-3">
                {options.map((option, index) => {
                  const optionLetter = String.fromCharCode(65 + index); // A, B, C, D
                  const isSelected = currentQuestion.selectedAnswers?.includes(optionLetter) || false;
                  
                  // FIX: Remove the redundant "A) " prefix from the option text itself.
                  const cleanedOption = option.replace(/^[A-D]\)\s*/, '');

                  return (
                    <label
                      key={optionLetter}
                      className={`flex items-start space-x-3 p-4 rounded-lg border cursor-pointer transition-colors ${
                        isSelected
                          ? 'border-red-500 bg-red-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type={isMultipleChoice ? 'checkbox' : 'radio'}
                        name={`question-${currentQuestion.id}`}
                        value={optionLetter}
                        checked={isSelected}
                        onChange={() => handleAnswerChange(currentQuestion.id, optionLetter)}
                        className="mt-1 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300"
                      />
                        <div className="flex-1 select-none pointer-events-none">
                        <span className="font-medium text-gray-900 mr-2">{optionLetter}.</span>
                        <span className="text-gray-700">{cleanedOption}</span>
                      </div>
                    </label>
                  );
                })}
        </div>

              {/* Navigation Buttons */}
              <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
                <button
                  onClick={() => goToQuestion(currentQuestionIndex - 1)}
                  disabled={currentQuestionIndex === 0}
                  className="flex items-center space-x-2 px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>Previous</span>
                </button>

                <span className="text-sm text-gray-500">
                  {currentQuestionIndex + 1} of {questions.length}
                </span>

          <button 
                  onClick={() => goToQuestion(currentQuestionIndex + 1)}
                  disabled={currentQuestionIndex === questions.length - 1}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>Next</span>
                  <ArrowRight className="h-4 w-4" />
          </button>
              </div>
            </div>
          </div>
        </div>
        </main>
      </div>

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={() => handleSubmitQuiz()}
        title="Submit Quiz"
        message={`You have ${getUnansweredQuestions().length} unanswered questions (${getUnansweredQuestions().join(', ')}). Are you sure you want to submit the quiz?`}
        type="warning"
        confirmText="Submit Anyway"
        cancelText="Continue Quiz"
        isLoading={isSubmitting}
      />


    </>
  );
};

export default MCQScreen;