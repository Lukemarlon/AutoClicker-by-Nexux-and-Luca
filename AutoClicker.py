"""
Auto Clicker
------------
Einstellbar:
  - Aktion: Linksklick / Rechtsklick / Mittelklick / beliebige Taste
  - Intervall in Millisekunden (0 = so schnell wie möglich, nach oben offen)
  - Start/Stopp per Button oder globalem Hotkey (Standard: F6)

Benötigte Bibliothek: pynput
    pip install pynput
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key, KeyCode, Listener as KeyListener


def is_windows_dark_mode():
    """Prüft, ob Windows aktuell im Dunkelmodus läuft."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return False


def try_round_window_corners(root):
    """Abgerundete Fensterecken auf Windows 11, falls verfügbar."""
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        pass


DARK = {
    "bg": "#202020",
    "card": "#2b2b2b",
    "card_hi": "#343434",
    "fg": "#f0f0f0",
    "fg_muted": "#9a9a9a",
    "entry_bg": "#1c1c1c",
    "accent": "#0078d4",
    "accent_fg": "#ffffff",
    "danger": "#d13438",
    "success": "#6bb700",
    "border": "#3a3a3a",
    "footer": "#181818",
}
LIGHT = {
    "bg": "#f3f3f3",
    "card": "#ffffff",
    "card_hi": "#e9e9e9",
    "fg": "#1a1a1a",
    "fg_muted": "#6b6b6b",
    "entry_bg": "#ffffff",
    "accent": "#0067c0",
    "accent_fg": "#ffffff",
    "danger": "#c42b1c",
    "success": "#107c10",
    "border": "#d6d6d6",
    "footer": "#e8e8e8",
}


class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, radius, bg_color, fg_color,
                 text, command, font, parent_bg):
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                          highlightthickness=0, bd=0)
        self.command = command
        self.radius = radius
        self.width = width
        self.height = height
        self.base_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self.font = font
        self._draw(bg_color)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
                  x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
                  x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(1, 1, self.width - 1, self.height - 1,
                          self.radius, fill=color, outline=color)
        self.create_text(self.width / 2, self.height / 2, text=self.text,
                          fill=self.fg_color, font=self.font)

    def _on_click(self, event):
        if self.command:
            self.command()

    def set_text(self, text):
        self.text = text
        self._draw(self.base_color)

    def set_colors(self, base_color, fg_color=None):
        self.base_color = base_color
        if fg_color:
            self.fg_color = fg_color
        self._draw(self.base_color)


