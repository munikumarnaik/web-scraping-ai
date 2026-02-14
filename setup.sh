#!/bin/bash

# Setup script for Domain Intelligence Platform

echo "🚀 Setting up Domain Intelligence Platform..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.9"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Python 3.9 or higher is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p media
mkdir -p staticfiles
mkdir -p logs

# Database setup
echo "🗄️  Setting up database..."
read -p "Do you want to run migrations? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py makemigrations
    python manage.py migrate
    echo "✅ Database migrations completed"
fi

# Create superuser
read -p "Do you want to create a superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your configuration (AWS, LLM keys, etc.)"
echo "2. Make sure Redis is running (required for Celery)"
echo "3. Start Celery worker: celery -A config worker -l info"
echo "4. Start development server: python manage.py runserver"
echo ""
echo "🌐 API will be available at: http://localhost:8000/api/"
echo "🔧 Admin panel: http://localhost:8000/admin/"
echo ""
