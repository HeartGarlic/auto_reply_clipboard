from clipboard_listener import watch_clipboard
from ui_window import ReplyWindow
import threading

if __name__ == "__main__":
    ui = ReplyWindow()
    threading.Thread(target=watch_clipboard, args=(ui.update_input,), daemon=True).start()
    ui.run()
