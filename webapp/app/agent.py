"""AI agent that manages tasks in the database via Google Gemini function calling.

The Gemini SDK runs the agentic loop automatically: the model decides which
Python tool functions to call (create/list/update/delete tasks), the SDK
executes them against the database and feeds results back until the model
produces a final answer.
"""

import os

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from . import crud, schemas

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = """\
أنت مساعد ذكي لإدارة المهام في تطبيق "مهامي".
تستطيع إنشاء المهام وعرضها وتعديلها وإكمالها وحذفها باستخدام الأدوات المتاحة.
- رد دائماً بنفس لغة المستخدم (العربية غالباً).
- عند إنشاء مهمة، استنتج الأولوية (low/normal/high) من سياق كلام المستخدم.
- قبل تعديل أو حذف مهمة، استخدم list_tasks لمعرفة رقمها إذا لم يذكره المستخدم.
- كن مختصراً وودوداً، ولخّص ما فعلته بعد استخدام الأدوات.
"""

# Conversation history per browser session (in-memory; tasks live in the DB).
_histories: dict[str, list] = {}


def _task_to_dict(task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
    }


def chat(db: Session, session_id: str, user_message: str) -> tuple[str, list[str]]:
    """Send a user message to the agent and return (reply, tools_used)."""
    client = genai.Client()  # reads GEMINI_API_KEY from the environment
    tools_used: list[str] = []

    # Tools are defined as closures so each request uses its own DB session.
    def create_task(title: str, description: str = "", priority: str = "normal") -> dict:
        """إنشاء مهمة جديدة في قاعدة البيانات.

        Args:
            title: عنوان المهمة.
            description: وصف تفصيلي اختياري.
            priority: أولوية المهمة: low أو normal أو high.
        """
        tools_used.append("create_task")
        if priority not in ("low", "normal", "high"):
            priority = "normal"
        task = crud.create_task(
            db, schemas.TaskCreate(title=title, description=description, priority=priority)
        )
        return {"created": _task_to_dict(task)}

    def list_tasks(status: str = "") -> dict:
        """عرض المهام من قاعدة البيانات.

        Args:
            status: تصفية حسب الحالة: pending أو done، أو نص فارغ لعرض الكل.
        """
        tools_used.append("list_tasks")
        tasks = crud.list_tasks(db, status=status or None)
        return {"tasks": [_task_to_dict(t) for t in tasks]}

    def update_task(
        task_id: int,
        title: str = "",
        description: str = "",
        status: str = "",
        priority: str = "",
    ) -> dict:
        """تعديل مهمة موجودة: تغيير العنوان أو الوصف أو الأولوية أو تعليمها كمكتملة.

        Args:
            task_id: رقم المهمة.
            title: العنوان الجديد (اتركه فارغاً لعدم التغيير).
            description: الوصف الجديد (اتركه فارغاً لعدم التغيير).
            status: الحالة الجديدة: pending أو done (اتركه فارغاً لعدم التغيير).
            priority: الأولوية الجديدة: low أو normal أو high (اتركه فارغاً لعدم التغيير).
        """
        tools_used.append("update_task")
        task = crud.get_task(db, task_id)
        if task is None:
            return {"error": f"لا توجد مهمة برقم {task_id}"}
        fields = {
            k: v
            for k, v in {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
            }.items()
            if v
        }
        task = crud.update_task(db, task, schemas.TaskUpdate(**fields))
        return {"updated": _task_to_dict(task)}

    def delete_task(task_id: int) -> dict:
        """حذف مهمة نهائياً من قاعدة البيانات.

        Args:
            task_id: رقم المهمة المراد حذفها.
        """
        tools_used.append("delete_task")
        task = crud.get_task(db, task_id)
        if task is None:
            return {"error": f"لا توجد مهمة برقم {task_id}"}
        crud.delete_task(db, task)
        return {"deleted": task_id}

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[create_task, list_tasks, update_task, delete_task],
    )

    chat_session = client.chats.create(
        model=MODEL,
        config=config,
        history=_histories.get(session_id, []),
    )
    response = chat_session.send_message(user_message)
    _histories[session_id] = chat_session.get_history()

    return response.text or "تم تنفيذ الطلب.", tools_used


def reset_session(session_id: str) -> None:
    _histories.pop(session_id, None)
