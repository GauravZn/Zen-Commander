# ⚡ ZEN COMMANDER // VOID EDITION
**A Secure, Zero-Mouse, Encrypted Note-Taking Environment.**

Zen Commander is a high-performance, keyboard-only terminal for the modern "Gentleman Hacker." It is designed to provide an absolute focus environment (Void Black) with industrial-grade encryption and a seamless modal workflow.

---

## 🛠 THE PHILOSOPHY
* **Zero Mouse:** Your cursor is nuked. Interaction is purely tactile.
* **Void Focus:** The UI is pitch black. No buttons, no distractions.
* **Encryption First:** Every note is AES-encrypted (Fernet) the moment it hits the disk.
* **Zen Flow:** Modal navigation—archive management on the left, pure creation on the right.

---

## ⌨️ OPERATOR MANUAL

### **Navigation**
| Key | Action |
| :--- | :--- |
| `Ctrl + Tab` | Toggle between **ARCHIVE** (Sidebar) and **EDITOR** |
| `Down / Up` | Navigate the file list (Archive mode) |
| `Enter` | Open selected file |
| `n` | Create new entry (While in Sidebar) |
| `r` | Rename entry (While in Sidebar) |
| `Delete` | Permanently discard entry (While in Sidebar) |
| `Esc` | **Force Save & Exit Application** |

### **The Command Protocol**
Type these commands directly into the editor and hit `Enter`:
* `>>time` — Inserts a formatted, distinct human timestamp.
* `>>save` — Saves the current work and returns focus to the Archive.
* `>>clearscreen` — Wipes the current file content.
* `>>exit_app` — Final save and system shutdown.

---

## 🚀 INSTALLATION & SETUP

### **For Users (.exe)**
1. Go to the [Releases](link-to-your-github-release) tab.
2. Download `ZenCommander.exe`.
3. Launch. (On first run, a `notes.key` and `notes/` folder will be generated locally).

### **For Developers (Source)**
1. Clone the repo.
2. Install dependencies: `pip install cryptography`.
3. Run `python zen_commander.py`.

---

## 🔒 SECURITY NOTE
Your `notes.key` is the **only** way to read your files. If you lose this key, your notes are lost to the void forever. **Never share your key.**