import re
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
from llm_reply_ollama import get_reply_suggestion

PROFILE_PATH = "profiles.json"
SELF_PROFILE_PATH = "self_profile.json"

class ReplyWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI 自动回复助手")
        self.root.geometry("800x640")
        self.root.configure(bg="#f4f4f4")
        
        self.auto_trigger_enabled = True
        self.profiles = self.load_profiles()
        # Ensure nested profile structure
        for k, v in self.profiles.items():
            if isinstance(v, str):
                self.profiles[k] = {"background": v, "scene": ""}
        self.self_profile = self.load_self_profile()

        self.person_var = tk.StringVar()
        self.selected_person = next(iter(self.profiles), "未指定")
        self.person_var.set(self.selected_person)

        self.tone_var = tk.StringVar(value="default")
        self.scene_context = ""
        self.conversation_context = []
        

        self.setup_tabs()

        # Initialize context fields for the default person
        self.update_context_display(self.person_var.get())

    def setup_tabs(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.tab_main = tk.Frame(notebook, bg="#ffffff")
        self.tab_self = tk.Frame(notebook, bg="#ffffff")
        self.tab_profiles = tk.Frame(notebook, bg="#ffffff")

        notebook.add(self.tab_main, text="💬 聊天回复")
        notebook.add(self.tab_self, text="🧍 我的信息")
        notebook.add(self.tab_profiles, text="👥 对话人管理")

        self.build_main_tab()
        self.build_self_tab()
        # 原场景背景输入区域已移除，直接构建对话人管理面板
        self.build_profiles_tab()

    def build_main_tab(self):
        frame = self.tab_main

        top = tk.Frame(frame, bg="#ffffff")
        top.pack(pady=10)
        tk.Label(top, text="选择对话人:", bg="#ffffff").pack(side=tk.LEFT, padx=5)
        dropdown = ttk.Combobox(top, textvariable=self.person_var, values=list(self.profiles.keys()), width=20, state="readonly")
        dropdown.pack(side=tk.LEFT, padx=5)
        dropdown.bind("<<ComboboxSelected>>", self.on_person_change)

        
        # 显示当前人物背景信息和场景信息（可编辑）
        tk.Label(frame, text="🧍 当前人物背景信息:", bg="#ffffff").pack(anchor="w", padx=15)
        self.context_background_text = tk.Text(frame, height=3, bg="#fffce6", font=("Arial", 10))
        self.context_background_text.pack(fill="x", padx=15, pady=(0, 5))

        tk.Label(frame, text="🌍 当前场景信息:", bg="#ffffff").pack(anchor="w", padx=15)
        self.context_scene_text = tk.Text(frame, height=3, bg="#eef9ff", font=("Arial", 10))
        self.context_scene_text.pack(fill="x", padx=15, pady=(0, 10))
    
        tk.Label(frame, text="原始对话内容:", bg="#ffffff").pack(anchor="w", padx=15)
        self.input_text = tk.Text(frame, height=5, font=("Microsoft YaHei", 10))
        self.input_text.pack(fill="x", padx=15)

        tone_frame = tk.Frame(frame, bg="#ffffff")
        tone_frame.pack(pady=5)
        tk.Label(tone_frame, text="语气风格:", bg="#ffffff").pack(side=tk.LEFT)
        for name, val in [("默认", "default"), ("幽默", "humorous"), ("正式", "formal"), ("亲切", "friendly"), ("犀利", "sharp"), ("安慰", "comforting")]:
            tk.Radiobutton(tone_frame, text=name, variable=self.tone_var, value=val, bg="#ffffff").pack(side=tk.LEFT)

        tk.Button(frame, text="生成回复", command=self.manual_generate).pack(pady=5)

        tk.Label(frame, text="AI 回复建议:", bg="#ffffff").pack(anchor="w", padx=15)
        self.output_text = tk.Text(frame, height=10, bg="#f9f9f9", font=("Microsoft YaHei", 10))
        self.output_text.pack(fill="both", padx=15, pady=5, expand=True)

        tk.Label(frame, text="🧠 模型思考内容（仅查看）:", bg="#ffffff", fg="#555").pack(anchor="w", padx=15)
        self.think_output_text = tk.Text(frame, height=4, bg="#f0f0f0", font=("Arial", 10), state="disabled")
        self.think_output_text.pack(fill="both", padx=15, pady=(0, 5))
        
        self.copy_btn = tk.Button(frame, text="复制回复", command=self.copy_reply)
        self.copy_btn.pack(pady=3)

        self.status_label = tk.Label(frame, text="", fg="gray", bg="#ffffff")
        self.status_label.pack()

    def build_self_tab(self):
        frame = self.tab_self
        tk.Label(frame, text="我的背景信息（用于生成更贴近我语气的回复）:", bg="#ffffff").pack(anchor="w", padx=15, pady=10)
        self.self_text = tk.Text(frame, height=12, bg="#fffbe6", font=("Microsoft YaHei", 10))
        self.self_text.insert(tk.END, self.self_profile)
        self.self_text.pack(fill="both", expand=True, padx=15)
        tk.Button(frame, text="保存我的信息", command=self.save_self_profile).pack(pady=10)

    def build_profiles_tab(self):
        frame = self.tab_profiles

        left = tk.Frame(frame, bg="#ffffff")
        left.pack(side="left", fill="y", padx=10, pady=10)

        right = tk.Frame(frame, bg="#ffffff")
        right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.profile_listbox = tk.Listbox(left, width=25, font=("Microsoft YaHei", 10))
        self.profile_listbox.pack(fill="y")
        self.profile_listbox.bind("<<ListboxSelect>>", self.on_select_profile)

        tk.Label(right, text="背景信息:").pack(anchor="w")
        self.profile_text = tk.Text(right, height=4, bg="#e6f7ff", font=("Microsoft YaHei", 10))
        self.profile_text.pack(fill="x", pady=5)

        tk.Label(right, text="当前背景信息:").pack(anchor="w")
        self.current_background_text = tk.Text(right, height=4, bg="#fffce6", font=("Microsoft YaHei", 10))
        self.current_background_text.pack(fill="x", pady=5)

        tk.Label(right, text="当前场景信息:").pack(anchor="w", pady=(10,0))
        self.scene_edit_text = tk.Text(right, height=4, bg="#fffbe6", font=("Microsoft YaHei", 10))
        self.scene_edit_text.pack(fill="x", pady=5)

        self.new_name_entry = tk.Entry(right, font=("Microsoft YaHei", 10))
        self.new_name_entry.pack(pady=2)

        tk.Button(right, text="添加对话人", command=self.add_profile).pack(pady=2)
        tk.Button(right, text="删除选中对话人", command=self.delete_profile).pack(pady=2)
        tk.Button(right, text="保存背景信息", command=self.save_current_profile).pack(pady=2)

        self.refresh_profile_list()

    def refresh_profile_list(self):
        self.profile_listbox.delete(0, tk.END)
        for name in self.profiles:
            self.profile_listbox.insert(tk.END, name)

    def on_select_profile(self, event):
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        name = self.profile_listbox.get(index)
        self.person_var.set(name)
        self.profile_text.delete("1.0", tk.END)
        self.profile_text.insert(tk.END, self.profiles.get(name, {}).get("background", ""))
        if hasattr(self, "current_background_text"):
            self.current_background_text.delete("1.0", tk.END)
            self.current_background_text.insert(tk.END, self.profiles.get(name, {}).get("background", ""))
        if hasattr(self, "scene_edit_text"):
            self.scene_edit_text.delete("1.0", tk.END)
            self.scene_edit_text.insert(tk.END, self.profiles.get(name, {}).get("scene", ""))
        self.update_context_display(name)

    def add_profile(self):
        name = self.new_name_entry.get().strip()
        if name and name not in self.profiles:
            self.profiles[name] = {"background": "", "scene": ""}
            self.save_profiles()
            self.refresh_profile_list()
            self.new_name_entry.delete(0, tk.END)

    def delete_profile(self):
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        name = self.profile_listbox.get(selection[0])
        if messagebox.askyesno("确认", f"确定要删除“{name}”吗？"):
            self.profiles.pop(name, None)
            self.save_profiles()
            self.refresh_profile_list()

    def save_current_profile(self):
        name = self.person_var.get()
        info = self.profile_text.get("1.0", tk.END).strip()
        current_info = self.current_background_text.get("1.0", tk.END).strip() if hasattr(self, "current_background_text") else info
        if name:
            self.profiles[name]["background"] = current_info
        scene = self.scene_edit_text.get("1.0", tk.END).strip()
        self.profiles[name]["scene"] = scene
        self.save_profiles()
        messagebox.showinfo("提示", f"已保存“{name}”的背景信息")

    def load_profiles(self):
        if os.path.exists("profiles.json"):
            with open("profiles.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {"未指定": ""}

    def save_profiles(self):
        with open("profiles.json", "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, ensure_ascii=False, indent=2)

    def load_self_profile(self):
        if os.path.exists(SELF_PROFILE_PATH):
            with open(SELF_PROFILE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def save_self_profile(self):
        text = self.self_text.get("1.0", tk.END).strip()
        with open(SELF_PROFILE_PATH, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("提示", "已保存我的背景信息")

    def manual_generate(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            return
        threading.Thread(target=self.generate_reply, args=(text,), daemon=True).start()

    
    
    
    
    def copy_reply(self):
        reply = self.output_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(reply)
        self.auto_trigger_enabled = False

    
    def update_input(self, text):
        if not self.auto_trigger_enabled:
            self.auto_trigger_enabled = True
            return
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, text)
        self.manual_generate()

    def run(self):
        self.update_context_display(self.person_var.get())
        self.root.mainloop()

    
    
    def generate_reply(self, text):
        name = self.person_var.get()
        self_profile = self.self_text.get("1.0", tk.END).strip()
        profile = self.context_background_text.get("1.0", tk.END).strip()
        scene = self.context_scene_text.get("1.0", tk.END).strip()

        self.profiles[name]["background"] = profile
        self.profiles[name]["scene"] = scene

        prefix = f"你是{name}口中的我，一个真实的人类。请代入我的身份与语气，不要透露任何 AI 痕迹。"
        if self_profile:
            prefix += f" 我的背景设定是：{self_profile}。"
        if profile:
            prefix += f" 对方背景信息：{profile}。"
        if scene:
            prefix += f" 当前聊天场景：{scene}。"
        if self.conversation_context:
            history = "".join(self.conversation_context[-5:])
            prefix += f" 以下是最近的聊天记录：{history}"

        final_text = f"{prefix}现在对方说：{text}请代我自然回复一句，不要解释过程，不要暴露你是AI。"

        self.status_label.config(text="正在思考中，请稍候...")
        reply = get_reply_suggestion(final_text, tone=self.tone_var.get())

        think = ""
        if "<think>" in reply and "</think>" in reply:
            m = re.search(r"<think>(.*?)</think>", reply, re.DOTALL)
            think = m.group(1).strip() if m else ""
            reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, reply)

        if hasattr(self, 'think_output_text'):
            self.think_output_text.config(state="normal")
            self.think_output_text.delete("1.0", tk.END)
            self.think_output_text.insert(tk.END, think)
            self.think_output_text.config(state="disabled")

        self.status_label.config(text="")
        self.conversation_context.append(f"对方：{text}我：{reply}")

        # 自动更新场景内容（每5轮总结）
        if len(self.conversation_context) % 5 == 0:
            summary_prompt = "请总结以下多轮对话所处的场景背景：" + "".join(self.conversation_context[-5:]) + "要求精简自然："
            summary = get_reply_suggestion(summary_prompt, tone="formal")
            self.context_scene_text.delete("1.0", tk.END)
            self.context_scene_text.insert(tk.END, summary)
            self.profiles[name]["scene"] = summary
    def update_context_display(self, name):
        info = self.profiles.get(name, {})
        background = info.get("background", "")
        scene = info.get("scene", "")
        if hasattr(self, 'context_background_text'):
            self.context_background_text.delete("1.0", tk.END)
            self.context_background_text.insert(tk.END, background)
        if hasattr(self, 'context_scene_text'):
            self.context_scene_text.delete("1.0", tk.END)
            self.context_scene_text.insert(tk.END, scene)
        if hasattr(self, 'current_background_text'):
            self.current_background_text.delete("1.0", tk.END)
            self.current_background_text.insert(tk.END, background)
        if hasattr(self, 'scene_edit_text'):
            self.scene_edit_text.delete("1.0", tk.END)
            self.scene_edit_text.insert(tk.END, scene)

    def on_person_change(self, event=None):
        self.update_context_display(self.person_var.get())


