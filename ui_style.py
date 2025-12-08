from tkinter import ttk

# Palette
COLOR_BG = "#11121C"
COLOR_CARD = "#181926"
COLOR_ACCENT = "#2c82c5"
COLOR_TEXT = "#ffffff"
COLOR_MUTED = "#c7c8ca"
COLOR_LOG_BG = "#0f1018"

# Layout
WINDOW_PAD = 96
BASE_PAD = 16

# Fonts
FONT_REG = ("Futura", 11)
FONT_BOLD = ("Futura", 13, "bold")
FONT_MONO = ("Futura", 9)


def apply_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("App.TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_CARD)
    style.configure("App.TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_REG)
    style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=FONT_REG)
    style.configure("Heading.TLabel", background=COLOR_BG, foreground=COLOR_ACCENT, font=FONT_BOLD)
    style.configure("Accent.TButton", background=COLOR_ACCENT, foreground=COLOR_TEXT, padding=BASE_PAD, borderwidth=0)
    style.map(
        "Accent.TButton",
        background=[("disabled", "#2a2d3a"), ("pressed", "#1f6ba4"), ("active", "#3c92d5"), ("!disabled", COLOR_ACCENT)],
        foreground=[("disabled", "#777777"), ("!disabled", COLOR_TEXT)],
    )
    style.configure("App.TEntry", fieldbackground="#1f2130", foreground=COLOR_TEXT, insertcolor=COLOR_TEXT, padding=8)
    style.configure("Card.TCheckbutton", background=COLOR_CARD, foreground=COLOR_TEXT)
    return style
