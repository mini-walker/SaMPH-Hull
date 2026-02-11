#--------------------------------------------------------------
# This file is used to create the main window of SaMPH
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-10-27  
#-------------------------------------------------------------- 

import sys  # Import system-specific parameters and functions
import os
import webbrowser
import re

from pathlib import Path


#-----------------------------------------------------------------------------------------
# Import PyQt5 widgets for UI elements
from PySide6.QtWidgets import ( 
    QApplication, 
    QMainWindow, QTextEdit, QToolBar, QDockWidget, QListWidget, QFileDialog,
    QLabel, QTextEdit, QFileDialog, QAbstractButton, QWidget, QStackedWidget, QTabWidget,    
    QLineEdit, QSplitter, 
    QPushButton, QRadioButton, QButtonGroup,
    QVBoxLayout, QHBoxLayout, QMdiArea, QMdiSubWindow,
    QFormLayout, QGridLayout,
    QMessageBox
)
from PySide6.QtGui import QPixmap, QFont, QIcon, QAction, QPainter              # Import classes for images, fonts, and icons
from PySide6.QtCore import Qt, QSize, QDateTime, Signal, QSettings, QThread, QTimer   # Import Qt core functionalities such as alignment
#--------------------------------------------------------------


# Add the parent directory to the Python path for debugging (independent execution)
# *** Sometimes, the Vscode will load wrong python interpreter, 
# *** if the code doesn't run, try to change the interpreter.
if __name__ == "__main__": 

    print("Debug mode!")   

    # Get project root folder (src directory)
    # __file__ = .../src/SaMPH_GUI/GUI_SaMPH.py
    # dirname -> .../src/SaMPH_GUI
    # dirname -> .../src
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if project_root not in sys.path: sys.path.insert(0, project_root)


#--------------------------------------------------------------
# Impot the class from the local python files
# from .Page_Log import LogWidget
# from .Page_Home import HomePage
# from .Page_Input import InputPageContinuous, InputPageDiscrete
# from .Page_Result import ResultPage
# from .Dock_Navigation import NavigationDock
# from .Dock_AI_API import AI_API
# from .Bar_Menu import MenuBuilder                # After you created navigation_dock, tab_dock, log_dock...
# from .Bar_Tool import create_tool_bar            # Some menu actions are show in the tool bar
# from .Preference import PreferenceWindow


from SaMPH_Utils.Utils import utils                               # Import utility function class

from SaMPH_Operations.Operation_MainWindow  import MainWindow_Operations
from SaMPH_Operations.Operation_InputPage   import InputPage_Operations
from SaMPH_Operations.Operation_Computing   import Computing_Operations
from SaMPH_Operations.Operation_ResultPage  import ResultPage_Operations
from SaMPH_Operations.Operation_Setting     import SettingPage_Operations
from SaMPH_Operations.Operation_GenerateReport import ReportGenerator_Operations

from SaMPH_AI.Operation_Chat_Controller import Operation_Chat_Controller

from SaMPH_GUI.Theme_SaMPH import Theme_SaMPH
from SaMPH_GUI.Language_Manager import Language_Manager

# Import UI Components
from SaMPH_GUI.Item_MenuBar import MenuBuilder
from SaMPH_GUI.Item_ToolBar import ToolbarBuilder
from SaMPH_GUI.Item_StatusBar import StatusBarBuilder
from SaMPH_GUI.Item_Left_SidePanel import Left_Side_Panel
from SaMPH_GUI.Item_Right_AIChat import Right_AIChat_Panel
from SaMPH_GUI.Item_Central_TabWidget import Central_Tab_Widget
from SaMPH_GUI.Item_Central_LogWindow import Central_Log_Widget
from SaMPH_GUI.Item_SettingPage import Setting_Window

#--------------------------------------------------------------


