import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, StringVar
from io import BytesIO
import tkinter.colorchooser as colorchooser

import requests
from PIL import Image, ImageTk, ImageOps

HISTORY_FILE = "pokemon_history.json"
SETTINGS_FILE = "settings.json"
DEFAULT_LOG = "pokemon_data.log"

pokemon_data = {}
player_history = {}
enemy_history = {}

THEMES = {
    "Light Mode": {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "entry_bg": "#FFFFFF",
        "entry_fg": "#000000",
        "listbox_bg": "#FFFFFF",
        "listbox_fg": "#000000",
        "text_bg": "#FFFFFF",
        "text_fg": "#000000",
        "button_bg": "#E0E0E0",
        "button_fg": "#000000",
    },
    "Dark Mode": {
        "bg": "#222222",
        "fg": "#EEEEEE",
        "entry_bg": "#333333",
        "entry_fg": "#FFFFFF",
        "listbox_bg": "#333333",
        "listbox_fg": "#FFFFFF",
        "text_bg": "#222222",
        "text_fg": "#EEEEEE",
        "button_bg": "#444444",
        "button_fg": "#FFFFFF",
    },
}

CUSTOM_THEME_KEY = "Custom Theme"

current_theme_name = "Light Mode"
current_theme = THEMES[current_theme_name]
custom_theme_colors = {}

def load_settings():
    global current_theme_name, current_theme, custom_theme_colors
    if not os.path.exists(SETTINGS_FILE):
        return
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        tn = data.get("theme", current_theme_name)
        if tn == CUSTOM_THEME_KEY:
            ct = data.get("custom_theme")
            if ct:
                custom_theme_colors = ct
                current_theme = ct
                current_theme_name = CUSTOM_THEME_KEY
            else:
                current_theme_name = "Light Mode"
                current_theme = THEMES[current_theme_name]
        elif tn in THEMES:
            current_theme_name = tn
            current_theme = THEMES[tn]
    except Exception:
        pass

def save_settings():
    try:
        if current_theme_name == CUSTOM_THEME_KEY:
            settings = {"theme": CUSTOM_THEME_KEY, "custom_theme": current_theme}
        else:
            settings = {"theme": current_theme_name}
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

def load_history():
    global player_history, enemy_history
    if not os.path.exists(HISTORY_FILE):
        player_history, enemy_history = {}, {}
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        player_history = {k: v for k, v in data.get("player_history", {}).items()}
        enemy_history  = {k: v for k, v in data.get("enemy_history", {}).items()}
    except Exception:
        player_history, enemy_history = {}, {}

def save_history():
    data = {
        "player_history": player_history,
        "enemy_history": enemy_history
    }
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_pokemon_data(file_path):
    pk = {}
    header_found = False
    headers = []

    with open(file_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if not header_found and line.upper().startswith("NUM|NAME"):
                headers = [h.strip().upper() for h in line.split("|")]
                header_found = True
                continue
            if header_found:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) != len(headers):
                    continue
                row = dict(zip(headers, parts))
                name_key = row.get("NAME", "").strip().lower()
                if not name_key:
                    continue
                for k in ["TYPE", "NUM", "HP", "ATK", "DEF", "SPE", "SATK", "SDEF"]:
                    row.setdefault(k, "")
                pk[name_key] = row
    return pk

def calculate_bst(data):
    total = 0
    for k in ["HP", "ATK", "DEF", "SPE", "SATK", "SDEF"]:
        try:
            v = str(data.get(k, "")).strip()
            total += int(v) if v.isdigit() or (v and v.replace("-", "").isdigit()) else 0
        except Exception:
            pass
    return total

def format_full_info(data):
    lines = []
    order = ["NUM","NAME","TYPE","HP","ATK","DEF","SPE","SATK","SDEF","ABILITY1","ABILITY2","ABILITY3","ITEM"]
    seen = set()
    for k in order:
        if k in data and str(data[k]).strip() != "":
            lines.append(f"{k}: {data[k]}")
            seen.add(k)
    for k, v in data.items():
        if k not in seen and str(v).strip() != "":
            lines.append(f"{k}: {v}")
    lines.append(f"BST (Base Stat Total): {calculate_bst(data)}")
    return "\n".join(lines) + "\n"

