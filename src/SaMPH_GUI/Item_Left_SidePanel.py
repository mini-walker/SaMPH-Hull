#--------------------------------------------------------------
# This file creates the left navigation side panel
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-27  
#-------------------------------------------------------------- 

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation
from PySide6.QtGui import QIcon

# Add the parent directory to the Python path for debugging
if __name__ == "__main__": 
    print("Debug mode!")   
    # Current: .../src/SaMPH_GUI/Item_Left_SidePanel.py
    # 1. .../src/SaMPH_GUI
    # 2. .../src (This is what we need)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path: 
        sys.path.insert(0, project_root)


from SaMPH_Utils.Utils import utils 


#==============================================================
class Left_Side_Panel(QWidget):
    """
    Left navigation sidebar component similar to VS Code's explorer panel.
    Features:
    - Collapsible/expandable with animation
    - Drag-resizable width
    - Navigation menu items
    """
    
    # Signals
    navigation_requested = Signal(str)  # Emit navigation request (item_name) for Input/Results
    home_toggle_requested = Signal(bool)  # Emit Home toggle request (True=show, False=hide) - same as toolbar
    result_page_requested = Signal(str)  # Emit request to open specific result page (e.g., "Rt", "Trim")
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Panel state
        self.panel_width = 280
        self.is_visible = True
        self.full_width = self.panel_width
        
        # Store reference to home nav item for icon updates
        self.home_nav_item = None
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):

        """Initialize the left sidebar UI"""
        
        # Set size policy
        self.setMinimumWidth(280)
        self.setMaximumWidth(600)
        self.setFixedWidth(self.panel_width)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ============ Header Section ============
        header = QWidget()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        # Title label
        title_label = QLabel("Navigation")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Add divider
        main_layout.addWidget(self.create_divider())
        
        # ============ Navigation Menu ============
        self.nav_tree = QTreeWidget()
        self.nav_tree.setIndentation(0)
        self.nav_tree.setFrameShape(QFrame.NoFrame)
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setIconSize(QSize(26, 26))
        self.nav_tree.setIndentation(20)
        self.nav_tree.itemClicked.connect(self.on_tree_item_clicked)
        
        # === Fix: enable click-to-expand without visible arrows ===
        self.nav_tree.setItemsExpandable(True)
        self.nav_tree.setExpandsOnDoubleClick(False)
        self.nav_tree.setAnimated(True)


        # Add navigation items
        # Home
        self.home_nav_item = QTreeWidgetItem(self.nav_tree)
        self.home_nav_item.setText(0, "Home")
        self.home_nav_item.setData(0, Qt.UserRole, "home")
        self.home_nav_item.setSizeHint(0, QSize(0, 40))
        try:
            icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-home.svg"))
            self.home_nav_item.setIcon(0, icon)
        except:
            pass
        
        # Input
        self.input_nav_item = QTreeWidgetItem(self.nav_tree)
        self.input_nav_item.setText(0, "Input")
        self.input_nav_item.setData(0, Qt.UserRole, "input")
        self.input_nav_item.setSizeHint(0, QSize(0, 40))
        try:
            icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-structured-document-data-100.png"))
            self.input_nav_item.setIcon(0, icon)
        except:
            pass
        
        # Results (expandable tree)
        self.results_nav_item = QTreeWidgetItem(self.nav_tree)
        self.results_nav_item.setText(0, "Results")
        self.results_nav_item.setData(0, Qt.UserRole, "results")
        self.results_nav_item.setSizeHint(0, QSize(0, 40))
        try:
            icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-combo-chart-100.png"))
            self.results_nav_item.setIcon(0, icon)
        except:
            pass
        

        # Add child items under Results
        result_types = [
            ("Bare hull resistance (Rw)", "Rw"),
            ("Spray resistance (Rs)", "Rs"),
            ("Air resistance (Ra)", "Ra"),
            ("Total resistance (Rt)", "Rt"),
            ("Trim", "Trim"),
            ("Sinkage", "Sinkage")
        ]
        
        for label, data_id in result_types:
            child = QTreeWidgetItem(self.results_nav_item)
            child.setText(0, label)
            child.setData(0, Qt.UserRole, data_id)
            child.setSizeHint(0, QSize(0, 35))
        
        main_layout.addWidget(self.nav_tree, 0)
        main_layout.addStretch()
        
        # ============ Styling ============
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F6FA;
            }
            QTreeWidget {
                background-color: #F5F6FA;
                border: none;
                outline: none;
            }
            QTreeWidget::item {
                padding: 10px 14px;
                border-radius: 4px;
                margin: 3px 10px;
                color: #2C3E50;
                font-size: 13px;
            }
            QTreeWidget::item:hover {
                background-color: #E8EAF6;
                border-left: 2px solid #5C6BC0;
            }
            QTreeWidget::item:selected {
                background-color: #C5CAE9;
                color: #1A237E;
                font-weight: 600;
            }
            QTreeWidget::branch {
                background: transparent;
            }
            /* Restore default arrows */
            QTreeWidget::branch:has-children:closed {
                image: url(:/qt-project.org/styles/commonstyle/images/right-arrow-16.png);
                border: none;
            }
            QTreeWidget::branch:has-children:open {
                image: url(:/qt-project.org/styles/commonstyle/images/down-arrow-16.png);
                border: none;
            }
        """)
    
    def on_tree_item_clicked(self, item, column):
        """Handle tree item click"""
        nav_id = item.data(0, Qt.UserRole)
        
        if nav_id == "home":
            self.home_toggle_requested.emit(True)
        elif nav_id == "input":
            self.navigation_requested.emit("input")
        elif nav_id == "results":
            # Toggle expansion state
            item.setExpanded(not item.isExpanded())
        elif nav_id in ["Rw", "Rs", "Ra", "Rt", "Trim", "Sinkage"]:
            # Child result item clicked - open result page
            self.result_page_requested.emit(nav_id)
    
    def create_divider(self):
        """Create a modern, subtle divider line"""
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 0, 0, 25),
                    stop:0.5 rgba(0, 0, 0, 45),
                    stop:1 rgba(0, 0, 0, 25)
                );
            }
        """)
        return line

    
    def update_home_icon(self, is_active):
        """Update Home button icon based on active state"""
        if self.home_nav_item is None:
            return
        
        if is_active:
            icon_path = "SaMPH_Images/WIN11-Icons/icons8-home.svg"
        else:
            icon_path = "SaMPH_Images/WIN11-Icons/icons8-home-deactive.svg"
        
        try:
            icon = QIcon(utils.local_resource_path(icon_path))
            self.home_nav_item.setIcon(0, icon)
        except:
            pass
    
    def toggle_panel(self):
        """Toggle panel visibility with parallel animation for min/max width"""
        # Import animation classes locally to ensure availability
        from PySide6.QtCore import QParallelAnimationGroup, QPropertyAnimation
        
        if self.is_visible:
            # Collapse
            self.full_width = self.width()
            start_width = self.width()
            target_width = 0
        else:
            # Expand
            # Ensure we have a reasonable width to restore to
            if self.full_width < 150:
                self.full_width = 320
            start_width = 0
            target_width = self.full_width
        
        # Create parallel animation group
        self.anim_group = QParallelAnimationGroup(self)
        
        # Animation for maximumWidth
        anim_max = QPropertyAnimation(self, b"maximumWidth")
        anim_max.setDuration(250)
        anim_max.setStartValue(start_width if not self.is_visible else self.full_width)
        anim_max.setEndValue(target_width)
        
        # Animation for minimumWidth
        anim_min = QPropertyAnimation(self, b"minimumWidth")
        anim_min.setDuration(250)
        anim_min.setStartValue(start_width if not self.is_visible else self.full_width)
        anim_min.setEndValue(target_width)
        
        self.anim_group.addAnimation(anim_max)
        self.anim_group.addAnimation(anim_min)
        
        # Update state
        self.is_visible = not self.is_visible
        
        # Start animation
        self.anim_group.start()

    def update_ui_texts(self, lang_manager):
        """Update UI texts based on current language."""
        if not lang_manager:
            return
        
        # Update title
        title_label = self.findChild(QLabel)
        if title_label:
            title_label.setText(lang_manager.get_text("Navigation"))
        
        # Update navigation items
        # Update navigation items
        # Iterate through top-level items in the tree widget
        root = self.nav_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            data = item.data(0, Qt.UserRole)
            
            if data == "home":
                item.setText(0, lang_manager.get_text("Home"))
            elif data == "input":
                item.setText(0, lang_manager.get_text("Input"))
            elif data == "results":
                item.setText(0, lang_manager.get_text("Results"))
                # Note: Result children (Rw, Rs, etc.) might not need translation 
                # or should be handled if they do. For now, we keep them as is 
                # since they are technical terms.
            elif data == "settings":
                item.setText(0, lang_manager.get_text("Settings"))


#--------------------------------------------------------------
# Test code
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    layout = QHBoxLayout(window)
    
    # Create panel
    panel = Left_Side_Panel()
    panel.navigation_requested.connect(lambda x: print(f"Navigation requested: {x}"))
    
    layout.addWidget(panel)
    
    # Add a toggle button for testing
    btn = QPushButton("Toggle Panel")
    btn.clicked.connect(panel.toggle_panel)
    layout.addWidget(btn)
    
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())
