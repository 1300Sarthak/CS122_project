import tkinter as tk
from tkinter import ttk
from datetime import date
import calendar


def make_date_triple(parent, text):
    """Helper function that makes it so choosing a date in add or edit transactions is done efficiently with the dropdown."""
    frm = ttk.Frame(parent)

    def _parse_iso(s):
        try:
            y, m, d = s.split("-")
            return int(y), int(m), int(d)
        except Exception:
            today = date.today()
            return today.year, today.month, today.day

    y0, m0, d0 = _parse_iso(text.get() or "")

    months = [f"{i:02d}" for i in range(1, 13)]
    years = [str(y) for y in range(y0 - 5, y0 + 6)]

    m_var = tk.StringVar(value=f"{m0:02d}")
    d_var = tk.StringVar(value=f"{d0:02d}")
    y_var = tk.StringVar(value=str(y0))

    m_cb = ttk.Combobox(frm, textvariable=m_var, values=months, width=4, state="readonly")
    d_cb = ttk.Combobox(frm, textvariable=d_var, width=4, state="readonly")
    y_cb = ttk.Combobox(frm, textvariable=y_var, values=years, width=6, state="readonly")

    m_cb.pack(side="left")
    ttk.Label(frm, text="/").pack(side="left")
    d_cb.pack(side="left")
    ttk.Label(frm, text="/").pack(side="left")
    y_cb.pack(side="left")

    def _sync_days():
        y = int(y_var.get())
        m = int(m_var.get())
        max_day = calendar.monthrange(y, m)[1]
        vals = [f"{i:02d}" for i in range(1, max_day + 1)]
        d_cb["values"] = vals
        if int(d_var.get()) > max_day:
            d_var.set(f"{max_day:02d}")

    def _sync_iso(*_):
        text.set(f"{int(y_var.get()):04d}-{int(m_var.get()):02d}-{int(d_var.get()):02d}")

    for v in (m_var, y_var):
        v.trace_add("write", lambda *_: (_sync_days(), _sync_iso()))
    d_var.trace_add("write", _sync_iso)

    _sync_days()
    _sync_iso()

    return frm