def format_enemy_info(data):
    name = str(data.get("NAME", "")).strip()
    typ  = str(data.get("TYPE", "Unknown")).strip()
    return f"{name}\nType: {typ}\n"

def show_pokemon_image(text_widget, data):
    try:
        dex_str = str(data.get("NUM","")).strip()
        dex_num = int(dex_str) if dex_str.isdigit() else 0
        if dex_num <= 0:
            text_widget.insert(tk.END, "\n[No dex number, cannot load image]\n")
            return

        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{dex_num}.png"
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        img = Image.open(BytesIO(r.content)).convert("RGBA")
        bg_color = current_theme["bg"]
        bg = Image.new("RGBA", img.size, bg_color)
        img = Image.alpha_composite(bg, img)

        img = img.resize((96, 96), Image.Resampling.LANCZOS)
        sprite = ImageTk.PhotoImage(img)

        text_widget.insert(tk.END, "\n")
        text_widget.image_create(tk.END, image=sprite)
        text_widget.insert(tk.END, "\n")

        if not hasattr(text_widget, "_images"):
            text_widget._images = []
        text_widget._images.append(sprite)
    except Exception as e:
        text_widget.insert(tk.END, f"\n[Could not load image: {e}]\n")

def ask_classification(display_name):
    result = {"choice": None}
    def choose(c):
        result["choice"] = c
        win.destroy()

    win = Toplevel(root)
    win.title("Classify Pokémon")
    win.geometry("320x150")
    win.resizable(False, False)
    win.grab_set()
    win.configure(bg=current_theme["bg"])

    tk.Label(win, text=f"Is {display_name} your Pokémon or an enemy?", font=("Arial", 11),
             bg=current_theme["bg"], fg=current_theme["fg"]).pack(pady=15)
    row = tk.Frame(win, bg=current_theme["bg"])
    row.pack()
    tk.Button(row, text="Yours",  width=12, command=lambda: choose("yours"),
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).grid(row=0, column=0, padx=8)
    tk.Button(row, text="Enemy",  width=12, command=lambda: choose("enemy"),
              bg=current_theme["button_bg"], fg=current_theme["button_fg"]).grid(row=0, column=1, padx=8)

    win.bind("<Escape>", lambda e: choose(None))
    win.wait_window()
    return result["choice"]

SECTION_PLAYER = "--- Player History ---"
SECTION_ENEMY  = "--- Enemy History ---"
SECTION_LOG    = "--- From Log ---"

def populate_listbox():
    pokemon_listbox.delete(0, tk.END)
    if player_history:
        pokemon_listbox.insert(tk.END, SECTION_PLAYER)
        for name_key in sorted(player_history.keys(), key=lambda n: player_history[n].get("NAME","").lower()):
            pokemon_listbox.insert(tk.END, player_history[name_key].get("NAME", name_key).strip())
    if enemy_history:
        pokemon_listbox.insert(tk.END, SECTION_ENEMY)
        for name_key in sorted(enemy_history.keys(), key=lambda n: enemy_history[n].get("NAME","").lower()):
            pokemon_listbox.insert(tk.END, enemy_history[name_key].get("NAME", name_key).strip())
    pokemon_listbox.insert(tk.END, SECTION_LOG)
    for name_key in sorted(pokemon_data.keys(), key=lambda n: pokemon_data[n].get("NAME","").lower()):
        pokemon_listbox.insert(tk.END, pokemon_data[name_key].get("NAME", name_key).strip())

def key_from_display(display_name):
    dn = display_name.strip().lower()
    for d in (player_history, enemy_history):
        for k, v in d.items():
            if v.get("NAME","").strip().lower() == dn or k == dn:
                return k, d
    for k, v in pokemon_data.items():
        if v.get("NAME","").strip().lower() == dn or k == dn:
            return k, pokemon_data
    return None, None

