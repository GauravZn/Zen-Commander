import tkinter as tk
from tkinter import messagebox
import os
from datetime import datetime
from cryptography.fernet import Fernet

# ================= CONFIGURATION =================
SAVE_FOLDER = "notes"
KEY_FILE = "notes.key"
AUTOSAVE_DELAY = 5000

# THEME: "Zen Commander"
THEME = {
    "bg_main":    "#000000",   # Void Black
    "bg_sidebar": "#111111",   # Dark Grey
    "bg_overlay": "#222222",   # Popup Background
    "fg_primary": "#00ffff",   # Cyan (Spark/Cursor)
    "fg_active":  "#ffffff",   # Bright White (OPEN FILE ONLY)
    "fg_dim":     "#005f5f",   # Dim Cyan (Inactive Files)
    "cursor":     "#00ffff",   # Editor Cursor
    "selection":  "#004444",   # Editor Selection
}

# FONTS
FONT_UI = ("Consolas", 14)
FONT_EDITOR = ("Consolas", 16)
FONT_BOLD = ("Consolas", 14, "bold")

os.makedirs(SAVE_FOLDER, exist_ok=True)

# ================= CRYPTO CORE =================
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f: f.write(key)
    else:
        with open(KEY_FILE, "rb") as f: key = f.read()
    return key

fernet = Fernet(load_key())

def encrypt(text): return fernet.encrypt(text.encode())
def decrypt(data): 
    try: return fernet.decrypt(data).decode()
    except: return ""

# ================= THE APP =================

