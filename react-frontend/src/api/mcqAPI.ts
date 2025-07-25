import axios, { InternalAxiosRequestConfig } from 'axios';

// Enhanced API logging utility
const createAPILogger = () => ({
  info: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [API] INFO: ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] [API] ERROR: ${message}`, error || '');
  },
  warn: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.warn(`[${timestamp}] [API] WARN: ${message}`, data || '');
  },
  debug: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [API] DEBUG: ${message}`, data || '');
  }
});

const apiLogger = createAPILogger();

// Configure axios instance with base URL
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://kaara-mcq-test.azurewebsites.net',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Log API configuration
apiLogger.info('API client initialized', {
  baseURL: API.defaults.baseURL,
  headers: API.defaults.headers,
  environment: import.meta.env.NODE_ENV
});

// Add request interceptor for logging
API.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
    
    apiLogger.debug('='.repeat(40));
    apiLogger.debug('OUTGOING API REQUEST');
    apiLogger.info(`${config.method?.toUpperCase()} ${config.url}`, {
      baseURL: config.baseURL,
      headers: { ...config.headers },
      hasToken: !!token,
      tokenLength: token ? token.length : 0
    });
    
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
      apiLogger.debug('Authorization header added to request');
    } else {
      apiLogger.warn('No access token found in localStorage');
    }
    
    // Log request data (without sensitive information)
    if (config.data) {
      if (config.data instanceof FormData) {
        apiLogger.debug('Request data: FormData object');
        // Log FormData keys without values for security
        const keys = [];
        for (const key of config.data.keys()) {
          keys.push(key);
        }
        apiLogger.debug('FormData keys:', keys);
      } else {
        apiLogger.debug('Request data:', config.data);
      }
    }
    
    return config;
  },
  (error) => {
    apiLogger.error('Request interceptor error', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging
API.interceptors.response.use(
  (response) => {
    apiLogger.info('API RESPONSE SUCCESS', {
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      method: response.config.method?.toUpperCase(),
      dataKeys: response.data ? Object.keys(response.data) : []
    });
    
    apiLogger.debug('Response headers:', response.headers);
    apiLogger.debug('Response data:', response.data);
    apiLogger.debug('='.repeat(40));
    
    return response;
  },
  (error) => {
    apiLogger.error('='.repeat(40));
    apiLogger.error('API RESPONSE ERROR');
    
    if (error.response) {
      // Server responded with error status
      apiLogger.error('HTTP Error Response', {
        status: error.response.status,
        statusText: error.response.statusText,
        url: error.config?.url,
        method: error.config?.method?.toUpperCase(),
        data: error.response.data,
        headers: error.response.headers
      });
    } else if (error.request) {
      // Request was made but no response received
      apiLogger.error('Network Error - No Response', {
        url: error.config?.url,
        method: error.config?.method?.toUpperCase(),
        message: 'Request was sent but no response received',
        timeout: error.config?.timeout,
        code: error.code
      });
    } else {
      // Something else happened
      apiLogger.error('Request Setup Error', {
        message: error.message,
        stack: error.stack
      });
    }
    
    apiLogger.debug('='.repeat(40));
    return Promise.reject(error);
  }
);

// Types
export interface LoginRequest {
  username: string; // Note: FastAPI expects 'username' field for OAuth2PasswordRequestForm
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface CorrectAnswer {
  answer: string;
}

export interface Question {
  id: number;
  question_text: string;
  options: string;
  correct_answers: CorrectAnswer[];
}

export interface QuizState {
  questions: Question[];
  quiz_started_at: string;
}

export interface QuizStatus {
  quiz_started_at: string;
  submitted_at?: string;
}

export interface Answer {
  question_id: number;
  selected_answer: string;
}

export interface SubmissionRequest {
  answers: Answer[];
}

export interface SubmissionResponse {
  message: string;
  score: number;
}

// API functions
export const loginUser = async (credentials: LoginRequest): Promise<LoginResponse> => {
  try {
    apiLogger.info('🚀 LOGIN REQUEST INITIATED');
    apiLogger.info('Preparing login credentials', {
      username: credentials.username,
      passwordProvided: !!credentials.password,
      passwordLength: credentials.password?.length || 0
    });

  const formData = new FormData();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);
    
    apiLogger.debug('FormData prepared for OAuth2PasswordRequestForm');
    
    const startTime = performance.now();
  
  const response = await API.post('/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    apiLogger.info('✅ LOGIN REQUEST SUCCESSFUL', {
      duration: `${duration.toFixed(2)}ms`,
      tokenReceived: !!response.data.access_token,
      tokenLength: response.data.access_token?.length || 0,
      tokenType: response.data.token_type
    });
    
  return response.data;
    
  } catch (error: any) {
    apiLogger.error('❌ LOGIN REQUEST FAILED');
    
    // Enhanced error logging for login failures
    if (error.response?.status === 401) {
      apiLogger.error('Authentication failed - Invalid credentials', {
        status: error.response.status,
        detail: error.response.data?.detail,
        username: credentials.username
      });
    } else if (error.response?.status === 422) {
      apiLogger.error('Validation error - Request format issue', {
        status: error.response.status,
        detail: error.response.data?.detail,
        validationErrors: error.response.data?.errors
      });
    } else if (error.response?.status >= 500) {
      apiLogger.error('Server error during login', {
        status: error.response.status,
        detail: error.response.data?.detail
      });
    } else if (!error.response) {
      apiLogger.error('Network error during login - No response from server', {
        code: error.code,
        message: error.message
      });
    }
    
    throw error;
  }
};

export const getQuestions = async (): Promise<QuizState> => {
  try {
    apiLogger.info('🚀 QUESTIONS REQUEST INITIATED');
    const startTime = performance.now();
    const response = await API.get<QuizState>('/questions/');
    const endTime = performance.now();
    const duration = endTime - startTime;
    apiLogger.info('✅ QUESTIONS REQUEST SUCCESSFUL', {
      duration: `${duration.toFixed(2)}ms`,
      questionCount: response.data.questions?.length || 0,
      quizStartedAt: response.data.quiz_started_at
    });
    return response.data;
  } catch (error) {
    apiLogger.error('❌ QUESTIONS REQUEST FAILED');
    throw error;
  }
};

export const getQuizStatus = async (): Promise<QuizStatus> => {
  try {
    const response = await API.get<QuizStatus>('/quiz-status');
  return response.data;
  } catch (error) {
    console.error('API Error: getQuizStatus failed', error);
    throw error;
  }
};

export const submitQuiz = async (submission: SubmissionRequest): Promise<SubmissionResponse> => {
  try {
    apiLogger.info('🚀 SUBMISSION REQUEST INITIATED');
    const startTime = performance.now();
    const response = await API.post<SubmissionResponse>('/submit', submission);
    const endTime = performance.now();
    const duration = endTime - startTime;
    apiLogger.info('✅ SUBMISSION REQUEST SUCCESSFUL', {
      duration: `${duration.toFixed(2)}ms`,
      score: response.data.score
    });
  return response.data;
  } catch (error) {
    apiLogger.error('❌ SUBMISSION REQUEST FAILED');
    throw error;
  }
};

// Helper function to parse options string
export const parseOptions = (optionsString: string): string[] => {
  return optionsString.split('||').map(option => option.trim());
};

// Helper function to check if a question has multiple correct answers
export const hasMultipleAnswers = (question: Question): boolean => {
  return question.correct_answers.length > 1;
};

// Storage helpers
export const setAuthToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

export const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token');
};

export const removeAuthToken = (): void => {
  localStorage.removeItem('access_token');
};

export const isAuthenticated = (): boolean => {
  return !!getAuthToken();
}; 