def on_list_select(event=None):
    sel = pokemon_listbox.curselection()
    if not sel:
        return
    display = pokemon_listbox.get(sel[0])
    if display in (SECTION_PLAYER, SECTION_ENEMY, SECTION_LOG):
        return

    key, source = key_from_display(display)
    if not key:
        return

    output_text.delete("1.0", tk.END)
    output_text._images = []

    if source is player_history:
        data = player_history[key]
        output_text.insert(tk.END, format_full_info(data))
        show_pokemon_image(output_text, data)
        return
    if source is enemy_history:
        data = enemy_history[key]
        output_text.insert(tk.END, format_enemy_info(data))
        show_pokemon_image(output_text, data)
        return

    data = pokemon_data[key]
    if key in player_history:
        output_text.insert(tk.END, format_full_info(player_history[key]))
        show_pokemon_image(output_text, player_history[key])
    elif key in enemy_history:
        output_text.insert(tk.END, format_enemy_info(enemy_history[key]))
        show_pokemon_image(output_text, enemy_history[key])
    else:
        display_name = data.get("NAME", key.title()).strip()
        choice = ask_classification(display_name)
        if not choice:
            output_text.insert(tk.END, "[Cancelled]\n")
            return
        if choice == "yours":
            player_history[key] = data.copy()
            save_history()
            populate_listbox()
            output_text.insert(tk.END, format_full_info(data))
            show_pokemon_image(output_text, data)
        else:
            enemy_history[key] = data.copy()
            save_history()
            populate_listbox()
            output_text.insert(tk.END, format_enemy_info(data))
            show_pokemon_image(output_text, data)

def search_pokemon(event=None):
    query = search_entry.get().strip().lower()
    output_text.delete("1.0", tk.END)
    output_text._images = []

    if not query:
        output_text.insert(tk.END, "Type a Pokémon name to search.\n")
        return

    def find_exact(q):
        if q in player_history: return ("player", q)
        if q in enemy_history:  return ("enemy", q)
        if q in pokemon_data:   return ("log", q)
        for role, d in (("player", player_history), ("enemy", enemy_history), ("log", pokemon_data)):
            for k, v in d.items():
                if v.get("NAME","").strip().lower() == q:
                    return (role, k)
        return (None, None)

    role, key = find_exact(query)
    if not key:
        def collect_matches(q, d):
            out = []
            for k, v in d.items():
                nm = v.get("NAME","").strip().lower()
                if q in nm or q in k:
                    out.append(k)
            return out

        matches = (
            collect_matches(query, player_history) +
            collect_matches(query, enemy_history) +
            collect_matches(query, pokemon_data)
        )
        matches = list(dict.fromkeys(matches))
        if not matches:
            output_text.insert(tk.END, "No matches found.\n")
            return
        if len(matches) > 1:
            output_text.insert(tk.END, "Multiple matches found:\n")
            for k in matches:
                nm = (player_history.get(k) or enemy_history.get(k) or pokemon_data.get(k) or {}).get("NAME", k)
                output_text.insert(tk.END, f"- {nm}\n")
            return
        key = matches[0]
        if key in player_history:
            role = "player"
        elif key in enemy_history:
            role = "enemy"
        else:
            role = "log"

    if role == "player":
        data = player_history[key]
        output_text.insert(tk.END, format_full_info(data))
        show_pokemon_image(output_text, data)
    elif role == "enemy":
        data = enemy_history[key]
        output_text.insert(tk.END, format_enemy_info(data))
        show_pokemon_image(output_text, data)
    else:
        data = pokemon_data.get(key)
        if not data:
            output_text.insert(tk.END, "Not found in current log.\n")
            return
        if key in player_history:
            output_text.insert(tk.END, format_full_info(player_history[key]))
            show_pokemon_image(output_text, player_history[key])
        elif key in enemy_history:
            output_text.insert(tk.END, format_enemy_info(enemy_history[key]))
            show_pokemon_image(output_text, enemy_history[key])
        else:
            display_name = data.get("NAME", key.title()).strip()
            choice = ask_classification(display_name)
            if not choice:
                output_text.insert(tk.END, "[Cancelled]\n")
                return
            if choice == "yours":
                player_history[key] = data.copy()
                save_history()
                populate_listbox()
                output_text.insert(tk.END, format_full_info(data))
                show_pokemon_image(output_text, data)
            else:
                enemy_history[key] = data.copy()
                save_history()
                populate_listbox()
                output_text.insert(tk.END, format_enemy_info(data))
                show_pokemon_image(output_text, data)

