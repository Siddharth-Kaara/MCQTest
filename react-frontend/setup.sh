#!/bin/bash

echo "🚀 Setting up MCQ Test React Frontend for Azure App Service..."

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    echo "VITE_API_URL=https://kaara-mcq-test.azurewebsites.net" > .env
    echo "✅ Created .env file with Azure App Service URL"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Your backend is already deployed at: https://kaara-mcq-test.azurewebsites.net"
echo "2. Start the development server: npm run dev"
echo "3. Open http://localhost:5173 in your browser"
echo ""
echo "🔐 Test credentials:"
echo "Email: siddharth.g@kaaratech.com"
echo "Password: password"
echo ""
echo "🎯 Features:"
echo "- Connected to your live Azure backend"
echo "- Real 25 questions from PostgreSQL database"
echo "- Question 6 supports multiple answers (A, C) = 0.5 points each"
echo "- 20-minute timer with auto-submission"
echo "- JWT authentication with session management"
echo "- Responsive design with Tailwind CSS"
echo ""
echo "🚀 Production Deployment:"
echo "To deploy this React frontend, build with: npm run build"
echo "Then deploy the dist/ folder to your preferred hosting service" 