#==============================================================
class GUI_SaMPH_Application(QMainWindow):     # Define the login window class, inheriting from QMainWindow

    # Singal from the main window
    home_panel_visible_changed = Signal(bool)
    left_panel_visible_changed = Signal(bool)
    right_panel_visible_changed = Signal(bool)
    log_window_visible_changed = Signal(bool)

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Constructor
    def __init__(self, parent=None):

        super().__init__(parent)        # Call the parent class constructor, makesure the parent class is QMainWindow
        
        # ========================== Initialize UI ==================================
        # Create the main window
        # Only functions defined in the present class can use self.function_name()
        self.init_styles()
        # ===========================================================================


        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Language manager
        self.language_manager = Language_Manager()               # The gobal language manager

        # Initialize the main window
        self.init_main_window_ui()
        
        # ========================= Initialize Functional Modules ====================
        # Initialize other pages and modules
        # Pass self as a parent so that the modules can access the main window
        # Save the created setting page in self.setting_page
        # Use self.setting_page.function_name() to access all items in the setting page
        self.setting_page = Setting_Window(self)


        # Initialize operations handler
        self.operations_main_window  = MainWindow_Operations(self)
        self.operations_input_page   = InputPage_Operations(self)
        self.operations_computing    = Computing_Operations(self)
        self.operations_result_page  = ResultPage_Operations(self)
        self.operations_setting_page = SettingPage_Operations(self)
        self.operations_report_gen   = ReportGenerator_Operations(self)

        # ========================= Load & Apply Settings ============================
        # Load the settings from the configuration file
        self.load_settings_on_startup()

        # Initialize operation modules after loading settings so that the chat controller can access them
        self.operation_chat = Operation_Chat_Controller(self)


        # =============== Initialize Debounce Timer for Drag ======================
        # Ref: Implementation in AIchat_Combo_V3
        # 100ms delay balances responsiveness and performance
        self.drag_debounce_timer = QTimer(self)
        self.drag_debounce_timer.setSingleShot(True)
        self.drag_debounce_timer.setInterval(100)  # 100ms debounce
        self.drag_debounce_timer.timeout.connect(self.update_input_after_drag)
        # ==========================================================================

        # Connect signals and slots
        self.init_signal_connections()

        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        



    #---------------------------------------------------------------------------------
    # Load the settings, if they exist
    # Otherwise, create default settings
    def load_settings_on_startup(self):
        """
        Check if settings.ini exists; if yes, load it.
        Otherwise, create one with default values.
        Includes migration logic for old 'Advanced' settings and adds new fields.
        """
        usr_folder = utils.get_global_usr_dir()
        settings_path = usr_folder / "Settings/settings.ini"
        
        # Create QSettings object (even if the file does not exist, Qt will create it upon writing)
        settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

        #---------------------------------------------------------------------------------
        # Helper function: Set default values if a key does not exist
        # This handles both "fresh installations" and "upgrades from older versions" (missing new fields)
        def check_and_set_default(key, default_value):
            if not settings.contains(key):
                settings.setValue(key, default_value)

        #---------------------------------------------------------------------------------
        # Check if this is the first run (settings file does not exist)
        is_first_run = not settings_path.exists()
        
        if is_first_run:
            print("[INFO] No settings.ini found. Creating default settings...")

        #---------------------------------------------------------------------------------
        # --- Font & Appearance ---
        # Default font supports Chinese to prevent garbled text
        check_and_set_default("Font/type", "Microsoft YaHei") 
        check_and_set_default("Font/size", 10)
        
        check_and_set_default("Appearance/theme", "Light")
        check_and_set_default("Appearance/toolbar_icons", True)
        check_and_set_default("Appearance/animations", True)
        check_and_set_default("Appearance/left_panel_width", 320)
        check_and_set_default("Appearance/right_panel_width", 400)
        
        # Background image path (default is empty)
        check_and_set_default("Appearance/central_background", "") 

        #---------------------------------------------------------------------------------
        # --- Language ---
        check_and_set_default("Language/type", "English")

        #---------------------------------------------------------------------------------
        # --- Search ---
        check_and_set_default("Search/Baidu", True)
        check_and_set_default("Search/Google", False)

        #---------------------------------------------------------------------------------
        # --- Result Chart ---
        check_and_set_default("ResultChart/curve_style", "Solid")
        check_and_set_default("ResultChart/curve_color", "#1F4788")
        check_and_set_default("ResultChart/curve_width", "2.0")
        check_and_set_default("ResultChart/scatter_style", "Circle")
        check_and_set_default("ResultChart/axis_style", "Solid")
        check_and_set_default("ResultChart/grid_style", "Solid")
        check_and_set_default("ResultChart/bg_color", "#FAFAFA")

        #---------------------------------------------------------------------------------
        # --- AI Settings & Migration ---
        # 1. Attempt to migrate old data (Advanced -> AI)
        old_key = settings.value("Advanced/api_key", "")
        if old_key and not settings.contains("AI/api_key"):
            print("[INFO] Migrating old API Key to new AI settings structure...")
            settings.setValue("AI/api_key", old_key)
            settings.remove("Advanced") # Clean up old group
        
        #---------------------------------------------------------------------------------
        # 2. Get the AI engine list from usr/account.json file
        usr_dir = utils.get_global_usr_dir()
        account_file = usr_dir / "Settings/account.json"
        
        # Use Right_AIChat_Panel's method to load config
        default_provider, default_base_url, default_key, default_models = self.right_panel.load_AI_config(account_file)
        
        # Log what was loaded from account.json
        if default_provider or default_base_url or default_key or default_models:
            print("[INFO] Loading AI configuration from account.json:")
            if default_provider:
                print(f"  - Provider: {default_provider}")
            if default_base_url:
                print(f"  - Base URL: {default_base_url}")
            if default_key:
                print(f"  - API Key: {'*' * min(8, len(default_key))}")
            if default_models:
                print(f"  - Models: {len(default_models)} models loaded")
        else:
            print("[INFO] No valid AI configuration found in account.json, will use defaults")

        #---------------------------------------------------------------------------------
        # 3. Set AI provider (if available from account.json)
        selected_provider = None
        
        if default_provider:
            default_provider_lower = default_provider.lower()
            found_index = -1

            # Iterate through ComboBox options to find matching provider
            if hasattr(self.setting_page, 'provider_combo'):
                for i in range(self.setting_page.provider_combo.count()):
                    item_lower = self.setting_page.provider_combo.itemText(i).lower()
                    if default_provider_lower in item_lower:
                        found_index = i
                        break

                # Set the provider combo box index
                if found_index != -1:
                    self.setting_page.provider_combo.setCurrentIndex(found_index)
                    selected_provider = self.setting_page.provider_combo.itemText(found_index)
                    print(f"[INFO] Set provider to '{selected_provider}' from account.json")
                else:
                    # Provider value exists but doesn't match any option - use Custom
                    custom_index = self.setting_page.provider_combo.findText("Custom")
                    if custom_index != -1:
                        self.setting_page.provider_combo.setCurrentIndex(custom_index)
                        selected_provider = "Custom"
                        print(f"[INFO] Provider '{default_provider}' not recognized, set to 'Custom'")
        
        # If no provider from account.json, check settings.ini or use default
        if not selected_provider:
            if settings.contains("AI/provider"):
                selected_provider = settings.value("AI/provider")
                print(f"[INFO] Using provider from settings.ini: {selected_provider}")
            else:
                selected_provider = "OpenRouter (Recommended)"
                print(f"[INFO] No provider configured, using default: {selected_provider}")

        #---------------------------------------------------------------------------------
        # 4. Set each AI field independently - use account.json if available, otherwise use defaults
        
        # Provider
        settings.setValue("AI/provider", selected_provider)
        
        # Base URL
        if default_base_url:
            settings.setValue("AI/base_url", default_base_url)
            print(f"[INFO] Set base_url from account.json")
        else:
            check_and_set_default("AI/base_url", "https://openrouter.ai/api/v1/chat/completions")
            if not settings.contains("AI/base_url"):
                print(f"[INFO] No base_url in account.json, using default")
        
        # API Key
        if default_key:
            settings.setValue("AI/api_key", default_key)
            print(f"[INFO] Set api_key from account.json")
        else:
            check_and_set_default("AI/api_key", "")
            if not settings.contains("AI/api_key") or not settings.value("AI/api_key"):
                print(f"[INFO] No api_key in account.json, using empty default")
        
        # Model
        if default_models and len(default_models) > 0:
            settings.setValue("AI/model", default_models[0])
            print(f"[INFO] Set model to '{default_models[0]}' from account.json")
        else:
            check_and_set_default("AI/model", "openai/gpt-oss-120b")
            if not settings.contains("AI/model"):
                print(f"[INFO] No models in account.json, using default model")

        # Set other AI defaults (system prompt, temperature)
        check_and_set_default("AI/system_prompt", "You are a helpful assistant.")
        check_and_set_default("AI/temperature", 0.7)

        #---------------------------------------------------------------------------------
        # Save the settings after all checks
        settings.sync()
        self.settings = settings
        
        if is_first_run:
            print("[INFO] Default settings created successfully.")
        else:
            print(f"[INFO] Settings loaded from: {settings_path}")

        #---------------------------------------------------------------------------------
        # Apply settings to the application UI
        if hasattr(self, "operations_setting_page"):
            self.operations_setting_page.apply_new_settings()
            
    #---------------------------------------------------------------------------------


    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Initialize the main window    
    def init_main_window_ui(self):

        window_ratio = 0.8
        total_window_height = window_ratio*1080                 # Total window height for reference
        total_window_with   = window_ratio*1920                 # Total window width for reference
        self.setWindowTitle("SaMPH-Hull")                       # Set the window title --- Savitsky-based Motion of Planing Hulls
        self.resize(total_window_with, total_window_height)     # Set the initial size of the main window

        # ============================ Main Windows =================================
        # Set the window icon (optional)
        window_icon_path = utils.local_resource_path("SaMPH_Images/planing-hull-app-logo.png")
        pix = QPixmap(window_icon_path)
        target_size = QSize(128, 128)
        pix = pix.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setWindowIcon(QIcon(pix))  

        # keep references for single-instance tabs
        self.page_home = None
        self.page_input = None
        self.home_tab_index = None
        self.input_tab_index = None

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Use the external Menu class to create the menu bar
        self.menu_bar = MenuBuilder(self)                
        self.setMenuBar(self.menu_bar)
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Use the external Tool_Bar class to create the tool bar
        self.tool_bar = ToolbarBuilder(self)       
        self.addToolBar(self.tool_bar)
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Create Status Bar
        self.status_bar = StatusBarBuilder(self)
        self.setStatusBar(self.status_bar)
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Create the VS Code-like three-panel layout
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        # ============ Left Navigation Sidebar ============
        self.left_panel = Left_Side_Panel(self)
        
        # ============ Left Drag Handle ============
        self.left_drag_handle = QWidget()
        self.left_drag_handle.setFixedWidth(2)  # Slightly thinner
        self.left_drag_handle.setCursor(Qt.CursorShape.SizeHorCursor)
        # Transparent background, only cursor changes
        self.left_drag_handle.setStyleSheet("background-color: transparent;")
        
        # Connect drag events for left handle
        self.left_drag_handle.mousePressEvent   = lambda event: self.operations_main_window.start_left_drag(event)
        self.left_drag_handle.mouseMoveEvent    = lambda event: self.operations_main_window.do_left_drag(event)
        self.left_drag_handle.mouseReleaseEvent = lambda event: self.operations_main_window.end_left_drag(event)
        
        # ============ Central Workspace with Vertical Splitter ============
        # Create vertical splitter for Tab Widget (upper) and Log Window (lower)
        self.central_splitter = QSplitter(Qt.Vertical)
        
        # Upper part: Tab Widget
        self.tab_widget = Central_Tab_Widget(self)
        self.central_splitter.addWidget(self.tab_widget)
        self.home_panel_visible = True
        
        # Lower part: Log Window
        self.log_window = Central_Log_Widget(self)
        self.central_splitter.addWidget(self.log_window)
        
        # Set initial sizes (tab:log = 4:1)
        self.central_splitter.setStretchFactor(0, 4)
        self.central_splitter.setStretchFactor(1, 1)
        self.central_splitter.setSizes([600, 250])  # Initial heights
        
        # Track log window visibility
        self.log_visible = True

        # ============ Right Drag Handle ============
        self.right_drag_handle = QWidget()
        self.right_drag_handle.setFixedWidth(2)  # Slightly thinner
        self.right_drag_handle.setCursor(Qt.CursorShape.SizeHorCursor)
        # Transparent background, only cursor changes
        self.right_drag_handle.setStyleSheet("background-color: transparent;")
        
        # Connect drag events for right handle
        self.right_drag_handle.mousePressEvent   = lambda event: self.operations_main_window.start_right_drag(event)
        self.right_drag_handle.mouseMoveEvent    = lambda event: self.operations_main_window.do_right_drag(event)
        self.right_drag_handle.mouseReleaseEvent = lambda event: self.operations_main_window.end_right_drag(event)
        
        # ============ Right AI Chat Sidebar ============
        self.right_panel = Right_AIChat_Panel(self)
        


        # ================ Main Layout ==================
        # Create central container widget
        central_container = QWidget()
        main_layout = QHBoxLayout(central_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add components to layout
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.left_drag_handle)
        main_layout.addWidget(self.central_splitter, 1)  # Central splitter gets stretch factor
        main_layout.addWidget(self.right_drag_handle)
        main_layout.addWidget(self.right_panel)
        
        # Set as central widget
        self.setCentralWidget(central_container)
        
        # Initialize drag state variables
        self.left_drag_start_x = 0
        self.left_drag_start_width = 0
        self.right_drag_start_x = 0
        self.right_drag_start_width = 0
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Initialize signal and slot connections
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def init_signal_connections(self):
        """Initialize all signal and slot connections here."""
        
        # Toolbar signals
        self.tool_bar.search_requested.connect(self.operations_main_window.handle_toolbar_search)

        # Unified Home toggle handler for toolbar and sidebar
        self.tool_bar.toggle_home_requested.connect(self.operations_main_window.toggle_home_page)
        self.tool_bar.toggle_left_requested.connect(self.operations_main_window.toggle_left_panel)
        self.tool_bar.toggle_log_requested.connect(self.operations_main_window.toggle_log_window)
        self.tool_bar.toggle_right_requested.connect(self.operations_main_window.toggle_right_panel)
        self.tool_bar.calculate_requested.connect(self.operations_computing.handle_calculate_request)
        self.tool_bar.clear_requested.connect(self.operations_computing.handle_clear_request)
        self.tool_bar.output_report_requested.connect(self.operations_report_gen.generate_report)
        
        # Menu Bar signals
        self.menu_bar.preferences_clicked.connect(self.show_preferences_dialog)
        self.menu_bar.open_file_clicked.connect(self.operations_input_page.load_input_data_from_csv)
        self.menu_bar.save_file_clicked.connect(self.operations_input_page.save_input_data_to_csv)
        
        # Help menu signals
        self.menu_bar.about_clicked.connect(self.operations_main_window.show_about_dialog)
        self.menu_bar.license_clicked.connect(self.operations_main_window.show_license_dialog)
        
        # View menu signals
        self.menu_bar.toggle_toolbar_visibility.connect(self.tool_bar.setVisible)
        self.menu_bar.toggle_navigation_visibility.connect(self.operations_main_window.toggle_left_panel)
        self.menu_bar.toggle_aichat_visibility.connect(self.operations_main_window.toggle_right_panel)
        self.menu_bar.toggle_logwindow_visibility.connect(self.operations_main_window.toggle_log_window)
        
        # Left Panel signals
        self.left_panel.navigation_requested.connect(self.operations_main_window.handle_navigation)
        self.left_panel.home_toggle_requested.connect(self.operations_main_window.toggle_home_page)
        self.left_panel.result_page_requested.connect(self.handle_result_page_request)
        
        # Log window signals
        self.log_window.close_requested.connect(self.operations_main_window.on_log_window_closed)



        # --- Connect signals from the right side panel ---
        # Chat signal
        self.right_panel.send_message_signal.connect(self.operation_chat.send_message)
        
        # Chat message signals
        self.right_panel.new_chat_request.connect(self.operation_chat.handle_new_chat)
        self.right_panel.new_folder_request.connect(self.right_panel.history_panel.on_new_folder)



        # Model change signal for both chat controller and worker
        self.right_panel.model_changed_signal.connect(self.operation_chat.worker.update_config)
        self.right_panel.model_changed_signal.connect(self.operation_chat.update_model_for_chat_controller)

        # Signal from history panel to open chat file
        self.right_panel.history_panel.chat_item_double_clicked.connect(self.operation_chat.handle_open_chat_file)

        # Signal from history panel to create new chat
        self.right_panel.history_panel.new_chat_request.connect(self.operation_chat.handle_new_chat)

        # Main Window custom signals (visibility updates)
        self.home_panel_visible_changed.connect(self.operations_main_window.update_home_panel_visibility)
        self.left_panel_visible_changed.connect(self.operations_main_window.update_left_panel_visibility)
        self.right_panel_visible_changed.connect(self.operations_main_window.update_right_panel_visibility)
        self.right_panel_visible_changed.connect(self.menu_bar.update_aichat_toggle_state) # Sync menu bar state
        self.log_window_visible_changed.connect(self.operations_main_window.update_log_window_visibility)

        # Splitter signals
        self.central_splitter.splitterMoved.connect(self.operations_main_window.handle_splitter_moved)


        #-----------------------------------------------------------------------
        # Connect settings page signals
        #-----------------------------------------------------------------------
        if hasattr(self.setting_page, 'apply_settings_signal'):
            self.setting_page.apply_settings_signal.connect(self.operations_setting_page.apply_new_settings)

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    # ---------------------------------------------------------------------------------
    def handle_result_page_request(self, result_type):
        """
        Handle request to open a result page from left panel tree.
        
        Args:
            result_type: Type identifier (e.g., "Rt", "Trim", "Sinkage")
        """
        # Create or get the result page
        page = self.operations_result_page.create_or_get_result_page(result_type)
        
        # Access the actual QTabWidget inside Central_Tab_Widget
        tab_widget = self.tab_widget.tab_widget
        
        # Check if already in tabs
        for i in range(tab_widget.count()):
            if tab_widget.widget(i) == page:
                # Already exists, just switch to it
                tab_widget.setCurrentIndex(i)
                return
        
        # Add as new tab
        result_label = self.operations_result_page.result_config.get(result_type, result_type)
        tab_widget.addTab(page, result_label)
        tab_widget.setCurrentWidget(page)
    # ---------------------------------------------------------------------------------

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Helper function to update input container after sidebar resize
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def update_input_after_drag(self):
        """
        在拖动防抖timer触发后更新输入框位置
        参考 AIchat_Combo_V3 的实现
        """
        if hasattr(self.right_panel, 'update_input_container_position'):
            self.right_panel.update_input_container_position()
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++




    # ======================== QSS setting ========================
    def init_styles(self):
        # QSS settings, this style sheet affects the entire application
        self.setStyleSheet(Theme_SaMPH.get_stylesheet())
    #===================================================================

    # ---------------------------------------------------------------------------------
    def show_preferences_dialog(self):
        """
        Show the preferences/settings dialog.
        Settings are applied only when user clicks Apply button.
        """
        # Show the setting page dialog (modal)
        result = self.setting_page.exec()
        
        # No automatic application of settings when dialog closes
        # Settings are applied only via Apply button in the dialog
        # Or will be loaded on next application restart
    # ---------------------------------------------------------------------------------

    # ---------------------------------------------------------------------------------
    def closeEvent(self, event):
        """Handle the window close event to properly shut down the application."""
        event.accept()
    # ---------------------------------------------------------------------------------


#------------------------------------------------------------------------
# Main execution block, this is only used for debugging
if __name__ == '__main__':  # Ensure this code runs only when the file is executed directly
    
    app = QApplication(sys.argv)    # Create the application object
    window = GUI_SaMPH_Application()         # Create an instance of the Login_Window class
    window.show()                   # Display the login window
    sys.exit(app.exec())            # Start the application's event loop
#------------------------------------------------------------------------
