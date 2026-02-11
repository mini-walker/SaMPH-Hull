#--------------------------------------------------------------
# This file Contains the global stylesheet (QSS) for the SaMPH application.
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-10-27  
#-------------------------------------------------------------- 

from SaMPH_Utils.Utils import utils         # Import utility function class


class Theme_SaMPH:
    """
    Class to manage the application theme and stylesheets.
    """
    @staticmethod
    def get_stylesheet():
        """
        Returns the complete QSS string for the application.
        """
        return """
            /* Main Window & General */
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            /* Separator */
            QMainWindow::separator {
                width: 4px;
                height: 4px;
                background: #e0e0e0;
            }
            
            /* Toolbar Styling */
            QToolBar {
                background-color: #fafafa;
                border-bottom: 1px solid #d0d0d0;
                spacing: 6px;
                padding: 4px;
            }
            
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 4px;
                margin: 0px 2px;
            }
            
            QToolButton:hover {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
            }
            
            QToolButton:pressed {
                background-color: #d8d8d8;
                border: 1px solid #c0c0c0;
            }
            
            /* LineEdit (Search Box etc.) */
            QLineEdit {
                padding: 0px 8px;   /* 4px top/bottom, 8px left/right */
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #ffffff;
                color: #333333;
                selection-background-color: #a0a0a0;
                font-size: 13px;
                min-height: 28px;
            }
            
            QLineEdit:focus {
                border: 1px solid black;
            }
            
            /* PushButton Styling - Professional & Minimal */
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 15px;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #bbbbbb;
            }
            
            QPushButton:pressed {
                background-color: #e0e0e0;
                border: 1px solid #aaaaaa;
            }
            
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #a0a0a0;
                border: 1px solid #dddddd;
            }
            
            /* Tab Widget Styling */
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background: #ffffff;
            }
            
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-bottom-color: #d0d0d0; /* Same as pane border */
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                min-width: 80px;
                padding: 6px 12px;
                color: #555555;
            }
            
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #ffffff;
                color: #333333;
            }
            
            QTabBar::tab:selected {
                border-color: #d0d0d0;
                border-bottom-color: #ffffff; /* Blend with pane */
                font-weight: bold;
            }
            
            /* ScrollBar Styling - Minimalist */
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #cdcdcd;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a6a6a6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #cdcdcd;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a6a6a6;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* ComboBox Styling - Professional & Modern */
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 0px 8px;
                padding-right: 30px;  /* Make room for arrow */
                min-height: 28px;
                color: #333333;
                font-size: 13px;
                selection-background-color: #0078d4;
            }
            
            QComboBox:hover {
                border: 1px solid #999999;
                background-color: #fafafa;
            }
            
            QComboBox:focus {
                border: 1px solid #0078d4;
                background-color: #ffffff;
            }
            
            QComboBox:disabled {
                background-color: #f5f5f5;
                color: #a0a0a0;
                border: 1px solid #dddddd;
            }
            
            /* Drop-down button area */
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #d0d0d0;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: transparent;
            }
            
            QComboBox::drop-down:hover {
                background-color: #e8e8e8;
            }
            
            QComboBox::drop-down:pressed {
                background-color: #d0d0d0;
            }
            
            /* Custom down arrow using image */
            QComboBox::down-arrow {
                image: url(%s);
                width: 16px;
                height: 16px;
            }
            
            QComboBox::down-arrow:hover {
                /* Optional: Add hover effect if needed, e.g. opacity */
            }
            
            QComboBox::down-arrow:disabled {
                opacity: 0.5;
            }
            
            /* When combo box is open */
            QComboBox::down-arrow:on {
                /* Optional: Rotate or change icon when open */
            }
            
            /* Drop-down list view */
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 3px 0px;
                selection-background-color: #f0f0f0;
                selection-color: #212121;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 5px 10px;
                border-radius: 0px;
                min-height: 24px;
                color: #424242;
                margin: 0px;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f0f0;
                color: #212121;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #f0f0f0;
                color: #212121;
                border-left: 2px solid #757575;
            }
            
            /* Splitter Styling */
            QSplitter::handle {
                background-color: #e0e0e0;
            }
            
            QSplitter::handle:horizontal {
                width: 2px;
            }
            
            QSplitter::handle:vertical {
                height: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #bdbdbd;
            }
            
        """ % (utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-expand-arrow-100.png").replace("\\", "/"))
