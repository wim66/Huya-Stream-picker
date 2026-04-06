#!/usr/bin/env python3
"""
HUYA Stream Picker — watch multiple streams simultaneously, with availability check.

Requirements:
  Python 3 with tkinter:
    Windows:          tkinter is included by default in Python 3
    Arch Linux:       sudo pacman -S tk
    Debian/Ubuntu:    sudo apt install python3-tk
    Fedora:           sudo dnf install python3-tkinter
    openSUSE:         sudo zypper install python3-tk

  streamlink:
    Windows:          pip install streamlink
    Arch Linux:       sudo pacman -S streamlink
    Debian/Ubuntu:    pip install streamlink  (or: sudo apt install streamlink)
    Fedora:           sudo dnf install streamlink
    openSUSE:         pip install streamlink
    Any distro:       pip install --user streamlink

Usage:
  Linux/macOS:       python3 stream_picker.py
  Windows:           python stream_picker.py

  Click a table button to start the stream.
  Click again to stop it.
  Multiple streams can run at the same time.

Windows Setup Instructions:
  1. Install Python 3 from https://www.python.org/downloads/
     (make sure to check "Add Python to PATH" during installation)
  2. Open Command Prompt (cmd.exe) or PowerShell
  3. Install streamlink: pip install streamlink
  4. Navigate to the folder where stream_picker.py is located
  5. Run: python stream_picker.py
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import json

STREAMS = [
    {"label": "T1", "group": "Tables 1–4", "url": "https://m.huya.com/20072620"},
    {"label": "T2", "group": "Tables 1–4", "url": "https://m.huya.com/20072621"},
    {"label": "T3", "group": "Tables 1–4", "url": "https://m.huya.com/18501408"},
    {"label": "T4", "group": "Tables 1–4", "url": "https://m.huya.com/18501324"},
    {"label": "T5", "group": "Tables 5–8", "url": "https://m.huya.com/17455465"},
    {"label": "T6", "group": "Tables 5–8", "url": "https://m.huya.com/18501329"},
    {"label": "T7", "group": "Tables 5–8", "url": "https://m.huya.com/18501166"},
    {"label": "T8", "group": "Tables 5–8", "url": "https://m.huya.com/17611732"},
]

BG          = "#0d0f14"
PANEL       = "#13161e"
BORDER      = "#1e2330"
ACCENT      = "#00e5ff"
ACCENT2     = "#ff3d6b"
TEXT        = "#e8eaf6"
MUTED       = "#5c6380"
BTN_NORMAL  = "#181c28"
BTN_HOVER   = "#1e2540"
BTN_PLAYING = "#003d2e"
C_ONLINE    = "#00e676"
C_OFFLINE   = "#ff3d6b"
C_CHECKING  = "#ffd600"
C_PLAYING   = "#00e676"

FONT_TITLE  = ("Courier New", 22, "bold")
FONT_GROUP  = ("Courier New", 10, "bold")
FONT_BTN    = ("Courier New", 15, "bold")
FONT_SUB    = ("Courier New", 9)
FONT_STATUS = ("Courier New", 8, "bold")
FONT_LOG    = ("Courier New", 9)


def check_stream(url: str) -> bool:
    """Check stream availability without starting playback."""
    try:
        result = subprocess.run(
            ["streamlink", "--json", url],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(result.stdout)
        return bool(data.get("streams"))
    except Exception:
        return False


class StreamPicker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HUYA Stream Picker")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._btn_refs = {}
        self._build_ui()
        self._center()
        self.after(200, self._check_all)

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG, pady=18)
        hdr.pack(fill="x", padx=30)
        tk.Label(hdr, text="◈  HUYA", font=FONT_TITLE, bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(hdr, text=" STREAM PICKER", font=FONT_TITLE, bg=BG, fg=TEXT).pack(side="left")

        tk.Frame(self, bg=ACCENT, height=1).pack(fill="x", padx=30)

        grid = tk.Frame(self, bg=BG, padx=30, pady=20)
        grid.pack()

        groups = {}
        for s in STREAMS:
            groups.setdefault(s["group"], []).append(s)

        for col, (grp_name, streams) in enumerate(groups.items()):
            col_frame = tk.Frame(grid, bg=PANEL, bd=0,
                                 highlightbackground=BORDER,
                                 highlightthickness=1,
                                 padx=16, pady=16)
            col_frame.grid(row=0, column=col, padx=10)
            tk.Label(col_frame, text=grp_name.upper(),
                     font=FONT_GROUP, bg=PANEL, fg=ACCENT2, pady=6).pack()
            tk.Frame(col_frame, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))
            for s in streams:
                self._make_btn(col_frame, s)

        tk.Frame(self, bg=ACCENT, height=1).pack(fill="x", padx=30)

        ctrl = tk.Frame(self, bg=BG, padx=30, pady=8)
        ctrl.pack(fill="x")
        self.refresh_btn = tk.Label(ctrl, text="⟳  Recheck all streams",
                                    font=FONT_SUB, bg=BG, fg=ACCENT, cursor="hand2")
        self.refresh_btn.pack(side="left")
        self.refresh_btn.bind("<Button-1>", lambda _: self._check_all())

        legend = tk.Frame(ctrl, bg=BG)
        legend.pack(side="right")
        for color, text in [(C_ONLINE, "online"), (C_OFFLINE, "offline"),
                            (C_PLAYING, "playing"), (C_CHECKING, "checking")]:
            tk.Label(legend, text="●", font=FONT_SUB, bg=BG, fg=color).pack(side="left", padx=(8, 1))
            tk.Label(legend, text=text, font=FONT_SUB, bg=BG, fg=MUTED).pack(side="left")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30)

        log_frame = tk.Frame(self, bg=BG, padx=30, pady=12)
        log_frame.pack(fill="x")
        tk.Label(log_frame, text="STATUS", font=FONT_GROUP, bg=BG, fg=MUTED).pack(anchor="w")
        self.log_var = tk.StringVar(value="Checking stream availability...")
        tk.Label(log_frame, textvariable=self.log_var,
                 font=FONT_LOG, bg=BG, fg=MUTED,
                 wraplength=500, justify="left").pack(anchor="w", pady=(4, 0))

        tk.Label(self, text="streamlink  *  best  *  HUYA",
                 font=FONT_SUB, bg=BG, fg=MUTED, pady=10).pack()

    def _make_btn(self, parent, stream):
        frm = tk.Frame(parent, bg=BTN_NORMAL,
                       highlightbackground=BORDER,
                       highlightthickness=1,
                       cursor="hand2")
        frm.pack(fill="x", pady=5)

        inner = tk.Frame(frm, bg=BTN_NORMAL, padx=14, pady=10)
        inner.pack(fill="x")

        lbl_title = tk.Label(inner, text=stream["label"],
                             font=FONT_BTN, bg=BTN_NORMAL, fg=TEXT, anchor="w")
        lbl_title.pack(side="left")

        right = tk.Frame(inner, bg=BTN_NORMAL)
        right.pack(side="right")

        lbl_dot = tk.Label(right, text="●", font=FONT_STATUS, bg=BTN_NORMAL, fg=C_CHECKING)
        lbl_dot.pack(side="left", padx=(0, 4))

        lbl_status = tk.Label(right, text="checking", font=FONT_STATUS, bg=BTN_NORMAL, fg=C_CHECKING)
        lbl_status.pack(side="left")

        widgets = [frm, inner, lbl_title, right, lbl_dot, lbl_status]

        ref = {
            "frm": frm, "inner": inner,
            "lbl_title": lbl_title, "right": right,
            "lbl_dot": lbl_dot, "lbl_status": lbl_status,
            "widgets": widgets,
            "available": None,
            "playing": False,
        }
        self._btn_refs[stream["label"]] = ref

        def on_enter(_):
            if not ref["playing"]:
                for w in widgets:
                    w.configure(bg=BTN_HOVER)
                frm.configure(highlightbackground=ACCENT)

        def on_leave(_):
            if not ref["playing"]:
                for w in widgets:
                    w.configure(bg=BTN_NORMAL)
                frm.configure(highlightbackground=ACCENT2 if ref["available"] is False else BORDER)

        def on_click(_):
            if ref["available"] is False:
                self.log_var.set(f"✗  {stream['label']} is offline — please select another table.")
                return
            if ref["playing"]:
                self._stop_stream(stream["label"])
            else:
                self._launch(stream)

        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    # ── button state ──────────────────────────────────────────────────────────

    def _set_playing(self, label, playing: bool):
        ref = self._btn_refs.get(label)
        if not ref:
            return
        ref["playing"] = playing
        if playing:
            for w in ref["widgets"]:
                w.configure(bg=BTN_PLAYING)
            ref["frm"].configure(highlightbackground=C_PLAYING)
            ref["lbl_title"].configure(fg=C_PLAYING)
            ref["lbl_dot"].configure(fg=C_PLAYING)
            ref["lbl_status"].configure(text="playing", fg=C_PLAYING)
        else:
            self._apply_availability_style(label)

    def _apply_availability_style(self, label):
        ref = self._btn_refs.get(label)
        if not ref:
            return
        av = ref["available"]
        for w in ref["widgets"]:
            w.configure(bg=BTN_NORMAL)
        ref["frm"].configure(highlightbackground=ACCENT2 if av is False else BORDER)
        c = C_ONLINE if av else C_OFFLINE if av is False else C_CHECKING
        t = "online" if av else "offline" if av is False else "checking"
        ref["lbl_dot"].configure(fg=c)
        ref["lbl_status"].configure(text=t, fg=c)
        ref["lbl_title"].configure(fg=MUTED if av is False else TEXT)
        ref["frm"].configure(cursor="hand2" if av is not False else "X_cursor")

    # ── availability check ────────────────────────────────────────────────────

    def _check_all(self):
        self.log_var.set("Checking availability for all streams...")
        self.refresh_btn.configure(fg=MUTED)
        for label, ref in self._btn_refs.items():
            if not ref["playing"]:
                ref["available"] = None
                ref["lbl_dot"].configure(fg=C_CHECKING)
                ref["lbl_status"].configure(text="checking", fg=C_CHECKING)

        done = [0]
        lock = threading.Lock()

        def check_one(stream):
            ok = check_stream(stream["url"])
            with lock:
                done[0] += 1
                finished = done[0] == len(STREAMS)
            self.after(0, self._update_availability, stream["label"], ok)
            if finished:
                self.after(0, self._check_done)

        for s in STREAMS:
            threading.Thread(target=check_one, args=(s,), daemon=True).start()

    def _update_availability(self, label, available):
        ref = self._btn_refs.get(label)
        if not ref or ref["playing"]:
            return
        ref["available"] = available
        self._apply_availability_style(label)

    def _check_done(self):
        online  = [s["label"] for s in STREAMS if self._btn_refs[s["label"]]["available"]]
        offline = [s["label"] for s in STREAMS if self._btn_refs[s["label"]]["available"] is False]
        msg = (f"Done  —  {len(online)} online: {', '.join(online) or '—'}"
               f"   |   {len(offline)} offline: {', '.join(offline) or '—'}")
        self.log_var.set(msg)
        self.refresh_btn.configure(fg=ACCENT)

    # ── launch / stop ─────────────────────────────────────────────────────────

    def _stop_stream(self, label):
        ref = self._btn_refs.get(label)
        if ref and ref.get("proc"):
            try:
                ref["proc"].terminate()
            except Exception:
                pass
        self.log_var.set(f"⏹  {label} stopped.")

    def _launch(self, stream):
        label = stream["label"]
        ref = self._btn_refs[label]
        cmd = ["streamlink", "-v", f"--title={label}", stream["url"], "best"]
        self.log_var.set(f"▶  Starting: {label}  ({stream['url']})")
        self.after(0, self._set_playing, label, True)

        def run():
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True)
                ref["proc"] = proc
                for line in proc.stdout:
                    line = line.strip()
                    if line:
                        self.after(0, self.log_var.set, line[-120:])
                proc.wait()
                ref["proc"] = None
                self.after(0, self._set_playing, label, False)
                self.after(0, self.log_var.set,
                           f"⏹  Stream {label} ended (exit {proc.returncode}).")
            except FileNotFoundError:
                self.after(0, messagebox.showerror,
                           "streamlink not found",
                           "Please install streamlink:\n\n"
                           "  Arch Linux:     sudo pacman -S streamlink\n"
                           "  Debian/Ubuntu:  pip install streamlink\n"
                           "  Fedora:         sudo dnf install streamlink\n"
                           "  Any distro:     pip install --user streamlink")
                self.after(0, self._set_playing, label, False)
                self.after(0, self.log_var.set, "✗  streamlink not found.")
            except Exception as e:
                self.after(0, self._set_playing, label, False)
                self.after(0, self.log_var.set, f"✗  Error: {e}")

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = StreamPicker()
    app.mainloop()