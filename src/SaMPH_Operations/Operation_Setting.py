#-----------------------------------------------------------------------
# Purpose: The operation controller for the setting page
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-12-01  
#-----------------------------------------------------------------------

import sys
import os
import webbrowser
import logging
import subprocess
import time
import json


from pathlib import Path
from urllib.parse import quote_plus

#-----------------------------------------------------------------------
# Import PySide6 widgets for UI elements
from PySide6.QtWidgets import ( 
    QApplication, 
    QMainWindow, QTextEdit, QToolBar, QDockWidget, QListWidget, QFileDialog,
    QLabel, QFileDialog, QAbstractButton, QWidget, QStackedWidget, QTabWidget, QGroupBox,    
    QLineEdit, QMenu, 
    QPushButton, QRadioButton, QButtonGroup, QWidgetAction,
    QVBoxLayout, QHBoxLayout, QSizePolicy, QTreeWidget, QTreeWidgetItem, QCheckBox,
    QFormLayout, QGridLayout, QDialog, QDialogButtonBox, QComboBox,
    QMessageBox
)
from PySide6.QtGui import QPixmap, QFont, QIcon, QAction, QPainter, QColor
from PySide6.QtCore import Qt, QSize, QDateTime, Signal, QSettings, QObject, Slot, QThread
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------
# Import the class from the local python files
from SaMPH_Utils.Utils import utils
from SaMPH_Operations.Operation_MainWindow import MainWindow_Operations
from SaMPH_GUI.Theme_SaMPH import Theme_SaMPH
#-----------------------------------------------------------------------


