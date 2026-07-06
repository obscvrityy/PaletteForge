"""
=========================================
PaletteForge
Version 0.1
Created by Obscurity
=========================================
"""

import customtkinter as ctk

# Import our main application window
from ui.window import PaletteForgeWindow


def main():
    """
    Starts the application.
    """

    # Set the look of the program
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Create the main window
    app = PaletteForgeWindow()

    # Start the application
    app.mainloop()


# Run the program
if __name__ == "__main__":
    main()
