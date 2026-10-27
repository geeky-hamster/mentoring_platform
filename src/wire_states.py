"""Shared state patterns figure (loading, empty, error, toast, confirm dialog, drawer) on the 520x300 wireframe canvas."""
from wirelib import *


def panel(w, x, y, pw, ph, title):
    w.rect(x, y, pw, ph, PANEL, colors.HexColor("#CBD3DE"), 0.7, r=3)
    w.rect(x, y, pw, 14, FAINT, None, r=3)
    w.bold(x + 6, y + 4, title, 6.6, NAVY)


def states(w):
    w.rect(0, 0, DW, DH, BG, None)
    pw, ph = 164, 138
    X = [8, 178, 348]
    Y = [10, 154]
    # 1 loading skeleton
    panel(w, X[0], Y[0], pw, ph, "1  Loading: skeleton")
    w.skel(X[0] + 10, Y[0] + 24, pw - 20, rows=3, rowh=9, gap=6)
    w.rect(X[0] + 10, Y[0] + 78, pw - 20, 24, SKEL, None, r=2)
    w.text(X[0] + 10, Y[0] + 112, "Grey rows keep layout stable;", 5.8, MUTE)
    w.text(X[0] + 10, Y[0] + 121, "no spinner for lists, spinner only on buttons.", 5.8, MUTE)
    # 2 empty
    panel(w, X[1], Y[0], pw, ph, "2  Empty state")
    w.empty(X[1] + 14, Y[0] + 24, pw - 28, 100, "No mentoring requests yet", "Find a mentor to send your first request.", "Find mentors")
    # 3 error banner
    panel(w, X[2], Y[0], pw, ph, "3  Error with retry")
    w.banner(X[2] + 10, Y[0] + 26, pw - 20, "Could not load requests (500).", "error", 15)
    w.button(X[2] + 10, Y[0] + 46, 50, 13, "Retry", "secondary", 6.4)
    w.text(X[2] + 10, Y[0] + 68, "Request id: req_01HZX3K8M2 (shown for support)", 5.6, MUTE)
    w.banner(X[2] + 10, Y[0] + 84, pw - 20, "Your session has expired. Sign in again.", "warn", 15)
    w.text(X[2] + 10, Y[0] + 108, "Inline banner; page content stays.", 5.8, MUTE)
    # 4 toast
    panel(w, X[0], Y[1], pw, ph, "4  Toast (non-blocking)")
    w.rect(X[0] + 14, Y[1] + 30, pw - 28, 20, colors.HexColor("#1F6B3F"), None, r=3)
    w.text(X[0] + 22, Y[1] + 37, "Request sent to Rohan Iyer", 6.4, colors.white, "DVC-B")
    w.rect(X[0] + 14, Y[1] + 58, pw - 28, 20, colors.HexColor("#8E2A37"), None, r=3)
    w.text(X[0] + 22, Y[1] + 65, "Slot no longer available (409)", 6.4, colors.white, "DVC-B")
    w.text(X[0] + 10, Y[1] + 96, "Auto-dismiss after 5 s; errors that need", 5.8, MUTE)
    w.text(X[0] + 10, Y[1] + 105, "action stay until closed. Announced to", 5.8, MUTE)
    w.text(X[0] + 10, Y[1] + 114, "screen readers (role=status / alert).", 5.8, MUTE)
    # 5 confirm / reason dialog
    panel(w, X[1], Y[1], pw, ph, "5  Confirm / reason dialog")
    w.rect(X[1] + 18, Y[1] + 24, pw - 36, 106, PANEL, STR, 0.8, r=3)
    w.bold(X[1] + 26, Y[1] + 30, "Decline this request?", 7)
    w.para(X[1] + 26, Y[1] + 42, pw - 52, "The student sees your reason and cannot ask again for 30 days.", 6)
    w.inp(X[1] + 26, Y[1] + 66, pw - 52, "Reason (optional)", "", h=22)
    w.button(X[1] + 26, Y[1] + 106, 48, 14, "Cancel", "secondary", 6.4)
    w.button(X[1] + 80, Y[1] + 106, 56, 14, "Decline", "primary", 6.4)
    # 6 drawer
    panel(w, X[2], Y[1], pw, ph, "6  Side drawer (detail)")
    w.rect(X[2] + 10, Y[1] + 22, 52, 108, FAINT, None, r=2)
    w.text(X[2] + 36, Y[1] + 72, "list", 6, MUTE, "DVC", "c")
    w.rect(X[2] + 66, Y[1] + 22, pw - 76, 108, PANEL, STR, 0.8, r=2)
    w.bold(X[2] + 72, Y[1] + 28, "Request detail", 6.6)
    w.badge(X[2] + 72, Y[1] + 42, "pending", "pending")
    w.skel(X[2] + 72, Y[1] + 58, pw - 88, rows=3, rowh=7, gap=5)
    w.button(X[2] + 72, Y[1] + 108, 50, 13, "Cancel request", "secondary", 5.8)