#-----------------------------------------------------------------------
class SettingPage_Operations(QObject):
    """
    Controller for applying settings to the main application UI.
    Handles settings from the new Settings Window with enhanced features.
    """

    def __init__(self, parent=None):
        """
        Initialize the settings controller.

        Args:
            parent: The main window instance of the application.
        """
        super().__init__(parent)

        #-----------------------------------------------------------------------
        # Get the main window, setting page, and components from the parent
        #-----------------------------------------------------------------------
        self.main_window    = parent
        self.tab_widget     = parent.tab_widget
        self.setting_page   = parent.setting_page
        self.tool_bar       = parent.tool_bar
        self.left_panel     = parent.left_panel
        self.right_panel    = parent.right_panel

        self.operation_mainwindow = MainWindow_Operations(self.main_window) 
        
        #-----------------------------------------------------------------------
        # Get the QSettings file path
        #-----------------------------------------------------------------------
        usr_folder = utils.get_global_usr_dir()
        self.settings_file_path = usr_folder / "Settings/settings.ini"

        #-----------------------------------------------------------------------
        # Connect settings page signals
        #-----------------------------------------------------------------------
        # if hasattr(self.setting_page, 'apply_settings_signal'):
        #     self.setting_page.apply_settings_signal.connect(self.apply_new_settings)

        # if hasattr(self.setting_page, 'language_changed'):
        #     self.setting_page.language_changed.connect(self.apply_language_change)
        # if hasattr(self.setting_page, 'theme_changed'):
        #     self.setting_page.theme_changed.connect(self.apply_theme_change)
        # if hasattr(self.setting_page, 'font_changed'):
        #     self.setting_page.font_changed.connect(self.apply_font_change)


    #-----------------------------------------------------------------------
    # Apply new settings from settings.ini to the main application
    #-----------------------------------------------------------------------
    def apply_new_settings(self):

        """
        Apply new settings from settings.ini to the main application.

        This function reads the .ini file and updates:
        - Font (type and size) for text-based widgets
        - Theme / Appearance (Light/Dark mode)
        - Toolbar icon visibility
        - Panel sizes and animations
        - Language
        - Search Engine
        - AI Configuration (Provider, Model, URL, Key, Prompt, Temperature)
        - Result Chart Settings
        """

        settings = QSettings(str(self.settings_file_path), QSettings.Format.IniFormat)

        # ---------------- Font Settings ----------------
        self.apply_font_change(
            settings.value("Font/type", "Microsoft YaHei"),
            int(settings.value("Font/size", "10"))
        )

        # ---------------- Appearance / Theme ----------------
        self.apply_theme_change(settings.value("Appearance/theme", "Light"))

        # ---------------- Panel Sizes ----------------
        self.apply_panel_sizes(settings)

        # ---------------- Animations ----------------
        animations_enabled = settings.value("Appearance/animations", True, type=bool)
        # Store this for panel toggle operations to use
        if hasattr(self.main_window, 'animations_enabled'):
            self.main_window.animations_enabled = animations_enabled

        # ---------------- Central Background ----------------
        background_path = settings.value("Appearance/central_background", "")
        if background_path and hasattr(self.tab_widget, "set_central_background"):

            self.tab_widget.set_central_background(background_path)
            print(f"[INFO] Applied central background: {background_path}")

        # ---------------- Toolbar Icons ----------------
        show_toolbar_icons = settings.value("Appearance/toolbar_icons", True, type=bool)
        if hasattr(self.main_window, "tool_bar"):
            self.tool_bar.setVisible(show_toolbar_icons)

        # ---------------- Language Settings ----------------
        self.apply_language_change(settings.value("Language/type", "English"))

        # ---------------- Search Settings ----------------
        # The search settings has been applied in operation_mainwindow
        # When the search settings are changed, the search engine will be updated
        # self.apply_search_settings(settings)

        # ---------------- AI Settings ----------------
        self.apply_ai_settings(settings)

        # ---------------- Result Chart Settings ----------------
        self.apply_result_chart_settings(settings)

        print("[INFO] All settings applied successfully")



    #-----------------------------------------------------------------------
    # Apply Font Change
    #-----------------------------------------------------------------------
    def apply_font_change(self, font_type, font_size):
        """Apply font settings to the application."""
        app_font = QFont(font_type, font_size)
        QApplication.instance().setFont(app_font)

        # Apply to all major windows
        total_windows = [
            self.main_window, 
            self.setting_page, 
            self.left_panel, 
            self.right_panel, 
            self.tool_bar,
            self.main_window.status_bar,
            self.right_panel.history_panel,
        ]
        
        text_widgets = (
            QTextEdit, QLineEdit, QComboBox, QPushButton,
            QLabel, QRadioButton, QCheckBox, QDialog, QGroupBox,
            QTreeWidget, QWidget
        )

        for window in total_windows:
            if not window or not isinstance(window, QWidget):
                continue
        
            window.setFont(app_font)

        # Apply to all text-based widgets
            for cls in text_widgets:
                for widget in window.findChildren(cls):
                    widget.setFont(app_font)
            window.setFont(app_font)

        # Apply to all major windows
        QApplication.instance().setFont(app_font)

        print(f"[INFO] Font applied: {font_type}, {font_size}pt")

    #-----------------------------------------------------------------------
    # Apply Theme Change
    #-----------------------------------------------------------------------
    def apply_theme_change(self, theme_mode):
        """Apply theme (Light/Dark) to the application."""
        
        # Always apply light theme (Dark theme removed)
        # Apply light theme (use Theme_SaMPH)
        light_qss = Theme_SaMPH.get_stylesheet()
        QApplication.instance().setStyleSheet(light_qss)
        if self.main_window:
            self.main_window.setStyleSheet(light_qss)
        if self.setting_page:
            self.setting_page.setStyleSheet(light_qss)

        print(f"[INFO] Theme applied: Light (Forced)")





    #-----------------------------------------------------------------------
    # Apply Language Change
    #-----------------------------------------------------------------------
    def apply_language_change(self, language_type):

        """Apply language settings to the application."""
        new_language = "Chinese" if language_type.startswith("Chinese") else "English"
        
        # Update language manager
        if hasattr(self.main_window, "language_manager"):
            self.main_window.language_manager.set_language(new_language)
            lang_manager = self.main_window.language_manager
        else:
            # Fallback if not found
            from SaMPH_GUI.Language_Manager import Language_Manager
            lang_manager = Language_Manager()
            lang_manager.set_language(new_language)

        # Update UI texts for all main components
        components = [
            self.main_window.menu_bar,
            self.main_window.tool_bar,
            self.main_window.left_panel,
            self.main_window.right_panel,
            self.main_window.tab_widget,
            self.main_window.log_window,
            self.main_window.status_bar,
            self.main_window.right_panel.history_panel,
            self.setting_page
        ]
        
        # Add report generator if it exists
        if hasattr(self.main_window, 'operations_report_generator'):
            components.append(self.main_window.operations_report_generator)

        for component in components:
            if component and hasattr(component, "update_ui_texts"):
                try:
                    component.update_ui_texts(lang_manager)
                except Exception as e:
                    print(f"[WARN] Failed to update texts for {component}: {e}")

        # Update all open tabs (pages)
        if hasattr(self.main_window.tab_widget, "tab_widget"):
            tab_widget = self.main_window.tab_widget.tab_widget
            for i in range(tab_widget.count()):
                page = tab_widget.widget(i)
                if hasattr(page, "update_ui_texts"):
                    try:
                        page.update_ui_texts(lang_manager)
                    except Exception as e:
                        print(f"[WARN] Failed to update texts for tab page {i}: {e}")

        print(f"[INFO] Language applied: {new_language}")

    #-----------------------------------------------------------------------
    # Apply Panel Sizes
    #-----------------------------------------------------------------------
    def apply_panel_sizes(self, settings):
        """Apply panel size settings."""
        left_width = settings.value("Appearance/left_panel_width", 320, type=int)
        right_width = settings.value("Appearance/right_panel_width", 400, type=int)

        if hasattr(self.main_window, 'left_panel') and self.left_panel:
            self.left_panel.panel_width = left_width
            self.left_panel.full_width = left_width
            if self.left_panel.is_visible:
                self.left_panel.setFixedWidth(left_width)
                self.left_panel.setMaximumWidth(600)

        if hasattr(self.main_window, 'right_panel') and self.right_panel:
            self.right_panel.panel_width = right_width
            self.right_panel.full_width = right_width
            if self.right_panel.is_visible:
                self.right_panel.setFixedWidth(right_width)
                self.right_panel.setMaximumWidth(800)

        print(f"[INFO] Panel sizes applied: Left={left_width}px, Right={right_width}px")

    #-----------------------------------------------------------------------
    # Apply Search Settings
    #-----------------------------------------------------------------------
    def apply_search_settings(self, settings):

        """Apply search engine settings."""

        print("[INFO] Applying search settings...")

        use_baidu = settings.value("Search/Baidu", True, type=bool)
        use_google = settings.value("Search/Google", False, type=bool)

        # Disconnect specific slots to avoid RuntimeWarning
        try:
            self.tool_bar.search_requested.disconnect(self.operation_mainwindow.perform_google_search)
        except Exception:
            pass
            
        try:
            self.tool_bar.search_requested.disconnect(self.operation_mainwindow.perform_baidu_search)
        except Exception:
            pass

        # Connect to appropriate search engine
        if use_google and not use_baidu:
            self.tool_bar.search_requested.connect(self.operation_mainwindow.perform_google_search)
        else:
            self.tool_bar.search_requested.connect(self.operation_mainwindow.perform_baidu_search)

        print(f"[INFO] Search engine: {'Google' if use_google and not use_baidu else 'Baidu'}")

    #-----------------------------------------------------------------------
    # Apply AI Settings
    #-----------------------------------------------------------------------
    def apply_ai_settings(self, settings):
        """Apply AI configuration settings."""
        
        # Update chat controller if exists
        if hasattr(self.main_window, "chat_controller"):
            current_model = settings.value("AI/model", "")
            if current_model:
                self.main_window.chat_controller.update_model_for_chat_controller(current_model, None)
                print(f"[INFO] AI model updated: {current_model}")

        # Update account.json with current settings before refreshing
        self.save_ai_settings_to_account_json(settings)

        # Reload models in Right Panel (in case account.json changed or was added)
        if hasattr(self.main_window, 'right_panel') and hasattr(self.main_window.right_panel, 'refresh_ai_models'):
            self.main_window.right_panel.refresh_ai_models()
            print("[INFO] AI models refreshed in right panel")
            
            # Update chat controller's model logo after refresh
            if hasattr(self.main_window, 'chat_controller'):
                current_model = settings.value("AI/model", "")
                current_logo = self.main_window.right_panel.get_current_AI_model_logo()
                if current_model and current_logo:
                    self.main_window.chat_controller.model_logo = current_logo
                    print(f"[INFO] Chat controller logo updated after refresh")

        # Update settings page controls if they exist
        if hasattr(self.setting_page, "controls") and "AI" in self.setting_page.controls:
            ai_ctrls = self.setting_page.controls["AI"]

            # Update model (load from account.json)
            if "model" in ai_ctrls and hasattr(self.setting_page, 'load_available_models'):
                available_models = self.setting_page.load_available_models()
                saved_model = settings.value("AI/model", "")
                if saved_model and saved_model in available_models:
                    ai_ctrls["model"].setCurrentText(saved_model)

            # Update base URL
            if "base_url" in ai_ctrls:
                default_url = "https://openrouter.ai/api/v1/chat/completions"
                saved_url = settings.value("AI/base_url", default_url)
                ai_ctrls["base_url"].setText(saved_url)

            # Update system prompt
            if "system_prompt" in ai_ctrls:
                default_prompt = "You are a helpful assistant."
                saved_prompt = settings.value("AI/system_prompt", default_prompt)
                ai_ctrls["system_prompt"].setPlainText(saved_prompt)

            # Update provider
            if "provider" in ai_ctrls:
                saved_provider = settings.value("AI/provider", "OpenRouter (Recommended)")
                ai_ctrls["provider"].setCurrentText(saved_provider)

            # Update API key
            if "api_key" in ai_ctrls:
                saved_key = settings.value("AI/api_key", "")
                ai_ctrls["api_key"].setText(saved_key)

            # Update temperature
            if "temperature" in ai_ctrls:
                saved_temp = float(settings.value("AI/temperature", 0.7))
                ai_ctrls["temperature"].setValue(int(saved_temp * 10))

        print("[INFO] AI settings applied")
    
    def save_ai_settings_to_account_json(self, settings):

        """
        Save AI settings from settings.ini to account.json.
        """
        
        try:
            usr_folder = utils.get_global_usr_dir()
            account_file = usr_folder / "Settings/account.json"
            
            # Read existing account.json or create new dict
            if account_file.exists():
                with open(account_file, 'r', encoding='utf-8') as f:
                    account_data = json.load(f)
            else:
                account_data = {}
            
            # Get current settings from settings.ini
            provider = settings.value("AI/provider", "")
            base_url = settings.value("AI/base_url", "")
            api_key = settings.value("AI/api_key", "")
            
            # Get models from settings page if available
            models = []
            if hasattr(self.setting_page, "controls") and "AI" in self.setting_page.controls:
                model_combo = self.setting_page.controls["AI"].get("model")
                if model_combo:
                    # Get all items from the combobox
                    models = [model_combo.itemText(i) for i in range(model_combo.count())]
                    # Filter out placeholder items
                    models = [m for m in models if m and m != "No models configured"]
            
            # If no models from combo, try to preserve existing models from account.json
            if not models and "models" in account_data:
                models = account_data.get("models", [])
            
            # Update account_data (support both naming conventions)
            # Map provider display name to internal name
            provider_reverse_map = {
                "OpenRouter (Recommended)": "openrouter",
                "OpenAI (Official)": "openai",
                "Alibaba Qwen (DashScope)": "qwen",
                "DeepSeek (Official)": "deepseek",
                "X.AI (Grok)": "xai",
                "Groq (Meta Llama/Mixtral)": "groq",
                "Google Gemini (via OpenRouter)": "gemini",
                "SiliconFlow (硅基流动)": "siliconflow",
                "Ollama (Localhost)": "ollama",
                "Arli": "arli"
            }
            
            internal_provider = provider_reverse_map.get(provider, provider.lower() if provider else "")
            
            # Use original field naming convention
            if internal_provider:
                account_data["Provider"] = internal_provider.capitalize()
            
            if base_url:
                account_data["base_url"] = base_url
            
            if api_key:
                account_data["API-Key"] = api_key
            
            if models:
                account_data["models"] = models
            
            # Write back to account.json
            account_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"[DEBUG] Attempting to save account.json to: {account_file}")
            print(f"[DEBUG] Account data to save: {json.dumps(account_data, ensure_ascii=False)}")
            
            with open(account_file, 'w', encoding='utf-8') as f:
                json.dump(account_data, f, indent=2, ensure_ascii=False)
            
            print(f"[INFO] Successfully updated account.json at {account_file}")
            
        except Exception as e:
            error_msg = f"Failed to update account.json at {account_file}\nError: {e}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Show error message box to user (helpful for EXE debugging)
            if hasattr(self, 'main_window'):
                QMessageBox.critical(self.main_window, "Save Error", error_msg)

    #-----------------------------------------------------------------------
    # Apply Result Chart Settings
    #-----------------------------------------------------------------------
    def apply_result_chart_settings(self, settings):
        """
        Apply result chart style settings from settings.ini.
        
        This updates:
        - Curve style (Solid, Dashed, Dotted)
        - Curve color (hex format)
        - Curve width
        - Scatter marker style (Circle, Square, Triangle)
        - Axis style
        - Grid style
        - Background color
        
        Args:
            settings (QSettings): The QSettings object containing saved settings
        """
        
        # Check if result pages exist
        if not hasattr(self.main_window, 'operations_result_page'):
            print("[WARN] operations_result_page not found in main_window")
            return
        
        result_operations = self.main_window.operations_result_page
        
        # Log the settings being applied
        curve_style = settings.value("ResultChart/curve_style", "Solid")
        curve_color = settings.value("ResultChart/curve_color", "#1F4788")
        curve_width = settings.value("ResultChart/curve_width", "2.0")
        scatter_style = settings.value("ResultChart/scatter_style", "Circle")
        axis_style = settings.value("ResultChart/axis_style", "Solid")
        grid_style = settings.value("ResultChart/grid_style", "Solid")
        bg_color = settings.value("ResultChart/bg_color", "#FAFAFA")
        
        print("[INFO] Applying Result Chart Settings:")
        print(f"       Curve Style: {curve_style}")
        print(f"       Curve Color: {curve_color}")
        print(f"       Curve Width: {curve_width}")
        print(f"       Scatter Style: {scatter_style}")
        print(f"       Axis Style: {axis_style}")
        print(f"       Grid Style: {grid_style}")
        print(f"       Background Color: {bg_color}")
        

        # -------- 2. Update the global config for the chart style-----------
        try:
            from SaMPH_GUI.Page_Result import ChartStyleManager
            ChartStyleManager.update_global_config({
                "curve_style": curve_style,
                "curve_color": curve_color,
                "curve_width": float(curve_width),
                "scatter_style": scatter_style,
                "axis_style": axis_style,
                "grid_style": grid_style,
                "bg_color": bg_color,
            })
        except Exception as e:
            print(f"[ERROR] Failed to update global ChartStyleManager config: {e}")
            return


        # 3. Iterate through all currently open result pages and refresh their styles
        for result_type, page in result_operations.result_pages.items():

            try:
                # Verify the page still exists
                _ = page.objectName()
                
                # Recreate the ChartStyleManager to reload settings
                if hasattr(page, 'style_manager'):
                    page.style_manager = __import__(
                        'SaMPH.SaMPH_GUI.Page_Result', 
                        fromlist=['ChartStyleManager']
                    ).ChartStyleManager()
                
                # Apply the new chart settings
                if hasattr(page, 'apply_chart_settings'):
                    page.apply_chart_settings()
                    print(f"[INFO] Updated Result Page: {result_type}")
                else:
                    print(f"[WARN] Result page '{result_type}' doesn't have apply_chart_settings method")
                    
            except RuntimeError:
                print(f"[DEBUG] Result page '{result_type}' has been deleted, skipping")
                continue
            except Exception as e:
                print(f"[ERROR] Failed to apply settings to result page '{result_type}': {str(e)}")
                continue
        
        print("[INFO] Result Chart Settings applied successfully")
    #-----------------------------------------------------------------------
