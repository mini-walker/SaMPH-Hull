#-----------------------------------------------------------------------------------------
# Purpouse: This file is the main function of the program
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-12 
#----------------------------------------------------------------------------------------- 


import sys  # Import system-specific parameters and functions
import os   # Provide access to environment variables and filesystem helpers

# Cross-platform path utilities, useful for resource loading
from pathlib import Path  

# Import the GUI_SaMPH class from the GUI_SaMPH_Application module
from SaMPH_GUI.GUI_SaMPH import GUI_SaMPH_Application  

#-----------------------------------------------------------------------------------------
# Import PySide6 widgets for UI elements. Keeping the import list explicit makes it easy
# to see what UI components are being used in this entry point.
from PySide6.QtWidgets import ( 
    QApplication,          # Core application object that runs the Qt event loop
    QWidget,               # Base class for all UI objects; kept for potential future use
    QLabel,                # Text/image display widget
    QLineEdit,             # Single-line text input
    QPushButton, QRadioButton, QButtonGroup,  # Button widgets for user interaction
    QVBoxLayout, QHBoxLayout,                 # Layout managers for arranging widgets
    QFormLayout, QGridLayout,                 # Additional layout managers for forms and grids
    QMessageBox            # Modal dialogs for feedback and errors
)
from PySide6.QtGui import QPixmap, QFont, QIcon         # Images, fonts, and icons used by the login UI
from PySide6.QtCore import Qt, QSize, QSettings         # Core utilities such as alignment flags and persistent settings
#-----------------------------------------------------------------------------------------


#----------------------------------------------------------
# Main execution block
if __name__ == '__main__':  # Ensure this code runs only when the file is executed directly
    
    #-------------------------------------------------------------------------------------
    # Instantiate the Qt application. Passing sys.argv lets Qt parse command line flags
    # such as "-style" or "-stylesheet" that might be provided in deployment scripts.
    app = QApplication(sys.argv)

    # Create the login window. All downstream navigation should originate from this
    # window after the user is authenticated.
    window = GUI_SaMPH_Application()  # Initialize the login window object

    # Showing the window before entering the event loop ensures it is rendered
    # immediately and gives users quick visual feedback that the app launched.
    window.show()

    # Start the Qt event loop. The return code is propagated back to the OS so that
    # automation scripts can detect abnormal exits.
    sys.exit(app.exec())
#----------------------------------------------------------
