"""AI agent that manages tasks in the database via Claude tool use.

The agent runs a manual agentic loop: Claude decides which tools to call
(create/list/update/delete tasks), we execute them against the database,
feed the results back, and repeat until Claude produces a final answer.
"""

import json
import os

import anthropic
from sqlalchemy.orm import Session

from . import crud, schemas

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")
MAX_AGENT_TURNS = 10

SYSTEM_PROMPT = """\
أنت مساعد ذكي لإدارة المهام في تطبيق "مهامي".
تستطيع إنشاء المهام وعرضها وتعديلها وإكمالها وحذفها باستخدام الأدوات المتاحة.
- رد دائماً بنفس لغة المستخدم (العربية غالباً).
- عند إنشاء مهمة، استنتج الأولوية (low/normal/high) من سياق كلام المستخدم.
- كن مختصراً وودوداً، ولخّص ما فعلته بعد استخدام الأدوات.
"""

TOOLS = [
    {
        "name": "create_task",
        "description": "إنشاء مهمة جديدة في قاعدة البيانات. استخدمها عندما يطلب المستخدم إضافة مهمة أو تذكير.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "عنوان المهمة"},
                "description": {"type": "string", "description": "وصف تفصيلي اختياري"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "description": "أولوية المهمة",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_tasks",
        "description": "عرض المهام من قاعدة البيانات. استخدمها عندما يسأل المستخدم عن مهامه أو قبل تعديل/حذف مهمة لمعرفة رقمها.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "done"],
                    "description": "تصفية حسب الحالة (اتركه فارغاً لعرض الكل)",
                },
            },
        },
    },
    {
        "name": "update_task",
        "description": "تعديل مهمة موجودة: تغيير العنوان أو الوصف أو الأولوية أو تعليمها كمكتملة (status=done).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "رقم المهمة"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "done"]},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "delete_task",
        "description": "حذف مهمة نهائياً من قاعدة البيانات.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "رقم المهمة المراد حذفها"},
            },
            "required": ["task_id"],
        },
    },
]

# Conversation history per browser session (in-memory; tasks live in the DB).
_sessions: dict[str, list[dict]] = {}


def _task_to_dict(task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
    }


def _execute_tool(db: Session, name: str, tool_input: dict) -> tuple[str, bool]:
    """Run a tool against the database. Returns (result_json, is_error)."""
    try:
        if name == "create_task":
            task = crud.create_task(db, schemas.TaskCreate(**tool_input))
            return json.dumps({"created": _task_to_dict(task)}, ensure_ascii=False), False

        if name == "list_tasks":
            tasks = crud.list_tasks(db, status=tool_input.get("status"))
            return json.dumps({"tasks": [_task_to_dict(t) for t in tasks]}, ensure_ascii=False), False

        if name == "update_task":
            task = crud.get_task(db, tool_input["task_id"])
            if task is None:
                return f"لا توجد مهمة برقم {tool_input['task_id']}", True
            fields = {k: v for k, v in tool_input.items() if k != "task_id"}
            task = crud.update_task(db, task, schemas.TaskUpdate(**fields))
            return json.dumps({"updated": _task_to_dict(task)}, ensure_ascii=False), False

        if name == "delete_task":
            task = crud.get_task(db, tool_input["task_id"])
            if task is None:
                return f"لا توجد مهمة برقم {tool_input['task_id']}", True
            crud.delete_task(db, task)
            return json.dumps({"deleted": tool_input["task_id"]}), False

        return f"أداة غير معروفة: {name}", True
    except Exception as exc:  # surface tool failures to the model so it can adapt
        return f"خطأ أثناء تنفيذ الأداة: {exc}", True


def chat(db: Session, session_id: str, user_message: str) -> tuple[str, list[str]]:
    """Send a user message to the agent and return (reply, tools_used)."""
    client = anthropic.Anthropic()

    history = _sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_message})

    tools_used: list[str] = []

    for _ in range(MAX_AGENT_TURNS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=history,
        )

        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tools_used.append(block.name)
                result, is_error = _execute_tool(db, block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                        "is_error": is_error,
                    }
                )
        history.append({"role": "user", "content": tool_results})

    reply = next(
        (b.text for b in response.content if b.type == "text"),
        "تم تنفيذ الطلب.",
    )
    return reply, tools_used


def reset_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
