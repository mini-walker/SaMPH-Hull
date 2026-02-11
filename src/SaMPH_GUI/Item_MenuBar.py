import sys  # Import system-specific parameters and functions
import os
import webbrowser

from pathlib import Path


#-----------------------------------------------------------------------------------------
# Import PyQt5 widgets for UI elements
from PySide6.QtWidgets import ( 
    QApplication, 
    QMainWindow, QTextEdit, QToolBar, QDockWidget, QListWidget, QFileDialog,
    QLabel, QTextEdit, QFileDialog, QAbstractButton, QWidget, QStackedWidget, QMenuBar,    
    QLineEdit, QSplitter, QMenu,
    QPushButton, QRadioButton, QButtonGroup, QWidgetAction,
    QVBoxLayout, QHBoxLayout, QSizePolicy,
    QFormLayout, QGridLayout, QDialog,
    QMessageBox, QStyle
)
from PySide6.QtGui import QPixmap, QFont, QIcon, QAction, QPainter   # Import classes for images, fonts, and icons
from PySide6.QtCore import Qt, QSize, QDateTime, Signal, QSettings   # Import Qt core functionalities such as alignment
#-----------------------------------------------------------------------------------------




#-----------------------------------------------------------------------------------------
# Impot the class from the local python files
from SaMPH_Utils.Utils import utils                                # Import utility function class
#-----------------------------------------------------------------------------------------




