# 📋 مهامي — Task Manager with AI Agent

تطبيق ويب كامل لإدارة المهام، مبني بالكامل بـ **Python**:

| المكوّن | التقنية |
|---|---|
| الباكند | FastAPI |
| الفرونت اند | Jinja2 templates + CSS/JS (يُقدَّم من FastAPI) |
| قاعدة البيانات | PostgreSQL (عبر SQLAlchemy) — أو SQLite للتشغيل المحلي |
| الإيجنت الذكي | Google Gemini (مجاني) مع Function Calling — يقرأ ويكتب في قاعدة البيانات |
| التشغيل | Docker + Docker Compose |

## ✨ الميزات

- إضافة / تعديل / إكمال / حذف المهام مع أولويات (منخفضة / عادية / عالية)
- مساعد ذكاء اصطناعي يفهم العربية ويدير مهامك بالكلام الطبيعي:
  - «أضف مهمة شراء الحليب بكرة» → ينشئ مهمة في قاعدة البيانات
  - «شو مهامي المعلّقة؟» → يستعلم من قاعدة البيانات
  - «خلّص مهمة رقم 3» → يحدّث حالتها إلى مكتملة
- REST API موثّق تلقائياً على `/docs`

## 🚀 التشغيل بـ Docker (الطريقة الموصى بها)

```bash
cd webapp
cp .env.example .env       # ثم ضع مفتاح GEMINI_API_KEY داخل .env (مجاني من aistudio.google.com)
docker compose up --build
```

افتح المتصفح على: **http://localhost:8000**

- توثيق الـ API: http://localhost:8000/docs
- فحص الصحة: http://localhost:8000/health

## 🖥️ التشغيل المحلي بدون Docker

```bash
cd webapp
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # ضع مفتاحك في .env
uvicorn app.main:app --reload
```

بدون `DATABASE_URL` سيستخدم التطبيق SQLite تلقائياً (`tasks.db`).

## 🏗️ البنية

```
webapp/
├── app/
│   ├── main.py          # نقطة الدخول — FastAPI + القوالب
│   ├── database.py      # اتصال SQLAlchemy
│   ├── models.py        # جدول المهام
│   ├── schemas.py       # نماذج Pydantic
│   ├── crud.py          # عمليات قاعدة البيانات
│   ├── agent.py         # الإيجنت الذكي (Gemini + Function Calling)
│   ├── routers/
│   │   ├── tasks.py     # REST API للمهام
│   │   └── chat.py      # API المحادثة مع الإيجنت
│   ├── templates/       # الفرونت اند (HTML)
│   └── static/          # CSS + JS
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🤖 كيف يعمل الإيجنت؟

الإيجنت يستخدم **Function Calling** مع نموذج Gemini:

1. المستخدم يرسل رسالة (مثلاً «أضف مهمة مذاكرة الرياضيات»)
2. Gemini يقرر استدعاء الأداة المناسبة (`create_task`)
3. الخادم ينفّذ الأداة على قاعدة البيانات ويرجع النتيجة لـ Gemini
4. تتكرر الحلقة حتى ينتهي النموذج ويرد على المستخدم

الأدوات المتاحة للإيجنت: `create_task` · `list_tasks` · `update_task` · `delete_task`
