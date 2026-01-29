import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

from assets import load_logo_image
from config import load_config
from ffmpeg_utils import ensure_ffmpeg
from file_ops import build_folder_structure, copy_selected_files, stitch_ms_files
from settings_manager import load_settings, save_settings
from ui_helpers import enable_mousewheel
from ui_style import (
    BASE_PAD,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_CARD,
    COLOR_LOG_BG,
    COLOR_MUTED,
    COLOR_TEXT,
    FONT_MONO,
    WINDOW_PAD,
    apply_styles,
)


# ---------------------------------------------------------
# FILENAME HELPERS
# ---------------------------------------------------------
def build_ms_filename(date_text, initials):
    date_part = date_text.strip()
    initials_part = initials.strip()
    if not date_part or not initials_part:
        return ""
    return f"Main_PSA_{date_part}_MS_1920x1080_H.264_{initials_part}.mp4"


def next_saturday_mmdd():
    today = datetime.today()
    days_ahead = (5 - today.weekday()) % 7
    target = today + timedelta(days=days_ahead)
    return target.strftime("%m%d")


def normalize_path(value: str) -> str:
    """Normalize UNC and local paths to keep separators consistent."""
    value = value.strip()
    if not value:
        return ""
    value = value.replace("/", "\\")
    value = os.path.normpath(value)
    if value.startswith("\\\\"):
        return "\\\\" + value.lstrip("\\")
    if value.startswith("\\"):
        # Promote single leading slash to UNC-style double
        return "\\\\" + value.lstrip("\\")
    return value


# ---------------------------------------------------------
# SETTINGS POPUP
# ---------------------------------------------------------
def open_settings_window(root, source_var, dest_root_var, app_config, settings, on_save=None):
    win = tk.Toplevel(root)
    win.title("Settings")
    win.geometry("500x150")

    tk.Label(win, text="Source Folder Path:").pack(anchor="w", pady=5)
    entry = tk.Entry(win, textvariable=source_var, width=60)
    entry.pack()

    tk.Label(win, text="Destination Root Folder:").pack(anchor="w", pady=5)
    dest_entry = tk.Entry(win, textvariable=dest_root_var, width=60)
    dest_entry.pack()

    def save_and_close():
        settings["source"] = normalize_path(source_var.get())
        settings["dest_root"] = normalize_path(dest_root_var.get())
        source_var.set(settings["source"])
        dest_root_var.set(settings["dest_root"])
        save_settings(settings, app_config)
        if on_save:
            on_save()
        win.destroy()

    tk.Button(win, text="Save", command=save_and_close).pack(pady=10)