def open_file():
    global pokemon_data
    path = filedialog.askopenfilename(
        title="Select Pokémon Data File",
        filetypes=[("Log/Text files", "*.log *.txt"), ("All files", "*.*")]
    )
    if not path:
        return
    try:
        pokemon_data = load_pokemon_data(path)
        messagebox.showinfo("Loaded", f"Loaded {len(pokemon_data)} Pokémon.")
        populate_listbox()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file:\n{e}")

def clear_history():
    if messagebox.askyesno("Clear History", "Clear Player and Enemy history? This cannot be undone."):
        player_history.clear()
        enemy_history.clear()
        save_history()
        populate_listbox()
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "History cleared.\n")
        output_text._images = []

def apply_theme():
    t = current_theme
    root.configure(bg=t["bg"])
    for widget in root.winfo_children():
        apply_theme_rec(widget, t)

def apply_theme_rec(widget, theme):
    cls = widget.__class__.__name__
    if cls in ("Frame", "LabelFrame"):
        widget.configure(bg=theme["bg"])
    elif cls == "Label":
        widget.configure(bg=theme["bg"], fg=theme["fg"])
    elif cls == "Button":
        widget.configure(bg=theme["button_bg"], fg=theme["button_fg"], activebackground=theme["button_bg"])
    elif cls == "Entry":
        widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
    elif cls == "Listbox":
        widget.configure(bg=theme["listbox_bg"], fg=theme["listbox_fg"], selectbackground=theme["button_bg"], selectforeground=theme["button_fg"])
    elif cls == "Text":
        widget.configure(bg=theme["text_bg"], fg=theme["text_fg"], insertbackground=theme["fg"])
    elif cls == "OptionMenu":
        widget.configure(bg=theme["button_bg"], fg=theme["button_fg"])
        # Also set menu colors:
        menu = widget["menu"]
        menu.configure(bg=theme["button_bg"], fg=theme["button_fg"])
    for child in widget.winfo_children():
        apply_theme_rec(child, theme)

def open_custom_theme_editor():
    global current_theme  # Use the global current_theme inside this function

    def pick_color(setting_key, btn):
        color = colorchooser.askcolor()[1]
        if color:
            custom_theme_colors[setting_key] = color
            btn.config(bg=color)

    def save_custom_theme():
        global current_theme, current_theme_name  # Declare globals at top of this inner function

        keys = [
            "bg", "fg", "entry_bg", "entry_fg",
            "listbox_bg", "listbox_fg", "text_bg", "text_fg",
            "button_bg", "button_fg"
        ]

        for k in keys:
            if k not in custom_theme_colors:
                # Now safe to use current_theme because of global declaration above
                custom_theme_colors[k] = current_theme.get(k, "#FFFFFF")

        current_theme = custom_theme_colors.copy()
        current_theme_name = CUSTOM_THEME_KEY
        apply_theme()
        save_settings()

        editor.destroy()

    editor = Toplevel(root)
    editor.title("Custom Theme Editor")
    editor.geometry("320x400")
    editor.configure(bg=current_theme.get("bg", "#FFFFFF"))

    labels = {
        "bg": "Background",
        "fg": "Foreground (text)",
        "entry_bg": "Entry Background",
        "entry_fg": "Entry Foreground",
        "listbox_bg": "Listbox Background",
        "listbox_fg": "Listbox Foreground",
        "text_bg": "Text Background",
        "text_fg": "Text Foreground",
        "button_bg": "Button Background",
        "button_fg": "Button Foreground",
    }

    for idx, (key, label_text) in enumerate(labels.items()):
        lbl = tk.Label(
            editor,
            text=label_text,
            bg=current_theme.get("bg", "#FFFFFF"),
            fg=current_theme.get("fg", "#000000"),
        )
        lbl.grid(row=idx, column=0, sticky="w", padx=10, pady=4)

        btn = tk.Button(editor, text="Pick", bg=current_theme.get(key, "#FFFFFF"))
        btn.config(command=lambda k=key, b=btn: pick_color(k, b))
        btn.grid(row=idx, column=1, padx=10)

    save_btn = tk.Button(
        editor,
        text="Save Custom Theme",
        command=save_custom_theme,
        bg=current_theme.get("button_bg", "#E0E0E0"),
        fg=current_theme.get("button_fg", "#000000"),
    )
    save_btn.grid(row=len(labels), column=0, columnspan=2, pady=20)

