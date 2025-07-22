# Startup script for Flask application

# Check for Python version (3.9+ required)
PYTHON_VERSION=$(python -V 2>&1 | grep -Po '(?<=Python )(.+)')

# Set up virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the PDF translator module to the current directory
cp ../pdf_translator.py .

# Create necessary directories
mkdir -p uploads downloads

# Run Flask development server
flask run --host=0.0.0.0 --port=5000
