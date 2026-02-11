#-----------------------------------------------------------------------------------------
# Purpose : Slide-out chat history panel that appears from the top of Right AI Chat Panel
# Author  : Shanqin Jin  
# Email   : sjin@mun.ca

# Updated : 2025-11-29
#----------------------------------------------------------------------------------------- 

from pathlib import Path
import json
from datetime import datetime
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QLineEdit, QFrame, QMenu, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QSize, Signal, QEvent, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PySide6.QtGui import QIcon
from SaMPH_Utils.Utils import utils


# ============================================================================
# Utility helpers
# ============================================================================
def sanitize_filename(name: str, max_len: int = 200) -> str:
    """
    Produce a filesystem-safe filename stem from an arbitrary title.
    """
    if not isinstance(name, str):
        name = str(name)
    
    cleaned = re.sub(r'[\/\\:\*\?\"\<\>\|]', '_', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip()
    
    cleaned = cleaned.rstrip(' .')
    
    if not cleaned:
        cleaned = datetime.now().strftime("Chat_%Y-%m-%d_%H-%M-%S")
    
    return cleaned


# ============================================================================
# Chat Item Widget
# ============================================================================

class ChatItemWidget(QWidget):
    """
    A QWidget representing a single chat item in the history list.
    Supports inline renaming.
    """
    def __init__(self, chat_title, icon_path, parent_listwidget_item, folder_name, history_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.parent_item = parent_listwidget_item
        self.folder_name = folder_name
        self.history_list = history_list
        self.editor = None
        
        self.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 0, 0, 0)
        layout.setSpacing(6)
        
        # Icon
        self.icon = QLabel()
        self.icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
        self.icon.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.icon)
        
        # Title label
        self.label = QLabel(chat_title)
        self.label.setStyleSheet("color:#333; background-color: transparent;")
        layout.addWidget(self.label)
        layout.addStretch()
    
    # =======================================================
    # [MOD] Rename start logic - Force vertical centering
    # =======================================================
    def start_rename(self):
        """Start inline rename (Fixed Layout & Centering)"""
        if self.editor:
            return
        
        # 1. Create editor
        self.editor = QLineEdit(self.label.text(), self)
        
        # 2. Style optimization
        self.editor.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #0078D4;
                border-radius: 4px;
                padding-left: 4px;
                padding-bottom: 2px;    /* Correct text vertical gravity */
                font-size: 14px;
                color: #333;
            }
        """)
        
        # 3. Set fixed height (enough for text and border)
        editor_height = 28
        self.editor.setFixedHeight(editor_height)
        
        # 4. [Core] Calculate vertical center coordinates
        # Get total height of current row (Item Widget)
        row_height = self.height()
        
        # Calculate Y coordinate: centering formula
        center_y = int((row_height - editor_height) / 2)
        
        # Calculate X coordinate: align with original label, slight left offset 2px to cover original text
        start_x = self.label.pos().x() - 2
        
        # Calculate width: slightly wider than original text, at least 160px
        min_width = max(self.label.width() + 50, 160)
        self.editor.setFixedWidth(min_width)
        
        # 5. Move to position (Overlay mode, preserve Layout)
        self.editor.move(start_x, center_y)
        
        # 6. Show and focus
        self.editor.show()
        self.editor.setFocus()
        self.editor.selectAll()
        
        # 7. Hide original Label (hide only, do not remove from layout, keep placeholder)
        self.label.hide()
        
        # Event listener
        self.editor.installEventFilter(self)
        self.editor.returnPressed.connect(self.finish_rename)

    # =======================================================
    # [MOD] Rename end logic - Adapt to Overlay mode
    # =======================================================
    def finish_rename(self):
        """Commit the inline rename"""
        if not self.editor:
            return
        
        old_title = self.label.text()
        new_title = self.editor.text().strip() or old_title
        
        # Update data
        self.parent_item.setData(Qt.UserRole, (self.folder_name, new_title))
        self.label.setText(new_title)
        
        # Call parent callback (if any)
        try:
            # history_list -> ChatHistoryPanel
            side_panel = self.history_list.parent() 
            # Note: The parent() structure here depends on your specific UI nesting.
            # Suggest using signals or a more robust method, but if old code works, keep this try-catch
            if hasattr(side_panel, "rename_chat"):
                side_panel.rename_chat(self.parent_item, old_title, new_title)
        except Exception as e:
            # print(f"[WARN] rename_chat call failed: {e}")
            pass
        
        # Destroy editor
        self.editor.deleteLater()
        self.editor = None
        
        # [Core] Restore Label display
        self.label.show()
    
    def eventFilter(self, obj, event):
        """Close editor on focus out"""
        if obj == self.editor:
            if event.type() == QEvent.FocusOut or \
               (event.type() == QEvent.MouseButtonPress and not self.editor.rect().contains(event.pos())):
                self.finish_rename()
        return super().eventFilter(obj, event)


# ============================================================================
# Collapsible Folder Widget
# ----------------------------------------------------------------------------
# Simple folder header that can be expanded/collapsed and supports inline rename.
# ============================================================================

class CollapsibleFolder(QWidget):

    toggled = Signal(bool)

    # -------------------------------------------------------------------------
    def __init__(self, name: str, parent=None):

        super().__init__(parent)

        self.setObjectName("CollapsibleFolder")

        self.name = name
        self.is_expanded = True
        self.editor = None

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(12)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        layout.addWidget(self.icon_label)

        # Folder name label
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("font-weight:500; background:transparent;")
        self.name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(self.name_label)
        layout.addStretch()

        # Hover / Press style
        self.setStyleSheet("""
            #CollapsibleFolder {
                background-color: transparent;
                border-radius: 6px;
            }
            #CollapsibleFolder:hover {
                background-color: #e9ecef;
            }
            #CollapsibleFolder:pressed {
                background-color: #d0d0d0;
            }
        """)

        self.update_icon()

    # -------------------------------------------------------------------------
    # Toggle expand / collapse state
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_expanded = not self.is_expanded
            self.update_icon()
            self.toggled.emit(self.is_expanded)
        super().mousePressEvent(event)

    # -------------------------------------------------------------------------
    # Refresh folder icon based on state
    # -------------------------------------------------------------------------
    def update_icon(self):
        closed = utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-folder-100.png")
        opened = utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-opened-folder-100.png")
        icon_path = opened if self.is_expanded else closed
        self.icon_label.setPixmap(QIcon(icon_path).pixmap(18, 18))

    # -------------------------------------------------------------------------
    # Inline rename workflow
    # -------------------------------------------------------------------------
    def start_rename(self):
        """Allow folder rename (Fixed Layout)"""
        if self.editor:
            return
            
        # 1. Create editor
        self.editor = QLineEdit(self.name_label.text(), self)
        
        # 2. Adjust style
        # Increase padding-bottom to fine-tune text vertical position
        self.editor.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #0078D4;
                border-radius: 4px;
                padding-left: 4px;      /* Left padding */
                padding-bottom: 1px;    /* Correct text vertical gravity */
                color: #333;
                font-size: 14px;        /* Keep consistent with Label */
                font-weight: 500;
            }
        """)
        
        # 3. [Critical Mod] Set more reasonable height
        # Font 14px, suggest height at least 26px preventing text clipping
        editor_height = 28  
        self.editor.setFixedHeight(editor_height)
        
        # 4. [Critical Mod] Calculate vertical center position
        # Get total height of current row (Folder Widget)
        row_height = self.height()
        
        # Vertical centering formula: (row height - input box height) / 2
        # int() floor to prevent blurring
        center_y = int((row_height - editor_height) / 2)
        
        # X axis still aligned with Label, but slight left offset to cover original Label
        start_x = self.name_label.pos().x() - 2 
        
        # Calculate width (Label width + extra space)
        min_width = max(self.name_label.width() + 40, 180)
        self.editor.setFixedWidth(min_width)
        
        # 5. Move to position
        self.editor.move(start_x, center_y)
        
        # 6. Show and focus
        self.editor.show()
        self.editor.setFocus()
        self.editor.selectAll()
        
        # Event filter
        self.editor.installEventFilter(self)
        self.editor.returnPressed.connect(self.finish_inline_edit)
        
        # Hide original Label
        self.name_label.hide()

    # -------------------------------------------------------------------------
    # Inline rename commit
    # -------------------------------------------------------------------------
    def finish_inline_edit(self):
        """
        Persist the inline rename changes by updating both the widget label and
        the cached folder name.
        """
        if not self.editor:
            return
        new_name = self.editor.text().strip()
        if new_name:
            self.name_label.setText(new_name)
            self.name = new_name
        self.editor.deleteLater()
        self.editor = None
        self.name_label.show()

    # -------------------------------------------------------------------------
    # Event filter for rename editor
    # -------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        """
        Close the rename editor whenever the input loses focus or the user
        clicks outside of the editing rectangle.
        """
        if obj == self.editor:
            if event.type() == QEvent.FocusOut:
                self.finish_inline_edit()
            elif event.type() == QEvent.MouseButtonPress:
                if not self.editor.rect().contains(event.pos()):
                    self.finish_inline_edit()
        return super().eventFilter(obj, event)


# ============================================================================
# Slideout Chat History Panel (Main Class)
# ============================================================================

class ChatHistoryPanel(QWidget):
    """
    A slide-out panel that appears from the top of the Right AI Chat Panel.
    Manages chat folders and chat history.
    """
    
    chat_clicked = Signal(str, str)
    chat_item_double_clicked = Signal(str, str)
    new_chat_request = Signal()
    panel_closed = Signal()
    
    def __init__(self, parent=None, storage_root: str = "usr/SaMPH/ChatHistory"):

        super().__init__(parent)
        
        # State
        self.is_visible = False
        self.animation_in_progress = False
        
        # Folder & Chat
        self.chats = {}
        self.folders = {}
        self.chat_counter = 0
        self.folder_counter = 0
        self.active_folder = None
        
        # Storage
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # *** Key: Set to float above parent widget ***
        # Removed Qt.Tool to ensure it positions relative to parent, not screen
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool) 
        # Just use basic widget flags or FramelessWindowHint if needed (though default for child is fine)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True) # Ensure background is painted
        
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Key: Allow transparent background
        self.setWindowFlags(Qt.FramelessWindowHint)           # Ensure no system border


        # Styling
        self.setStyleSheet("""
            ChatHistoryPanel {
                background-color: #f8f9fa; /* Solid background color */
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QPushButton { 
                background: transparent; 
                border: none; 
                padding: 10px 16px; 
                text-align: left; 
                font-size: 14px; 
                border-radius: 8px; 
            }
            QPushButton:hover { background: #e9ecef; }
            QListWidget { border: none; background: transparent; }
            QListWidget::item { 
                padding: 6px 12px; 
                border-radius: 6px; 
                margin: 1px 0; 
            }
            QListWidget::item:hover { background: #e9ecef; }
            QListWidget::item:selected { 
                background-color: #f0f0f0; 
                color: #333; 
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.3);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Build UI
        self.init_ui()
        
        # Load history
        self.load_chat_history()
        
        # Initially hidden
        self.hide()

    def paintEvent(self, event):
        """Manually paint background to ensure opacity"""
        from PySide6.QtGui import QPainter, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#f8f9fa"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 0, 0) # Draw solid background
        # Or if using border radius in stylesheet, just fill rect or let stylesheet handle it
        # But explicit paint is safest for "transparency" issues
        super().paintEvent(event)
    
    def init_ui(self):
        
        """Build the panel UI (without top buttons)"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)
        
        # Header with title and close button
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 4, 8, 4)
        header_layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Chat History")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton()
        close_btn.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-close-100.png")))
        close_btn.setFixedSize(32, 32)
        close_btn.setIconSize(QSize(18, 18)) # Explicitly set icon size for centering
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 16px;
                padding: 7px; /* Ensure no padding affects alignment */
            }
            QPushButton:hover {
                background: #dee2e6;
            }
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.hide_panel)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        layout.addWidget(self.create_divider())
        
        # Chat History List
        self.history_list = QListWidget()
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.history_list.customContextMenuRequested.connect(self.show_context_menu)
        self.history_list.itemClicked.connect(self.on_chat_item_clicked)
        self.history_list.itemDoubleClicked.connect(self.on_chat_item_double_clicked)
        layout.addWidget(self.history_list, 1)
    




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
    
    # ==========================================================================
    # Show/Hide with slide animation
    # ==========================================================================
    
    def toggle_panel(self):
        """Toggle panel visibility with animation"""
        if self.animation_in_progress:
            return
        
        if self.is_visible:
            self.hide_panel()
        else:
            self.show_panel()
    
    def show_panel(self):
        """Show panel with slide-down animation"""
        if self.is_visible or self.animation_in_progress:
            return
        
        self.animation_in_progress = True
        
        # Position at top of parent, but below header (50px)
        if self.parent():
            parent_width = self.parent().width()
            # Height: 60% of parent height, max 400
            panel_height = min(400, int(self.parent().height() * 0.6))
            self.setFixedSize(parent_width, panel_height)
            
            # Start position: y = 50 - panel_height (hidden "behind" header)
            # End position: y = 50 (just below header)
            header_height = 50
            start_y = header_height - panel_height
            end_y = header_height
            
            self.move(0, start_y) 
            
            # Slide down animation
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(300)
            self.anim.setStartValue(QPoint(0, start_y))
            self.anim.setEndValue(QPoint(0, end_y))
            self.anim.setEasingCurve(QEasingCurve.OutCubic)
            self.anim.finished.connect(lambda: self.on_show_finished())
            self.anim.start()
            
            self.show()
            self.raise_()
            
            # Ensure header stays on top if we want it to look like it comes from under
            # But since we are a child of Right_AIChat_Panel, and header is also a child...
            # If we raise_(), we are on top of everything.
            # To look like "coming from under header", we should be below header in Z-order.
            # BUT, if we are below header, and start_y < 50, we are hidden by header (good).
            # So we should NOT raise_() above header.
            # Let's try stackUnder(header) if we can access it, or just don't raise_() to top.
            # However, we need to be above chat_display.
            # Safest: raise_() then manually stack under header if possible, or just rely on geometry clip.
            # For now, let's just animate from y=50 with height 0 -> height=target?
            # No, slide is requested.
            # Let's try simple slide from 50-height to 50.
            
        else:
            # Fallback if no parent
            self.show()
            self.on_show_finished()
    
    def on_show_finished(self):
        """Called when show animation completes"""
        self.is_visible = True
        self.animation_in_progress = False
    
    def hide_panel(self):
        """Hide panel with slide-up animation"""
        if not self.is_visible or self.animation_in_progress:
            return
        
        self.animation_in_progress = True
        
        # Slide up animation
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(250)
        self.anim.setStartValue(self.pos())
        
        # Calculate target position (move up by height, back to 50-height)
        header_height = 50
        panel_height = self.height()
        target_pos = QPoint(0, header_height - panel_height)
        
        self.anim.setEndValue(target_pos)
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        self.anim.finished.connect(lambda: self.on_hide_finished())
        self.anim.start()
    
    def on_hide_finished(self):
        """Called when hide animation completes"""
        self.hide()
        self.is_visible = False
        self.animation_in_progress = False
        self.panel_closed.emit()
    
    # ==========================================================================
    # Folder / Chat Creation / UI management
    # ==========================================================================
    
    def create_folder(self, name=None):
        """Create a folder header"""
        if name is None:
            self.folder_counter += 1
            name = f"Default folder" if self.folder_counter==1 else f"New folder {self.folder_counter-1}"
        
        folder_widget = CollapsibleFolder(name)
        item = QListWidgetItem()
        item.setSizeHint(QSize(0,36))
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setData(Qt.UserRole, (name,""))
        self.history_list.addItem(item)
        self.history_list.setItemWidget(item, folder_widget)
        
        self.folders[name] = {"widget":folder_widget,"item":item,"items":[],"expanded":True}
        
        folder_widget.toggled.connect(lambda expanded, fw=folder_widget: self.on_folder_toggled(fw, expanded))
        
        if not self.active_folder:
            self.active_folder = name
    
    def on_folder_toggled(self, folder_widget, expanded):
        """Toggle folder expansion"""
        folder_name = None
        for k,v in self.folders.items():
            if v["widget"] is folder_widget:
                folder_name = k
                break
        if folder_name is None: return
        folder = self.folders[folder_name]
        folder["expanded"] = expanded
        for chat_item in folder["items"]:
            chat_item.setHidden(not expanded)
    
    def on_chat_item_clicked(self,item):
        """Handle chat item click"""
        data = item.data(Qt.UserRole)
        if not data:
            return
        folder_name, chat_title = data
        if chat_title == "":
            self.active_folder = folder_name
            self.history_list.clearSelection()
        else:
            self.chat_clicked.emit(folder_name, chat_title)
    
    def on_chat_item_double_clicked(self, item):
        
        """Handle chat item double-click"""

        folder_name, chat_title = item.data(Qt.UserRole)
        if chat_title:
            self.chat_item_double_clicked.emit(folder_name, chat_title)
    
    # -------------------------------------------------------------------------
    def on_new_chat(self):
        """
        Ensure that a folder is active (creating or reusing one when necessary)
        and emit the `new_chat_request` signal so the host view can reset the
        chat editor area.
        """
        # Ensure there is an active folder; if not, choose the last folder
        if not self.active_folder:
            if self.folders:
                # choose the last folder in insertion order
                self.active_folder = list(self.folders.keys())[-1]
            else:
                # create a default folder
                self.create_folder()

        # Notify main window to clear current chat UI and reset state
        self.new_chat_request.emit()
    

    def save_chat_to_folder(self, folder_name, title=None, save_json=True):
        """Add chat to folder"""
        folder = self.folders.get(folder_name)
        if not folder:
            self.create_folder(folder_name)
            folder = self.folders[folder_name]
        
        self.chat_counter += 1
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H-%M-%S")
        chat_title = title if title else f"Chat {time_str}"
        
        # Add to UI
        item = QListWidgetItem()
        item.setSizeHint(QSize(0,36))
        item.setData(Qt.UserRole, (folder_name, chat_title))
        chat_widget = ChatItemWidget(
            chat_title=chat_title,
            icon_path=utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-chat-100.png"),
            parent_listwidget_item=item,
            folder_name=folder_name,
            history_list=self.history_list
        )
        row = self.history_list.row(folder["item"]) + len(folder["items"]) + 1
        self.history_list.insertItem(row, item)
        self.history_list.setItemWidget(item, chat_widget)
        folder["items"].append(item)
        item.rename_chat_inline = chat_widget.start_rename
        
        # Save JSON to disk
        if save_json:
            folder_path = self.storage_root / folder_name
            folder_path.mkdir(exist_ok=True)
            safe_stem = sanitize_filename(chat_title)
            chat_file = folder_path / f"{safe_stem}.json"
            chat_data = {"title": chat_title, "messages": []}
            try:
                with open(chat_file, "w", encoding="utf-8") as f:
                    json.dump(chat_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Failed to save chat {chat_title}: {e}")
        
        return item
    
    # -------------------------------------------------------------------------
    # Right-click menu actions: Rename, Delete, New chat, New folder, Settings
    # -------------------------------------------------------------------------
    def show_context_menu(self, pos):
        """
        Build a contextual menu based on the current selection (single folder,
        single chat, or multi-selection) and wire up the relevant actions.
        """
        
        selected_items = self.get_selected_items()
        if not selected_items:
            return

        menu = QMenu()
        menu.setContentsMargins(0,4,0,4)  # Left, Top, Right, Bottom

        # Style: white background, hover light gray, rounded corners
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;      /* white background */
                color: #333333;                 /* dark text */
                border: 1px solid #cccccc;      /* light border */
                border-radius: 8px;             /* rounded corners */
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 24px 6px 24px;     /* Adjust padding for comfort */
                border-radius: 6px;
                margin: 2px 4px;                /* Add margin for rounded look */
            }
            /* This controls the hover color */
            QMenu::item:selected {
                background-color: #f0f0f0;      /* hover light gray */
                color: #000000;
            }
            QMenu::separator {
                height: 1px;
                background: #dddddd;
                margin: 4px 0;
            }
        """)
        
        # Only allow delete when multiple items are selected
        if len(selected_items) == 1:
            item = selected_items[0]
            folder_name, chat_title = item.data(Qt.UserRole)
            if chat_title == "":
                menu.addAction("Rename", lambda: self.rename_folder_inline(item))
                menu.addAction("Delete", lambda: self.delete_folder(item))
            else:
                menu.addAction("Rename", lambda: item.rename_chat_inline())
                menu.addAction("Delete", lambda: self.delete_chat(item))
        else:
            menu.addAction("Delete", lambda: self.delete_selected_items(selected_items))

        menu.addSeparator()
        menu.addAction("New chat", self.on_new_chat)
        menu.addAction("New folder", self.on_new_folder)
        
        menu.exec(self.history_list.mapToGlobal(pos))



    # -------------------------------------------------------------------------
    def get_selected_items(self):
        """
        Convenience helper to fetch the currently selected list widget items.
        """
        return self.history_list.selectedItems()


    # -------------------------------------------------------------------------
    def delete_selected_items(self, items):
        """
        Iterate through a collection of selected items and dispatch to the
        specific folder/chat delete handlers.
        """
        for item in items:
            folder_name, chat_title = item.data(Qt.UserRole)
            if chat_title == "":
                self.delete_folder(item)
            else:
                self.delete_chat(item)

    # -------------------------------------------------------------------------
    # Folder Rename
    # -------------------------------------------------------------------------
    def rename_folder_inline(self,item):
        """
        Kick off the inline rename workflow for a folder header and ensure the
        resulting name change propagates back through `update_folder_name`.
        """
        folder_name,_ = item.data(Qt.UserRole)
        folder_widget = self.folders[folder_name]["widget"]
        folder_widget.start_rename()
        if folder_widget.editor:
            # when editingFinished fires, folder_widget.name has been updated in finish_inline_edit
            folder_widget.editor.editingFinished.connect(lambda fw=folder_widget,it=item,old=folder_name: self.update_folder_name(it, old, fw.name))
    


    # =========================================================================
    def refresh_chat_list(self):
        """
        Iterate through folders/chats and trigger lightweight repaints so custom
        widgets pick up any style or icon changes.
        """
        for folder_name, folder in self.folders.items():

            folder["widget"].update_icon()  # update folder icon
            for chat_item in folder["items"]:
                widget = self.history_list.itemWidget(chat_item)
                if widget:
                    widget.repaint()  # Use repaint() to force immediate refresh
    # =========================================================================





    # =========================================================================
    # Load Chat History from disk into the Side Panel
    # - supports old-format (list) and new-format (dict with 'title' + 'messages')
    # =========================================================================
    def load_chat_history(self):
        """
        Load all folders and chats from ChatHistory directory.
        Supports both old-style JSON (list of messages) and new-style (dict with title + messages).
        """
        for folder_path in sorted(self.storage_root.iterdir()):
            
            if not folder_path.is_dir():
                continue
            folder_name = folder_path.name
            self.create_folder(folder_name)
            folder = self.folders[folder_name]

            for chat_file in sorted(folder_path.glob("*.json")):
                try:
                    with open(chat_file, "r", encoding="utf-8") as f:
                        chat_data = json.load(f)

                    # ---------------- Detect format ----------------
                    if isinstance(chat_data, dict):
                        chat_title = chat_data.get("title", chat_file.stem)
                        messages = chat_data.get("messages", [])
                    elif isinstance(chat_data, list):
                        # old format: list of messages
                        chat_title = chat_file.stem
                        messages = chat_data
                        # wrap into dict for compatibility
                        chat_data = {"title": chat_title, "messages": messages}
                    else:
                        print(f"[WARN] Unknown chat file format: {chat_file}")
                        continue

                    # ---------------- Add to side panel ----------------
                    item = self.save_chat_to_folder(folder_name, title=chat_title, save_json=False)
                    # optionally attach loaded messages to the item for later display
                    item.chat_messages = messages
                    print(f"[INFO] Loaded chat: {chat_title} ({len(messages)} messages)")

                except Exception as e:
                    print(f"[ERROR] Failed to load {chat_file}: {e}")


    # =========================================================================
    # Disk rename helper — main fix point
    # - This method performs a safe rename of the underlying JSON file when a chat
    #   is renamed in the UI. It attempts to find the existing file (old_title)
    #   and rename it to new_title (sanitized for filename safety).
    # =========================================================================
    def rename_chat(self, listwidget_item: QListWidgetItem, old_title: str, new_title: str):
        """
        Attempt to rename the underlying JSON file for this chat.
        - listwidget_item: the QListWidgetItem representing this chat row.
        - old_title: previous visible title (UI)
        - new_title: new visible title (UI)
        This function tries a few heuristics:
         1. Exact match: {old_title}.json
         2. Sanitized match: sanitize_filename(old_title) + .json
         3. Case-insensitive / normalized search inside folder for closest stem
        """
        try:
            folder_name, _ = listwidget_item.data(Qt.UserRole)
            folder_path = self.storage_root / folder_name
            if not folder_path.exists():
                # No folder on disk — nothing to rename
                return

            # Candidate file names to check (exact UI string and sanitized)
            candidates = []
            candidates.append(folder_path / f"{old_title}.json")
            candidates.append(folder_path / f"{sanitize_filename(old_title)}.json")

            # Add also possible JSON files in folder (fallback search)
            all_jsons = list(folder_path.glob("*.json"))

            # Try exact or sanitized matches first
            chosen = None
            for c in candidates:
                if c.exists():
                    chosen = c
                    break

            # If none found, attempt reasonable fallback: case-insensitive / normalized matching
            if chosen is None:
                norm_new = sanitize_filename(new_title).lower()
                for p in all_jsons:
                    stem_norm = sanitize_filename(p.stem).lower()
                    if stem_norm == norm_new or stem_norm == sanitize_filename(old_title).lower():
                        chosen = p
                        break

            # Final fallback: try match by title inside JSON 'title' field
            if chosen is None:
                for p in all_jsons:
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict) and data.get("title", "") == old_title:
                                chosen = p
                                break
                    except Exception:
                        continue

            if chosen:
                # Compose new filename using sanitized stem
                new_stem = sanitize_filename(new_title)
                target = folder_path / f"{new_stem}.json"

                # If target already exists and it's the same as chosen, nothing to do
                if target.exists() and target.samefile(chosen):
                    return

                # If target exists but is different, we choose a safe fallback by appending timestamp
                if target.exists() and not target.samefile(chosen):
                    ts = datetime.now().strftime("%Y%m%d%H%M%S")
                    target = folder_path / f"{new_stem}_{ts}.json"

                try:
                    chosen.rename(target)
                    print(f"[INFO] Renamed chat file: {chosen} -> {target}")
                except Exception as e:
                    print(f"[ERROR] Failed to rename chat file {chosen} -> {target}: {e}")
            else:
                # No file found to rename — this is OK (maybe it was never saved to disk)
                print(f"[INFO] No underlying chat file found for rename: '{old_title}' in folder '{folder_name}'")
        except Exception as e:
            print(f"[ERR] rename_chat general failure: {e}")


    # =========================================================================
    # Delete Folder / Chat operations
    # =========================================================================

    # -------------------------------------------------------------------------
    def on_new_folder(self):
        """
        Create a brand-new folder both in the UI list and on disk, then mark it
        as the active folder for immediate use.
        """
        self.folder_counter += 1
        folder_name = f"New folder {self.folder_counter}"
        self.create_folder(folder_name)
        self.active_folder = folder_name

        # Create folder on disk
        folder_path = self.storage_root / folder_name
        folder_path.mkdir(exist_ok=True)

    # -------------------------------------------------------------------------
    # Update Folder Name
    # -------------------------------------------------------------------------
    def update_folder_name(self,item,old_name,new_name):
        """
        Apply a folder rename by updating in-memory dictionaries, list widget
        items, and the on-disk directory if it exists.
        """
        if not new_name or new_name==old_name: return
        if new_name in self.folders: return

        # Rename folder in memory
        self.folders[new_name] = self.folders.pop(old_name)
        self.folders[new_name]["item"].setData(Qt.UserRole,(new_name,""))
        for chat_item in self.folders[new_name]["items"]:
            fn, title = chat_item.data(Qt.UserRole)
            chat_item.setData(Qt.UserRole, (new_name, title))
        if self.active_folder == old_name:
            self.active_folder = new_name

        # Rename folder on disk
        old_path = self.storage_root / old_name
        new_path = self.storage_root / new_name
        if old_path.exists():
            try:
                old_path.rename(new_path)
            except Exception as e:
                print(f"Failed to rename folder {old_name} -> {new_name}: {e}")

    # -------------------------------------------------------------------------
    # Delete Folder
    # -------------------------------------------------------------------------
    def delete_folder(self, item):
        """
        Remove a folder header, all of its child chats, and the corresponding
        directory on disk. Also keeps the active folder pointer in sync.
        """
        folder_name, _ = item.data(Qt.UserRole)
        if folder_name not in self.folders:
            return
        folder = self.folders.pop(folder_name)

        # remove all chat items under the folder
        for chat_item in folder["items"]:
            self.history_list.takeItem(self.history_list.row(chat_item))
        # remove folder header
        self.history_list.takeItem(self.history_list.row(folder["item"]))

        # Delete folder on disk
        folder_path = self.storage_root / folder_name
        if folder_path.exists():
            import shutil
            try:
                shutil.rmtree(folder_path)
            except Exception as e:
                print(f"Failed to delete folder {folder_name}: {e}")

        # Update active folder
        if self.active_folder == folder_name:
            self.active_folder = list(self.folders.keys())[-1] if self.folders else None

    # -------------------------------------------------------------------------
    # Delete Chat
    # -------------------------------------------------------------------------
    def delete_chat(self, item):
        """
        Remove a single chat row and delete its persisted JSON file if present.
        """
        folder_name, chat_title = item.data(Qt.UserRole)
        folder = self.folders.get(folder_name)
        if not folder or item not in folder["items"]:
            return
        folder["items"].remove(item)
        self.history_list.takeItem(self.history_list.row(item))

        # Delete JSON file on disk
        chat_file = self.storage_root / folder_name / f"{chat_title}.json"
        # Try sanitized filename deletion as well (safer)
        chat_file_alt = self.storage_root / folder_name / f"{sanitize_filename(chat_title)}.json"
        try:
            if chat_file.exists():
                chat_file.unlink()
            elif chat_file_alt.exists():
                chat_file_alt.unlink()
        except Exception as e:
            print(f"Failed to delete chat {chat_title}: {e}")



    def update_ui_texts(self, lang_manager):

        """Update UI texts based on current language."""
        
        if not lang_manager:
            return
        
        # Update title
        title_labels = self.findChildren(QLabel)
        if title_labels:
            title_labels[0].setText(lang_manager.get_text("Chat History"))