class MenuBuilder(QMenuBar):

    # Define signals for external connections
    # File menu signals
    open_file_clicked = Signal()            # Open file
    save_file_clicked = Signal()            # Save file
    
    # Edit menu signals
    undo_clicked = Signal()                 # Undo operation
    redo_clicked = Signal()                 # Redo operation
    cut_clicked = Signal()                  # Cut operation
    copy_clicked = Signal()                 # Copy operation
    paste_clicked = Signal()                # Paste operation
    
    # View menu signals (toggle visibility)
    toggle_toolbar_visibility = Signal(bool)      # Toggle toolbar visibility
    toggle_navigation_visibility = Signal(bool)      # Toggle tab dock visibility
    toggle_aichat_visibility = Signal(bool)       # Toggle AI chat visibility
    toggle_logwindow_visibility = Signal(bool)    # Toggle log window visibility
    
    # Settings menu signals
    preferences_clicked = Signal()          # Show preferences dialog
    
    # Help menu signals
    about_clicked = Signal()                # Show about dialog
    license_clicked = Signal()              # Show license dialog
    
    # Action signals with data
    action_logged = Signal(str)             # Log message signal

    # Constructor
    def __init__(self, parent=None):
        
        # Initialize the parent
        super().__init__(parent)
        
        # Store parent reference for methods that need it
        self.parent_window = parent

        # Apply menu bar styling
        self.menubar_style()

        # Initialize the menu bar
        self.create_menu_bar()
    #----------------------------------------------------------------------------------------


    #----------------------------------------------------------------------------------------
    def create_menu_bar(self):

        # MenuBuilder already inherits from QMenuBar, so use self directly
        # No need to create a new QMenuBar instance

        # ---------------------------------- Menu order --------------------------------------
        # As self is already a QMenuBar instance, we can use it directly
        file_menu       = self.addMenu("File")
        edit_menu       = self.addMenu("Edit")
        view_menu       = self.addMenu("View")
        settings_menu   = self.addMenu("Settings")
        help_menu       = self.addMenu("Help")


        #-------------------------------------------------------------------------------------
        # File menu actions configuration
        # Format: (action_name, display_name, icon_name, signal, log_message)
        file_actions_config = [
            ("open",  "Open",  "icons8-opened-folder-100.png", self.open_file_clicked, "Open file"),
            ("save",  "Save",  "icons8-save-100.png",          self.save_file_clicked, "Save file"),
            ("exit",  "Exit",  "icons8-close-100.png",         None,                   "Exit application"),
        ]
        
        # Create File menu actions using loop
        for action_name, display_name, icon_name, signal, log_msg in file_actions_config:
            # Create action
            action = QAction(
                QIcon(utils.local_resource_path(f"SaMPH_Images/Win11-Icons/{icon_name}")),
                display_name,
                self
            )
            
            # Connect to signal or internal method
            if signal is not None:
                # Connect to signal for external handling
                # Use lambda with default parameter to capture current signal (avoid closure issue)
                action.triggered.connect(lambda checked=False, sig=signal: sig.emit())
                # Also emit log message
                if log_msg:
                    action.triggered.connect(lambda checked=False, msg=log_msg: self.action_logged.emit(msg))
            else:
                # Exit action - connect to internal close method
                action.triggered.connect(self.close_application)
                if log_msg:
                    action.triggered.connect(lambda msg=log_msg: self.action_logged.emit(msg))
            
            # Store action as instance attribute
            setattr(self, f"{action_name}_action", action)
        
        # Add actions to File menu
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        #-------------------------------------------------------------------------------------


        #-------------------------------------------------------------------------------------
        # Edit menu actions configuration
        # Format: (action_name, display_name, icon_name, signal)
        edit_actions_config = [
            ("undo",  "Undo",  "icons8-undo-100.png",     self.undo_clicked),
            ("redo",  "Redo",  "icons8-redo-100.png",     self.redo_clicked),
            ("cut",   "Cut",   "icons8-cut-100.png",      self.cut_clicked),
            ("copy",  "Copy",  "icons8-copy-100.png",     self.copy_clicked),
            ("paste", "Paste", "icons8-transfer-100.png", self.paste_clicked),
        ]
        
        # Create Edit menu actions using loop
        for action_name, display_name, icon_name, signal in edit_actions_config:
            # Create action
            action = QAction(
                QIcon(utils.local_resource_path(f"SaMPH_Images/Win11-Icons/{icon_name}")),
                display_name,
                self
            )
            
            # Connect to signal for external handling
            action.triggered.connect(signal.emit)
            
            # Store action as instance attribute
            setattr(self, f"{action_name}_action", action)
        
        # Add actions to Edit menu
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        #-------------------------------------------------------------------------------------



        #------------------------------------ Settings & Help --------------------------------
        # Add actions to Settings menu
        self.pref_action = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-gear-100.png")),
            "Preferences",
            self
        )
        self.pref_action.triggered.connect(self.preferences_clicked.emit)
        settings_menu.addAction(self.pref_action)

        # Add actions to Help menu
        self.about_action = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-about-100.png")),
            "About",
            self
        )
        self.about_action.triggered.connect(self.about_clicked.emit)
        help_menu.addAction(self.about_action)

        self.license_action = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-license-100.png")),
            "License",
            self
        )
        self.license_action.triggered.connect(self.license_clicked.emit)
        help_menu.addAction(self.license_action)
        #-------------------------------------------------------------------------------------



        #-------------------------------------------------------------------------------------
        # View menu - Toggle visibility of UI components
        # Format: (action_name, display_name, signal, default_visible)
        view_actions_config = [
            ("toolbar",    "Toolbar",      self.toggle_toolbar_visibility,    True),
            ("navigation", "Navigation",   self.toggle_navigation_visibility,    True),
            ("aichat",     "AI Assistant", self.toggle_aichat_visibility,     True),
            ("logwindow",  "Log Window",   self.toggle_logwindow_visibility,  True),
        ]
        
        # Create View menu actions using loop
        for action_name, display_name, signal, default_visible in view_actions_config:
            # Create checkable action
            action = QAction(display_name, self)
            action.setCheckable(True)
            action.setChecked(default_visible)
            
            # Set initial icon if checked
            if default_visible:
                action.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            
            # Connect toggled signal (toggled signal passes bool directly)
            action.toggled.connect(signal.emit)
            
            # Update icon when toggled
            # Use lambda to capture the specific action instance
            action.toggled.connect(lambda checked, act=action: 
                act.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton) if checked else QIcon())
            )
            
            view_menu.addAction(action)
            setattr(self, f"toggle_{action_name}_action", action)
        #-------------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------
    # Internal methods (implemented within MenuBuilder)
    def close_application(self):
        """Close the application"""
        if self.parent_window:
            self.parent_window.close()
    #-----------------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------
    def update_ui_texts(self, lang_manager):
        
        """Update all menu texts based on current language."""
        if not lang_manager:
            return

        print("[INFO] Updating menu language texts...")
        
        # Update menu titles
        menus = self.findChildren(QMenu)
        for menu in menus:
            title = menu.title()
            if title in ["File", "文件"]:
                menu.setTitle(lang_manager.get_text("File"))
            elif title in ["Edit", "编辑"]:
                menu.setTitle(lang_manager.get_text("Edit"))
            elif title in ["View", "视图"]:
                menu.setTitle(lang_manager.get_text("View"))
            elif title in ["Settings", "设置"]:
                menu.setTitle(lang_manager.get_text("Settings"))
            elif title in ["Help", "帮助"]:
                menu.setTitle(lang_manager.get_text("Help"))
        
        # Update File menu actions
        if hasattr(self, 'open_action'):
            self.open_action.setText(lang_manager.get_text("Open"))
        if hasattr(self, 'save_action'):
            self.save_action.setText(lang_manager.get_text("Save"))
        if hasattr(self, 'exit_action'):
            self.exit_action.setText(lang_manager.get_text("Exit"))
        
        # Update Edit menu actions
        if hasattr(self, 'undo_action'):
            self.undo_action.setText(lang_manager.get_text("Undo"))
        if hasattr(self, 'redo_action'):
            self.redo_action.setText(lang_manager.get_text("Redo"))
        if hasattr(self, 'cut_action'):
            self.cut_action.setText(lang_manager.get_text("Cut"))
        if hasattr(self, 'copy_action'):
            self.copy_action.setText(lang_manager.get_text("Copy"))
        if hasattr(self, 'paste_action'):
            self.paste_action.setText(lang_manager.get_text("Paste"))
        
        # Update View menu actions
        if hasattr(self, 'toggle_toolbar_action'):
            self.toggle_toolbar_action.setText(lang_manager.get_text("Toolbar"))
        if hasattr(self, 'toggle_navigation_action'):
            self.toggle_navigation_action.setText(lang_manager.get_text("Navigation"))
        if hasattr(self, 'toggle_aichat_action'):
            self.toggle_aichat_action.setText(lang_manager.get_text("AI Assistant"))
        if hasattr(self, 'toggle_logwindow_action'):
            self.toggle_logwindow_action.setText(lang_manager.get_text("Log Window"))
        
        # Update Settings menu actions
        if hasattr(self, 'pref_action'):
            self.pref_action.setText(lang_manager.get_text("Preferences"))
        
        # Update Help menu actions
        if hasattr(self, 'about_action'):
            self.about_action.setText(lang_manager.get_text("About"))
        if hasattr(self, 'license_action'):
            self.license_action.setText(lang_manager.get_text("License"))
    #-----------------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------
    def update_aichat_toggle_state(self, checked):
        """
        Update the state of the AI Assistant toggle action.
        This is called when the panel visibility changes from other sources (toolbar, context menu).
        """
        if hasattr(self, 'toggle_aichat_action'):
            # Block signals to prevent re-triggering the toggle operation
            # Although the operation handler has a check, blocking signals is safer/cleaner for UI updates
            self.toggle_aichat_action.blockSignals(True)
            self.toggle_aichat_action.setChecked(checked)
            # Manually update icon since we blocked signals (and the lambda won't run)
            self.toggle_aichat_action.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton) if checked else QIcon())
            self.toggle_aichat_action.blockSignals(False)
    #-----------------------------------------------------------------------------------------



    #-----------------------------------------------------------------------------------------
    def menubar_style(self):

        """Apply professional, minimalist styling for scientific software"""
    
        self.setStyleSheet("""
            
            /* ===================== Menu Bar Styling ===================== */
            QMenuBar {
                background-color: #fafafa;           /* Very light gray background */
                border-bottom: 1px solid #d0d0d0;    /* Subtle border */
                padding: 2px 4px;
                font-size: 13px;
            }
            
            /* Menu bar items (File, Edit, etc.) */
            QMenuBar::item {
                padding: 4px 12px;                    /* Padding: 6px top/bottom, 12px left/right */
                background: transparent;
                color: #424242;                      /* Dark gray text */
                border-radius: 2px;                  /* Minimal rounding */
                margin: 1px 2px;
            }
            
            /* Hover effect - subtle and professional */
            QMenuBar::item:selected {
                background-color: #e8e8e8;           /* Light gray hover */
                color: #212121;                      /* Slightly darker text */
                border: 1px solid #d0d0d0;           /* Subtle border */
            }
            
            /* Pressed state */
            QMenuBar::item:pressed {
                background-color: #d8d8d8;           /* Slightly darker gray */
                color: #000000;
            }
            
            /* ===================== Drop-down Menu Styling ===================== */
            QMenu {
                background-color: #ffffff;           /* Clean white background */
                border: 1px solid #c0c0c0;          /* Gray border */
                border-radius: 3px;
                padding: 3px 0px;
                font-size: 13px;
            }
            
            /* Menu items in drop-down */
            QMenu::item {
                padding: 5px 30px 5px 26px;        /* Padding: top 5px, bottom 5px, left 30px, right 26px */
                background-color: transparent;
                color: #424242;                    /* Dark gray text */
                margin: 1px 3px;
            }
            
            /* Menu item icon spacing */
            QMenu::icon {
                padding-left: 6px;
            }
            
            /* Hover effect for menu items - minimal */
            QMenu::item:selected {
                background-color: #f0f0f0;           /* Very light gray */
                color: #212121;
                border-left: 2px solid #757575;      /* Subtle gray accent */
            }
            
            /* Disabled menu items */
            QMenu::item:disabled {
                color: #bdbdbd;                      /* Light gray for disabled */
                background-color: transparent;
            }
            
            /* Menu separator */
            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 3px 6px;
            }
            
            /* Checkable menu items (View menu) - professional look */
            QMenu::item:checked {
                background-color: #eeeeee;           /* Light gray background */
                color: #424242;
                font-weight: normal;                 /* No bold */
            }
            
            /* Removed custom indicator styling to use standard icon */
        """)
    #-----------------------------------------------------------------------------------------
