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
    QRadioButton, QButtonGroup, QScrollArea, QSpinBox, QSizePolicy,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle
)
from PySide6.QtCore import Qt, Signal, QSettings, QRect, QPoint, QEvent
from PySide6.QtGui import QFont, QIcon, QColor, QPalette
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
    connection_test_signal = Signal(bool, str)  # (success, message)
    models_changed_signal = Signal(list, str)   # (models_list, selected_model)


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

        # Provider cache
        self.account_providers = []
        self.custom_account_provider = None

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

        # 2. Model Selection - populated dynamically from account.json
        self.lbl_model = QLabel("Model:")
        
        model_container = QWidget()
        model_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        model_layout = QHBoxLayout(model_container)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(5)
        
        self.models_combo = QComboBox()
        self.models_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.models_delegate = _ModelDeleteDelegate(self.models_combo.view(), delete_callback=self.delete_model_callback)
        self.models_combo.view().setItemDelegate(self.models_delegate)
        self.models_combo.view().setMouseTracking(True)
        self.models_combo.view().viewport().installEventFilter(self)
        
        self.btn_add_model = QPushButton()
        self.btn_add_model.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-plus-math-100.png")))
        self.btn_add_model.setObjectName("Add_Custom_Model_Button")
        self.btn_add_model.setFixedSize(34, 34)
        self.btn_add_model.setToolTip("Add Custom Model")
        self.btn_add_model.clicked.connect(self.add_custom_model_dialog)
        
        model_layout.addWidget(self.models_combo, 1)
        model_layout.addWidget(self.btn_add_model)
        
        self.controls["AI"]["model"] = self.models_combo

        # 3. Base URL
        self.lbl_base_url = QLabel("Base URL:")
        base_url_input = QLineEdit()
        base_url_input.setPlaceholderText("https://...")
        default_url = "https://openrouter.ai/api/v1/chat/completions"
        base_url_input.setText(self.settings.value("AI/base_url", default_url))
        self.controls["AI"]["base_url"] = base_url_input

        # 4. API Key
        self.lbl_api_key = QLabel("API Key:")
        
        api_key_container = QWidget()
        api_key_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        api_key_layout = QHBoxLayout(api_key_container)
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        api_key_layout.setSpacing(5)
        
        api_input = QLineEdit()
        api_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        api_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_input.setPlaceholderText("sk-...")
        api_input.setText(self.settings.value("AI/api_key", ""))
        self.controls["AI"]["api_key"] = api_input
        
        self.btn_toggle_key = QPushButton()
        self.btn_toggle_key.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-blind-100.png")))
        self.btn_toggle_key.setObjectName("Show_API_Key_Button")
        self.btn_toggle_key.setFixedSize(34, 34)
        self.btn_toggle_key.setToolTip("Show/Hide API Key")
        self.btn_toggle_key.clicked.connect(self.toggle_api_key_visibility)



        api_key_layout.addWidget(api_input, 1)
        api_key_layout.addWidget(self.btn_toggle_key)

        # 5. Test Connection Button - 横向布局
        test_connection_container = QWidget()
        test_connection_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        test_connection_layout = QHBoxLayout(test_connection_container)
        test_connection_layout.setContentsMargins(0, 0, 0, 0)
        test_connection_layout.setSpacing(5)
        
        self.btn_test_connection = QPushButton()
        self.btn_test_connection.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-rdp-connection-100.png")))
        self.btn_test_connection.setObjectName("Test_API_Connection_Button")
        self.btn_test_connection.setFixedSize(34, 34)
        self.btn_test_connection.setToolTip("Test API Connection")
        self.btn_test_connection.clicked.connect(self.on_test_connection_clicked)
        self.controls["AI"]["test_connection_btn"] = self.btn_test_connection
        
        self.lbl_connection_status = QLabel("")
        self.lbl_connection_status.setStyleSheet("color: gray; font-size: 13px;")
        
        test_connection_layout.addStretch()
        test_connection_layout.addWidget(self.lbl_connection_status)
        test_connection_layout.addSpacing(10)
        test_connection_layout.addWidget(self.btn_test_connection)

        api_layout.addRow(self.lbl_provider, self.provider_combo)
        api_layout.addRow(self.lbl_base_url, base_url_input)
        api_layout.addRow(self.lbl_model, model_container)
        api_layout.addRow(self.lbl_api_key, api_key_container)
        api_layout.addRow("", test_connection_container)
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
        """Handle provider change: update base URL, API key and models list."""
        matched_provider = self._account_provider_for_display(provider_name)
        
        # Standard URL map - always used as the correct default
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
        
        # Set base_url from standard map (always correct for known providers)
        if provider_name in url_map:
            self.controls["AI"]["base_url"].setText(url_map[provider_name])
        elif self._is_custom_provider_display(provider_name):
            # For Custom, use account.json or clear
            if matched_provider:
                self.controls["AI"]["base_url"].setText(matched_provider.get("base_url", ""))
            else:
                self.controls["AI"]["base_url"].clear()
        
        # Set API key from account.json if available
        if matched_provider and "api_key" in self.controls["AI"]:
            self.controls["AI"]["api_key"].setText(matched_provider.get("API-Key", ""))
        
        if matched_provider:
            # Populate models from account.json
            self._populate_models_for_provider(provider_name)
            saved_model = self.settings.value("AI/model", "")
            if saved_model:
                idx = self.controls["AI"]["model"].findText(saved_model)
                if idx != -1:
                    self.controls["AI"]["model"].setCurrentIndex(idx)
            print(f"[INFO] Settings Page: loaded config for matched provider '{provider_name}' from account.json")
        else:
            self.controls["AI"]["model"].clear()
        
        # IMPORTANT: Save base_url and api_key to settings.ini BEFORE emitting models_changed_signal.
        # This ensures that when update_model_for_chat_controller reads from settings.ini,
        # it gets the NEW provider's values, not the OLD provider's stale values.
        self.settings.setValue("AI/base_url", self.controls["AI"]["base_url"].text().strip())
        self.settings.setValue("AI/api_key", self.controls["AI"]["api_key"].text().strip())
        self.settings.sync()
        print(f"[INFO] on_provider_changed: saved new base_url/api_key to settings.ini for '{provider_name}'")
        
        self._emit_models_changed()

    # -------------------------------------------------------------------------
    # Provider helper methods (ported from AIchat_Combo)
    # -------------------------------------------------------------------------
    def _provider_name(self, provider):
        if not isinstance(provider, dict):
            return ""
        return str(provider.get("Provider") or provider.get("provider") or "").lower().strip()

    def _provider_matches_display(self, provider_name, display_text):
        provider = str(provider_name or "").lower().strip()
        display = str(display_text or "").lower().strip()
        return bool(provider and display and (provider in display or display in provider))

    def _is_custom_provider_display(self, display_text):
        return str(display_text or "").lower().strip() == "custom"

    def _find_custom_account_provider(self):
        explicit_custom = None
        known_items = [
            self.provider_combo.itemText(i)
            for i in range(self.provider_combo.count())
            if self.provider_combo.itemText(i).lower().strip() != "custom"
        ]
        for provider in self.account_providers:
            provider_name = self._provider_name(provider)
            if provider_name == "custom":
                explicit_custom = provider
                break
            if provider_name and not any(self._provider_matches_display(provider_name, item) for item in known_items):
                if explicit_custom is None:
                    explicit_custom = provider
        return explicit_custom

    def _account_provider_for_display(self, display_text):
        if self._is_custom_provider_display(display_text):
            if self.custom_account_provider is None:
                self.custom_account_provider = self._find_custom_account_provider()
            return self.custom_account_provider
        for provider in self.account_providers:
            provider_name = provider.get("Provider") or provider.get("provider") or ""
            if self._provider_matches_display(provider_name, display_text):
                return provider
        return None

    def _provider_combo_index_for_account_provider(self, provider_name):
        for i in range(self.provider_combo.count()):
            item_text = self.provider_combo.itemText(i)
            if item_text.lower().strip() == "custom":
                continue
            if self._provider_matches_display(provider_name, item_text):
                return i
        return self.provider_combo.findText("Custom") if self.custom_account_provider else -1

    def _account_provider_name_for_display(self, display_text):
        matched_provider = self._account_provider_for_display(display_text)
        if matched_provider:
            return (matched_provider.get("Provider") or matched_provider.get("provider") or "").lower().strip()
        if self._is_custom_provider_display(display_text):
            return "custom"
        return str(display_text or "").lower().strip()

    def _populate_models_for_provider(self, provider_name):
        """Load model list for the given provider from account.json and populate the combo."""
        self.controls["AI"]["model"].blockSignals(True)
        self.controls["AI"]["model"].clear()
        matched = self._account_provider_for_display(provider_name)
        if matched:
            models = matched.get("models", [])
            for m in models:
                self.controls["AI"]["model"].addItem(m)
        self.controls["AI"]["model"].blockSignals(False)

    def _current_models(self):
        model_combo = self.controls["AI"]["model"]
        return [model_combo.itemText(i) for i in range(model_combo.count())]

    def _emit_models_changed(self):
        self.models_changed_signal.emit(self._current_models(), self.controls["AI"]["model"].currentText())

    def add_custom_model_dialog(self):
        """Show dialog to add a custom model name for the current provider."""
        from PySide6.QtWidgets import QInputDialog
        provider_name = self.provider_combo.currentText()
        
        model_name, ok = QInputDialog.getText(
            self, "Add Custom Model", f"Enter custom model name for {provider_name}:"
        )
        if ok and model_name.strip():
            model_name = model_name.strip()
            if self.models_combo.findText(model_name) != -1:
                QMessageBox.warning(self, "Warning", "This model name already exists!")
                return
            self.models_combo.addItem(model_name)
            self.models_combo.setCurrentText(model_name)
            self.save_new_model_to_account_json(provider_name, model_name)
            self._emit_models_changed()
            QMessageBox.information(self, "Success", f"Model '{model_name}' has been added successfully!")

    def save_new_model_to_account_json(self, provider_name, new_model):
        """Save the new model back to account.json for the matching provider."""
        import json
        usr_folder = utils.get_global_usr_dir()
        account_file = usr_folder / "Settings/account.json"
        if not account_file.exists():
            return
        try:
            with open(account_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return

        updated = False
        provider_name_lower = str(provider_name or "").lower().strip()
        target_map = {
            "OpenRouter (Recommended)": "OpenRouter", "OpenAI (Official)": "OpenAI",
            "Alibaba Qwen (DashScope)": "Qwen", "DeepSeek (Official)": "DeepSeek",
            "X.AI (Grok)": "X.AI", "Groq (Meta Llama/Mixtral)": "Groq",
            "Google Gemini (via OpenRouter)": "Gemini", "SiliconFlow (硅基流动)": "SiliconFlow",
            "Ollama (Localhost)": "Ollama", "Arli": "Arli",
        }
        target_name = target_map.get(provider_name, "Custom")
        target_lower = target_name.lower().strip()

        def update_item(item):
            nonlocal updated
            prov = str(item.get("Provider") or item.get("provider") or "").lower().strip()
            if prov and (prov == target_lower or target_lower in prov or prov in target_lower):
                if "models" not in item:
                    item["models"] = []
                if new_model not in item["models"]:
                    item["models"].append(new_model)
                    updated = True

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    update_item(item)
                    if updated:
                        break

        if updated:
            try:
                with open(account_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"[INFO] Added model '{new_model}' for provider '{provider_name}' in account.json")
                self._set_account_provider_cache(data)
            except Exception as e:
                print(f"[ERROR] Failed to save account.json with new model: {e}")

    def toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        api_input = self.controls["AI"]["api_key"]
        if api_input.echoMode() == QLineEdit.EchoMode.Password:
            api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_key.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-eye-100.png")))
        else:
            api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_key.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-blind-100.png")))
            
    def _set_account_provider_cache(self, data):
        if isinstance(data, list):
            self.account_providers = [item for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            if "Provider" in data or "provider" in data:
                self.account_providers = [data]
            else:
                providers = []
                for key, val in data.items():
                    if isinstance(val, dict):
                        item = val.copy()
                        if "Provider" not in item and "provider" not in item:
                            item["Provider"] = key
                        providers.append(item)
                self.account_providers = providers
        else:
            self.account_providers = []
        self.custom_account_provider = self._find_custom_account_provider()

    def load_all_AI_configs(self, config_path):
        """Load all provider configurations from account.json."""
        import json
        if not os.path.exists(config_path):
            return []
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load account file: {e}")
            return []

        providers = []
        def parse_single(item):
            if not isinstance(item, dict):
                return None
            prov = item.get("Provider") or item.get("provider")
            base = item.get("base_url") or item.get("baseUrl")
            key = item.get("API-Key") or item.get("api_key") or item.get("apiKey")
            models = item.get("models")
            if prov and models is not None:
                if isinstance(models, list):
                    model_list = list(models)
                elif isinstance(models, (tuple, set)):
                    model_list = list(models)
                else:
                    model_list = [str(models)]
                return {
                    "Provider": str(prov),
                    "base_url": str(base or ""),
                    "API-Key": str(key or ""),
                    "models": model_list
                }
            return None

        if isinstance(data, list):
            for item in data:
                parsed = parse_single(item)
                if parsed:
                    providers.append(parsed)
        elif isinstance(data, dict):
            parsed = parse_single(data)
            if parsed:
                providers.append(parsed)
            else:
                for key, val in data.items():
                    if isinstance(val, dict):
                        item = val.copy()
                        if "Provider" not in item and "provider" not in item:
                            item["Provider"] = key
                        parsed = parse_single(item)
                        if parsed:
                            providers.append(parsed)
        return providers

    def update_provider_states(self, providers):
        """Enable/disable provider combobox items based on account.json definition."""
        self.account_providers = providers
        self.custom_account_provider = self._find_custom_account_provider()
        
        enabled_color = QColor("#333333")
        disabled_color = QColor("#9ca3af")

        model = self.provider_combo.model()
        for i in range(self.provider_combo.count()):
            item_text = self.provider_combo.itemText(i)
            is_custom = self._is_custom_provider_display(item_text)
            is_enabled = is_custom or self._account_provider_for_display(item_text) is not None
            
            item = model.item(i, 0)
            if item:
                item.setEnabled(is_enabled)
                item.setData(enabled_color if is_enabled else disabled_color, Qt.ForegroundRole)
                item.setData(is_enabled, Qt.UserRole)  # Store enabled state for delegate
                item.setToolTip("" if is_enabled else "Not configured in account.json")
        
        # Use a custom delegate to ensure disabled items appear gray even with global QSS
        delegate = _ProviderItemDelegate(self.provider_combo.view())
        self.provider_combo.view().setItemDelegate(delegate)
        self.provider_combo.view().viewport().update()

        if providers:
            first_provider_name = providers[0].get("Provider") or providers[0].get("provider") or ""
            default_index = self._provider_combo_index_for_account_provider(first_provider_name)
            if default_index != -1:
                self.provider_combo.setCurrentIndex(default_index)

        self.on_provider_changed(self.provider_combo.currentText())


    def on_test_connection_clicked(self):
        """Handle test connection button click (threaded, non-blocking)."""
        from threading import Thread
        
        api_key = self.controls["AI"]["api_key"].text().strip()
        base_url = self.controls["AI"]["base_url"].text().strip()
        model = self.controls["AI"]["model"].currentText().strip()
        
        if not api_key:
            self.update_connection_status(False, "❌ API Key is required")
            return
        if not base_url:
            self.update_connection_status(False, "❌ Base URL is required")
            return
        if not model:
            self.update_connection_status(False, "❌ Model is required")
            return
        
        self.btn_test_connection.setEnabled(False)
        self.update_connection_status(None, "🔄 Testing connection...")
        
        def test_connection():
            try:
                response = requests.post(
                    base_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 10
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.update_connection_status(True, "✅ Connection successful!")
                    self.connection_test_signal.emit(True, "Connection successful")
                else:
                    error_msg = f"❌ Connection failed (HTTP {response.status_code})"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg += f": {error_data['error'].get('message', 'Unknown error')}"
                    except:
                        pass
                    self.update_connection_status(False, error_msg)
                    self.connection_test_signal.emit(False, error_msg)
            except requests.exceptions.Timeout:
                self.update_connection_status(False, "❌ Connection timeout")
                self.connection_test_signal.emit(False, "Connection timeout")
            except requests.exceptions.ConnectionError:
                self.update_connection_status(False, "❌ Connection error - Check URL and network")
                self.connection_test_signal.emit(False, "Connection error")
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                self.update_connection_status(False, error_msg)
                self.connection_test_signal.emit(False, str(e))
            finally:
                self.btn_test_connection.setEnabled(True)
        
        thread = Thread(target=test_connection, daemon=True)
        thread.start()
    
    def update_connection_status(self, success, message):
        """Update the connection status label."""
        self.lbl_connection_status.setText(message)
        
        if success is True:
            self.lbl_connection_status.setStyleSheet("color: #00aa00; font-size: 13px; font-weight: bold;")
        elif success is False:
            self.lbl_connection_status.setStyleSheet("color: #ff4444; font-size: 13px; font-weight: bold;")
        else:
            self.lbl_connection_status.setStyleSheet("color: #0099ff; font-size: 13px; font-weight: bold;")
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
        t = lang_manager.get_text
        
        self.setWindowTitle(t("Preferences"))
        self.item_ai.setText(0, t("AI Configuration"))
        self.item_appearance.setText(0, t("Appearance"))
        self.item_font.setText(0, t("Font Settings"))
        self.item_language.setText(0, t("Language Settings"))
        self.item_search.setText(0, t("Search"))
        self.item_result_chart.setText(0, t("Result Chart"))

        self.button_box.button(QDialogButtonBox.Ok).setText(t("Save"))
        self.button_box.button(QDialogButtonBox.Apply).setText(t("Apply"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(t("Cancel"))

        # AI Connection group
        self.group_ai_api.setTitle(t("API Connection"))
        self.lbl_provider.setText(t("Provider:"))
        self.lbl_model.setText(t("Model:"))
        self.lbl_base_url.setText(t("Base URL:"))
        self.lbl_api_key.setText(t("API Key:"))
        self.btn_add_model.setToolTip(t("Add Custom Model"))
        self.btn_toggle_key.setToolTip(t("Show/Hide API Key"))
        self.btn_test_connection.setToolTip(t("Test API Connection"))
        base_url_input = self.controls["AI"]["base_url"]
        base_url_input.setPlaceholderText("https://...")
        api_key_input = self.controls["AI"]["api_key"]
        api_key_input.setPlaceholderText("sk-...")
        self.lbl_connection_status.setText("")

        # Behavior group
        self.group_ai_behavior.setTitle(t("Behavior"))
        self.lbl_sys_prompt.setText(t("System Prompt:"))
        self.lbl_temperature.setText(t("Temperature:"))
        sys_prompt = self.controls["AI"]["system_prompt"]
        sys_prompt.setPlaceholderText(t("You are a helpful assistant...") if lang_manager.current_language == "Chinese" else "You are a helpful assistant...")
        self.btn_reset_ai.setText(t("Reset AI Settings"))

        # Appearance
        self.group_theme.setTitle(t("Theme & UI"))
        self.lbl_theme_mode.setText(t("Theme mode:"))
        self.chk_toolbar_icons.setText(t("Show toolbar icons"))
        self.chk_animations.setText(t("Enable panel animations"))
        self.group_panels.setTitle(t("Default Panel Sizes"))
        self.lbl_left_width.setText(t("Left Panel Width:"))
        self.lbl_right_width.setText(t("Right Panel Width:"))
        self.group_bg.setTitle(t("Central Background"))
        self.lbl_bg_instruction.setText(t("Select a custom background image (JPG, PNG, GIF):"))
        self.btn_browse_bg.setText(t("Browse Image..."))
        self.btn_clear_bg.setText(t("Clear / Reset"))

        # Font
        self.group_font.setTitle(t("Font Settings"))
        self.lbl_font_type.setText(t("Font type:"))
        self.lbl_font_size.setText(t("Font size:"))
        self.lbl_font_preview.setText(t("Preview:"))

        # Language
        self.group_language.setTitle(t("Language Settings"))
        self.lbl_lang_type.setText(t("Language type:"))

        # Search
        self.group_search.setTitle(t("Search Engine"))
        self.lbl_search_engine.setText(t("Default search engine:"))

        # Result Chart
        self.group_result_chart.setTitle(t("Result Chart Settings"))
        self.lbl_curve_style.setText(t("Curve Style:"))
        self.lbl_curve_color.setText(t("Curve Color:"))
        self.lbl_curve_width.setText(t("Curve Width:"))
        self.lbl_scatter_style.setText(t("Scatter Style:"))
        self.lbl_axis_style.setText(t("Axis Style:"))
        self.lbl_grid_style.setText(t("Grid Style:"))
        self.lbl_bg_color.setText(t("Background Color:"))

    #-------------------------------------------------------------------------------------
    # Getters for retrieving specific settings
    def get_api_key(self):
        return self.settings.value("AI/api_key", "", type=str)


    def _model_delete_button_rect(self, item_rect):
        btn_width = 24
        btn_height = 20
        return QRect(
            item_rect.right() - btn_width - 5,
            item_rect.top() + (item_rect.height() - btn_height) // 2,
            btn_width, btn_height
        )
    def eventFilter(self, watched, event):
        if watched == self.models_combo.view().viewport():
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
                index = self.models_combo.view().indexAt(pos)
                if index.isValid():
                    item_rect = self.models_combo.view().visualRect(index)
                    if self._model_delete_button_rect(item_rect).contains(pos):
                        if event.type() == QEvent.Type.MouseButtonRelease:
                            self.delete_model_callback(index.row())
                        return True
        return super().eventFilter(watched, event)
    def delete_model_callback(self, row):
        model_name = self.models_combo.itemText(row)
        if not model_name:
            return
        provider_name = self.provider_combo.currentText()
        confirm = QMessageBox.question(
            self, "Delete Model",
            f"Are you sure you want to delete the model '{model_name}' for provider '{provider_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.remove_model_from_account_json(provider_name, model_name)
            self.models_combo.removeItem(row)
            self.models_combo.showPopup()
            saved_model = self.settings.value("AI/model", "")
            if saved_model == model_name:
                self.settings.setValue("AI/model", self.models_combo.currentText())
                self.settings.sync()
            self._emit_models_changed()
    def remove_model_from_account_json(self, provider_name, model_to_delete):
        import json
        usr_folder = utils.get_global_usr_dir()
        account_file = usr_folder / "Settings/account.json"
        if not account_file.exists():
            return
        try:
            with open(account_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        target_map = {"OpenRouter (Recommended)": "OpenRouter", "OpenAI (Official)": "OpenAI",
            "Alibaba Qwen (DashScope)": "Qwen", "DeepSeek (Official)": "DeepSeek",
            "X.AI (Grok)": "X.AI", "Groq (Meta Llama/Mixtral)": "Groq",
            "Google Gemini (via OpenRouter)": "Gemini", "SiliconFlow (硅基流动)": "SiliconFlow",
            "Ollama (Localhost)": "Ollama", "Arli": "Arli"}
        target_lower = target_map.get(provider_name, "Custom").lower().strip()
        updated = False
        def update_item(item):
            nonlocal updated
            prov = str(item.get("Provider") or item.get("provider") or "").lower().strip()
            if prov and (prov == target_lower or target_lower in prov or prov in target_lower):
                if "models" in item and model_to_delete in item["models"]:
                    item["models"].remove(model_to_delete)
                    updated = True
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    update_item(item)
                    if updated:
                        break
        if updated:
            try:
                with open(account_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._set_account_provider_cache(data)
            except Exception as e:
                print(f"[ERROR] Failed to save account.json after model deletion: {e}")
#-----------------------------------------------------------------------------------------
    def get_base_url(self):
        return self.settings.value("AI/base_url", "", type=str)

    def get_system_prompt(self):
        return self.settings.value("AI/system_prompt", "You are a helpful assistant.", type=str)

    def get_model(self):
        return self.settings.value("AI/model", "gpt-4-turbo", type=str)
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
class _ProviderItemDelegate(QStyledItemDelegate):
    """Custom delegate that respects per-item enabled state colors regardless of global QSS."""
    def paint(self, painter, option, index):
        is_enabled = index.data(Qt.UserRole)
        if is_enabled is not None and not is_enabled:
            # Bypass QSS entirely: draw gray text + clear background directly
            painter.save()
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            else:
                painter.fillRect(option.rect, option.palette.base())
            painter.setPen(QColor("#9ca3af"))
            text = index.data(Qt.DisplayRole)
            text_rect = option.rect.adjusted(8, 0, -8, 0)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text if text else "")
            painter.restore()
        else:
            super().paint(painter, option, index)


class _ModelDeleteDelegate(QStyledItemDelegate):
    """Delegate that paints a delete (×) button on each model item."""
    def __init__(self, parent=None, delete_callback=None):
        super().__init__(parent)
        self.delete_callback = delete_callback

    def paint(self, painter, option, index):
        item_option = QStyleOptionViewItem(option)
        item_option.rect = option.rect.adjusted(0, 0, -34, 0)
        super().paint(painter, item_option, index)
        painter.save()
        rect = option.rect
        btn_width = 16
        btn_height = 16
        btn_rect = QRect(rect.right() - btn_width - 5, rect.top() + (rect.height() - btn_height) // 2, btn_width, btn_height)
        icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-close-100.png"))
        icon.paint(painter, btn_rect)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            rect = option.rect
            btn_width = 24
            btn_height = 20
            btn_rect = QRect(rect.right() - btn_width - 5, rect.top() + (rect.height() - btn_height) // 2, btn_width, btn_height)
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if btn_rect.contains(pos):
                if event.type() == QEvent.Type.MouseButtonRelease:
                    if self.delete_callback:
                        self.delete_callback(index.row())
                return True
        return super().editorEvent(event, model, option, index)

