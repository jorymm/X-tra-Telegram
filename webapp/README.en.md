# 📋 Muhammiy — AI-Powered Task Management Application

A full-stack web application for intelligent task management, entirely built with **Python**. Combines modern technologies with natural language processing to provide an intuitive task management experience.

## 🎯 Overview

Muhammiy is a task management system that leverages artificial intelligence to help users organize their daily tasks. Users can interact with the application both through a traditional UI and through a natural language interface powered by Google's Gemini AI.

| Component | Technology |
|---|---|
| Backend | FastAPI |
| Frontend | Jinja2 Templates + CSS/JavaScript (served by FastAPI) |
| Database | PostgreSQL (via SQLAlchemy) — or SQLite for local development |
| AI Agent | Google Gemini (Free Tier) with Function Calling — reads and writes to database |
| Deployment | Docker + Docker Compose |

## ✨ Key Features

### Task Management
- ✅ Create, read, update, and delete tasks
- ✅ Set task priorities: Low, Normal, High
- ✅ Track task status: Pending or Completed
- ✅ Organize tasks with titles, descriptions, and timestamps
- ✅ Filter tasks by status
- ✅ RESTful API with automatic documentation at `/docs`

### AI Assistant
- 🤖 **Natural Language Processing:** Understands Arabic and English
- 🤖 **Intelligent Task Management:** Create, modify, and complete tasks through conversation
- 🤖 **Function Calling:** The AI agent automatically selects and executes appropriate tools
- 🤖 **Free & Fast:** Uses Google Gemini's free tier (no credit card required)
- 🤖 **Contextual Understanding:** Infers task priorities and manages tasks intelligently

### Example AI Interactions
```
User: "Add a task to buy milk tomorrow with high priority"
AI: ✅ Created task "buy milk" with high priority

User: "What are my pending tasks?"
AI: 📋 Shows all pending tasks with details

User: "Mark task #3 as complete"
AI: ✅ Updated task #3 status to completed

User: "Delete the shopping task"
AI: ✅ Removed the shopping task from database
```

## 🚀 Quick Start with Docker (Recommended)

