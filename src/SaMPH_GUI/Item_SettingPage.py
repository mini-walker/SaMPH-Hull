#-----------------------------------------------------------------------------------------
# Purpose: This file is used to create the Settings Window with multi-language support
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-12-01 
#----------------------------------------------------------------------------------------- 

import sys
import os
import json
import requests
from pathlib import Path

#-----------------------------------------------------------------------------------------
# Import PySide6 widgets for creating the UI components
from PySide6.QtWidgets import ( 
    QFileDialog, QDialog, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QDialogButtonBox, QLineEdit, QLabel, QComboBox, QCheckBox, 
    QMessageBox, QPushButton, QWidget, QGroupBox, QFormLayout, QSlider, QTextEdit,
    QRadioButton, QButtonGroup, QScrollArea, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Import utility functions and theme
try:
    from SaMPH_Utils.Utils import utils 
    from SaMPH_GUI.Theme_SaMPH import Theme_SaMPH
except ImportError:
    class Utils:
        def get_global_usr_dir(self): return Path("usr")
    utils = Utils()
    class Theme_SaMPH:
        @staticmethod
        def get_stylesheet(): return ""
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Define the Setting_Window class for the Preferences Dialog
class Setting_Window(QDialog):

    """
    Preferences Dialog with Multi-language Support and Complete Functionality.
    """

    # Signals for settings changes
    settings_page_operation_signal = Signal(str)
    apply_settings_signal = Signal()
    language_changed = Signal(str)
    theme_changed = Signal(str)
    font_changed = Signal(str, int)
    ai_settings_changed = Signal()


    #-------------------------------------------------------------------------------------
    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Preferences")
        self.resize(800, 600) 

        #---------------------------------------------------------------------------------
        # Setup Settings File
        usr_folder = utils.get_global_usr_dir()
        os.makedirs(usr_folder, exist_ok = True)
        setting_file_path = usr_folder / "Settings/settings.ini"
        self.settings = QSettings(str(setting_file_path), QSettings.Format.IniFormat)
        #---------------------------------------------------------------------------------

        #---------------------------------------------------------------------------------
        # Main Layout
        main_layout = QHBoxLayout()

        # Left: Navigation Tree
        self.preference_tree = QTreeWidget()
        self.preference_tree.setHeaderHidden(True)
        self.preference_tree.setFixedWidth(180)
        main_layout.addWidget(self.preference_tree)

        #---------------------------------------------------------------------------------
        # Define navigation tree items
        self.item_ai = QTreeWidgetItem(["AI Configuration"]) 
        self.item_appearance = QTreeWidgetItem(["Appearance"])
        self.item_font = QTreeWidgetItem(["Font Settings"])
        self.item_language = QTreeWidgetItem(["Language Settings"])
        self.item_search = QTreeWidgetItem(["Search"])
        self.item_result_chart = QTreeWidgetItem(["Result Chart"])
        
        self.preference_tree.addTopLevelItems([
            self.item_ai, 
            self.item_appearance, 
            self.item_font, 
            self.item_language, 
            self.item_search,
            self.item_result_chart
        ])
        self.preference_tree.setIndentation(0)

        # Style the navigation tree
        self.preference_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #D3D3D3;
                border-radius: 8px;
                padding: 0px;
                background-color: #fafafa;
            }
            QTreeWidget::item { 
                padding: 10px; 
                color: #333333;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QTreeWidget::item:hover { 
                background-color: #E8E8E8; 
            }
            QTreeWidget::item:selected { 
                background-color: #DCDCDC; 
                color: #333333;
                font-weight: bold;
            }
        """)

        # Right: Pages in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        self.stack = QStackedWidget()
        scroll.setWidget(self.stack)
        main_layout.addWidget(scroll, 1)

        self.controls = {
            "AI": {}, "Font": {}, "Search": {}, "Language": {}, "Appearance": {}, "ResultChart": {}
        }

        #---------------------------------------------------------------------------------
        # Create pages
        self.ai_page = self.create_ai_page_in_setting()
        self.appearance_page = self.create_appearance_page_in_setting()
        self.font_page = self.create_font_page_in_setting()
        self.language_page = self.create_language_page_in_setting()
        self.search_page = self.create_search_page_in_setting()
        self.result_chart_page = self.create_result_chart_page_in_setting()

        self.stack.addWidget(self.ai_page)
        self.stack.addWidget(self.appearance_page)
        self.stack.addWidget(self.font_page)
        self.stack.addWidget(self.language_page)
        self.stack.addWidget(self.search_page)
        self.stack.addWidget(self.result_chart_page)

        #---------------------------------------------------------------------------------
        # Connect navigation
        self.preference_tree.currentItemChanged.connect(self.change_page)
        self.preference_tree.setCurrentItem(self.item_ai)

        #---------------------------------------------------------------------------------
        # Add dialog buttons with Apply
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        )
        self.button_box.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        self.button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(main_layout)
        layout.addWidget(self.button_box)

        # Apply theme styling
        self.setStyleSheet(Theme_SaMPH.get_stylesheet())
    #-------------------------------------------------------------------------------------





    #-------------------------------------------------------------------------------------
    # Create the AI Settings Page
    def create_ai_page_in_setting(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # --- Group 1: API Connection ---
        self.group_ai_api = QGroupBox("API Connection") 
        api_layout = QFormLayout()
        api_layout.setVerticalSpacing(10)

        # 1. Provider
        self.lbl_provider = QLabel("Provider:")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "OpenRouter (Recommended)", 
            "OpenAI (Official)",
            "Alibaba Qwen (DashScope)", 
            "DeepSeek (Official)", 
            "X.AI (Grok)", 
            "Groq (Meta Llama/Mixtral)",
            "Google Gemini (via OpenRouter)",
            "SiliconFlow (硅基流动)", 
            "Ollama (Localhost)",
            "Arli", 
            "Custom" 
        ])
        
        saved_provider = self.settings.value("AI/provider", "OpenRouter (Recommended)")
        self.provider_combo.setCurrentText(saved_provider)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.controls["AI"]["provider"] = self.provider_combo

        # 2. Model Selection - Load from account.json
        self.lbl_model = QLabel("Model:")
        model_input = QComboBox()
        model_input.setEditable(True)
        
        # Load available models from account.json
        available_models = self.load_available_models()
        if available_models:
            model_input.addItems(available_models)
        else:
            # Fallback if file doesn't exist or is empty
            model_input.addItem("No models configured")
        
        saved_model = self.settings.value("AI/model", "")
        if saved_model and saved_model in available_models:
            model_input.setCurrentText(saved_model)
        elif available_models:
            model_input.setCurrentIndex(0)
        
        self.controls["AI"]["model"] = model_input

        # 3. Base URL
        self.lbl_base_url = QLabel("Base URL:")
        base_url_input = QLineEdit()
        base_url_input.setPlaceholderText("https://...")
        default_url = "https://openrouter.ai/api/v1/chat/completions"
        base_url_input.setText(self.settings.value("AI/base_url", default_url))
        self.controls["AI"]["base_url"] = base_url_input

        # 4. API Key
        self.lbl_api_key = QLabel("API Key:")
        api_input = QLineEdit()
        api_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_input.setPlaceholderText("sk-...")
        api_input.setText(self.settings.value("AI/api_key", ""))
        self.controls["AI"]["api_key"] = api_input

        # 5. Test Connection Button
        self.btn_test_connection = QPushButton("Test Connection")
        self.btn_test_connection.clicked.connect(self.test_ai_connection)

        api_layout.addRow(self.lbl_provider, self.provider_combo)
        api_layout.addRow(self.lbl_model, model_input)
        api_layout.addRow(self.lbl_base_url, base_url_input)
        api_layout.addRow(self.lbl_api_key, api_input)
        api_layout.addRow("", self.btn_test_connection)
        self.group_ai_api.setLayout(api_layout)
        layout.addWidget(self.group_ai_api)

        # --- Group 2: Behavior ---
        self.group_ai_behavior = QGroupBox("Behavior")
        behavior_layout = QFormLayout()
        behavior_layout.setVerticalSpacing(10)

        # 6. System Prompt
        self.lbl_sys_prompt = QLabel("System Prompt:")
        sys_prompt = QTextEdit()
        sys_prompt.setPlaceholderText("You are a helpful assistant...")
        sys_prompt.setMaximumHeight(80)
        sys_prompt.setPlainText(self.settings.value("AI/system_prompt", "You are a helpful assistant."))
        self.controls["AI"]["system_prompt"] = sys_prompt

        # 7. Temperature
        self.lbl_temperature = QLabel("Temperature:")
        temp_container = QWidget()
        temp_h = QHBoxLayout(temp_container)
        temp_h.setContentsMargins(0,0,0,0)
        
        temp_slider = QSlider(Qt.Orientation.Horizontal)
        temp_slider.setRange(0, 20) 
        saved_temp = int(float(self.settings.value("AI/temperature", 0.7)) * 10)
        temp_slider.setValue(saved_temp)
        
        temp_label = QLabel(str(saved_temp / 10.0))
        temp_label.setFixedWidth(35)
        temp_slider.valueChanged.connect(lambda v: temp_label.setText(str(v/10.0)))
        
        temp_h.addWidget(temp_slider)
        temp_h.addWidget(temp_label)
        self.controls["AI"]["temperature"] = temp_slider

        behavior_layout.addRow(self.lbl_sys_prompt, sys_prompt)
        behavior_layout.addRow(self.lbl_temperature, temp_container)
        self.group_ai_behavior.setLayout(behavior_layout)
        layout.addWidget(self.group_ai_behavior)

        # --- Reset Button ---
        self.btn_reset_ai = QPushButton("Reset AI Settings")
        self.btn_reset_ai.clicked.connect(self.reset_AI_preferences)
        layout.addWidget(self.btn_reset_ai)

        layout.addStretch()
        return page

    def on_provider_changed(self, provider_name):
        """Map providers to their OpenAI-Compatible Endpoint URLs."""
        # Safety check: base_url control might not exist yet during initialization
        if not hasattr(self, 'controls') or "AI" not in self.controls or "base_url" not in self.controls["AI"]:
            return
            
        url_map = {
            "OpenRouter (Recommended)": "https://openrouter.ai/api/v1/chat/completions",
            "OpenAI (Official)": "https://api.openai.com/v1/chat/completions",
            "Alibaba Qwen (DashScope)": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "DeepSeek (Official)": "https://api.deepseek.com/chat/completions",
            "X.AI (Grok)": "https://api.x.ai/v1/chat/completions",
            "Groq (Meta Llama/Mixtral)": "https://api.groq.com/openai/v1/chat/completions",
            "Google Gemini (via OpenRouter)": "https://openrouter.ai/api/v1/chat/completions",
            "SiliconFlow (硅基流动)": "https://api.siliconflow.cn/v1/chat/completions",
            "Ollama (Localhost)": "http://localhost:11434/v1/chat/completions",
            "Arli": "https://api.arliai.com/v1/chat/completions"
        }
        if provider_name in url_map:
            self.controls["AI"]["base_url"].setText(url_map[provider_name])

    def load_available_models(self):
        """
        Load AI configuration from usr/SaMPH/Settings/account.json file.
        Populates provider, base_url, api_key, and returns models list.
        """
        try:
            usr_folder = utils.get_global_usr_dir()
            account_file = usr_folder / "Settings/account.json"
            
            if not account_file.exists():
                print("[INFO] account.json not found, using defaults")
                return []
            
            with open(account_file, 'r', encoding='utf-8') as f:
                account_data = json.load(f)
            
            # Load provider if available
            provider = account_data.get("Provider", "")
            if provider and hasattr(self, 'controls') and "AI" in self.controls:
                if "provider" in self.controls["AI"]:
                    # Map internal provider names to display names
                    provider_map = {
                        "openrouter": "OpenRouter (Recommended)",
                        "openai": "OpenAI (Official)",
                        "qwen": "Alibaba Qwen (DashScope)",
                        "deepseek": "DeepSeek (Official)",
                        "xai": "X.AI (Grok)",
                        "x.ai": "X.AI (Grok)",
                        "groq": "Groq (Meta Llama/Mixtral)",
                        "gemini": "Google Gemini (via OpenRouter)",
                        "siliconflow": "SiliconFlow (硅基流动)",
                        "ollama": "Ollama (Localhost)",
                        "arli": "Arli"
                    }
                    display_name = provider_map.get(provider.lower(), "Custom")
                    self.controls["AI"]["provider"].setCurrentText(display_name)
                    print(f"[INFO] Loaded provider: {display_name}")
            
            # Load base_url if available
            base_url = account_data.get("base_url", "")
            if base_url and hasattr(self, 'controls') and "AI" in self.controls:
                if "base_url" in self.controls["AI"]:
                    self.controls["AI"]["base_url"].setText(base_url)
                    print(f"[INFO] Loaded base_url: {base_url}")
            
            # Load api_key if available
            api_key = account_data.get("API-Key", "")
            if api_key and hasattr(self, 'controls') and "AI" in self.controls:
                if "api_key" in self.controls["AI"]:
                    self.controls["AI"]["api_key"].setText(api_key)
                    print(f"[INFO] Loaded api_key: {'*' * min(8, len(api_key))}")
            
            # Get models list from the JSON file
            models = account_data.get("models", [])
            if models:
                print(f"[INFO] Loaded {len(models)} models from account.json")
            return models if isinstance(models, list) else []
            
        except Exception as e:
            print(f"[WARN] Failed to load AI configuration from account.json: {e}")
            return []


    def test_ai_connection(self):
        """Test the AI API connection."""
        api_key = self.controls["AI"]["api_key"].text().strip()
        base_url = self.controls["AI"]["base_url"].text().strip()
        
        if not api_key or not base_url:
            QMessageBox.warning(self, "Missing Information", "Please provide both API Key and Base URL.")
            return
        
        self.btn_test_connection.setEnabled(False)
        self.btn_test_connection.setText("Testing...")
        
        try:
            # Simple test request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.controls["AI"]["model"].currentText(),
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }
            
            response = requests.post(base_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "✓ Connection successful!")
            else:
                QMessageBox.warning(self, "Connection Failed", 
                    f"Status Code: {response.status_code}\n{response.text[:200]}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error:\n{str(e)}")
        finally:
            self.btn_test_connection.setEnabled(True)
            self.btn_test_connection.setText("Test Connection")
    #-------------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------------
    # Create the Appearance Settings Page
    def create_appearance_page_in_setting(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # --- Group 1: Theme ---
        self.group_theme = QGroupBox("Theme & UI")
        form = QFormLayout(self.group_theme)
        form.setVerticalSpacing(15)

        self.lbl_theme_mode = QLabel("Theme mode:")
        mode_combo = QComboBox()
        mode_combo.addItems(["Light"])
        mode_combo.setCurrentText(self.settings.value("Appearance/theme", "Light"))
        mode_combo.currentTextChanged.connect(lambda theme: self.theme_changed.emit(theme))
        self.controls["Appearance"]["theme"] = mode_combo
        
        self.chk_toolbar_icons = QCheckBox("Show toolbar icons")
        self.chk_toolbar_icons.setChecked(self.settings.value("Appearance/toolbar_icons", True, type=bool))
        self.controls["Appearance"]["toolbar_icons"] = self.chk_toolbar_icons

        self.chk_animations = QCheckBox("Enable panel animations")
        self.chk_animations.setChecked(self.settings.value("Appearance/animations", True, type=bool))
        self.controls["Appearance"]["animations"] = self.chk_animations

        form.addRow(self.lbl_theme_mode, mode_combo)
        form.addRow("", self.chk_toolbar_icons)
        form.addRow("", self.chk_animations)
        layout.addWidget(self.group_theme)

        # --- Group 2: Panel Sizes ---
        self.group_panels = QGroupBox("Default Panel Sizes")
        panel_layout = QFormLayout(self.group_panels)
        
        self.lbl_left_width = QLabel("Left Panel Width:")
        left_width_spin = QSpinBox()
        left_width_spin.setRange(200, 600)
        left_width_spin.setSingleStep(10)
        left_width_spin.setValue(self.settings.value("Appearance/left_panel_width", 320, type=int))
        self.controls["Appearance"]["left_panel_width"] = left_width_spin
        
        self.lbl_right_width = QLabel("Right Panel Width:")
        right_width_spin = QSpinBox()
        right_width_spin.setRange(250, 800)
        right_width_spin.setSingleStep(10)
        right_width_spin.setValue(self.settings.value("Appearance/right_panel_width", 400, type=int))
        self.controls["Appearance"]["right_panel_width"] = right_width_spin
        
        panel_layout.addRow(self.lbl_left_width, left_width_spin)
        panel_layout.addRow(self.lbl_right_width, right_width_spin)
        layout.addWidget(self.group_panels)

        # --- Group 3: Central Background ---
        self.group_bg = QGroupBox("Central Background")
        bg_layout = QVBoxLayout(self.group_bg)
        
        self.lbl_bg_instruction = QLabel("Select a custom background image (JPG, PNG, GIF):")
        
        self.bg_path_input = QLineEdit()
        self.bg_path_input.setPlaceholderText("No image selected (Default)")
        self.bg_path_input.setReadOnly(True)
        saved_bg = self.settings.value("Appearance/central_background", "")
        self.bg_path_input.setText(saved_bg)
        self.controls["Appearance"]["central_background"] = self.bg_path_input

        btn_layout = QHBoxLayout()
        self.btn_browse_bg = QPushButton("Browse Image...")
        self.btn_browse_bg.clicked.connect(self.browse_background_image)
        
        self.btn_clear_bg = QPushButton("Clear / Reset")
        self.btn_clear_bg.clicked.connect(lambda: self.bg_path_input.setText(""))

        btn_layout.addWidget(self.btn_browse_bg)
        btn_layout.addWidget(self.btn_clear_bg)
        
        bg_layout.addWidget(self.lbl_bg_instruction)
        bg_layout.addWidget(self.bg_path_input)
        bg_layout.addLayout(btn_layout)
        
        layout.addWidget(self.group_bg)
        layout.addStretch()
        return page

    def browse_background_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Background Image", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.bg_path_input.setText(file_path)
    #-------------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------------
    # Create the Font Settings Page
    def create_font_page_in_setting(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        self.group_font = QGroupBox("Font Settings")
        font_layout = QVBoxLayout(self.group_font)

        # --- Font Type ---
        self.lbl_font_type = QLabel("Font type:")
        font_combo = QComboBox()
        
        font_list = [
            "Arial", "Calibri", "Times New Roman", "Courier New", 
            "Microsoft YaHei", "SimHei", "SimSun", 
            "KaiTi", "FangSong", 
            "STHeiti", "STKaiti", "STSong", "STFangsong", "PingFang SC"
        ]
        font_combo.addItems(font_list)
        saved_font = self.settings.value("Font/type", "Microsoft YaHei")
        font_combo.setCurrentText(saved_font)
        font_combo.currentTextChanged.connect(self.update_font_preview)
        font_layout.addWidget(self.lbl_font_type)
        font_layout.addWidget(font_combo)
        self.controls["Font"]["type"] = font_combo

        # --- Font Size ---
        self.lbl_font_size = QLabel("Font size:")
        size_combo = QComboBox()
        size_combo.addItems([str(s) for s in range(8, 30)])
        saved_size = self.settings.value("Font/size", "10")
        size_combo.setCurrentText(saved_size)
        size_combo.currentTextChanged.connect(self.update_font_preview)
        font_layout.addWidget(self.lbl_font_size)
        font_layout.addWidget(size_combo)
        self.controls["Font"]["size"] = size_combo

        # --- Font Preview ---
        self.lbl_font_preview = QLabel("Preview:")
        self.font_preview = QTextEdit()
        self.font_preview.setPlainText("The quick brown fox jumps over the lazy dog.\n快速的棕色狐狸跳过懒狗。\n0123456789")
        self.font_preview.setMaximumHeight(100)
        self.font_preview.setReadOnly(True)
        font_layout.addWidget(self.lbl_font_preview)
        font_layout.addWidget(self.font_preview)
        
        # Update preview initially
        self.update_font_preview()

        layout.addWidget(self.group_font)
        layout.addStretch()
        return page

    def update_font_preview(self):
        """Update the font preview text."""
        font_name = self.controls["Font"]["type"].currentText()
        font_size = int(self.controls["Font"]["size"].currentText())
        font = QFont(font_name, font_size)
        self.font_preview.setFont(font)
    #-------------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------------
    # Create the Language Settings Page
    def create_language_page_in_setting(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        self.group_language = QGroupBox("Language Settings")
        lang_layout = QVBoxLayout(self.group_language)
        
        # --- Language Type ---
        self.lbl_lang_type = QLabel("Language type:")
        language_combo = QComboBox()
        language_combo.addItems(["English", "Chinese"])
        saved_lang = self.settings.value("Language/type", "English")
        language_combo.setCurrentText(saved_lang)
        language_combo.currentTextChanged.connect(lambda lang: self.language_changed.emit(lang))
        lang_layout.addWidget(self.lbl_lang_type)
        lang_layout.addWidget(language_combo)
        self.controls["Language"]["type"] = language_combo
        
        # --- Restart Warning ---
        warning_label = QLabel("⚠️ Application restart required for language changes to take full effect.")
        warning_label.setStyleSheet("color: #ff6b00; padding: 10px; background-color: #fff3e0; border-radius: 4px;")
        warning_label.setWordWrap(True)
        lang_layout.addWidget(warning_label)
        
        layout.addWidget(self.group_language)
        layout.addStretch()
        return page
    #-------------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------------
    # Create the Search Settings Page
    def create_search_page_in_setting(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        self.group_search = QGroupBox("Search Engine")
        search_layout = QVBoxLayout(self.group_search)
        
        self.lbl_search_engine = QLabel("Default search engine:")
        
        # --- Search Engine ---
        baidu_radio = QRadioButton("Baidu")
        google_radio = QRadioButton("Google")
        
        if self.settings.value("Search/Google", False, type=bool):
            google_radio.setChecked(True)
        else:
            baidu_radio.setChecked(True)

        bg = QButtonGroup(page)
        bg.addButton(baidu_radio)
        bg.addButton(google_radio)

        search_layout.addWidget(self.lbl_search_engine)
        search_layout.addWidget(baidu_radio)
        search_layout.addWidget(google_radio)

        self.controls["Search"]["Baidu"] = baidu_radio
        self.controls["Search"]["Google"] = google_radio
        
        layout.addWidget(self.group_search)
        layout.addStretch()
        return page
    #-------------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------------
    # Create the Result Chart Settings Page
    def create_result_chart_page_in_setting(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        self.group_result_chart = QGroupBox("Result Chart Settings")
        chart_layout = QFormLayout(self.group_result_chart)
        chart_layout.setVerticalSpacing(10)

        # --- Curve Style ---
        self.lbl_curve_style = QLabel("Curve Style:")
        curve_combo = QComboBox()
        curve_combo.addItems(["Solid", "Dashed", "Dotted"])
        curve_combo.setCurrentText(self.settings.value("ResultChart/curve_style", "Solid"))
        chart_layout.addRow(self.lbl_curve_style, curve_combo)
        self.controls["ResultChart"]["curve_style"] = curve_combo

        # --- Curve Color ---
        self.lbl_curve_color = QLabel("Curve Color:")
        curve_color_combo = QComboBox()
        
        self.color_presets = [
            ("Dark Blue", "#1F4788"),
            ("Navy Blue", "#000080"),
            ("Red", "#FF0000"),
            ("Green", "#00AA00"),
            ("Black", "#000000"),
            ("Purple", "#800080"),
            ("Orange", "#FF8C00"),
            ("Cyan", "#00FFFF"),
            ("Dark Gray", "#404040"),
            ("Brown", "#8B4513"),
        ]
        
        for color_name, color_hex in self.color_presets:
            curve_color_combo.addItem(color_name, color_hex)
        
        saved_curve_color = self.settings.value("ResultChart/curve_color", "#1F4788")
        for i, (name, hex_val) in enumerate(self.color_presets):
            if hex_val == saved_curve_color:
                curve_color_combo.setCurrentIndex(i)
                break
        
        self.setup_color_combo_display(curve_color_combo)
        chart_layout.addRow(self.lbl_curve_color, curve_color_combo)
        self.controls["ResultChart"]["curve_color"] = curve_color_combo

        # --- Curve Width ---
        self.lbl_curve_width = QLabel("Curve Width:")
        curve_width_combo = QComboBox()
        curve_width_combo.addItems(["1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0"])
        saved_width = self.settings.value("ResultChart/curve_width", "2.0")
        if saved_width in ["1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0"]:
            curve_width_combo.setCurrentText(saved_width)
        else:
            curve_width_combo.setCurrentText("2.0")
        chart_layout.addRow(self.lbl_curve_width, curve_width_combo)
        self.controls["ResultChart"]["curve_width"] = curve_width_combo

        # --- Scatter Style ---
        self.lbl_scatter_style = QLabel("Scatter Style:")
        scatter_combo = QComboBox()
        scatter_combo.addItems(["Circle", "Square", "Triangle"])
        scatter_combo.setCurrentText(self.settings.value("ResultChart/scatter_style", "Circle"))
        chart_layout.addRow(self.lbl_scatter_style, scatter_combo)
        self.controls["ResultChart"]["scatter_style"] = scatter_combo

        # --- Axis Style ---
        self.lbl_axis_style = QLabel("Axis Style:")
        axis_combo = QComboBox()
        axis_combo.addItems(["Solid", "Dashed", "Dotted"])
        axis_combo.setCurrentText(self.settings.value("ResultChart/axis_style", "Solid"))
        chart_layout.addRow(self.lbl_axis_style, axis_combo)
        self.controls["ResultChart"]["axis_style"] = axis_combo

        # --- Grid Style ---
        self.lbl_grid_style = QLabel("Grid Style:")
        grid_combo = QComboBox()
        grid_combo.addItems(["Solid", "Dashed", "Dotted"])
        grid_combo.setCurrentText(self.settings.value("ResultChart/grid_style", "Solid"))
        chart_layout.addRow(self.lbl_grid_style, grid_combo)
        self.controls["ResultChart"]["grid_style"] = grid_combo

        # --- Background Color ---
        self.lbl_bg_color = QLabel("Background Color:")
        bg_color_combo = QComboBox()
        
        self.bg_color_presets = [
            ("White", "#FFFFFF"),
            ("Light Gray", "#FAFAFA"),
            ("Light Blue", "#F0F8FF"),
            ("Light Green", "#F0FFF0"),
            ("Cream", "#FFFDD0"),
            ("Snow", "#FFFAFA"),
            ("Ghost White", "#F8F8FF"),
            ("Light Yellow", "#FFFFE0"),
            ("Off White", "#FAF0E6"),
            ("Honeydew", "#F0FFF0"),
        ]
        
        for color_name, color_hex in self.bg_color_presets:
            bg_color_combo.addItem(color_name, color_hex)
        
        saved_bg_color = self.settings.value("ResultChart/bg_color", "#FAFAFA")
        for i, (name, hex_val) in enumerate(self.bg_color_presets):
            if hex_val == saved_bg_color:
                bg_color_combo.setCurrentIndex(i)
                break
        
        self.setup_color_combo_display(bg_color_combo)
        chart_layout.addRow(self.lbl_bg_color, bg_color_combo)
        self.controls["ResultChart"]["bg_color"] = bg_color_combo

        layout.addWidget(self.group_result_chart)
        
        # --- Export/Import Buttons ---
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Export Settings")
        btn_export.clicked.connect(self.export_chart_settings)
        btn_import = QPushButton("Import Settings")
        btn_import.clicked.connect(self.import_chart_settings)
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_import)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        return page

    def setup_color_combo_display(self, combo_box):
        """Setup color combo box to display color preview."""
        def update_color_display():
            hex_color = combo_box.currentData()
            if hex_color:
                combo_box.setStyleSheet(f"""
                    QComboBox {{
                        background-color: {hex_color};
                        color: {'#000000' if hex_color in ['#FFFFFF', '#FFFDD0', '#FFFAFA', '#F8F8FF', '#FFFFE0', '#FAF0E6', '#F0FFF0'] else '#FFFFFF'};
                        padding: 2px;
                        border-radius: 3px;
                    }}
                """)
        
        combo_box.currentIndexChanged.connect(update_color_display)
        update_color_display()

    def export_chart_settings(self):
        """Export chart settings to JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            settings = {
                "curve_style": self.controls["ResultChart"]["curve_style"].currentText(),
                "curve_color": self.controls["ResultChart"]["curve_color"].currentData(),
                "curve_width": self.controls["ResultChart"]["curve_width"].currentText(),
                "scatter_style": self.controls["ResultChart"]["scatter_style"].currentText(),
                "axis_style": self.controls["ResultChart"]["axis_style"].currentText(),
                "grid_style": self.controls["ResultChart"]["grid_style"].currentText(),
                "bg_color": self.controls["ResultChart"]["bg_color"].currentData()
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(settings, f, indent=2)
                QMessageBox.information(self, "Success", "Chart settings exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings:\n{str(e)}")

    def import_chart_settings(self):
        """Import chart settings from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Chart Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    settings = json.load(f)
                
                # Apply imported settings
                if "curve_style" in settings:
                    self.controls["ResultChart"]["curve_style"].setCurrentText(settings["curve_style"])
                if "curve_width" in settings:
                    self.controls["ResultChart"]["curve_width"].setCurrentText(settings["curve_width"])
                if "scatter_style" in settings:
                    self.controls["ResultChart"]["scatter_style"].setCurrentText(settings["scatter_style"])
                if "axis_style" in settings:
                    self.controls["ResultChart"]["axis_style"].setCurrentText(settings["axis_style"])
                if "grid_style" in settings:
                    self.controls["ResultChart"]["grid_style"].setCurrentText(settings["grid_style"])
                
                QMessageBox.information(self, "Success", "Chart settings imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings:\n{str(e)}")
    #-------------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------------
    # Change the current page
    def change_page(self, current, previous):
        if not current: return
        
        if current == self.item_ai:
            self.stack.setCurrentWidget(self.ai_page)
        elif current == self.item_appearance:
            self.stack.setCurrentWidget(self.appearance_page)
        elif current == self.item_font:
            self.stack.setCurrentWidget(self.font_page)
        elif current == self.item_language:
            self.stack.setCurrentWidget(self.language_page)
        elif current == self.item_search:
            self.stack.setCurrentWidget(self.search_page)
        elif current == self.item_result_chart:
            self.stack.setCurrentWidget(self.result_chart_page)

    #-------------------------------------------------------------------------------------
    # Validate settings before saving
    def validate_settings(self):
        """Validate all settings before saving."""
        # Validate AI settings
        api_key = self.controls["AI"]["api_key"].text().strip()
        base_url = self.controls["AI"]["base_url"].text().strip()
        
        if api_key and not base_url:
            QMessageBox.warning(self, "Validation Error", "Base URL is required when API Key is provided.")
            return False
        
        if base_url and not base_url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Validation Error", "Base URL must start with http:// or https://")
            return False
        
        return True

    #-------------------------------------------------------------------------------------
    # Apply settings without closing
    def apply(self):
        """Apply settings without closing the dialog."""
        if not self.validate_settings():
            return
        
        self.save_all_settings()
        self.apply_settings_signal.emit()
        self.settings_page_operation_signal.emit("Settings applied successfully!")
        QMessageBox.information(self, "Applied", "Settings have been applied.")


    #-------------------------------------------------------------------------------------
    # Save all settings
    def save_all_settings(self):
        """Save all settings to file."""
        # AI settings
        ai = self.controls["AI"]
        self.settings.setValue("AI/provider", ai["provider"].currentText())
        self.settings.setValue("AI/model", ai["model"].currentText())
        self.settings.setValue("AI/base_url", ai["base_url"].text().strip())
        self.settings.setValue("AI/api_key", ai["api_key"].text().strip())
        self.settings.setValue("AI/system_prompt", ai["system_prompt"].toPlainText().strip())
        self.settings.setValue("AI/temperature", ai["temperature"].value() / 10.0)
        
        # Appearance settings
        self.settings.setValue("Appearance/theme", self.controls["Appearance"]["theme"].currentText())
        self.settings.setValue("Appearance/toolbar_icons", self.controls["Appearance"]["toolbar_icons"].isChecked())
        self.settings.setValue("Appearance/animations", self.controls["Appearance"]["animations"].isChecked())
        self.settings.setValue("Appearance/left_panel_width", self.controls["Appearance"]["left_panel_width"].value())
        self.settings.setValue("Appearance/right_panel_width", self.controls["Appearance"]["right_panel_width"].value())
        self.settings.setValue("Appearance/central_background", self.controls["Appearance"]["central_background"].text())

        # Font settings
        font_type = self.controls["Font"]["type"].currentText()
        font_size = self.controls["Font"]["size"].currentText()
        self.settings.setValue("Font/type", font_type)
        self.settings.setValue("Font/size", font_size)
        self.font_changed.emit(font_type, int(font_size))

        # Language settings
        self.settings.setValue("Language/type", self.controls["Language"]["type"].currentText())

        # Search settings
        self.settings.setValue("Search/Baidu", self.controls["Search"]["Baidu"].isChecked())
        self.settings.setValue("Search/Google", self.controls["Search"]["Google"].isChecked())

        # Result chart settings
        result_chart = self.controls["ResultChart"]
        self.settings.setValue("ResultChart/curve_style", result_chart["curve_style"].currentText())
        self.settings.setValue("ResultChart/curve_color", result_chart["curve_color"].currentData())
        self.settings.setValue("ResultChart/curve_width", result_chart["curve_width"].currentText())
        self.settings.setValue("ResultChart/scatter_style", result_chart["scatter_style"].currentText())
        self.settings.setValue("ResultChart/axis_style", result_chart["axis_style"].currentText())
        self.settings.setValue("ResultChart/grid_style", result_chart["grid_style"].currentText())
        self.settings.setValue("ResultChart/bg_color", result_chart["bg_color"].currentData())

        self.settings.sync()
        self.ai_settings_changed.emit()

    #-------------------------------------------------------------------------------------
    # Accept and save
    def accept(self):
        """Save all settings to file (without applying to UI or closing dialog)."""
        if not self.validate_settings():
            return
        
        # Save settings to file only (no UI changes)
        self.save_all_settings()
        self.settings_page_operation_signal.emit("Settings saved to file successfully!")
        
        # Show confirmation message
        QMessageBox.information(self, "Saved", "Settings have been saved to file.\nClick 'Apply' to apply them immediately.")
        
        # Do NOT close dialog - let user continue editing
        # Do NOT call super().accept()
    #-------------------------------------------------------------------------------------
    # Reject and discard
    def reject(self):

        self.settings_page_operation_signal.emit("Settings discarded!")
        super().reject()

    #-------------------------------------------------------------------------------------
    # Reset AI preferences
    def reset_AI_preferences(self):

        ai = self.controls["AI"]

        ai["provider"].setCurrentText("OpenRouter (Recommended)")
        ai["model"].setCurrentText("gpt-4-turbo")
        ai["base_url"].setText("https://openrouter.ai/api/v1/chat/completions")
        ai["api_key"].setText("")
        ai["system_prompt"].setPlainText("You are a helpful assistant.")
        ai["temperature"].setValue(7)
        
        QMessageBox.information(self, "Reset", "AI Settings reset to defaults.")

    #-------------------------------------------------------------------------------------
    # Update UI Texts for Translation
    def update_ui_texts(self, lang_manager):

        """Refreshes all text based on the current language."""
        if not lang_manager: return
        
        self.setWindowTitle(lang_manager.get_text("Preferences"))
        self.item_ai.setText(0, lang_manager.get_text("AI Configuration"))
        self.item_appearance.setText(0, lang_manager.get_text("Appearance"))
        self.item_font.setText(0, lang_manager.get_text("Font Settings"))
        self.item_language.setText(0, lang_manager.get_text("Language Settings"))
        self.item_search.setText(0, lang_manager.get_text("Search"))
        self.item_result_chart.setText(0, lang_manager.get_text("Result Chart"))

        self.button_box.button(QDialogButtonBox.Ok).setText(lang_manager.get_text("Save"))
        self.button_box.button(QDialogButtonBox.Apply).setText(lang_manager.get_text("Apply"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(lang_manager.get_text("Cancel"))

    #-------------------------------------------------------------------------------------
    # Getters for retrieving specific settings
    def get_api_key(self):
        return self.settings.value("AI/api_key", "", type=str)

    def get_base_url(self):
        return self.settings.value("AI/base_url", "", type=str)

    def get_system_prompt(self):
        return self.settings.value("AI/system_prompt", "You are a helpful assistant.", type=str)

    def get_model(self):
        return self.settings.value("AI/model", "gpt-4-turbo", type=str)