def on_theme_change(new_theme_name):
    global current_theme_name, current_theme, custom_theme_colors
    if new_theme_name == CUSTOM_THEME_KEY:
        # Load custom colors from settings if any
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    s = json.load(f)
                    custom_theme_colors = s.get("custom_theme", {})
            except Exception:
                custom_theme_colors = {}
        else:
            custom_theme_colors = {}

        if not custom_theme_colors:
            custom_theme_colors = current_theme.copy()

        open_custom_theme_editor()
        # Reset dropdown to previous if cancel
        theme_var.set(current_theme_name)
        return

    if new_theme_name in THEMES:
        current_theme_name = new_theme_name
        current_theme = THEMES[new_theme_name]
        apply_theme()
        save_settings()

        sel = pokemon_listbox.curselection()
        if sel:
            on_list_select()

root = tk.Tk()
root.title("Pokémon Randomizer Info")
root.geometry("880x520")
root.minsize(720, 440)

# Controls frame on top
controls_frame = tk.Frame(root)
controls_frame.pack(fill=tk.X, padx=8, pady=6)

# Theme dropdown
theme_var = StringVar(value=current_theme_name)
theme_options = list(THEMES.keys()) + [CUSTOM_THEME_KEY]
theme_menu = tk.OptionMenu(controls_frame, theme_var, *theme_options, command=on_theme_change)
theme_menu.pack(side=tk.LEFT, padx=(0, 10))

# Load file button
load_btn = tk.Button(controls_frame, text="Load Log File", command=open_file)
load_btn.pack(side=tk.LEFT, padx=(0, 10))

# Clear history button
clear_btn = tk.Button(controls_frame, text="Clear History", command=clear_history)
clear_btn.pack(side=tk.LEFT, padx=(0, 10))

# Search entry
search_entry = tk.Entry(controls_frame)
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
search_entry.bind("<Return>", search_pokemon)

# Search button
search_btn = tk.Button(controls_frame, text="Search", command=search_pokemon)
search_btn.pack(side=tk.LEFT)

# Main frame horizontally divides listbox and output
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

# Listbox on the left
pokemon_listbox = tk.Listbox(main_frame, height=25, width=30)
pokemon_listbox.pack(side=tk.LEFT, fill=tk.Y)
pokemon_listbox.bind("<<ListboxSelect>>", on_list_select)

# Output text on the right
output_text = tk.Text(main_frame, height=25)
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8,0))
output_text._images = []

# Load settings, history, default data
load_settings()
load_history()

# Load default log file if exists
if os.path.exists(DEFAULT_LOG):
    try:
        pokemon_data = load_pokemon_data(DEFAULT_LOG)
        messagebox.showinfo("Loaded", f"Loaded {len(pokemon_data)} Pokémon from {DEFAULT_LOG}")
    except Exception as e:
        messagebox.showerror("Error loading default log file", str(e))
else:
    pokemon_data = {}

populate_listbox()
apply_theme()

root.mainloop()
