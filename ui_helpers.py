def enable_mousewheel(widget, target):
    def _on_mousewheel(event):
        delta = 0
        if event.num == 4:
            delta = -120
        elif event.num == 5:
            delta = 120
        else:
            delta = -1 * int(event.delta)
        target.yview_scroll(int(delta / 120), "units")

    def _bind(_):
        widget.bind_all("<MouseWheel>", _on_mousewheel)
        widget.bind_all("<Button-4>", _on_mousewheel)
        widget.bind_all("<Button-5>", _on_mousewheel)

    def _unbind(_):
        widget.unbind_all("<MouseWheel>")
        widget.unbind_all("<Button-4>")
        widget.unbind_all("<Button-5>")

    widget.bind("<Enter>", _bind)
    widget.bind("<Leave>", _unbind)