class ZenCommander:
    def __init__(self, root):
        self.root = root
        self.root.title("ZEN COMMANDER")
        
        # 1. ROOT CURSOR KILL
        self.root.configure(bg=THEME["bg_main"], cursor="none")
        self.root.attributes('-fullscreen', True)

        # State
        self.focus_mode = "sidebar" 
        self.files = []
        self.current_file_path = None
        self.current_open_filename = None # Tracks active file for highlighting
        self.selected_file_index = -1 

        self.setup_ui()
        self.refresh_file_list()
        
        # --- GLOBAL BINDINGS ---
        self.root.bind("<Escape>", self.quit_app)
        
        # --- EDITOR BINDINGS ---
        self.text.bind("<Control-s>", self.manual_save)
        self.text.bind("<Return>", self.check_commands)
        self.text.bind("<Button-1>", lambda e: "break")
        
        # Switch Focus (Override Tab)
        self.text.bind("<Control-Tab>", self.toggle_focus) 
        self.text.bind("<Tab>", lambda e: "break") 

        # --- SIDEBAR BINDINGS ---
        self.list_display.bind("<Up>", self.nav_up)
        self.list_display.bind("<Down>", self.nav_down)
        self.list_display.bind("<Return>", self.on_enter)
        self.list_display.bind("n", self.custom_input_dialog) 
        self.list_display.bind("r", self.rename_dialog)
        self.list_display.bind("<Delete>", self.delete_file)
        
        # Switch Focus (Override Tab)
        self.list_display.bind("<Control-Tab>", self.toggle_focus)
        self.list_display.bind("<Tab>", lambda e: "break") 
        
        self.list_display.focus_set()
        self.show_instructions()
        self.update_visuals()
        self.autosave_loop()

    def setup_ui(self):
        # Apply cursor="none" to EVERYTHING
        self.container = tk.Frame(self.root, bg=THEME["bg_main"], cursor="none")
        self.container.pack(fill=tk.BOTH, expand=True)

        # --- Sidebar ---
        self.sidebar = tk.Frame(self.container, bg=THEME["bg_sidebar"], width=350, cursor="none")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.lbl_sb = tk.Label(self.sidebar, text="\n  [ ARCHIVE ]\n", 
                               bg=THEME["bg_sidebar"], fg=THEME["fg_dim"], font=FONT_BOLD, anchor="w", padx=20, cursor="none")
        self.lbl_sb.pack(fill=tk.X)

        self.list_display = tk.Text(self.sidebar, bg=THEME["bg_sidebar"], fg=THEME["fg_primary"],
                                    font=FONT_UI, state="disabled", cursor="none", bd=0, padx=20)
        self.list_display.pack(fill=tk.BOTH, expand=True)

        # --- Editor ---
        self.editor_pane = tk.Frame(self.container, bg=THEME["bg_main"], cursor="none")
        self.editor_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.lbl_ed = tk.Label(self.editor_pane, text=" ", bg=THEME["bg_main"], font=("Arial", 16), cursor="none")
        self.lbl_ed.pack(fill=tk.X)

        self.text = tk.Text(self.editor_pane, bg=THEME["bg_main"], fg=THEME["fg_primary"],
                            insertbackground=THEME["cursor"], selectbackground=THEME["selection"],
                            font=FONT_EDITOR, wrap=tk.WORD, bd=0, padx=100, pady=20, undo=True,
                            blockcursor=True, insertwidth=4, insertontime=600, insertofftime=300, cursor="none")
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # --- Status Bar ---
        self.status = tk.Label(self.root, text="SYSTEM READY", bg=THEME["bg_main"], fg=THEME["fg_dim"], 
                               font=("Consolas", 10), anchor="e", padx=20, pady=10, cursor="none")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ================= COMMAND SYSTEM =================

    def check_commands(self, event):
        current_line = self.text.get("insert linestart", "insert lineend").strip()
        
        if current_line == ">>time":
            self.text.delete("insert linestart", "insert lineend")
            self.insert_timestamp()
            return "break"

        elif current_line == ">>save":
            self.text.delete("insert linestart", "insert lineend")
            self.save_current()
            self.text.delete(1.0, tk.END)
            
            # --- RESET STATE ---
            self.current_file_path = None
            self.current_open_filename = None # Remove white highlight
            self.focus_mode = "sidebar"
            
            # CRITICAL FIX: DO NOT RESET 'self.selected_file_index' TO -1
            # We keep it exactly where it is, so the user can just hit Enter to re-open.
            
            self.list_display.focus_set()
            
            self.update_visuals()
            self.show_instructions()
            return "break"

        elif current_line == ">>clearscreen":
            self.text.delete(1.0, tk.END)
            return "break"

        elif current_line == ">>exit_app":
            self.text.delete("insert linestart", "insert lineend")
            self.save_current()
            self.root.destroy()
            return "break"

        return None

    def insert_timestamp(self):
        now = datetime.now()
        date_str = now.strftime("%A, %d %B %Y — %I:%M %p")
        dashes = "-" * 20
        line = f"\n{dashes}{date_str}{dashes}\n\n"
        self.text.insert(tk.INSERT, line)
        self.text.see(tk.INSERT)

    def show_instructions(self):
        manual = """
        ZEN COMMANDER v12.0 // MANUAL
        =============================

        [ NAVIGATION ]
        Ctrl + Tab      : Toggle Sidebar / Editor
        Down            : Enter Archive List
        n               : New File
        r               : Rename File
        Delete          : Delete File
        Esc             : Save & Quit

        [ COMMANDS ]
        >>time          : Insert Timestamp
        >>save          : Save & Return Home
        >>clearscreen   : Wipe content
        >>exit_app      : Quit Application
        """
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, manual)
        self.text.config(fg=THEME["fg_dim"])

    # ================= INPUT DIALOGS =================

    def show_overlay_input(self, title, callback):
        top = tk.Toplevel(self.root)
        top.geometry("500x150")
        x = (self.root.winfo_screenwidth() // 2) - 250
        y = (self.root.winfo_screenheight() // 2) - 150
        top.geometry(f"+{x}+{y}")
        top.configure(bg=THEME["bg_overlay"], cursor="none") 
        top.overrideredirect(True)
        
        lbl = tk.Label(top, text=title, bg=THEME["bg_overlay"], fg=THEME["fg_primary"], font=FONT_BOLD, cursor="none")
        lbl.pack(pady=(30, 10))
        
        entry = tk.Entry(top, bg="#000000", fg=THEME["fg_primary"], font=FONT_UI, 
                         insertbackground=THEME["cursor"], bd=2, relief="flat", justify="center", cursor="none")
        entry.pack(ipady=5, ipadx=5, fill=tk.X, padx=50)
        entry.focus_set()

        entry.bind("<Tab>", lambda e: "break") # Block Tab in popup

        def submit(event=None):
            val = entry.get()
            top.destroy()
            if val: callback(val)

        def cancel(event=None):
            top.destroy()
            self.list_display.focus_set()

        entry.bind("<Return>", submit)
        entry.bind("<Escape>", cancel)

    def custom_input_dialog(self, event=None):
        if self.focus_mode != "sidebar": return
        self.show_overlay_input("NEW ENTRY NAME:", self.create_file)
        return "break"

    def rename_dialog(self, event=None):
        if self.focus_mode != "sidebar" or self.selected_file_index == -1: return
        self.show_overlay_input("RENAME TO:", self.perform_rename)
        return "break"

    def create_file(self, name):
        if not name.endswith(".nt"): name += ".nt"
        path = os.path.join(SAVE_FOLDER, name)
        if not os.path.exists(path):
            with open(path, "wb") as f: f.write(encrypt(""))
            self.refresh_file_list()
            try: self.selected_file_index = self.files.index(name)
            except: pass
            self.render_file_list()
            self.open_file()

    def perform_rename(self, new_name):
        if not new_name.endswith(".nt"): new_name += ".nt"
        old_name = self.files[self.selected_file_index]
        old_path = os.path.join(SAVE_FOLDER, old_name)
        new_path = os.path.join(SAVE_FOLDER, new_name)
        try:
            os.rename(old_path, new_path)
            if self.current_open_filename == old_name:
                self.current_open_filename = new_name
            self.refresh_file_list()
            try: self.selected_file_index = self.files.index(new_name)
            except: self.selected_file_index = 0
            self.update_visuals()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= LOGIC & NAV =================

    def toggle_focus(self, event=None):
        if self.focus_mode == "sidebar":
            self.focus_mode = "editor"
            self.text.focus_set()
        else:
            self.focus_mode = "sidebar"
            self.list_display.focus_set()
        self.update_visuals()
        return "break"

    def update_visuals(self):
        self.render_file_list()
        
        if self.focus_mode == "sidebar":
            if self.selected_file_index == -1:
                self.lbl_sb.config(fg=THEME["fg_primary"]) 
            else:
                self.lbl_sb.config(fg=THEME["fg_dim"])
            self.text.config(fg=THEME["fg_dim"])
        else:
            self.lbl_sb.config(fg=THEME["fg_dim"])
            self.text.config(fg=THEME["fg_primary"])

    def refresh_file_list(self):
        self.files = sorted([f for f in os.listdir(SAVE_FOLDER) if f.endswith(".nt")])

    def render_file_list(self):
        self.list_display.config(state="normal")
        self.list_display.delete(1.0, tk.END)
        
        if not self.files:
            self.list_display.insert(tk.END, "\n  [NO FILES]\n  Press 'n'")
            
        for i, f in enumerate(self.files):
            # 1. Base Prefix
            prefix = "   "
            
            # 2. Logic for Colors
            fg_tag = "dim_cyan" # Default
            bg_tag = None
            
            # STRICT: Is this the current open file?
            if self.current_open_filename is not None and f == self.current_open_filename:
                fg_tag = "bright_white"
            
            # Is the cursor currently hovering over this row?
            if i == self.selected_file_index:
                prefix = " > "
                bg_tag = "cursor_bg"
                
                # High contrast for hover
                fg_tag = "black_text" 

            # Apply Tags
            tags = [fg_tag]
            if bg_tag: tags.append(bg_tag)

            self.list_display.insert(tk.END, f"{prefix}{f}\n", tuple(tags))
            
        # --- TAGS ---
        self.list_display.tag_config("bright_white", foreground=THEME["fg_active"]) 
        self.list_display.tag_config("dim_cyan", foreground=THEME["fg_dim"])
        self.list_display.tag_config("black_text", foreground="#000000")
        self.list_display.tag_config("cursor_bg", background=THEME["fg_primary"])
        
        self.list_display.config(state="disabled")
        
        if self.selected_file_index != -1:
            self.list_display.see(f"{self.selected_file_index + 1}.0")

    def open_file(self):
        if not self.files: return
        self.save_current()
        filename = self.files[self.selected_file_index]
        self.current_file_path = os.path.join(SAVE_FOLDER, filename)
        
        self.current_open_filename = filename # Set Open Status
        
        with open(self.current_file_path, "rb") as f:
            content = decrypt(f.read())
        
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, content)
        self.text.config(fg=THEME["fg_primary"])
        
        self.focus_mode = "editor"
        self.text.focus_set()
        self.update_visuals()
        self.status.config(text=f"EDITING: {filename}")

    # ================= NAV CONTROLS =================

    def nav_down(self, e):
        if self.selected_file_index == -1:
            if self.files:
                self.selected_file_index = 0
                self.update_visuals()
        elif self.selected_file_index < len(self.files) - 1:
            self.selected_file_index += 1
            self.update_visuals()
        return "break"

    def nav_up(self, e):
        if self.selected_file_index > 0:
            self.selected_file_index -= 1
            self.update_visuals()
        return "break"

    def on_enter(self, e):
        if self.selected_file_index != -1:
            self.open_file()
        return "break"

    def delete_file(self, e=None):
        if self.files and self.selected_file_index != -1:
            target = self.files[self.selected_file_index]
            if messagebox.askyesno("DELETE", f"Destroy {target}?"):
                os.remove(os.path.join(SAVE_FOLDER, target))
                
                # If we deleted the active file, reset state
                if self.current_open_filename == target:
                    self.current_open_filename = None
                    self.text.delete(1.0, tk.END)
                
                self.refresh_file_list()
                self.selected_file_index = max(0, self.selected_file_index - 1)
                if not self.files: self.selected_file_index = -1
                self.update_visuals()
                self.show_instructions()
        return "break"

    def manual_save(self, e=None):
        self.save_current()
        self.status.config(text="MANUAL SAVE", fg=THEME["accent"])
        return "break"

    def save_current(self):
        if self.current_file_path:
            content = self.text.get(1.0, tk.END + "-1c")
            with open(self.current_file_path, "wb") as f:
                f.write(encrypt(content))
            self.status.config(text=f"AUTOSAVED", fg=THEME["fg_dim"])

    def quit_app(self, event=None):
        self.save_current()
        self.root.destroy()

    def autosave_loop(self):
        if self.current_file_path: self.save_current()
        self.root.after(AUTOSAVE_DELAY, self.autosave_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = ZenCommander(root)
    root.mainloop()