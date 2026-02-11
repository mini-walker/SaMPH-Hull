#--------------------------------------------------------------
# This file creates the status bar widget
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-27  
#-------------------------------------------------------------- 

import sys
import os
import time
import json
import socket
import threading
from urllib.request import urlopen

from PySide6.QtWidgets import (
    QStatusBar, QLabel, QWidget, QHBoxLayout, QFrame
)
from PySide6.QtCore import QTimer, QDateTime, Qt, Signal, QObject, QSize
from PySide6.QtGui import QIcon, QFont


#-------------------------------------------------------------- 
# Add the parent directory to the Python path for debugging
if __name__ == "__main__": 
    print("Debug mode!")   
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path: 
        sys.path.insert(0, project_root)
#-------------------------------------------------------------- 

# Import utils from the folder Utils
from SaMPH_Utils.Utils import utils 


#-------------------------------------------------------------- 
class LocationWorker(QObject):

    """
    Worker to fetch location in a separate thread
    """
    finished = Signal(str)

    def fetch_location(self):
        try:
            # Use ip-api.com for geolocation (free for non-commercial use)
            response = urlopen("http://ip-api.com/json/", timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            if data['status'] == 'success':
                location = f"{data['city']}, {data['country']}"
                self.finished.emit(location)
            else:
                self.finished.emit("Location Unavailable")
        except Exception as e:
            # print(f"Location fetch error: {e}")
            self.finished.emit("Location Unavailable")
#-------------------------------------------------------------- 


#-------------------------------------------------------------- 
class StatusBarBuilder(QStatusBar):

    """
    Custom Status Bar displaying:
    - Computer Name (left)
    - Runtime duration
    - Local Time
    - Geolocation with custom icon
    """

    #----------------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.start_time = time.time()
        
        self.init_ui()
        self.start_timers()
        self.get_location()
        
    #----------------------------------------------------------


    #----------------------------------------------------------
    def init_ui(self):

        """Initialize status bar UI elements"""
        
        # Set style (Lighter Gradient)
        # Lighter gray gradient, professional look
        self.setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f8f8, stop:1 #e0e0e0);
                color: #333333;
                border-top: 1px solid #c0c0c0;
            }
            QStatusBar::item {
                border: none;
            }
            QLabel {
                color: #333333;
                padding: 0 8px;
                font-size: 12px;
                background: transparent;
            }
        """)
        
        # ============ Left Side: Computer Name ============
        self.computer_widget = QWidget()
        comp_layout = QHBoxLayout(self.computer_widget)
        comp_layout.setContentsMargins(5, 0, 5, 0)
        comp_layout.setSpacing(6)
        
        # Custom Computer Icon
        self.comp_icon_label = QLabel()
        self.comp_icon_label.setStyleSheet("padding: 0;") # Reset padding for icon
        # Try to load icon
        comp_icon_path = utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-desktop-100.png")
        if os.path.exists(comp_icon_path):
            pixmap = QIcon(comp_icon_path).pixmap(QSize(16, 16))
            self.comp_icon_label.setPixmap(pixmap)
        else:
            self.comp_icon_label.setText("🖥️") # Fallback
            
        comp_layout.addWidget(self.comp_icon_label)
        
        # Computer Name Text
        computer_name = socket.gethostname()
        self.comp_text_label = QLabel(computer_name)
        self.comp_text_label.setStyleSheet("font-weight: bold; padding: 0;")
        comp_layout.addWidget(self.comp_text_label)
        
        self.addWidget(self.computer_widget)
        
        # ============ Right Side Widgets ============
        
        # 1. Runtime Label
        self.runtime_label = QLabel("Runtime: 00:00:00")
        self.addPermanentWidget(self.runtime_label)
        
        # 2. Local Time Label
        self.time_label = QLabel()
        self.addPermanentWidget(self.time_label)
        
        # 3. Location Label with Icon
        self.location_widget = QWidget()
        loc_layout = QHBoxLayout(self.location_widget)
        loc_layout.setContentsMargins(5, 0, 5, 0)
        loc_layout.setSpacing(4)
        
        # Custom Location Icon
        self.loc_icon_label = QLabel()
        self.loc_icon_label.setStyleSheet("padding: 0;")
        
        loc_icon_path = utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-location-100.png")
        if os.path.exists(loc_icon_path):
            pixmap = QIcon(loc_icon_path).pixmap(QSize(16, 16))
            self.loc_icon_label.setPixmap(pixmap)
        else:
            self.loc_icon_label.setText("📍")
            
        loc_layout.addWidget(self.loc_icon_label)
        
        self.loc_text_label = QLabel("Locating...")
        self.loc_text_label.setStyleSheet("padding: 0;")
        loc_layout.addWidget(self.loc_text_label)
        
        self.addPermanentWidget(self.location_widget)
    #----------------------------------------------------------


    #----------------------------------------------------------
    def start_timers(self):
        """Start timers for updating time and runtime"""
        # Update time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)
        
        # Initial update
        self.update_status()
    #----------------------------------------------------------

    #----------------------------------------------------------
    def update_status(self):
        """Update time and runtime labels"""
        # Update Local Time
        current_time = QDateTime.currentDateTime()
        self.time_label.setText(current_time.toString("yyyy-MM-dd HH:mm:ss"))
        
        # Update Runtime
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        self.runtime_label.setText(f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
    #----------------------------------------------------------


    #---------------------------------------------------------- 
    def get_location(self):
        """Fetch location asynchronously"""
        self.worker = LocationWorker()
        self.worker.finished.connect(self.update_location)
        
        # Run in a separate thread to avoid freezing UI
        threading.Thread(target=self.worker.fetch_location, daemon=True).start()
    #----------------------------------------------------------     

    #----------------------------------------------------------
    def update_location(self, location):
        """Update location label"""
        self.loc_text_label.setText(location)
    #----------------------------------------------------------

    #----------------------------------------------------------
    def update_ui_texts(self, lang_manager):
        """Update UI texts based on current language."""
        if not lang_manager:
            return
        
        # Status bar shows dynamic system information (time, location, etc.)
        # These are language-independent or updated dynamically
        pass
    #----------------------------------------------------------



#--------------------------------------------------------------
# Test code
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Status Bar Test")
    window.resize(800, 600)
    
    status_bar = StatusBarBuilder(window)
    window.setStatusBar(status_bar)
    
    window.show()
    
    sys.exit(app.exec())