class SegmentedControl(tk.Frame):
    def __init__(self, parent, options, variable, colors, command=None):
        super().__init__(parent, bg=colors["card"])
        self.variable = variable
        self.colors = colors
        self.command = command
        self.buttons = {}

        wrap = tk.Frame(self, bg=colors["entry_bg"], padx=3, pady=3)
        wrap.pack(fill="x")

        for value, label in options:
            btn = tk.Label(wrap, text=label, font=("Segoe UI", 9),
                            padx=8, pady=7, cursor="hand2")
            btn.pack(side="left", expand=True, fill="x")
            btn.bind("<Button-1>", lambda e, v=value: self._select(v))
            self.buttons[value] = btn

        self._refresh()

    def _select(self, value):
        self.variable.set(value)
        self._refresh()
        if self.command:
            self.command()

    def _refresh(self):
        c = self.colors
        current = self.variable.get()
        for value, btn in self.buttons.items():
            if value == current:
                btn.config(bg=c["accent"], fg=c["accent_fg"])
            else:
                btn.config(bg=c["entry_bg"], fg=c["fg_muted"])


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg_color):
        super().__init__(parent, bg=bg_color)

        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg_color)

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self._resize_inner)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _resize_inner(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-2, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(2, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 40)), "units")


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker")
        self.root.minsize(380, 420)
        self.root.geometry("420x600")
        self._center_window(420, 600)

        self.colors = DARK if is_windows_dark_mode() else LIGHT

        self.mouse = MouseController()
        self.keyboard = KeyboardController()

        self.running = False
        self.click_thread = None
        self.click_count = 0

        self.custom_key = Key.space
        self.custom_key_name = "Leertaste"
        self.waiting_for_key = False

        self.hotkey = Key.f6
        self.hotkey_name = "F6"
        self.waiting_for_hotkey = False

        self._apply_base_theme()
        self._build_ui()
        self._start_hotkey_listener()
        try_round_window_corners(self.root)

    def _center_window(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 3
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _apply_base_theme(self):
        c = self.colors
        self.root.configure(bg=c["bg"])
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["fg"],
                         bordercolor=c["border"], insertcolor=c["fg"], padding=6)
        style.configure("Vertical.TScrollbar", background=c["card_hi"],
                         troughcolor=c["bg"], bordercolor=c["bg"],
                         arrowcolor=c["fg_muted"])
        style.map("Vertical.TScrollbar", background=[("active", c["accent"])])

    def _card(self, parent, title):
        outer = tk.Frame(parent, bg=self.colors["bg"])
        outer.pack(fill="x", padx=20, pady=(0, 14))

        if title:
            tk.Label(outer, text=title.upper(), font=("Segoe UI", 8, "bold"),
                     bg=self.colors["bg"], fg=self.colors["fg_muted"]).pack(
                anchor="w", pady=(0, 6))

        card = tk.Frame(outer, bg=self.colors["card"], highlightthickness=1,
                         highlightbackground=self.colors["border"])
        card.pack(fill="x")
        inner = tk.Frame(card, bg=self.colors["card"])
        inner.pack(fill="both", padx=14, pady=13)
        return inner

    def _build_ui(self):
        c = self.colors

        # Kopfleiste (schlicht, ohne Verlauf/Emoji)
        header = tk.Frame(self.root, bg=c["accent"], height=64)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="Auto Clicker", font=("Segoe UI", 15, "bold"),
                 bg=c["accent"], fg="#ffffff").pack(anchor="w", padx=20, pady=(14, 0))
        tk.Label(header, text="Version 1.0", font=("Segoe UI", 8),
                 bg=c["accent"], fg="#e6f1fb").pack(anchor="w", padx=20)

        scroll = ScrollableFrame(self.root, c["bg"])
        scroll.pack(fill="both", expand=True)
        content = scroll.inner

        tk.Frame(content, bg=c["bg"], height=16).pack()

        # Aktion
        action_card = self._card(content, "Aktion")
        self.action_var = tk.StringVar(value="left")
        SegmentedControl(
            action_card,
            [("left", "Links"), ("right", "Rechts"), ("middle", "Mitte"), ("key", "Taste")],
            self.action_var, c, command=self._on_action_change
        ).pack(fill="x")

        self.key_row = tk.Frame(action_card, bg=c["card"])
        tk.Label(self.key_row, text="Taste:", bg=c["card"], fg=c["fg"],
                 font=("Segoe UI", 9)).pack(side="left")
        self.key_label = tk.Label(self.key_row, text=self.custom_key_name, width=12,
                                   bg=c["entry_bg"], fg=c["fg"], font=("Segoe UI", 9),
                                   pady=4)
        self.key_label.pack(side="left", padx=8)
        self._mini_button(self.key_row, "Ändern", self._capture_key).pack(side="left")
        self._on_action_change()

        # Intervall
        interval_card = self._card(content, "Intervall (Millisekunden)")
        self.interval_var = tk.StringVar(value="100")
        vcmd = (self.root.register(self._validate_number), "%P")
        entry = tk.Entry(interval_card, textvariable=self.interval_var,
                          validate="key", validatecommand=vcmd,
                          font=("Segoe UI", 14), bg=c["entry_bg"], fg=c["fg"],
                          insertbackground=c["fg"], relief="flat", justify="center")
        entry.pack(fill="x", ipady=7)
        tk.Label(interval_card, text="0 = so schnell wie möglich, keine Obergrenze",
                 font=("Segoe UI", 8), bg=c["card"], fg=c["fg_muted"]).pack(
            anchor="w", pady=(6, 0))

        # Hotkey
        hotkey_card = self._card(content, "Start- / Stopp-Hotkey")
        hk_row = tk.Frame(hotkey_card, bg=c["card"])
        hk_row.pack(fill="x")
        self.hotkey_label = tk.Label(hk_row, text=self.hotkey_name, width=12,
                                      bg=c["entry_bg"], fg=c["fg"], font=("Segoe UI", 9),
                                      pady=4)
        self.hotkey_label.pack(side="left")
        self._mini_button(hk_row, "Ändern", self._capture_hotkey).pack(side="left", padx=8)

        # Status + Zähler
        status_wrap = tk.Frame(content, bg=c["bg"])
        status_wrap.pack(pady=(4, 10))
        self.status_label = tk.Label(status_wrap, text="Bereit", font=("Segoe UI", 10, "bold"),
                                      bg=c["bg"], fg=c["success"])
        self.status_label.pack()
        self.count_label = tk.Label(status_wrap, text="", font=("Segoe UI", 8),
                                     bg=c["bg"], fg=c["fg_muted"])
        self.count_label.pack()

        # Start/Stopp
        btn_wrap = tk.Frame(content, bg=c["bg"])
        btn_wrap.pack(fill="x", padx=20, pady=(0, 6))
        self.toggle_btn = RoundedButton(
            btn_wrap, width=380, height=46, radius=8,
            bg_color=c["accent"], fg_color=c["accent_fg"],
            text="Start", command=self.toggle, font=("Segoe UI", 11, "bold"),
            parent_bg=c["bg"]
        )
        self.toggle_btn.pack()

        tk.Frame(content, bg=c["bg"], height=18).pack()

        # Footer
        footer = tk.Frame(self.root, bg=c["footer"])
        footer.pack(fill="x", side="bottom")
        tk.Frame(footer, bg=c["border"], height=1).pack(fill="x")
        cred_inner = tk.Frame(footer, bg=c["footer"])
        cred_inner.pack(pady=10)
        tk.Label(cred_inner, text="NexuxGames", font=("Segoe UI", 9, "bold"),
                 bg=c["footer"], fg=c["fg"]).pack(side="left")
        tk.Label(cred_inner, text="   ·   Provider: Luca", font=("Segoe UI", 9),
                 bg=c["footer"], fg=c["fg_muted"]).pack(side="left")

    def _mini_button(self, parent, text, command):
        c = self.colors
        btn = tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
                        bg=c["card_hi"], fg=c["fg"], padx=10, pady=5, cursor="hand2")
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg=c["accent"], fg=c["accent_fg"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=c["card_hi"], fg=c["fg"]))
        return btn

    def _on_action_change(self):
        if self.action_var.get() == "key":
            self.key_row.pack(fill="x", pady=(10, 0))
        else:
            self.key_row.pack_forget()

    def _validate_number(self, value):
        return value == "" or value.isdigit()

    def _capture_key(self):
        self.key_label.config(text="Taste drücken...")
        self.waiting_for_key = True

    def _capture_hotkey(self):
        self.hotkey_label.config(text="Taste drücken...")
        self.waiting_for_hotkey = True

    def _start_hotkey_listener(self):
        def on_press(key):
            if self.waiting_for_key:
                self.custom_key = key
                self.custom_key_name = self._key_to_name(key)
                self.root.after(0, lambda: self.key_label.config(text=self.custom_key_name))
                self.waiting_for_key = False
                return

            if self.waiting_for_hotkey:
                self.hotkey = key
                self.hotkey_name = self._key_to_name(key)
                self.root.after(0, lambda: self.hotkey_label.config(text=self.hotkey_name))
                self.waiting_for_hotkey = False
                return

            if self._keys_equal(key, self.hotkey):
                self.root.after(0, self.toggle)

        self.listener = KeyListener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()

    @staticmethod
    def _key_to_name(key):
        if isinstance(key, KeyCode):
            return key.char if key.char else str(key)
        return str(key).replace("Key.", "")

    @staticmethod
    def _keys_equal(a, b):
        return a == b

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        try:
            interval_ms = int(self.interval_var.get() or "0")
        except ValueError:
            messagebox.showerror("Fehler", "Bitte eine gültige Zahl eingeben.")
            return

        if interval_ms < 0:
            interval_ms = 0

        self.running = True
        self.click_count = 0
        self.status_label.config(text="Läuft...", fg=self.colors["danger"])
        self.toggle_btn.set_text("Stopp")
        self.toggle_btn.set_colors(self.colors["danger"], "#ffffff")

        self.click_thread = threading.Thread(
            target=self._click_loop, args=(interval_ms,), daemon=True
        )
        self.click_thread.start()
        self._update_counter_label()

    def stop(self):
        self.running = False
        self.status_label.config(text="Bereit", fg=self.colors["success"])
        self.toggle_btn.set_text("Start")
        self.toggle_btn.set_colors(self.colors["accent"], self.colors["accent_fg"])

    def _update_counter_label(self):
        if self.running:
            self.count_label.config(text=f"{self.click_count:,} Klicks".replace(",", "."))
            self.root.after(150, self._update_counter_label)
        else:
            self.count_label.config(text="")

    def _click_loop(self, interval_ms):
        delay = interval_ms / 1000.0
        action = self.action_var.get()

        while self.running:
            if action == "left":
                self.mouse.click(Button.left)
            elif action == "right":
                self.mouse.click(Button.right)
            elif action == "middle":
                self.mouse.click(Button.middle)
            elif action == "key":
                self.keyboard.press(self.custom_key)
                self.keyboard.release(self.custom_key)

            self.click_count += 1

            if delay > 0:
                time.sleep(delay)


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
