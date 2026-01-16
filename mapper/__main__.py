"""
Entry point for the Mapper application.

Run with: python -m mapper
"""

import tkinter as tk

from mapper.editor import Mapper


def main() -> None:
    """Launch the Mapper application."""
    root = tk.Tk()
    root.geometry("1024x768")
    Mapper(root)
    root.mainloop()


if __name__ == "__main__":
    main()
