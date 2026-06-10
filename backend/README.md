# Women Health Expert Backend - Quick Start Guide

## Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

## 2 Steps to Run Locally (No Docker)

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python main.py
```

**That's it!** Your API will be running at:
- **http://localhost:8000/docs** - API Documentation
- **http://localhost:8000/** - API Root

---

## Configuration

The `env` file in the `backend` folder contains all API keys and configuration. Make sure it has:

```
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=your_index_name
PINECONE_ENVIRONMENT=your_environment
```

---

## Troubleshooting

### Python version error?
Make sure you have Python 3.11+:
```bash
python --version
```

### Module not found error?
Install dependencies again:
```bash
pip install -r requirements.txt
```

### Port 8000 already in use?
Change the port in `main.py` (line 15) from `8000` to another port like `8080`.

---

## API Endpoints

- **POST** `/api/v1/chat` - Chat with the AI
- **GET** `/api/v1/health` - Health check
- **GET** `/docs` - Interactive API documentation