# ---------------------------------------------------------
# MAIN GUI
# ---------------------------------------------------------
def run_gui():
    app_config = load_config()
    settings = load_settings(app_config)

    root = tk.Tk()
    root.title("PSA File Drop Utility")
    root.geometry("900x1000")
    root.configure(bg=COLOR_BG)

    apply_styles(root)

    outer = ttk.Frame(root, style="App.TFrame", padding=0)
    outer.pack(fill="both", expand=True)

    outer_canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0)
    outer_canvas.pack(side="left", fill="both", expand=True)

    outer_scrollbar = ttk.Scrollbar(outer, orient="vertical", command=outer_canvas.yview)
    outer_scrollbar.pack(side="right", fill="y")

    outer_canvas.configure(yscrollcommand=outer_scrollbar.set)

    container = ttk.Frame(outer_canvas, style="App.TFrame", padding=WINDOW_PAD)
    container_window = outer_canvas.create_window((0, 0), window=container, anchor="nw")

    def _update_scrollregion(_=None):
        outer_canvas.configure(scrollregion=outer_canvas.bbox("all"))

    container.bind("<Configure>", _update_scrollregion)
    outer_canvas.bind("<Configure>", lambda e: outer_canvas.itemconfigure(container_window, width=e.width))
    enable_mousewheel(container, outer_canvas)
    enable_mousewheel(outer_canvas, outer_canvas)

    # Logo and heading
    logo_img = load_logo_image(root, app_config.get("logo_path", ""))
    if logo_img:
        root.iconphoto(True, logo_img)
        logo_label = tk.Label(container, image=logo_img, bg=COLOR_BG)
        logo_label.image = logo_img
        logo_label.pack(anchor="w", pady=(0, BASE_PAD))

    ttk.Label(container, text="PSA Utility", style="Heading.TLabel").pack(anchor="w", pady=(0, BASE_PAD))
    ttk.Label(container, text="Organize RS + stitch MS assets", style="App.TLabel", foreground=COLOR_MUTED).pack(anchor="w", pady=(0, BASE_PAD * 2))

    # Destination path
    dest_root_var = tk.StringVar(value=normalize_path(settings.get("dest_root", app_config.get("default_dest_root", ""))))

    ttk.Label(container, text="Select Destination Folder (inside root):", style="App.TLabel").pack(anchor="w")
    dest_var = tk.StringVar()
    week_var = tk.StringVar(value="1")
    dest_combo_row = ttk.Frame(container, style="App.TFrame")
    dest_combo_row.pack(fill="x", pady=(8, BASE_PAD // 2))
    dest_combo = ttk.Combobox(dest_combo_row, textvariable=dest_var, state="readonly", width=50)
    dest_combo.pack(side="left", fill="x", expand=True)
    ttk.Button(dest_combo_row, text="Refresh List", style="Accent.TButton", command=lambda: refresh_all_lists()).pack(side="right", padx=(BASE_PAD, 0))

    week_row = ttk.Frame(container, style="App.TFrame")
    week_row.pack(fill="x", pady=(0, BASE_PAD))
    ttk.Label(week_row, text="What week is this? (number)", style="App.TLabel").pack(side="left")
    ttk.Entry(week_row, textvariable=week_var, width=10, style="App.TEntry").pack(side="left", padx=(BASE_PAD, 0))

    new_folder_row = ttk.Frame(container, style="App.TFrame")
    new_folder_row.pack(fill="x", pady=(0, BASE_PAD))
    new_folder_var = tk.StringVar()
    ttk.Entry(new_folder_row, textvariable=new_folder_var, width=30, style="App.TEntry").pack(side="left", fill="x", expand=True)
    ttk.Button(new_folder_row, text="Add Folder", style="Accent.TButton", command=lambda: create_new_folder()).pack(side="right", padx=(BASE_PAD, 0))

    # Settings (source folder)
    source_var = tk.StringVar(value=normalize_path(settings.get("source", app_config.get("default_source", ""))))
    ttk.Button(
        container,
        text="Settings",
        style="Accent.TButton",
        command=lambda: open_settings_window(root, source_var, dest_root_var, app_config, settings, on_save=refresh_all_lists),
    ).pack(anchor="w", pady=(0, BASE_PAD))

    # ---------- RS SECTION ----------
    rs_card = ttk.Frame(container, style="Card.TFrame", padding=BASE_PAD * 2)
    rs_card.pack(fill="x", expand=False, pady=(0, BASE_PAD * 2))

    rs_header = ttk.Frame(rs_card, style="Card.TFrame")
    rs_header.pack(fill="x", pady=(0, BASE_PAD))
    ttk.Label(rs_header, text="RS Segments (MOV + WAV copy)", style="Heading.TLabel").pack(side="left")
    ttk.Button(rs_header, text="Refresh Segments", command=lambda: refresh_all_lists(), style="TButton").pack(side="right")

    search_var = tk.StringVar()
    rs_search_row = ttk.Frame(rs_card, style="Card.TFrame")
    rs_search_row.pack(fill="x", pady=(0, BASE_PAD))
    ttk.Entry(rs_search_row, textvariable=search_var, width=40, style="App.TEntry").pack(side="left", fill="x", expand=True)
    ttk.Button(rs_search_row, text="Clear Selection", command=lambda: clear_rs_selection(), style="TButton").pack(side="right", padx=(BASE_PAD, 0))

    rs_content_row = ttk.Frame(rs_card, style="Card.TFrame")
    rs_content_row.pack(fill="both", expand=True)

    rs_frame = tk.Frame(rs_content_row, bg=COLOR_CARD)
    rs_frame.pack(side="left", fill="both", expand=True)

    rs_canvas = tk.Canvas(rs_frame, bg=COLOR_CARD, highlightthickness=0)
    rs_canvas.pack(side="left", fill="both", expand=True)

    rs_scrollbar = ttk.Scrollbar(rs_frame, orient="vertical", command=rs_canvas.yview)
    rs_scrollbar.pack(side="right", fill="y")

    rs_canvas.configure(yscrollcommand=rs_scrollbar.set)
    rs_canvas.bind("<Configure>", lambda e: rs_canvas.configure(scrollregion=rs_canvas.bbox("all")))

    list_frame = tk.Frame(rs_canvas, bg=COLOR_CARD)
    rs_canvas.create_window((0, 0), window=list_frame, anchor="nw")
    enable_mousewheel(rs_canvas, rs_canvas)
    enable_mousewheel(list_frame, rs_canvas)

    rs_selected_set = set()
    rs_checkbuttons = []
    rs_selected_display_var = tk.StringVar(value="(none)")

    rs_selected_box = ttk.Frame(rs_content_row, style="Card.TFrame", width=220)
    rs_selected_box.pack(side="right", fill="y", padx=(BASE_PAD, 0))
    ttk.Label(rs_selected_box, text="Selected RS clips:", style="Card.TLabel").pack(anchor="w")
    ttk.Label(rs_selected_box, textvariable=rs_selected_display_var, style="Card.TLabel", justify="left").pack(anchor="w", pady=(BASE_PAD // 2, 0))

    def update_rs_selected_display():
        if not rs_selected_set:
            rs_selected_display_var.set("(none)")
            return
        rs_selected_display_var.set("\n".join(sorted(rs_selected_set)))

    def load_file_list(filter_text=""):
        for widget in list_frame.winfo_children():
            widget.destroy()
        rs_checkbuttons.clear()

        source_path = source_var.get()
        if not os.path.isdir(source_path):
            tk.Label(list_frame, text="Invalid source folder", bg=COLOR_CARD, fg=COLOR_TEXT).pack()
            return

        items = [f[:-4] for f in os.listdir(source_path) if f.lower().endswith(".mov")]
        items = sorted(items)

        for item in items:
            if filter_text.lower() in item.lower():
                var = tk.BooleanVar()
                if item in rs_selected_set:
                    var.set(True)

                def on_toggle(n=item, v=var):
                    if v.get():
                        rs_selected_set.add(n)
                    else:
                        rs_selected_set.discard(n)
                    update_rs_selected_display()

                chk = tk.Checkbutton(
                    list_frame,
                    text=item,
                    variable=var,
                    command=on_toggle,
                    bg=COLOR_CARD,
                    fg=COLOR_TEXT,
                    selectcolor=COLOR_CARD,
                    activebackground=COLOR_CARD,
                    activeforeground=COLOR_TEXT,
                )
                chk.var = var
                chk.name = item
                chk.pack(anchor="w", pady=2)
                rs_checkbuttons.append(chk)

        update_rs_selected_display()

    def clear_rs_selection():
        rs_selected_set.clear()
        for chk in rs_checkbuttons:
            chk.var.set(False)
        update_rs_selected_display()

    load_file_list()
    search_var.trace_add("write", lambda *args: load_file_list(search_var.get()))

    # ---------- MS SECTION ----------
    ms_card = ttk.Frame(container, style="Card.TFrame", padding=BASE_PAD * 2)
    ms_card.pack(fill="both", expand=True)

    ttk.Label(ms_card, text="MS Segments (MP4 stitch)", style="Heading.TLabel").pack(anchor="w", pady=(0, BASE_PAD))

    ms_search_var = tk.StringVar()
    ms_search_row = ttk.Frame(ms_card, style="Card.TFrame")
    ms_search_row.pack(fill="x", pady=(0, BASE_PAD))
    ttk.Entry(ms_search_row, textvariable=ms_search_var, width=40, style="App.TEntry").pack(side="left", fill="x", expand=True)
    ttk.Button(ms_search_row, text="Clear Selection", command=lambda: clear_ms_selection(), style="TButton").pack(side="right", padx=(BASE_PAD, 0))

    ms_frame = tk.Frame(ms_card, bg=COLOR_CARD)
    ms_frame.pack(fill="both", expand=True)

    ms_canvas = tk.Canvas(ms_frame, bg=COLOR_CARD, highlightthickness=0)
    ms_canvas.pack(side="left", fill="both", expand=True)

    ms_scrollbar = ttk.Scrollbar(ms_frame, orient="vertical", command=ms_canvas.yview)
    ms_scrollbar.pack(side="right", fill="y")

    ms_canvas.configure(yscrollcommand=ms_scrollbar.set)
    ms_canvas.bind("<Configure>", lambda e: ms_canvas.configure(scrollregion=ms_canvas.bbox("all")))

    ms_list_frame = tk.Frame(ms_canvas, bg=COLOR_CARD)
    ms_canvas.create_window((0, 0), window=ms_list_frame, anchor="nw")
    enable_mousewheel(ms_canvas, ms_canvas)
    enable_mousewheel(ms_list_frame, ms_canvas)

    ms_selection_order = []
    ms_selected_set = set()
    ms_checkbuttons = []
    ms_variants = []  # each: {"name_var": StringVar, "order": list}
    ms_add_target_idx = None
    ms_order_label_var = tk.StringVar(value="Order: (none)")

    def update_ms_order_label():
        if ms_add_target_idx is not None and ms_add_target_idx < len(ms_variants):
            target_name = ms_variants[ms_add_target_idx]["name_var"].get().strip() or "MS"
            detail = " -> ".join(ms_selection_order) if ms_selection_order else "(select clips)"
            ms_order_label_var.set(f"Add to {target_name}: {detail}")
            return
        if not ms_selection_order:
            ms_order_label_var.set("Order: (none)")
        else:
            ms_order_label_var.set("Order: " + " -> ".join(ms_selection_order))

    def on_ms_toggle(name, var):
        if var.get():
            if name not in ms_selection_order:
                ms_selection_order.append(name)
                ms_selected_set.add(name)
        else:
            if name in ms_selection_order:
                ms_selection_order.remove(name)
            ms_selected_set.discard(name)
        update_ms_order_label()

    def clear_ms_selection():
        ms_selection_order.clear()
        ms_selected_set.clear()
        for chk in ms_checkbuttons:
            chk.var.set(False)
        update_ms_order_label()

    def add_ms_variant():
        nonlocal ms_add_target_idx
        if not ms_selection_order:
            messagebox.showerror("Error", "Select clips and order them before creating a version.")
            return
        name_var = tk.StringVar(value="MS")
        variant = {"name_var": name_var, "order": list(ms_selection_order)}
        ms_variants.append(variant)
        clear_ms_selection()
        ms_add_target_idx = None
        render_ms_variants()

    def duplicate_ms_variant(idx):
        if idx < 0 or idx >= len(ms_variants):
            return
        src = ms_variants[idx]
        name_copy = tk.StringVar(value=src["name_var"].get())
        copy_variant = {"name_var": name_copy, "order": list(src["order"])}
        ms_variants.insert(idx + 1, copy_variant)
        render_ms_variants()

    def delete_ms_variant(idx):
        nonlocal ms_add_target_idx
        if idx < 0 or idx >= len(ms_variants):
            return
        del ms_variants[idx]
        if ms_add_target_idx == idx:
            ms_add_target_idx = None
            clear_ms_selection()
        elif ms_add_target_idx is not None and ms_add_target_idx > idx:
            ms_add_target_idx -= 1
        render_ms_variants()

    def start_or_finish_add(idx):
        nonlocal ms_add_target_idx
        if idx < 0 or idx >= len(ms_variants):
            return
        if ms_add_target_idx == idx:
            # Finish add mode: append current selection to variant order
            if ms_selection_order:
                ms_variants[idx]["order"].extend(ms_selection_order)
            clear_ms_selection()
            ms_add_target_idx = None
            render_ms_variants()
            return
        # Switch to add mode for this variant
        clear_ms_selection()
        ms_add_target_idx = idx
        render_ms_variants()
        update_ms_order_label()

    def edit_ms_variant_order(idx):
        if idx < 0 or idx >= len(ms_variants):
            return
        variant = ms_variants[idx]

        win = tk.Toplevel(root)
        win.title("Edit Order")
        win.geometry("400x400")
        win.configure(bg=COLOR_BG)

        tk.Label(win, text="Drag to reorder; select and Remove to drop clips.", bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", padx=BASE_PAD, pady=(BASE_PAD // 2, BASE_PAD // 2))

        lb = tk.Listbox(win, selectmode="browse", activestyle="none")
        lb.pack(fill="both", expand=True, padx=BASE_PAD, pady=(0, BASE_PAD))
        for item in variant["order"]:
            lb.insert("end", item)

        drag_data = {"index": None}

        def on_start(event):
            drag_data["index"] = lb.nearest(event.y)

        def on_drag(event):
            if drag_data["index"] is None:
                return
            new_index = lb.nearest(event.y)
            if new_index == drag_data["index"]:
                return
            item_text = lb.get(drag_data["index"])
            lb.delete(drag_data["index"])
            lb.insert(new_index, item_text)
            drag_data["index"] = new_index

        lb.bind("<Button-1>", on_start)
        lb.bind("<B1-Motion>", on_drag)

        btn_row = ttk.Frame(win, style="App.TFrame")
        btn_row.pack(fill="x", padx=BASE_PAD, pady=(0, BASE_PAD))

        def remove_selected():
            sel = lb.curselection()
            if sel:
                lb.delete(sel[0])

        ttk.Button(btn_row, text="Move Up", command=lambda: move_selection(-1)).pack(side="left", padx=(0, BASE_PAD))
        ttk.Button(btn_row, text="Move Down", command=lambda: move_selection(1)).pack(side="left", padx=(0, BASE_PAD))
        ttk.Button(btn_row, text="Remove", command=remove_selected).pack(side="left")

        def move_selection(delta):
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            new_idx = idx + delta
            if new_idx < 0 or new_idx >= lb.size():
                return
            item_text = lb.get(idx)
            lb.delete(idx)
            lb.insert(new_idx, item_text)
            lb.selection_set(new_idx)

        def save_and_close():
            variant["order"] = list(lb.get(0, "end"))
            render_ms_variants()
            win.destroy()

        ttk.Button(win, text="Save", style="Accent.TButton", command=save_and_close).pack(pady=(0, BASE_PAD))

    def render_ms_variants():
        for widget in ms_variants_frame.winfo_children():
            widget.destroy()

        for idx, variant in enumerate(ms_variants):
            row = ttk.Frame(ms_variants_frame, style="Card.TFrame")
            row.pack(fill="x", pady=(0, BASE_PAD // 2))

            ttk.Label(row, text="Campus/Version:", style="Card.TLabel").pack(side="left")
            ttk.Entry(row, textvariable=variant["name_var"], width=18, style="App.TEntry").pack(side="left", padx=(BASE_PAD // 2, BASE_PAD))

            summary = " -> ".join(variant["order"]) if variant["order"] else "(none)"
            ttk.Label(row, text=summary, style="Card.TLabel", foreground=COLOR_MUTED).pack(side="left", expand=True, fill="x")

            add_btn_text = "Done" if ms_add_target_idx == idx else "Add Clips"
            ttk.Button(row, text=add_btn_text, command=lambda i=idx: start_or_finish_add(i), style="TButton").pack(side="right", padx=(BASE_PAD // 2, 0))
            ttk.Button(row, text="Edit Order", command=lambda i=idx: edit_ms_variant_order(i), style="TButton").pack(side="right", padx=(BASE_PAD // 2, 0))
            ttk.Button(row, text="Duplicate", command=lambda i=idx: duplicate_ms_variant(i), style="TButton").pack(side="right", padx=(BASE_PAD // 2, 0))
            ttk.Button(row, text="Delete", command=lambda i=idx: delete_ms_variant(i), style="TButton").pack(side="right")

    def load_ms_list(filter_text=""):
        for widget in ms_list_frame.winfo_children():
            widget.destroy()
        ms_checkbuttons.clear()

        source_path = source_var.get()
        source_ms = os.path.join(source_path, "MS")
        if not os.path.isdir(source_ms):
            tk.Label(ms_list_frame, text="Invalid MS folder (expecting /MS with MP4s)", bg=COLOR_CARD, fg=COLOR_TEXT).pack()
            return

        items = [f[:-4] for f in os.listdir(source_ms) if f.lower().endswith(".mp4")]
        items = sorted(items)

        for item in items:
            if filter_text.lower() in item.lower():
                var = tk.BooleanVar()
                if item in ms_selected_set:
                    var.set(True)
                    if item not in ms_selection_order:
                        ms_selection_order.append(item)
                chk = tk.Checkbutton(
                    ms_list_frame,
                    text=item,
                    variable=var,
                    bg=COLOR_CARD,
                    fg=COLOR_TEXT,
                    selectcolor=COLOR_CARD,
                    activebackground=COLOR_CARD,
                    activeforeground=COLOR_TEXT,
                    command=lambda n=item, v=var: on_ms_toggle(n, v),
                )
                chk.var = var
                chk.name = item
                chk.pack(anchor="w", pady=2)
                ms_checkbuttons.append(chk)
        update_ms_order_label()

    load_ms_list()
    ms_search_var.trace_add("write", lambda *args: load_ms_list(ms_search_var.get()))

    def _list_rs_items():
        source_path = source_var.get()
        if not os.path.isdir(source_path):
            return None
        return sorted([f[:-4] for f in os.listdir(source_path) if f.lower().endswith(".mov")])

    def _list_ms_items():
        source_path = source_var.get()
        source_ms = os.path.join(source_path, "MS")
        if not os.path.isdir(source_ms):
            return None
        return sorted([f[:-4] for f in os.listdir(source_ms) if f.lower().endswith(".mp4")])

    def _prune_missing_selections():
        missing_sections = []

        rs_items = _list_rs_items()
        if rs_items is not None:
            rs_available = set(rs_items)
            missing_rs = sorted(rs_selected_set - rs_available)
            if missing_rs:
                rs_selected_set.difference_update(missing_rs)
                missing_sections.append(("RS selections removed", missing_rs))

        ms_items = _list_ms_items()
        if ms_items is not None:
            ms_available = set(ms_items)
            missing_ms = [name for name in ms_selection_order if name not in ms_available]
            if missing_ms:
                ms_selection_order[:] = [name for name in ms_selection_order if name in ms_available]
                ms_selected_set.intersection_update(ms_available)
                missing_sections.append(("MS selection removed", missing_ms))

            missing_variant_lines = []
            for variant in ms_variants:
                missing_variant = [name for name in variant["order"] if name not in ms_available]
                if missing_variant:
                    variant["order"] = [name for name in variant["order"] if name in ms_available]
                    variant_name = variant["name_var"].get().strip() or "MS"
                    missing_variant_lines.append(f"{variant_name}: {', '.join(missing_variant)}")
            if missing_variant_lines:
                missing_sections.append(("MS versions missing clips", missing_variant_lines))

        return missing_sections

    def refresh_all_lists():
        missing_sections = _prune_missing_selections()
        refresh_dest_options()
        load_file_list(search_var.get())
        load_ms_list(ms_search_var.get())
        render_ms_variants()
        if missing_sections:
            lines = ["Some selected clips were missing after refresh and were removed:"]
            for title, items in missing_sections:
                if not items:
                    continue
                if title == "MS versions missing clips":
                    lines.append(f"{title}:")
                    for entry in items:
                        lines.append(f"- {entry}")
                else:
                    lines.append(f"{title}: {', '.join(items)}")
            messagebox.showwarning("Missing Clips", "\n".join(lines))

    order_row = ttk.Frame(ms_card, style="Card.TFrame")
    order_row.pack(fill="x", pady=(BASE_PAD // 2, BASE_PAD))
    ttk.Label(order_row, textvariable=ms_order_label_var, style="Card.TLabel", foreground=COLOR_MUTED).pack(side="left", fill="x", expand=True)
    ttk.Button(order_row, text="New Version", command=add_ms_variant, style="TButton").pack(side="right", padx=(BASE_PAD, 0))

    name_frame = ttk.Frame(ms_card, style="Card.TFrame")
    name_frame.pack(fill="x", pady=(0, BASE_PAD))

    ttk.Label(name_frame, text="Date (First Play Date: MMDD):", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, BASE_PAD))
    date_var = tk.StringVar(value=next_saturday_mmdd())
    ttk.Entry(name_frame, textvariable=date_var, width=12, style="App.TEntry").grid(row=0, column=1, sticky="w", padx=(0, BASE_PAD))

    ttk.Label(name_frame, text="Initials:", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=(0, BASE_PAD))
    initials_var = tk.StringVar()
    ttk.Entry(name_frame, textvariable=initials_var, width=10, style="App.TEntry").grid(row=0, column=3, sticky="w")

    ms_filename_var = tk.StringVar()

    def refresh_filename(*_):
        filename = build_ms_filename(date_var.get(), initials_var.get())
        ms_filename_var.set(filename if filename else "Main_PSA_[date]_MS_1920x1080_H.264_[initials].mp4")

    date_var.trace_add("write", refresh_filename)
    initials_var.trace_add("write", refresh_filename)
    refresh_filename()

    ttk.Label(ms_card, textvariable=ms_filename_var, style="Card.TLabel", foreground=COLOR_MUTED).pack(anchor="w", pady=(0, BASE_PAD))

    ttk.Label(ms_card, text="Versions:", style="Heading.TLabel").pack(anchor="w", pady=(0, BASE_PAD // 2))
    ms_variants_frame = ttk.Frame(ms_card, style="Card.TFrame")
    ms_variants_frame.pack(fill="x", pady=(0, BASE_PAD))

    # ---------- DESTINATION + ACTION (BOTTOM) ----------
    ttk.Label(container, text="Destination Folder (full path):", style="App.TLabel").pack(anchor="w", pady=(BASE_PAD, BASE_PAD // 2))
    dest_path_var = tk.StringVar()
    dest_row = ttk.Frame(container, style="App.TFrame")
    dest_row.pack(fill="x", pady=(0, BASE_PAD))
    dest_entry = ttk.Entry(dest_row, textvariable=dest_path_var, width=70, style="App.TEntry")
    dest_entry.pack(side="left", fill="x", expand=True, pady=0)
    action_btn = ttk.Button(dest_row, text="Copy Files", style="Accent.TButton")
    action_btn.pack(side="right", padx=(BASE_PAD, 0))

    # ---------- PROGRESS + ACTION ----------
    action_frame = ttk.Frame(container, style="App.TFrame")
    action_frame.pack(side="bottom", fill="x", expand=False, pady=(BASE_PAD, BASE_PAD))

    header_row = ttk.Frame(action_frame, style="App.TFrame")
    header_row.pack(fill="x", pady=(0, BASE_PAD // 2))
    ttk.Label(header_row, text="Status", style="Heading.TLabel").pack(side="left")

    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(action_frame, variable=progress_var, maximum=100, mode="determinate")
    progress_bar.pack(fill="x", pady=(0, BASE_PAD // 2))

    log_text = tk.Text(action_frame, height=6, bg=COLOR_LOG_BG, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, font=FONT_MONO, relief="flat", wrap="word")
    log_text.pack(fill="both", expand=True)
    log_text.config(state="disabled")

    def log(msg):
        log_text.config(state="normal")
        log_text.insert("end", msg + "\n")
        log_text.see("end")
        log_text.config(state="disabled")

    def set_progress(value):
        progress_var.set(value)
        progress_bar.update_idletasks()

    def update_full_dest():
        root_path = normalize_path(dest_root_var.get().strip())
        dest_root_var.set(root_path)
        choice = dest_var.get().strip()
        week = week_var.get().strip()
        if not (root_path and choice):
            dest_path_var.set("")
            return
        week_folder = f"Week {week}" if week else ""
        full = os.path.join(root_path, choice, week_folder) if week_folder else os.path.join(root_path, choice)
        dest_path_var.set(normalize_path(full))

    def refresh_dest_options():
        root_path = dest_root_var.get().strip()
        if not root_path or not os.path.isdir(root_path):
            dest_combo["values"] = []
            dest_var.set("")
            dest_path_var.set("")
            return
        subdirs = [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))]
        subdirs.sort()
        dest_combo["values"] = subdirs
        if subdirs:
            dest_combo.current(0)
            apply_dest_selection()
        else:
            dest_var.set("")
            dest_path_var.set("")

    def apply_dest_selection(*_):
        update_full_dest()

    def create_new_folder():
        root_path = dest_root_var.get().strip()
        name = new_folder_var.get().strip()
        if not root_path or not os.path.isdir(root_path):
            messagebox.showerror("Error", "Enter a valid destination root path first.")
            return
        if not name:
            messagebox.showerror("Error", "Enter a folder name.")
            return
        new_path = os.path.join(root_path, name)
        try:
            os.makedirs(new_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create folder: {e}")
            return
        refresh_dest_options()
        if name in dest_combo["values"]:
            dest_var.set(name)
            apply_dest_selection()
        new_folder_var.set("")
        update_full_dest()

    dest_combo.bind("<<ComboboxSelected>>", apply_dest_selection)
    week_var.trace_add("write", lambda *_: update_full_dest())

    def execute_all():
        source = source_var.get().strip()
        set_progress(0)
        log_text.config(state="normal")
        log_text.delete("1.0", "end")
        log_text.config(state="disabled")

        week_text = week_var.get().strip()
        if not week_text:
            messagebox.showerror("Error", "Please enter a week number.")
            return
        try:
            int(week_text)
        except ValueError:
            messagebox.showerror("Error", "Week must be a number.")
            return

        root_path = dest_root_var.get().strip()
        choice = dest_var.get().strip()
        if not root_path or not os.path.isdir(root_path):
            messagebox.showerror("Error", "Destination root is invalid. Update Settings.")
            return
        if not choice:
            messagebox.showerror("Error", "Select a destination folder inside the root.")
            return

        week_name = f"Week {week_text}"
        dest = os.path.join(root_path, choice, week_name)
        dest_path_var.set(dest)

        try:
            os.makedirs(dest, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create destination: {e}")
            return

        any_work = False
        rs_selected = list(rs_selected_set)
        ms_selected = list(ms_selection_order)
        ms_variant_targets = ms_variants if ms_variants else [{"name_var": tk.StringVar(value="MS"), "order": ms_selected}]

        try:
            build_folder_structure(dest)
        except Exception as e:
            messagebox.showerror("Error", f"Could not prepare destination: {e}")
            return

        # RS copy
        try:
            if rs_selected:
                any_work = True
                log("Copying RS clips and music...")
                copy_selected_files(dest, rs_selected, source)
                log("RS copy complete.")
                set_progress(40)
        except Exception as e:
            log(f"RS copy failed: {e}")
            messagebox.showerror("Error", f"RS copy failed: {e}")
            return

        # MS stitch
        try:
            if ms_variant_targets and any(v["order"] for v in ms_variant_targets):
                if not os.path.isdir(os.path.join(source, "MS")):
                    messagebox.showerror("Error", "MS folder not found under source path.")
                    return

                ffmpeg_path = ensure_ffmpeg(app_config.get("ffmpeg_names", []), app_config.get("ffmpeg_download_url", ""))
                for variant in ms_variant_targets:
                    order_list = variant["order"]
                    if not order_list:
                        continue
                    name_token = variant["name_var"].get().strip() or "MS"
                    base_filename = build_ms_filename(date_var.get(), initials_var.get())
                    if not base_filename:
                        messagebox.showerror("Error", "Enter both date and initials for the output name.")
                        return
                    filename = base_filename.replace("_MS_", f"_{name_token}_")
                    any_work = True
                    log(f"Stitching MS clips ({name_token})...")
                    output_path = stitch_ms_files(dest, order_list, source, filename, ffmpeg_path)
                    log(f"MS stitch complete: {output_path}")
                set_progress(80)
        except Exception as e:
            log(f"MS stitch failed: {e}")
            messagebox.showerror("Error", f"MS stitch failed: {e}")
            return

        if not any_work:
            messagebox.showinfo("No Action", "No RS or MS selections to process.")
            return

        set_progress(100)
        log("All operations complete.")
        messagebox.showinfo("Success", "RS copy and MS stitch complete.")

    action_btn.config(command=execute_all)
    refresh_dest_options()

    root.mainloop()


if __name__ == "__main__":
    run_gui()
