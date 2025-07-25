# MCQ Test React Frontend

This is the React frontend for the Kaara MCQ Test Platform, integrated with your **Azure App Service** FastAPI backend.

## Features

- **JWT Authentication** with login/logout functionality
- **Real-time Questions** fetched from Azure-hosted backend
- **Multiple Answer Support** for Question 6 (0.5 points each)
- **20-minute Timer** with automatic submission
- **Progress Tracking** with question overview
- **Responsive Design** with Tailwind CSS
- **TypeScript** for type safety

## Quick Setup

### Windows
```bash
# Run the setup script
setup.bat
```

### Linux/Mac
```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh
```

### Manual Setup

```bash
# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=https://kaara-mcq-test.azurewebsites.net" > .env

# Start development server
npm run dev
```

## Azure Integration

### Backend Configuration
- **Live Backend**: `https://kaara-mcq-test.azurewebsites.net`
- **Database**: PostgreSQL on Azure
- **Authentication**: JWT with session management
- **CORS**: Already configured for React frontend

### Test Credentials
```
Email: siddharth.g@kaaratech.com
Password: password
```

## Question 6 Special Handling

Question 6 is automatically detected as having multiple correct answers:
- **Question Text**: "Which signals would most strongly indicate a good outbound target? (Select two)"
- **Correct Answers**: A (Increased hiring for analytics roles) + C (Recent funding or expansion news)  
- **Scoring**: 0.5 points for each correct selection (total 1.0 if both selected)
- **UI**: Shows checkboxes instead of radio buttons
- **Submission**: Sends separate API calls for each selected answer
- **Database**: Score stored as FLOAT to support decimal values

## Production Deployment

### Option 1: Azure Static Web Apps
```bash
# Build the project
npm run build

# Deploy to Azure Static Web Apps
# (Connect your GitHub repo in Azure portal)
```

### Option 2: Netlify
```bash
# Build the project
npm run build

# Deploy dist/ folder to Netlify
```

### Option 3: Vercel
```bash
# Build the project
npm run build

# Deploy using Vercel CLI
npx vercel --prod
```

### Option 4: Azure Blob Storage + CDN
```bash
# Build the project
npm run build

# Upload dist/ contents to Azure Blob Storage
# Configure as static website
# Add Azure CDN for performance
```

## Environment Variables

### Development (.env)
```bash
VITE_API_URL=https://kaara-mcq-test.azurewebsites.net
```

### Production
Set the environment variable in your hosting platform:
- **Netlify**: Site Settings → Environment Variables
- **Vercel**: Project Settings → Environment Variables  
- **Azure Static Web Apps**: Configuration → Application Settings

## API Endpoints Used

The frontend integrates with these backend endpoints:

- `POST /token` - User authentication
- `POST /start` - Start quiz session
- `GET /questions/` - Fetch 25 questions with answers
- `POST /submit` - Submit quiz answers

## File Structure

```
react-frontend/
├── src/
│   ├── api/
│   │   └── mcqAPI.ts          # Azure backend integration
│   ├── components/
│   │   ├── LoginScreen.tsx    # Authentication UI
│   │   └── MCQScreen.tsx      # Quiz interface
│   ├── App.tsx                # Router with route protection
│   └── main.tsx              # Entry point
├── setup.bat                  # Windows setup script
├── setup.sh                   # Linux/Mac setup script
└── README.md                  # This file
```

## Development Workflow

1. **Backend**: Already deployed at Azure App Service
2. **Database**: PostgreSQL with 25 real questions populated
3. **Frontend**: Run locally with `npm run dev`
4. **Testing**: Use test credentials to verify full flow
5. **Deploy**: Build and deploy to your preferred hosting

## Scoring Logic

Your backend handles scoring automatically:

```typescript
// Questions 1-5, 7-25 (single answer): 1 point each
{ question_id: 1, selected_answer: "C" } // = 1 point

// Question 6 (multiple answers): 0.5 points each
{ question_id: 6, selected_answer: "A" } // = 0.5 points  
{ question_id: 6, selected_answer: "C" } // = 0.5 points
// Total for Q6 if both correct: 1 point
```

## CORS Configuration

Your backend is already configured with CORS for React development:

```python
allow_origins=["https://kaara-mcq-test.azurewebsites.net"]
```

For production deployment, you may need to add your production domain to the CORS origins in `backend/main.py`.

## Support

The React frontend is fully integrated with your existing Azure infrastructure:
- ✅ PostgreSQL database with real questions
- ✅ JWT authentication system  
- ✅ Question 6 multi-answer scoring
- ✅ 20-minute timer enforcement
- ✅ Session management
- ✅ Admin dashboard (accessible via backend)

Ready to use immediately! 