### Prerequisites
- Docker & Docker Compose installed
- Free Gemini API key from [aistudio.google.com](https://aistudio.google.com/apikey)

### Setup & Run
```bash
cd webapp

# Copy environment template
cp .env.example .env

# Add your Gemini API key to .env
# GEMINI_API_KEY=AIza...

# Start the application
docker compose up --build
```

### Access the Application
- **Web UI:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 🖥️ Local Development (Without Docker)

### Prerequisites
- Python 3.10+
- pip or poetry
- SQLite (included with Python)

### Setup
```bash
cd webapp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your Gemini API key

# Run application
uvicorn app.main:app --reload
```

**Note:** Without `DATABASE_URL` environment variable, the app will automatically use SQLite (`tasks.db`) for local data storage.

## 🏗️ Project Structure

```
webapp/
├── app/
│   ├── main.py              # Application entry point — FastAPI setup & routing
│   ├── database.py          # SQLAlchemy database configuration
│   ├── models.py            # Task database model (ORM)
│   ├── schemas.py           # Pydantic validation schemas for API
│   ├── crud.py              # Database operations (Create, Read, Update, Delete)
│   ├── agent.py             # AI Agent logic (Gemini + Function Calling)
│   ├── routers/
│   │   ├── tasks.py         # REST API endpoints for task management
│   │   └── chat.py          # WebSocket & REST endpoints for AI chat
│   ├── templates/
│   │   └── index.html       # Main frontend page
│   └── static/
│       ├── app.js           # Frontend JavaScript (event handling, API calls)
│       └── style.css        # Styling (dark theme, responsive design)
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Multi-container orchestration (web + PostgreSQL)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # Documentation (Arabic)
```

## 🤖 How the AI Agent Works

The AI agent uses **Function Calling** with Google's Gemini model:

### Agent Loop
1. **User Message:** User sends a natural language request
2. **Model Decision:** Gemini analyzes the request and decides which tool to use
3. **Tool Execution:** The backend executes the appropriate database operation
4. **Result Feedback:** Database results are returned to Gemini
5. **Response:** Model generates a natural language response to the user
6. **Iteration:** Repeat steps 2-5 until the model completes the task

### Available Tools
- `create_task(title, description, priority)` — Create a new task
- `list_tasks(status)` — Retrieve tasks (optionally filtered by status)
- `update_task(task_id, title, description, status, priority)` — Modify existing task
- `delete_task(task_id)` — Remove a task from database

### System Prompt
The AI operates under a system prompt that ensures:
- Responses match the user's language (Arabic primarily)
- Task priorities are inferred from context
- Task IDs are looked up when needed
- Responses are concise and user-friendly

## 📡 API Endpoints

### Task Management
```
GET    /api/tasks                    → List all tasks (optional: ?status=pending)
POST   /api/tasks                    → Create new task
PATCH  /api/tasks/{task_id}          → Update task details
DELETE /api/tasks/{task_id}          → Remove task
```

### AI Chat
```
POST   /api/chat                     → Send message to AI agent
DELETE /api/chat/{session_id}        → Reset conversation history
```

### Application
```
GET    /                             → Main web interface
GET    /health                       → Health check endpoint
GET    /docs                         → Interactive API documentation (Swagger UI)
```

## 🗄️ Database Schema

### Tasks Table
```sql
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    status      VARCHAR(20) DEFAULT 'pending',  -- 'pending' or 'done'
    priority    VARCHAR(20) DEFAULT 'normal',   -- 'low', 'normal', or 'high'
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuration

### Environment Variables
```bash
# Google Gemini API Key (required)
GEMINI_API_KEY=AIza...

# AI Model selection (optional, defaults to gemini-2.5-flash)
GEMINI_MODEL=gemini-2.5-flash

# Database URL (optional, defaults to SQLite for local dev)
DATABASE_URL=postgresql+psycopg2://tasks:tasks@db:5432/tasksdb
```

### Docker Compose Services
- **web:** FastAPI application container
- **db:** PostgreSQL database (optional, only with Docker)

## 🚢 Deployment Considerations

### Production Deployment
- Use PostgreSQL instead of SQLite for concurrency and reliability
- Enable CORS if hosting frontend separately
- Use environment variables for sensitive data
- Consider implementing API authentication
- Monitor Gemini API usage and rate limits

### Jetson AGX Orin Support
The application is compatible with ARM64 architecture (Jetson AGX Orin):
- Uses compatible Python packages
- Docker images support multi-platform builds
- No architecture-specific code dependencies

### Local Network Access
Run the application to be accessible from other devices:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Then access from other devices: `http://<your-ip>:8000`

## 📋 Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Language** | Python 3.12+ | Modern, readable, widely supported |
| **Web Framework** | FastAPI | Async-first, automatic API docs, validation |
| **ORM** | SQLAlchemy 2.0+ | Database abstraction, type-safe queries |
| **Validation** | Pydantic | Type hints, automatic validation |
| **Template Engine** | Jinja2 | Server-side rendering, flexible |
| **AI/ML** | Google Gemini | Free tier, multimodal, function calling |
| **Database** | SQLite/PostgreSQL | Lightweight/Enterprise-grade options |
| **Containerization** | Docker | Isolated, reproducible environments |
| **Database Driver** | psycopg2 | Fast, reliable PostgreSQL driver |

## 🎨 User Interface Features

- **Dark Theme:** Easy on the eyes for extended use
- **Responsive Design:** Works on desktop, tablet, and mobile
- **Right-to-Left (RTL):** Full Arabic language support
- **Real-time Updates:** Dynamic task list without page refresh
- **Dual Interface:** Both traditional UI and natural language chat
- **Status Indicators:** Visual priority and status badges

## 🔐 Security Features

- **Input Validation:** Pydantic schemas validate all inputs
- **SQL Injection Prevention:** SQLAlchemy parameterized queries
- **XSS Protection:** Jinja2 template escaping
- **CORS Ready:** Configure for multi-origin access
- **Environment-based Config:** No hardcoded secrets

## 📈 Scalability

### Vertical Scaling
- Increase container resources (CPU, memory)
- Upgrade database server

### Horizontal Scaling
- Multiple FastAPI instances behind load balancer
- Shared PostgreSQL database
- Session state management (currently in-memory, could migrate to Redis)

## 🐛 Error Handling

### AI Agent Errors
- **API Key Missing:** Clear error message guiding user to get API key
- **Rate Limited (429):** User-friendly message to wait and retry
- **Invalid Key (401/403):** Guidance to check configuration
- **API Errors (5xx):** Safe error messages without exposing internals

### Database Errors
- **Task Not Found:** Returns 404 with descriptive message
- **Validation Error:** Returns 400 with field-specific errors

## 🚀 Performance Optimization

- **Async Database:** FastAPI async support for I/O-bound operations
- **Function Calling:** Efficient AI loop reducing API calls
- **Static File Caching:** Browser caching for CSS/JS
- **Connection Pooling:** SQLAlchemy connection pool management

## 📝 API Response Examples

### Create Task (POST /api/tasks)
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "pending",
  "priority": "high",
  "created_at": "2024-01-15T10:30:00+00:00"
}
```

### Chat Response (POST /api/chat)
```json
{
  "reply": "تم إضافة مهمة شراء الحليب بأولوية عالية ✅",
  "tools_used": ["create_task"]
}
```

## 🤝 Contributing

Feel free to fork, modify, and extend this project. It's designed to be maintainable and understandable for developers of all levels.

## 📄 License

Check the project's LICENSE file for details.

## 🙋 Support

For issues, questions, or feature requests:
1. Check the API documentation at `/docs`
2. Review error messages carefully
3. Ensure Gemini API key is valid
4. Check database connectivity

## 🌟 Highlights

✨ **100% Python Stack:** Consistent language across frontend logic and backend  
✨ **Completely Free:** Gemini API free tier, no credit card required  
✨ **Production Ready:** Docker, PostgreSQL, error handling all configured  
✨ **Natural Language:** Converse with your task manager in Arabic or English  
✨ **Open Source:** Easily modifiable for custom workflows  
✨ **Educational:** Great example of modern web development with AI integration  

---

**Last Updated:** 2026  
**Status:** Fully Functional  
**Deployment Ready:** ✅
