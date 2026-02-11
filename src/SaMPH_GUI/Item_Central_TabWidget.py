#--------------------------------------------------------------
# This file creates the central tab widget (without log)
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-27  
#-------------------------------------------------------------- 

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QTabWidget, QTextEdit, QTabBar, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal, QRect
from PySide6.QtGui import QIcon, QPixmap, QPainter, QMovie

# Add the parent directory to the Python path for debugging
if __name__ == "__main__": 
    print("Debug mode!")   
    # Current: .../src/SaMPH_GUI/Item_Central_TabWidget.py
    # 1. .../src/SaMPH_GUI
    # 2. .../src (This is what we need)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path: 
        sys.path.insert(0, project_root)

from SaMPH_Utils.Utils import utils
from SaMPH_GUI.Page_Home import HomePage


#==============================================================
class AspectRatioLabel(QLabel):
    """
    Custom Label: Implement Cover (adaptive scaling)
    Support GIF and static images, prevent jitter
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ignore layout size limits, follow window scaling completely
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setScaledContents(False)
        self.m_pixmap = None
        self.m_movie = None

    def setPixmap(self, pixmap):
        if self.m_movie:
            self.m_movie.stop()
            self.m_movie = None
        self.m_pixmap = pixmap
        self.update()

    def setMovie(self, movie):
        if self.m_movie:
            self.m_movie.stop()
        self.m_movie = movie
        self.m_pixmap = None
        self.m_movie.frameChanged.connect(self.repaint)
        self.m_movie.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        current_pix = None
        if self.m_movie:
            current_pix = self.m_movie.currentPixmap()
        elif self.m_pixmap:
            current_pix = self.m_pixmap

        if current_pix and not current_pix.isNull():
            win_w = self.width()
            win_h = self.height()
            img_w = current_pix.width()
            img_h = current_pix.height()
            if img_w == 0 or img_h == 0: 
                return

            # Cover algorithm: Use max ratio to ensure filling the window
            ratio = max(win_w / img_w, win_h / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            
            # Draw centered
            x = (win_w - new_w) // 2
            y = (win_h - new_h) // 2
            target_rect = QRect(x, y, new_w, new_h)
            painter.drawPixmap(target_rect, current_pix)


#==============================================================
class Central_Tab_Widget(QWidget):
    """
    Central tab widget - only manages tabs, no log window.
    Features:
    - Tab-based interface with adaptive background
    - Closeable tabs
    - Welcome/home page
    """
    
    # Signals
    tab_closed = Signal(int)  # Emit when a tab is closed (index)
    all_tabs_closed = Signal()  # Emit when all tabs are closed
    tabs_opened = Signal()  # Emit when tabs are opened (from 0 to 1+)
    home_page_state_changed = Signal(bool)  # Emit when Home page visibility changes (True=visible, False=hidden)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Track home tab reference
        self.home_widget = None
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the tab widget UI"""
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ============ Background + Tab Stacked Container ============
        self.stacked_widget = QStackedWidget()
        
        # ============ Layer 1: Background Image Layer (Bottom) ============
        self.background_widget = self.create_background_widget()
        self.stacked_widget.addWidget(self.background_widget)
        
        # ============ Layer 2: Tab Widget (Top) ============
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Make Tab Widget background transparent to show background image below
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 0px;
            }
            QTabBar {
                font-size: 13px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-bottom-color: #d0d0d0;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 80px;
                max-height: 28px;
                padding: 4px 12px;
                margin-right: 2px;
                margin-top: 2px;
                color: #555555;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #333333;
                border-color: #d0d0d0;
                border-bottom-color: #ffffff;
                font-weight: 600;
                padding-bottom: 5px;
            }
            QTabBar::tab:hover:!selected {
                background: #e8e8e8;
                color: #333333;
            }
            QTabBar::close-button {
                image: url(%s);
                subcontrol-position: right;
                margin: 2px;
            }
            QTabBar::close-button:hover {
                background: rgba(220, 53, 69, 0.15);
                border-radius: 3px;
            }
            QTabBar::close-button:pressed {
                background: rgba(220, 53, 69, 0.25);
            }
        """ % (utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-close-100.png").replace("\\", "/")))
        
        self.stacked_widget.addWidget(self.tab_widget)
        
        # Show tab widget initially (we'll add welcome tab)
        self.stacked_widget.setCurrentWidget(self.tab_widget)
        
        # Add welcome tab
        self.add_welcome_tab()
        
        main_layout.addWidget(self.stacked_widget)
    #------------------------------------------------------------------------


    #------------------------------------------------------------------------
    # Create the background widget
    def create_background_widget(self):
        """Create background widget with adaptive image"""

        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create background label (initially empty)
        self.bg_label = AspectRatioLabel()
        self.bg_label.setAlignment(Qt.AlignCenter)
        
        # Initialize with no background image
        # Background will be set via set_central_background() if configured
        self.movie = None
        
        layout.addWidget(self.bg_label)
        
        return widget
    #------------------------------------------------------------------------



    #------------------------------------------------------------------------
    # Add the welcome/home tab using Page_Home component
    def add_welcome_tab(self):

        """Add the welcome/home tab using Page_Home component"""
        # If showing background, switch back to tab view
        if self.stacked_widget.currentWidget() == self.background_widget:
            self.stacked_widget.setCurrentWidget(self.tab_widget)
            self.tabs_opened.emit()
        
        # Create HomePage instance
        home_page = HomePage()
        
        # Store reference to home widget
        self.home_widget = home_page
        
        # Add as first tab (deletable)
        self.tab_widget.addTab(home_page, "Home")
        
        # Emit signal that Home page is now visible
        self.home_page_state_changed.emit(True)
        
        return home_page
    #------------------------------------------------------------------------

    #------------------------------------------------------------------------
    def add_tab(self, widget, title):

        """Add a new tab"""

        # If showing background, switch back to tab view
        if self.stacked_widget.currentWidget() == self.background_widget:
            self.stacked_widget.setCurrentWidget(self.tab_widget)
            self.tabs_opened.emit()
        
        index = self.tab_widget.addTab(widget, title)
        self.tab_widget.setCurrentIndex(index)
        return index
    #------------------------------------------------------------------------

    #------------------------------------------------------------------------
    def close_tab(self, index):
        """Close a tab"""
        widget = self.tab_widget.widget(index)
        
        # Check if this is the Home tab BEFORE clearing reference
        is_home_tab = (widget is self.home_widget)
        
        # Clear home widget reference if closing home tab
        if is_home_tab:
            self.home_widget = None
        
        self.tab_widget.removeTab(index)
        
        if widget:
            widget.deleteLater()
        
        # Emit signal with index (operations will check if it was Home)
        self.tab_closed.emit(index)
        
        # Emit Home page state change if Home was closed
        if is_home_tab:
            self.home_page_state_changed.emit(False)
        
        # If no tabs left, show background
        if self.tab_widget.count() == 0:
            self.stacked_widget.setCurrentWidget(self.background_widget)
            self.all_tabs_closed.emit()
    #------------------------------------------------------------------------


    #------------------------------------------------------------------------
    def get_current_tab(self):
        """Get the currently active tab widget"""
        return self.tab_widget.currentWidget()
    #------------------------------------------------------------------------

    #------------------------------------------------------------------------
    def get_current_tab_index(self):
        """Get the index of the currently active tab"""
        return self.tab_widget.currentIndex()
    #------------------------------------------------------------------------
    
    #------------------------------------------------------------------------
    def set_central_background(self, background_path):
        """
        Set a custom background image for the central tab widget.
        
        Args:
            background_path (str): Path to the background image (JPG, PNG, GIF)
                                   Empty string or invalid path will clear the background
        """
        # Stop any existing movie
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()
            self.movie = None
        
        # If path is empty or invalid, clear the background
        if not background_path or not os.path.exists(background_path):
            if background_path:
                print(f"[WARN] Invalid background path: {background_path}")
            else:
                print(f"[INFO] Clearing background (no image)")
            
            # Clear the background label
            self.bg_label.setPixmap(QPixmap())  # Empty pixmap
            return
        
        # Check if it's a GIF
        if background_path.lower().endswith('.gif'):
            self.movie = QMovie(background_path)
            if self.movie.isValid():
                self.movie.setCacheMode(QMovie.CacheAll)
                self.bg_label.setMovie(self.movie)
                print(f"[INFO] Background set to GIF: {background_path}")
            else:
                print(f"[ERROR] Invalid GIF file: {background_path}")
                self.bg_label.setPixmap(QPixmap())  # Clear on error
        else:
            # Load as static image
            pixmap = QPixmap(background_path)
            if not pixmap.isNull():
                self.bg_label.setPixmap(pixmap)
                print(f"[INFO] Background set to image: {background_path}")
            else:
                print(f"[ERROR] Failed to load image: {background_path}")
                self.bg_label.setPixmap(QPixmap())  # Clear on error
    #------------------------------------------------------------------------

    #------------------------------------------------------------------------
    def update_ui_texts(self, lang_manager):
        
        """Update UI texts based on current language."""
        if not lang_manager:
            return
        
        # Update tab names if they exist
        tab_names = {0: "Home", 1: "Input", 2: "Results"}
        for i, name in tab_names.items():
            if i < self.tab_widget.count():
                current_text = self.tab_widget.tabText(i)
                # Only update if it matches expected pattern
                if current_text in ["Home", "主页", "Input", "输入", "Results", "结果"]:
                    self.tab_widget.setTabText(i, lang_manager.get_text(name))
    #------------------------------------------------------------------------


#==============================================================
# Sample page widgets that can be added to tabs
#==============================================================

class SampleInputPage(QWidget):
    """Sample input page"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        label = QLabel("Input Page")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Enter your input data here...")
        layout.addWidget(text_edit)


class SampleResultPage(QWidget):
    """Sample result page"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        label = QLabel("Results Page")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)
        
        result_text = QLabel("Results will be displayed here...")
        result_text.setStyleSheet("padding: 20px;")
        layout.addWidget(result_text)
        layout.addStretch()


#--------------------------------------------------------------
# Test code
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QPushButton, QHBoxLayout
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    layout = QVBoxLayout(window)
    
    # Create tab widget
    tab_widget = Central_Tab_Widget()
    layout.addWidget(tab_widget)
    
    # Add test buttons
    btn_layout = QHBoxLayout()
    
    btn_add_input = QPushButton("Add Input Tab")
    btn_add_input.clicked.connect(
        lambda: tab_widget.add_tab(SampleInputPage(), "Input")
    )
    btn_layout.addWidget(btn_add_input)
    
    btn_add_result = QPushButton("Add Result Tab")
    btn_add_result.clicked.connect(
        lambda: tab_widget.add_tab(SampleResultPage(), "Results")
    )
    btn_layout.addWidget(btn_add_result)
    
    layout.addLayout(btn_layout)
    
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())
