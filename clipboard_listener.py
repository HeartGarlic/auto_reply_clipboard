import pyperclip
import time

def watch_clipboard(on_new_text):
    last_text = ""
    while True:
        try:
            text = pyperclip.paste()
            if text != last_text and isinstance(text, str) and len(text.strip()) > 0:
                last_text = text
                on_new_text(text)
        except Exception as e:
            print(f"[剪贴板错误]: {e}")
        time.sleep(1)
