import requests
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

def get_reply_suggestion(user_input, tone="default"):
    if not user_input.strip():
        return "[无输入内容]"

    prompt = f"你是Bob，对方说：“{user_input}”，请用自然、简洁的语气回复一句。"
    if tone == "humorous":
        prompt += " 回复应带有幽默感。"
    elif tone == "formal":
        prompt += " 回复应正式而礼貌。"

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=20
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
        else:
            return f"[本地模型错误]: {response.status_code} - {response.text}"
    except Exception as e:
        return f"[请求失败]: {e}"
