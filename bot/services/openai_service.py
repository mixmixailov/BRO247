import logging
from typing import List, Dict, Any
import asyncio
from openai import OpenAI

# 1. System prompt builder
def build_prompt(user: dict) -> str:
    style = user.get("style", "street")
    lang = user.get("language", "RU")
    gender = user.get("gender", "")
    persona = user.get("persona", {})
    name = user.get("name", "пользователь" if lang == "RU" else "user")

    if lang == "RU":
        gender_line = "женщина" if gender == "female" else "мужчина" if gender == "male" else "человек"
    else:
        gender_line = "female" if gender == "female" else "male" if gender == "male" else "person"

    traits = [f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in persona.items()]
    traits.append(f"Имя: {name}" if lang == "RU" else f"Name: {name}")
    traits.append(f"Пол: {gender_line}" if lang == "RU" else f"Gender: {gender_line}")

    extra = ". ".join(traits)

    style_prompt_ru = {
        "street": "Ты уличный бот-бро. Говори просто, с юмором, можешь вставлять лёгкий сленг, немного неформальности. Главное — поддержка и уверенность.",
        "coach": "Ты коуч и наставник. Говоришь уверенно, мотивируешь, даёшь советы чётко и по делу.",
        "psych": "Ты психолог. Говоришь мягко, внимательно, с эмпатией. Помогаешь разобраться в чувствах, задаёшь наводящие вопросы."
    }
    style_prompt_en = {
        "street": "You're a street-style AI bro. Speak casually, with slang and humor. Be confident and supportive.",
        "coach": "You're a motivational coach. Speak clearly, confidently, and give concrete, action-oriented advice.",
        "psych": "You're an empathetic psychologist. Speak gently and attentively, help the user understand their emotions and thoughts."
    }

    style_prompt = style_prompt_ru if lang == "RU" else style_prompt_en
    return style_prompt.get(style, "") + " " + extra

# 2. Format chat history for OpenAI API
def format_chat_history(history: List[Dict[str, str]], prompt: str) -> List[Dict[str, str]]:
    """
    Формирует массив сообщений для OpenAI API:
    - prompt (system)
    - history[-12:]
    """
    chat = [{"role": "system", "content": prompt}]
    chat.extend(history[-12:])  # Берём только последние 12
    return chat

# 3. Общение с OpenAI
async def ask_openai(
    user_id: int,
    message: str,
    user_ctx: Dict[int, List[Dict[str, str]]],
    user_data: Dict[str, dict],
    client: OpenAI,
    model: str = "gpt-3.5-turbo"
) -> str:
    """
    Получить ответ от OpenAI. Обновляет историю сообщений user_ctx для user_id.
    """
    # Готовим user info и prompt
    user = user_data.get(str(user_id), {})
    prompt = build_prompt(user)
    chat_history = user_ctx.setdefault(user_id, [])
    chat_history.append({"role": "user", "content": message})
    # Готовим messages для OpenAI
    messages = format_chat_history(chat_history, prompt)

    try:
        # Новый OpenAI API (>=1.14.3)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=messages,
        )
        reply = response.choices[0].message.content.strip()
        logging.info(f"OpenAI reply for user {user_id}: {reply[:60]}...")
    except Exception as e:
        logging.error(f"OpenAI Error for user {user_id}: {e}")
        reply = "Ошибка. Попробуй ещё или /start."
    # Добавляем ответ ассистента в историю
    chat_history.append({"role": "assistant", "content": reply})
    user_ctx[user_id] = chat_history[-12:]
    return reply
