#--------------------------------------------------------------
# This file creates the Home page with mode selection
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-28  
#-------------------------------------------------------------- 

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

# Add the parent directory to the Python path for debugging
if __name__ == "__main__": 
    print("Debug mode!")   
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path: 
        sys.path.insert(0, project_root)

from SaMPH_Utils.Utils import utils 
from SaMPH_GUI.Language_Manager import Language_Manager


#==============================================================
class HomePage(QWidget):
    """
    Home page with multilingual support.
    Features:
    - Auto language switching based on system settings
    - Clean and modern design
    - Software introduction and features display
    """
    
    # Signals
    log_signal = Signal(str)                    # Signal to log messages to the main window
    add_input_window_signal = Signal(str)       # Signal to add new tab for Input Page
    
    def __init__(self, parent=None):

        super().__init__(parent)

        # Initialize language manager
        self.lang_manager = Language_Manager()

        # Store UI elements for language switching
        self.ui_elements = {}

        # Initialize UI
        self.init_ui()
    
    def init_ui(self):

        """Initialize the home page UI"""
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Center Container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(10)
        center_widget.setMinimumHeight(0) # Allow shrinking
        
        # Add top stretch to center content vertically
        center_layout.addStretch(1)
        
        icon_label = QLabel()
        pixmap = QPixmap(utils.local_resource_path("SaMPH_Images/planing-hull-app-logo.png"))
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(120, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("[Logo Not Found]")
        
        icon_label.setAlignment(Qt.AlignCenter)
        # Allow shrinking but prefer natural size
        icon_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        icon_label.setMinimumHeight(0)
        center_layout.addWidget(icon_label)
        
        # ============ App Title ============
        home_title = self.lang_manager.get_text("home_title") or "Planing Hull Analysis System"
        title = QLabel(home_title)
        # Font size fixed in stylesheet to ignore global settings
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-size: 32pt;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        # Allow shrinking but prefer natural size
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        title.setMinimumHeight(0)
        center_layout.addWidget(title)
        self.ui_elements["title"] = title
        
        # ============ Subtitle (LARGER) ============
        home_subtitle = self.lang_manager.get_text("home_subtitle") or "A Modern Tool for Hull Performance Evaluation"
        subtitle = QLabel(home_subtitle)
        # Font size fixed in stylesheet to ignore global settings
        subtitle.setStyleSheet("""
            QLabel {
                color: black;
                background: transparent;
                margin: 0px 0px;
                font-size: 20pt;
            }
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(False)   # Prevent word wrapping(multi-lines)
        # Allow shrinking but prefer natural size
        subtitle.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        subtitle.setMinimumHeight(0)
        center_layout.addWidget(subtitle)
        self.ui_elements["subtitle"] = subtitle
        
        center_layout.addSpacing(20)
        
        # ============ Features Description ============
        features_title = self.lang_manager.get_text("home_features_title") or "Features:"
        features_content = self.lang_manager.get_text("home_features_text") or "- Multilingual support\n- Modern UI\n- Fast calculation\n- Easy to use"
        features_text = f"""
        <p style="font-size: 13px; color: #34495e; line-height: 1.8;">
            <b>{features_title}</b><br>
            {features_content}
        </p>
        """
        features_label = QLabel(features_text)
        features_label.setStyleSheet("background: transparent;")
        features_label.setAlignment(Qt.AlignCenter)
        features_label.setMaximumWidth(600)
        features_label.setWordWrap(True)

        # Allow shrinking but prefer natural size
        features_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        features_label.setMinimumHeight(0)
        center_layout.addWidget(features_label)
        self.ui_elements["features"] = features_label
        
        # Add bottom stretch to center content vertically
        center_layout.addStretch(1)
        
        main_layout.addWidget(center_widget, 1)
        
        # ============ Copyright - Bottom Right ============
        bottom_layout = QHBoxLayout()

        # Push the copyright label to the right
        bottom_layout.addStretch()
        
        copyright_text = self.lang_manager.get_text("home_copyright") or "© 2025 AMHL Team. All rights reserved."
        copyright_label = QLabel(copyright_text)
        copyright_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #95a5a6;
                background: transparent;
            }
        """)
        bottom_layout.addWidget(copyright_label)
        self.ui_elements["copyright"] = copyright_label
        
        main_layout.addLayout(bottom_layout)
        
        # ============ Main Page Styling (Gradient Background) ============
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa,
                    stop:1 #e9ecef
                );
            }
        """)
        
    def update_ui_texts(self, lang_manager):
        """Update UI texts based on current language."""
        print(f"[DEBUG] Page_Home.update_ui_texts called. Lang Manager: {lang_manager}")

        if not lang_manager:
            return
        
        # Use existing switch_language method
        current_lang = lang_manager.get_current_language()
        print(f"[DEBUG] Page_Home switching to: {current_lang}")
        self.switch_language(current_lang)

    def switch_language(self, language):
        """
        Switch the UI language dynamically.
        
        Args:
            language (str): "English" or "Chinese"
        """
        print(f"[DEBUG] Page_Home.switch_language called with: {language}")
        self.lang_manager.set_language(language)
        
        # Update all text elements
        if "title" in self.ui_elements:
            text = self.lang_manager.get_text("home_title")
            print(f"[DEBUG] Title text: {text}")
            self.ui_elements["title"].setText(text or "Planing Hull Analysis System")
        
        if "subtitle" in self.ui_elements:
            text = self.lang_manager.get_text("home_subtitle")
            print(f"[DEBUG] Subtitle text: {text}")
            self.ui_elements["subtitle"].setText(text or "A Modern Tool for Hull Performance Evaluation")
        
        if "features" in self.ui_elements:
            features_title = self.lang_manager.get_text("home_features_title") or "Features:"
            features_content = self.lang_manager.get_text("home_features_text") or "- Multilingual support\n- Modern UI\n- Fast calculation\n- Easy to use"
            features_text = f"""
        <p style="font-size: 13px; color: #34495e; line-height: 1.8;">
            <b>{features_title}</b><br>
            {features_content}
        </p>
        """
            print(f"[DEBUG] Features text updated")
            self.ui_elements["features"].setText(features_text)
        
        if "copyright" in self.ui_elements:
            text = self.lang_manager.get_text("home_copyright")
            print(f"[DEBUG] Copyright text: {text}")
            self.ui_elements["copyright"].setText(text or "© 2025 HydroX Team. All rights reserved.")
    #==============================================================


    #==============================================================
    def on_confirm(self):

        """Handle confirm button click"""

        # Simplified - just log that home page is displayed
        self.log_signal.emit("Home page displayed")
    #==============================================================

#--------------------------------------------------------------
# Test code
if __name__ == '__main__':

    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = HomePage()
    window.setWindowTitle("Home Page Test")
    window.resize(900, 700)
    window.show()
    
    # Connect signals for testing
    window.log_signal.connect(lambda msg: print(f"Log: {msg}"))
    window.add_input_window_signal.connect(lambda mode: print(f"Add Input Page: {mode}"))
    
    # Test language switching after 2 seconds
    def test_language_switch():
        current = window.lang_manager.get_current_language()
        new_lang = "Chinese" if current == "English" else "English"
        print(f"Switching language to: {new_lang}")
        window.switch_language(new_lang)
    
    from PySide6.QtCore import QTimer
    QTimer.singleShot(2000, test_language_switch)
    
    sys.exit(app.exec())
