#--------------------------------------------------------------
# This file creates the log window widget
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-27  
#-------------------------------------------------------------- 

import sys
import logging
from PySide6.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame
)
from PySide6.QtCore import QDateTime, Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QTextCursor


# Add the parent directory to the Python path for debugging
if __name__ == "__main__": 
    print("Debug mode!")
    # __file__ = .../src/SaMPH_GUI/Item_Central_LogWindow.py
    # dirname -> .../src/SaMPH_GUI
    # dirname -> .../src
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path: 
        sys.path.insert(0, project_root)

from SaMPH_Utils.Utils import utils

class Central_Log_Widget(QWidget):
    
    # Signal to notify parent when close button is clicked
    close_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ============ Header Section ============
        header_widget = QWidget()
        header_widget.setFixedHeight(24)  # Even slimmer header
        # Minimalist style: No border, light background matching VS Code terminal
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #f3f3f3;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 0, 5, 0)
        header_layout.setSpacing(0)

        # Title "OUTPUT" or "LOG" - Uppercase looks more like a terminal tab
        title_label = QLabel("LOG")
        title_label.setStyleSheet("""
            font-weight: bold;
            color: #555555;
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
            border: none;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()

        # Close Button (×)
        self.btn_close = QPushButton()
        self.btn_close.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/Win11-Icons/icons8-close-500.png")))
        self.btn_close.setIconSize(QSize(20, 20))
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Close Panel")
        self.btn_close.clicked.connect(self.on_close_clicked)
        self.btn_close.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 16px;
                color: #666;
                font-weight: bold;
                border-radius: 3px;
                margin-top: 1px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333;
            }
        """)
        header_layout.addWidget(self.btn_close)

        layout.addWidget(header_widget)

        # ============ Log Content Area ============
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        
        # Use Monospace font for scientific data alignment
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.log_window.setFont(font)
        
        self.log_window.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #ffffff;
                color: #333333;
                selection-background-color: #0078d7;
                selection-color: #ffffff;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_window)

        # Initialize with start message
        self.log_message("Application started successfully.")

    def log_message(self, message, level=logging.INFO):

        """Log messages to the log window with timestamp and level-based styling"""
        
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        # Define colors based on log level
        if level == logging.ERROR:
            color = "#d32f2f"  # Red
            level_str = "ERROR"
        elif level == logging.WARNING:
            color = "#f57c00"  # Orange
            level_str = "WARNING"
        elif level == logging.DEBUG:
            color = "#757575"  # Gray
            level_str = "DEBUG"
        else:
            color = "#333333"  # Default/Info
            level_str = "INFO"
            
        # Use HTML to format timestamp in blue (scientific/console style)
        # and message in level-based color
        html_msg = (
            f'<span style="color: #0056b3; font-weight: bold;">[{current_time}]</span> '
            f'<span style="color: {color};">[{level_str}] {message}</span>'
        )
        
        self.log_window.append(html_msg)
        
        # Auto scroll to bottom
        scrollbar = self.log_window.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_close_clicked(self):
        """Handle close button click"""
        self.close_requested.emit()
        self.hide()

    def clear_log(self):

        """Clear all log messages"""

        self.log_window.clear()
        self.log_message("Log cleared.")


    def update_ui_texts(self, lang_manager):

        """Update UI texts based on current language."""

        if not lang_manager:

            return
        
        # Log window uses technical output, minimal translation needed
        # Title is hardcoded as "LOG" which is universally understood
        pass
