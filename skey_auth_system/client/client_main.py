"""Client app entry point."""

from __future__ import annotations

import os
import sys
import tkinter as tk

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from client.client_ui import ClientUI


def main() -> None:
    """Run tkinter main loop."""
    root = tk.Tk()
    ClientUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
