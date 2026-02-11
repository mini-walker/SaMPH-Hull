import sys  # Import system-specific parameters and functions
import os

from pathlib import Path


#-----------------------------------------------------------------------------------------
# Import PyQt5 widgets for UI elements
from PySide6.QtWidgets import ( 
    QApplication, 
    QMainWindow, QTextEdit, QToolBar, QDockWidget, QListWidget, QFileDialog,
    QLabel, QTextEdit, QFileDialog, QAbstractButton, QWidget, QStackedWidget, QTabWidget,    
    QLineEdit, QSplitter, 
    QPushButton, QRadioButton, QSizePolicy,
    QVBoxLayout, QHBoxLayout,
    QFormLayout, QGridLayout,
    QMessageBox
)
from PySide6.QtGui import QPixmap, QFont, QIcon, QAction, QPainter              # Import classes for images, fonts, and icons
from PySide6.QtCore import Qt, QSize, QDateTime, Signal                         # Import Qt core functionalities such as alignment
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Impot the class from the local python files
from SaMPH_Utils.Utils import utils                                # Import utility function class

# from Home_Page import HomePage
# from Input_Data_Page import InputPageContinuous, InputPageDiscrete
# from Log_Windows import LogWindow

#-----------------------------------------------------------------------------------------
class ToolbarBuilder(QToolBar):

    # Define signals for external connections
    search_requested = Signal(str)                    # Search requested signal (str)   
    toggle_home_requested = Signal(bool)              # Toggle home requested signal
    toggle_left_requested = Signal(bool)              # Toggle left requested signal (bool)
    toggle_log_requested = Signal(bool)               # Toggle log requested signal (bool)
    toggle_right_requested = Signal(bool)             # Toggle right requested signal (bool)
    calculate_requested = Signal(bool)                # Calculate requested signal (bool: True=start, False=stop)
    clear_requested = Signal()                        # Clear requested signal
    output_report_requested = Signal()                # Output report requested signal
    
    """
    Create a toolbar with common actions (VS Code style)
    self must be of type QMainWindow; self is typically your main window instance.
    Return the created QToolBar instance.
    """

    # Initialize the toolbar
    def __init__(self, parent):

        super().__init__(parent)  

        # Get the main window instance which has been created before tool bar creation
        self.main_window = parent  

        self.toolbar_style()

        self.create_tool_bar()
    #-------------------------------------------------------------------------------------



    #-------------------------------------------------------------------------------------
    def create_tool_bar(self):

        # Self is the toolbar instance created in the constructor, 
        # you can use it to add actions to the toolbar directly.
        self.addAction(self.main_window.menu_bar.open_action)
        self.addAction(self.main_window.menu_bar.save_action)

        self.addSeparator()

        self.addAction(self.main_window.menu_bar.undo_action)
        self.addAction(self.main_window.menu_bar.redo_action)    
        self.addAction(self.main_window.menu_bar.cut_action)
        self.addAction(self.main_window.menu_bar.copy_action)
        self.addAction(self.main_window.menu_bar.paste_action)

        self.addSeparator()


        # --------------------------------------------------------------------------------
        # Panel Toggle Actions (VS Code style)
        # Toggle Central home page
        self.action_toggle_home = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-home.svg")), 
            "Toggle Home", 
            self
        )
        self.action_toggle_home.setCheckable(True)
        self.action_toggle_home.setChecked(True) # Default is visible
        self.action_toggle_home.triggered.connect(self.emit_toggle_home)
        self.addAction(self.action_toggle_home)

        # Toggle Left Panel
        self.action_toggle_left = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-dashboard-layout-100.png")), 
            "Toggle Navigation", 
            self
        )
        self.action_toggle_left.setCheckable(True)
        self.action_toggle_left.setChecked(True) # Default is visible
        self.action_toggle_left.triggered.connect(self.emit_toggle_left)
        self.addAction(self.action_toggle_left)
        

        # Toggle Log Window
        self.action_toggle_log = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-log-100.png")), 
            "Toggle Log", 
            self
        )
        self.action_toggle_log.setCheckable(True)
        self.action_toggle_log.setChecked(True) # Default is visible
        self.action_toggle_log.triggered.connect(self.emit_toggle_log)
        self.addAction(self.action_toggle_log)
        
        # Toggle Right Panel
        self.action_toggle_right = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-claude-ai-100.png")), 
            "Toggle AI Chat", 
            self
        )
        self.action_toggle_right.setCheckable(True)
        self.action_toggle_right.setChecked(True) # Default is visible
        self.action_toggle_right.triggered.connect(self.emit_toggle_right)
        self.addAction(self.action_toggle_right)

        # Connect signals from main window to update checked state
        self.main_window.home_panel_visible_changed.connect(self.update_home_toggle_state)
        self.main_window.left_panel_visible_changed.connect(self.update_left_toggle_state)
        self.main_window.log_window_visible_changed.connect(self.update_log_toggle_state)
        self.main_window.right_panel_visible_changed.connect(self.update_right_toggle_state)
        # --------------------------------------------------------------------------------

        self.addSeparator()

        # --------------------------------------------------------------------------------
        # Calculation Controls
        # Calculate/Stop button (toggleable)
        self.action_calculate = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-play-100.png")), 
            "Calculate", 
            self
        )
        self.action_calculate.setCheckable(True)
        self.action_calculate.setChecked(False)  # Default is not calculating
        self.action_calculate.triggered.connect(self.emit_calculate)
        self.addAction(self.action_calculate)
        
        # Clear button
        self.action_clear = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-clear-100.png")), 
            "Clear", 
            self
        )
        self.action_clear.triggered.connect(self.emit_clear)
        self.addAction(self.action_clear)


        # Output report buttion
        self.action_output_report = QAction(
            QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-pdf-100.png")), 
            "Output Report", 
            self
        )
        self.action_output_report.triggered.connect(self.emit_output_report)
        self.addAction(self.action_output_report)
        # --------------------------------------------------------------------------------

        self.addSeparator()

        # Check the status of the action and set the icon accordingly
        self.addAction(self.main_window.menu_bar.pref_action)

        

        # Add spacer to push Search button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)


        # --------------------------------------------------------------------------------
        # Add Search input and button (currently commented out)
        self.search_container = QWidget(self)
        self.search_container.setFixedWidth(338)  # Adjusted width
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input (VS Code-like)
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search by Google ...")  # VS Code-like placeholder
        self.search_input.setFixedWidth(300)  # Adjusted width
        # self.search_input.setFixedHeight(28)  # Slightly taller
        self.search_input.setClearButtonEnabled(True) # Enable built-in clear button
        
        # Add magnifying glass icon on the left
        self.search_input.addAction(
            QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-Google-100.png")),
            QLineEdit.LeadingPosition
        )
        
        self.search_input.returnPressed.connect(self.emit_search_signal)

        # Search button
        self.search_button = QPushButton()
        self.search_button.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-website-100.png")))
        self.search_button.setIconSize(QSize(26, 26))
        self.search_button.setFixedWidth(28)   # Compact width for icon-only button
        self.search_button.setFixedHeight(28)  # Match QLineEdit height
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
        """)
        self.search_button.clicked.connect(self.emit_search_signal)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        self.addWidget(self.search_container)

    #-------------------------------------------------------------------------------------


    #-------------------------------------------------------------------------------------

    def update_home_toggle_state(self, checked):
        """Update home toggle button state and icon."""
        self.action_toggle_home.setChecked(checked)
        self.update_home_icon(checked)

    def update_left_toggle_state(self, checked):
        """Update left panel toggle button state and icon."""
        self.action_toggle_left.setChecked(checked)
        self.update_left_icon(checked)

    def update_log_toggle_state(self, checked):
        """Update log window toggle button state and icon."""
        self.action_toggle_log.setChecked(checked)
        self.update_log_icon(checked)

    def update_right_toggle_state(self, checked):
        """Update right panel toggle button state and icon."""
        self.action_toggle_right.setChecked(checked)
        self.update_right_icon(checked)

    #-------------------------------------------------------------------------------------
    # Icon update helpers
    def update_home_icon(self, checked):
        icon_path = "SaMPH_Images/WIN11-Icons/icons8-home.svg" if checked else "SaMPH_Images/WIN11-Icons/icons8-home-deactive.svg"
        self.action_toggle_home.setIcon(QIcon(utils.local_resource_path(icon_path)))

    def update_left_icon(self, checked):
        icon_path = "SaMPH_Images/WIN11-Icons/icons8-dashboard-layout-100.png" if checked else "SaMPH_Images/WIN11-Icons/icons8-dashboard-layout-deactive-100.png"
        self.action_toggle_left.setIcon(QIcon(utils.local_resource_path(icon_path)))

    def update_log_icon(self, checked):
        icon_path = "SaMPH_Images/WIN11-Icons/icons8-log-100.png" if checked else "SaMPH_Images/WIN11-Icons/icons8-log-deactive-100.png"
        self.action_toggle_log.setIcon(QIcon(utils.local_resource_path(icon_path)))

    def update_right_icon(self, checked):
        icon_path = "SaMPH_Images/WIN11-Icons/icons8-claude-ai-100.png" if checked else "SaMPH_Images/WIN11-Icons/icons8-claude-ai-deactive-100.png"
        self.action_toggle_right.setIcon(QIcon(utils.local_resource_path(icon_path)))

    #-------------------------------------------------------------------------------------
    # Emit methods (called by button click)
    def emit_toggle_home(self, checked):
        """Emit request to toggle the central home view."""
        self.update_home_icon(checked)
        self.toggle_home_requested.emit(bool(checked))

    def emit_toggle_left(self, checked):
        """Emit request to toggle the left navigation panel."""
        self.update_left_icon(checked)
        self.toggle_left_requested.emit(bool(checked))

    def emit_toggle_log(self, checked):
        """Emit request to toggle the log window."""
        self.update_log_icon(checked)
        self.toggle_log_requested.emit(bool(checked))

    def emit_toggle_right(self, checked):
        """Emit request to toggle the right AI chat panel."""
        self.update_right_icon(checked)
        self.toggle_right_requested.emit(bool(checked))
    
    def emit_calculate(self, checked):
        """Emit request to start/stop calculation."""
        # UI state is now managed by Computing_Operations
        self.calculate_requested.emit(bool(checked))
    
    def emit_clear(self):
        """Emit request to clear input fields."""
        self.clear_requested.emit()
    
    def emit_output_report(self):
        """Emit request to generate report."""
        self.output_report_requested.emit()
    #-------------------------------------------------------------------------------------


    #-------------------------------------------------------------------------------------
    def emit_search_signal(self):
        """Emit a search request signal instead of invoking the handler directly."""
        query = self.search_input.text().strip() if hasattr(self, "search_input") else ""
        self.search_requested.emit(query)
    #-------------------------------------------------------------------------------------



























    #-------------------------------------------------------------------------------------
    def toolbar_style(self):

        # Set the toolbar properties
        self.setMovable(False)
        # self.setMaximumHeight(32)
        self.setIconSize(QSize(24, 24))
        self.setStyleSheet("""
            QToolBar {
                background-color: #fafafa;
                border-bottom: 1px solid #d0d0d0;
                spacing: 6px;
                padding: 0px 2px;      /* 2px for spacing */
            }
            
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 2px;      /* 2px for spacing */
                margin: 0px 2px;   /* margin between buttons: 2px left and right, 0px top and bottom */
            }
            
            QToolButton:hover {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
            }
            
            QToolButton:pressed {
                background-color: #d8d8d8;
                border: 1px solid #c0c0c0;
            }
            
            /* Search Input Styling */
            QLineEdit {
                padding: 0px 8px;
                padding-left: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #ffffff;
                color: #333333;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border: 1px solid #888888;
            }
            
            /* Search Button Styling */
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
        """)
    #-------------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------------
    def update_ui_texts(self, lang_manager):
        """Update all toolbar texts based on current language."""
        if not lang_manager:
            return
        
        # Update search placeholder
        if hasattr(self, 'search_input'):
            self.search_input.setPlaceholderText(lang_manager.get_text("Search by Google"))
        
        # Update toggle button tooltips
        if hasattr(self, 'action_toggle_home'):
            self.action_toggle_home.setToolTip(lang_manager.get_text("Toggle Home"))
        if hasattr(self, 'action_toggle_left'):
            self.action_toggle_left.setToolTip(lang_manager.get_text("Toggle Navigation"))
        if hasattr(self, 'action_toggle_log'):
            self.action_toggle_log.setToolTip(lang_manager.get_text("Toggle Log"))
        if hasattr(self, 'action_toggle_right'):
            self.action_toggle_right.setToolTip(lang_manager.get_text("Toggle AI Chat"))
        
        # Update calculate button tooltip
        if hasattr(self, 'action_calculate'):
            self.action_calculate.setToolTip(lang_manager.get_text("Calculate"))
        
        # Update clear button tooltip
        if hasattr(self, 'action_clear'):
            self.action_clear.setToolTip(lang_manager.get_text("Clear"))

        # Update output report button tooltip
        if hasattr(self, 'action_output_report'):
            self.action_output_report.setToolTip(lang_manager.get_text("Output Report"))

        # Update search button tooltip
        if hasattr(self, 'search_button'):
            self.search_button.setToolTip(lang_manager.get_text("Search"))
    #-------------------------------------------------------------------------------------

