import React from 'react';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import kaaraLogo from '../kaara.svg';
import { loginUser, setAuthToken } from '../api/mcqAPI';

// Enhanced logging utility for frontend
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

const logger = createLogger('LoginScreen');

const LoginScreen: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [showPassword, setShowPassword] = React.useState(false);
  const [emailError, setEmailError] = React.useState('');
  const [loginError, setLoginError] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  // Log component mount
  React.useEffect(() => {
    logger.info('LoginScreen component mounted');
    logger.debug('Environment check', {
      apiUrl: import.meta.env.VITE_API_URL,
      nodeEnv: import.meta.env.NODE_ENV,
      userAgent: navigator.userAgent
    });
  }, []);

  // Email validation function
  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    
    logger.debug('Email field changed', { emailLength: value.length });
    
    if (value && !validateEmail(value)) {
      setEmailError('Please enter a valid email address');
      logger.warn('Invalid email format detected', { email: value });
    } else {
      setEmailError('');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    logger.info('='.repeat(50));
    logger.info('LOGIN ATTEMPT STARTED');
    logger.info('='.repeat(50));
    
    const attemptTimestamp = new Date().toISOString();
    logger.info('Login attempt details', {
      timestamp: attemptTimestamp,
      email: email,
      emailLength: email.length,
      passwordProvided: !!password,
      passwordLength: password.length,
      apiUrl: import.meta.env.VITE_API_URL
    });

    // Validation checks
    if (!email || !password) {
      const errorMsg = 'Please enter both email and password';
      setLoginError(errorMsg);
      logger.error('Validation failed: Missing credentials', {
        emailProvided: !!email,
        passwordProvided: !!password
      });
      return;
    }

    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      logger.error('Validation failed: Invalid email format', { email });
      return;
    }

    setIsLoading(true);
    setLoginError('');

    try {
      logger.info('STEP 1: Preparing login request');
      
      const loginCredentials = {
        username: email, // FastAPI expects 'username' field
        password: password
      };

      logger.debug('Login credentials prepared', {
        username: loginCredentials.username,
        passwordProvided: !!loginCredentials.password
      });

      // Login to get token
      logger.info('STEP 2: Sending login request to backend');
      const loginStartTime = performance.now();
      
      const response = await loginUser(loginCredentials);
      
      const loginEndTime = performance.now();
      const loginDuration = loginEndTime - loginStartTime;

      logger.info('STEP 2 SUCCESS: Login request completed', {
        duration: `${loginDuration.toFixed(2)}ms`,
        tokenReceived: !!response.access_token,
        tokenLength: response.access_token?.length || 0,
        tokenType: response.token_type
      });

      // Store the token
      logger.info('STEP 3: Storing authentication token');
      setAuthToken(response.access_token);
      logger.info('STEP 3 SUCCESS: Token stored in localStorage');
      
      // Step 4: Determine user role and navigate accordingly
      logger.info('STEP 4: Starting user role determination');
      logger.debug('Raw email value:', { email });
      logger.debug('Email after processing:', { 
        original: email,
        lowercased: email.toLowerCase(), 
        trimmed: email.trim(),
        finalProcessed: email.toLowerCase().trim() 
      });
      
      const isAdmin = email.toLowerCase().trim() === 'admin@kaaratech.com';
      
      logger.info('STEP 4: Admin check completed', {
        email: email,
        emailProcessed: email.toLowerCase().trim(),
        adminEmail: 'admin@kaaratech.com',
        isAdmin: isAdmin,
        userRole: isAdmin ? 'admin' : 'student',
        comparison: `"${email.toLowerCase().trim()}" === "admin@kaaratech.com"`,
        stringMatch: email.toLowerCase().trim() === 'admin@kaaratech.com'
      });
      
      if (isAdmin) {
        logger.info('STEP 5: Admin user detected - navigating to dashboard');
        logger.info('ADMIN NAVIGATION: Routing to /admin');
        navigate('/admin');
      } else {
        logger.info('STEP 5: Regular user detected - navigating to assessment');
        logger.info('STUDENT NAVIGATION: Routing to /assessment');
    navigate('/assessment');
      }
      
      const totalDuration = performance.now() - loginStartTime;
      logger.info('LOGIN FLOW COMPLETED SUCCESSFULLY', {
        totalDuration: `${totalDuration.toFixed(2)}ms`,
        timestamp: new Date().toISOString()
      });
      logger.info('='.repeat(50));
      
    } catch (error: any) {
      const errorTimestamp = new Date().toISOString();
      logger.error('LOGIN FAILED', {
        timestamp: errorTimestamp,
        error: error.message,
        errorType: error.constructor.name
      });

      // Log detailed error information
      if (error.response) {
        logger.error('HTTP Response Error Details', {
          status: error.response.status,
          statusText: error.response.statusText,
          data: error.response.data,
          headers: error.response.headers
        });
      } else if (error.request) {
        logger.error('Network Request Error', {
          request: error.request,
          message: 'No response received from server'
        });
      } else {
        logger.error('General Error', {
          message: error.message,
          stack: error.stack
        });
      }

      // Set user-friendly error messages
      if (error.response?.status === 401) {
        const errorMsg = 'Invalid email or password. Please try again.';
        setLoginError(errorMsg);
        logger.warn('Authentication failed - Invalid credentials');
      } else if (error.response?.status === 400) {
        const errorMsg = 'You cannot start the quiz at this time.';
        setLoginError(errorMsg);
        logger.warn('Bad request - Quiz cannot be started');
      } else if (error.response?.status >= 500) {
        const errorMsg = 'Server error. Please try again later.';
        setLoginError(errorMsg);
        logger.error('Server error encountered');
      } else if (error.code === 'NETWORK_ERROR' || !error.response) {
        const errorMsg = 'Network error. Please check your connection and try again.';
        setLoginError(errorMsg);
        logger.error('Network connectivity issue');
      } else {
        const errorMsg = 'Login failed. Please check your connection and try again.';
        setLoginError(errorMsg);
        logger.error('Unknown error during login');
      }
      
      logger.info('='.repeat(50));
    } finally {
      setIsLoading(false);
      logger.debug('Login attempt finished, loading state reset');
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Left Side - Dark Testimonial Section */}
      <div className="w-full lg:w-1/2 bg-gradient-to-br from-black via-gray-900 to-red-900 relative overflow-hidden flex min-h-[300px] lg:min-h-screen">
        {/* Geometric Pattern Background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-1/3 left-1/3 w-16 lg:w-32 h-16 lg:h-32 border-2 border-white transform rotate-45"></div>
          <div className="absolute top-1/4 left-1/4 w-8 lg:w-16 h-8 lg:h-16 border border-white transform rotate-45"></div>
          <div className="absolute bottom-1/3 right-1/4 w-12 lg:w-24 h-12 lg:h-24 border border-white transform rotate-45"></div>
          <div className="absolute top-2/3 left-1/2 w-4 lg:w-8 h-4 lg:h-8 border border-white transform rotate-45"></div>
        </div>
        
        <div className="flex flex-col justify-center px-6 lg:px-12 z-10">
       
          
         
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 bg-gray-50 flex flex-col flex-1">
        {/* Header */}
        <div className="flex justify-between items-center p-4 lg:p-6">
          <div className="flex items-center space-x-2">
            <img src={kaaraLogo} alt="Kaara" className="h-5 lg:h-6" />
          </div>
          
          
        </div>

        {/* Main Content */}
        <div className="flex-1 flex items-center justify-center px-4 lg:px-6 py-6 lg:py-0">
          <div className="w-full max-w-md">
            <div className="text-center mb-6 lg:mb-8">
              <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-2 flex items-center justify-center">
                Welcome 
                <span className="ml-2 text-2xl lg:text-3xl">👋</span>
              </h1>
              <p className="text-sm lg:text-base text-gray-600">Sign in to take the MCQ Quiz</p>
            </div>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-4 lg:space-y-6">
              {/* Email Field */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={handleEmailChange}
                  className={`w-full px-3 lg:px-4 py-2 lg:py-3 border rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors text-sm lg:text-base ${
                    emailError ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter your email address"
                  required
                />
                {emailError && (
                  <p className="text-red-500 text-xs lg:text-sm mt-1">{emailError}</p>
                )}
              </div>

              {/* Password Field */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 lg:px-4 py-2 lg:py-3 pr-10 lg:pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors text-sm lg:text-base"
                    placeholder="Enter your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2 lg:right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4 lg:w-5 lg:h-5" /> : <Eye className="w-4 h-4 lg:w-5 lg:h-5" />}
                  </button>
                </div>
              </div>

              {/* Sign In Button */}
              <button 
                type="submit"
                className="w-full text-white py-2 lg:py-3 rounded-lg font-semibold transition-colors shadow-sm text-sm lg:text-base flex items-center justify-center"
                style={{ backgroundColor: '#671C1F' }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#5a1719'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#671C1F'}
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isLoading ? 'Signing In...' : 'Sign In'}
              </button>
              {loginError && (
                <p className="text-red-500 text-xs lg:text-sm mt-2 text-center">{loginError}</p>
              )}
            </form>

           
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen; 