#--------------------------------------------------------------
# This file creates the right AI chat side panel
# Refactored with Floating Input Container & Dynamic Positioning
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-29 
#-------------------------------------------------------------- 

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QToolButton,
    QTextEdit, QScrollArea, QFrame, QSizePolicy, QComboBox, QFileDialog,
    QGraphicsDropShadowEffect, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEvent, QDateTime, QTimer
from PySide6.QtGui import QIcon, QTextImageFormat, QTextCursor, QColor

# Add the parent directory to the Python path for debugging
if __name__ == "__main__": 
    print("Debug mode!")   
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path: 
        sys.path.insert(0, project_root)




from SaMPH_Utils.Utils import utils
from SaMPH_AI.Operation_Bubble_Message import BubbleMessage
from SaMPH_GUI.Item_AIChatHistoryPanel import ChatHistoryPanel



#==============================================================
class Right_AIChat_Panel(QWidget):
    """
    Right AI chat sidebar component with floating input container.
    """
    
    # Signals
    send_message_signal = Signal(str, list, bool)  # Emit when user sends a message (text, images, show_user_message)

    show_chathistory_panel_requested = Signal()
    model_changed_signal             = Signal(str, QIcon)  # Send the new model name

    new_chat_request          = Signal()
    new_folder_request        = Signal()


    def __init__(self, parent=None):

        super().__init__(parent)
        
        # Panel state
        self.panel_width = 400 # slightly wider for the new layout
        self.is_visible = True
        self.full_width = 400  # Store expanded width for toggle animation
        
        # Data state
        self.pending_images = []
        self.messages_count = 0 # Track message count for positioning
        
        # Debounce for Enter key
        self._last_send_time = 0
        self._send_debounce_ms = 300

        # Input box configuration - Increase height for better visual breathing room
        self.input_min_height = 120  # Minimum height (px) - Increased to avoid crowding
        self.input_max_height = 220  # Maximum height (px) - Allows more text input
        
        # Language manager (will be set by main window)
        self.lang_manager = None
        
        # Initialize UI
        self.init_ui()
        





    def init_ui(self):
        """Initialize the right AI chat panel UI"""
        
        # Set size policy
        self.setMinimumWidth(400)
        self.setMaximumWidth(800)
        # self.setFixedWidth(self.panel_width) # Optional: fixed width
        
        # Main layout (Background layer)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # ============ 1. Header Section ============
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("background-color: #f8f9fa;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        # Title label
        title_label = QLabel("AI Assistant")
        title_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #333;")
        header_layout.addWidget(title_label)


        header_layout.addStretch()

        # Hide button
        self.btn_chathistory_panel = QPushButton()
        self.btn_chathistory_panel.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-order-history-100.png")))
        self.btn_chathistory_panel.setIconSize(QSize(24, 24))
        self.btn_chathistory_panel.setFixedWidth(32)
        self.btn_chathistory_panel.setFixedHeight(32)
        self.btn_chathistory_panel.setCursor(Qt.PointingHandCursor)
        self.btn_chathistory_panel.setToolTip("Show/Hide Chat History")
        self.btn_chathistory_panel.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover { 
                background-color: #F0F0F0;  /* Hover color */ 
            }
            QPushButton:pressed { 
                background-color: #005a9e;   /* Pressed color */ 
            }
        """)



        header_layout.addWidget(self.btn_chathistory_panel)
        
        self.main_layout.addWidget(header)

        # Add divider
        self.main_layout.addWidget(self.create_divider())

        
        # ============ 2. Chat Scroll Area ============
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent;")
        
        # Chat container (Vertical Layout for bubbles)
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #f4f6f9;")
        self.result_layout = QVBoxLayout(self.chat_container)
        self.result_layout.setAlignment(Qt.AlignTop)
        self.result_layout.setSpacing(15)
        self.result_layout.setContentsMargins(15, 15, 15, 15)
        
        
        # *** Spacer for Floating Input ***
        # This empty widget sits at the bottom of the scroll area
        # pushing the last message up so the floating input doesn't cover it.
        self.bottom_buffer = QWidget()
        self.bottom_buffer.setFixedHeight(220) # Initial buffer size
        self.bottom_buffer.setStyleSheet("background: transparent;")
        
        self.result_layout.addWidget(self.bottom_buffer)
        
        self.scroll_area.setWidget(self.chat_container)
        self.main_layout.addWidget(self.scroll_area)

        # ============ 3. Floating Input Container ============
        # Important: Parent is self, NOT added to main_layout
        self.input_container = QFrame(self)
        self.input_container.setObjectName("FloatingInput")
        self.input_container.setStyleSheet("""
            QFrame#FloatingInput {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Add Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        self.input_container.setGraphicsEffect(shadow)

        # Build the internal 3-part layout
        self.setup_input_layout()
        
        # *** CRITICAL FIX: Initial positioning ***
        # We need to delay the positioning until after the widget is fully shown
        # Otherwise the container will appear at (0,0) initially
        QTimer.singleShot(0, self.update_input_container_position)
        QTimer.singleShot(50, self.adjust_input_height)




        # ============ 4. Chat History Panel (Overlay) ============
        # Initialize the slide-out history panel
        # It is a child of self, so it overlays on top
        self.history_panel = ChatHistoryPanel(self)
        
        # Connect header button to toggle history panel
        self.btn_chathistory_panel.clicked.connect(self.history_panel.toggle_panel)
        
        # Connect history panel signals
        # Connect history button in input container to toggle history panel
        if hasattr(self, 'btn_history'):
            try:
                # Disconnect first to avoid multiple connections if re-initialized
                try: self.btn_history.clicked.disconnect() 
                except: pass
                self.btn_history.clicked.connect(self.history_panel.toggle_panel)
                print("[DEBUG] Connected btn_history to toggle_panel")
            except Exception as e:
                print(f"[ERROR] Failed to connect btn_history: {e}")
    #----------------------------------------------------------------------------




    #----------------------------------------------------------------------------
    # Private methods:
    #----------------------------------------------------------------------------
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



    # Setup the internal 3-part layout inside the floating container
    def setup_input_layout(self):

        """Build the 3-row layout inside the floating container, optimize spacing for better visual effect"""

        layout = QVBoxLayout(self.input_container)
        # Increase padding for more breathing room
        layout.setContentsMargins(14, 6, 14, 6)  # left, top, right, bottom
        layout.setSpacing(10)  # Increase spacing between rows

        # ---- ROW 1: Top Buttons (History, Folder, New Chat) ----
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)  # Increase spacing between buttons
        
        # Helper to create styled small buttons
        def create_icon_btn(icon_path, tooltip):

            btn = QPushButton()
            # Use icon if exists, else text for debug
            if os.path.exists(utils.local_resource_path(icon_path)):
                btn.setIcon(QIcon(utils.local_resource_path(icon_path)))
            else:
                btn.setText(tooltip[0]) # First letter fallback
            
            btn.setIconSize(QSize(18, 18))
            btn.setFixedSize(28, 28)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { border: none; border-radius: 4px; background: transparent; }
                QPushButton:hover { background-color: #f0f0f0; }
            """)
            return btn

        self.btn_history = create_icon_btn(
            "SaMPH_Images/WIN11-Icons/icons8-order-history-100.png", 
            "Chat history"
        )
        self.btn_new_folder = create_icon_btn(
            "SaMPH_Images/WIN11-Icons/icons8-folder-100.png", 
            "New folder"
        )
        self.btn_new_chat = create_icon_btn(
            "SaMPH_Images/WIN11-Icons/icons8-computer-chat-100.png", 
            "New chat"
        )
        
        # Connect New Chat
        self.btn_new_chat.clicked.connect(self.new_chat_request.emit)

        # Connect New Folder
        self.btn_new_folder.clicked.connect(self.new_folder_request.emit)

        top_layout.addWidget(self.btn_history)
        top_layout.addWidget(self.btn_new_folder)
        top_layout.addWidget(self.btn_new_chat)
        top_layout.addStretch() # Push buttons to left
        
        layout.addLayout(top_layout)

        # ---- ROW 2: Text Input (Chat Line Edit) ----
        self.chat_line_edit = QTextEdit()
        self.chat_line_edit.setPlaceholderText("Ask anything...")
        self.chat_line_edit.setFrameShape(QFrame.NoFrame)
        
        # *** Critical Fix: Set text box size policy and height limits ***
        # Set to Expanding vertical policy, but with max height limit
        self.chat_line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Set minimum and preferred height to prevent text box from expanding too much
        self.chat_line_edit.setMinimumHeight(30)  # Minimum height: single line text
        self.chat_line_edit.setMaximumHeight(120)  # Maximum height: prevent taking up too much space
        
        self.chat_line_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                font-size: 14px;
                color: #333;
                selection-background-color: #0078d4;
            }
        """)
        self.chat_line_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # *** Critical Optimization: Do not connect textChanged directly ***
        # Text change naturally triggers resizeEvent, avoiding frequent updates
        # self.chat_line_edit.textChanged.connect(self.adjust_input_height)  # Connection removed
        
        self.chat_line_edit.installEventFilter(self) # For Shift+Enter
        
        layout.addWidget(self.chat_line_edit)

        # ---- ROW 3: Bottom Controls (Image, Model, Send) ----
        bot_layout = QHBoxLayout()
        bot_layout.setSpacing(12)  # Increase spacing between bottom controls

        # Insert Image
        self.btn_insert_image = QPushButton()
        self.btn_insert_image.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-add-image-100.png")))
        self.btn_insert_image.setIconSize(QSize(20, 20))
        self.btn_insert_image.setFixedSize(32, 32)
        self.btn_insert_image.setCursor(Qt.PointingHandCursor)
        self.btn_insert_image.clicked.connect(self.insert_image)
        self.btn_insert_image.setStyleSheet("""
            QPushButton { 
                border: 1px solid #aaaaaa;
                border-radius: 6px; 
                background: transparent; 
            }
            QPushButton:hover { 
                background-color: #f0f0f0; 
            }
        """)
        bot_layout.addWidget(self.btn_insert_image)

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ComboBox: AI Engine selection
        # ComboBox: AI Engine selection
        self.AI_engine_box = QComboBox()

        # Connect the combobox selection change signal to the corresponding slot
        self.AI_engine_box.currentIndexChanged.connect(self.emit_model_changed)

        # Set style for the combobox
        arrow_path = utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-expand-arrow-100.png")

        print(f"[DEBUG] Loading arrow from: {arrow_path}")

        arrow_path = arrow_path.replace("\\", "/")
        self.AI_engine_box.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid #aaaaaa;
                border-radius: 8px;
                padding: 2px 0px 2px 0px;
                min-width: 6em;
                height: 26px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: url("{arrow_path}");
                width: 16px;
                height: 16px;
            }}
            QComboBox::item:hover {{
                background-color: #F0F0F0;  /* Hover color */
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid #aaaaaa;
                border-radius: 6px;
                selection-background-color: #d0f0c0;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #F0F0F0;      /* Hover color: very light gray */
                border-radius: 6px;              /* Keep rounded corners */
                color: black;                   /* Hover text color */
            }}
        """)
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        bot_layout.addWidget(self.AI_engine_box)
        bot_layout.addStretch() # Spacer between model and send button

        # Send Button
        self.btn_send = QPushButton("")
        self.btn_send.setIcon(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-enter-100.png")))
        self.btn_send.setIconSize(QSize(18, 18))
        self.btn_send.setFixedSize(36, 36)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.clicked.connect(self.on_send_clicked)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #aaaaaa;
                border-radius: 18px; /* Circular */
            }
            QPushButton:hover { 
                background-color: #F0F0F0;  /* Hover color */ 
            }
            QPushButton:pressed { 
                background-color: #005a9e; 
            }
        """)
        bot_layout.addWidget(self.btn_send)

        layout.addLayout(bot_layout)

        # Initial load of AI models
        self.refresh_ai_models()

    def refresh_ai_models(self):
        """
        Reload AI configuration and refresh the model combobox.
        Can be called dynamically when settings change.
        """
        # Clear existing items
        self.AI_engine_box.clear()
        self.model_icons = [] # Initialize here to ensure it exists
        
        # Get the AI engine list from usr/account.josn file
        usr_dir = utils.get_global_usr_dir()
        account_file = usr_dir / "Settings/account.json"
        
        # Load config (now safe if file missing)
        self.AI_provider, self.base_url, self.api_key, self.models = self.load_AI_config(account_file)
        
        if self.api_key and self.models:
            print("[INFO] API Key:", self.api_key)
            print("[INFO] Models:", self.models)
        else:
            print("[INFO] No AI configuration loaded (account.json missing or empty).")
            # Use language manager if available, otherwise use English text
            placeholder = "No AI Models Configured"
            if hasattr(self, 'lang_manager') and self.lang_manager:
                placeholder = self.lang_manager.get_text("No AI Models Configured")
            self.AI_engine_box.addItem(placeholder)
            return

        for full_model_name in self.models:
            
            if "/" in full_model_name:
                # print(f"[WARNING] Your model format is 'provider/model_name', such as those in OpenRouter and Groq.")
                AI_engine = full_model_name.split("/")[1]
            else:
                # print(f"[WARNING] Your model format is 'model_name', such as those in DeepSeek or Qwen.")
                AI_engine = full_model_name

            fname_lower = full_model_name.lower()
            if any(k in fname_lower for k in ["openai", "gpt"]):
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-chatgpt-100-2.png"))
            elif "openrouter" in fname_lower:
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-openrouter-100.png"))
            elif "tngtech" in fname_lower:
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-tngtech-100.png"))
            elif "deepseek" in fname_lower:
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-deepseek-100.png"))
            elif "qwen" in fname_lower:
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-qwen-100.png"))
            elif any(k in fname_lower for k in ["google", "gemma", "gemini"]):
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-Gemma-100.png"))
            elif any(k in fname_lower for k in ["meta", "llama"]):
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-meta-100.png"))
            elif "kwaipilot" in fname_lower:
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-meta-100.png"))
            elif any(k in fname_lower for k in ["x-ai", "grok"]):
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-grok-100.png"))
            elif any(k in fname_lower for k in ["mistral"]):
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-Mistral-100.svg"))
            else:
                icon = QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-Mistral-100.svg"))  # default blank icon

            # Add the model to the combobox
            self.AI_engine_box.addItem(icon, AI_engine)
            self.model_icons.append(icon)











    # ================= LAYOUT CONSTANTS =================
    # Layout constants: Unify management of all margins and ratios for easy adjustment
    # These values are carefully tuned for optimal visual effect
    LAYOUT_CONSTANTS = {
        'horizontal_margin': 10,        # Horizontal margin (px) - Increased for better breathing room
        'bottom_margin': 10,            # Bottom margin (px) - Leave enough space to avoid being too close to the edge
        'center_vertical_ratio': 0.50,  # Vertical center ratio (0.45 = Golden ratio, visually most comfortable)
        'width_ratio_center': 0.85,     # Width ratio when centered - More focused, avoid being too wide
        'width_ratio_bottom': 0.95,     # Width ratio when at bottom - Utilize space but not edge-to-edge
        'text_padding': 42,             # Extra space for text height (px) - Compact but not cramped
    }

    # ================= LOGIC FUNCTIONS =================
    def adjust_input_height(self):
        """
        Smartly adjust input container height and position
        
        Functionality:
        1. Dynamically adjust container height based on text content (input box grows upwards)
        2. Adjust width based on message count (narrower when no messages, wider when active)
        3. Atomic update of position and size to avoid visual jitter
        
        Note: Text box height is now controlled by CSS maxHeight, only container is adjusted here
        """
        # Calculate ideal container height
        # Text box height is now limited to 30-120px by CSS, handles scrolling automatically
        doc_height = self.chat_line_edit.document().size().height()
        text_height = min(max(doc_height, 30), 120)  # Limit to 30-120px
        
        # Container height = text height + top row(~38px) + bottom row(~42px) + padding(12px) + spacing(20px)
        container_height = text_height + 38 + 42 + 12 + 20
        new_height = int(max(self.input_min_height, min(self.input_max_height, container_height)))
        
        curr_height = self.input_container.height()
        
        # Dynamically adjust width: always use bottom width ratio
        # if self.messages_count == 0:
        #     width_ratio = self.LAYOUT_CONSTANTS['width_ratio_center']
        # else:
        width_ratio = self.LAYOUT_CONSTANTS['width_ratio_bottom']
        
        new_width = int(self.scroll_area.width() * width_ratio)
        # Prevent negative or too small widths
        new_width = max(50, new_width)
        curr_width = self.input_container.width()
        
        # Check if width or height changed
        width_changed = (new_width != curr_width)
        height_changed = (new_height != curr_height)
        
        # If width or height changed, update position
        if width_changed or height_changed:
            geo = self.input_container.geometry()
            h = self.scroll_area.height()
            
            # *** Critical Fix: Only recalculate Y position when height changes ***
            # If only width changes, keep Y position constant to avoid vertical jitter
            if height_changed:
                # Always fixed at bottom, leave margin
                margin = self.LAYOUT_CONSTANTS['bottom_margin']
                new_y = h - new_height - margin
            else:
                # Width changed but height unchanged: keep current Y position
                new_y = geo.y()
            
            # Calculate horizontal center position
            h_margin = self.LAYOUT_CONSTANTS['horizontal_margin']
            new_x = h_margin
            
            # Atomic update: set position and size together to prevent visual jitter
            self.input_container.setGeometry(
                new_x, 
                new_y, 
                new_width, 
                new_height
            )

    def update_input_container_position(self):
        """
        Update input container position (handles horizontal centering and vertical positioning)
        
        Positioning strategy:
        - No messages (messages_count == 0): Horizontally and vertically centered, slightly upwards
        - With messages (messages_count > 0): Fixed at bottom, horizontal margins
        """
        parent_w = self.width()
        parent_h = self.height()
        container_h = self.input_container.height()
        
        # Calculate container width and horizontal position
        h_margin = self.LAYOUT_CONSTANTS['horizontal_margin']
        container_w = parent_w - (h_margin * 2)
        # Prevent negative or too small widths
        container_w = max(50, container_w)
        x = h_margin  # Left margin
        
        self.input_container.setFixedWidth(container_w)
        
        # Calculate vertical position
        # Always fixed at bottom
        margin_bottom = self.LAYOUT_CONSTANTS['bottom_margin']
        y = parent_h - container_h - margin_bottom
        
        # if self.messages_count == 0:
        #     # Center mode: use visual center (slightly up)
        #     y = int((parent_h - container_h) * self.LAYOUT_CONSTANTS['center_vertical_ratio'])
        # else:
        #     # Bottom mode: fixed at bottom
        #     margin_bottom = self.LAYOUT_CONSTANTS['bottom_margin']
        #     y = parent_h - container_h - margin_bottom
        
        # Apply position and raise to top
        self.input_container.move(x, y)
        self.input_container.raise_()
    #-----------------------------------------------------------------------------

    #-----------------------------------------------------------------------------
    # The send button
    def on_send_clicked(self):

        """
        Handles sending a message from the chat input area.
        
        Steps:
        1. Retrieves the text and pending images.
        2. Skips sending if both are empty.
        3. Emits the custom signal with text and images.
        4. Clears the input and pending image list.
        """

        text = self.chat_line_edit.toPlainText().strip()
        if not text and not self.pending_images:
            return  # Do not send empty messages

        # Copy images to avoid mutation during async send
        images = self.pending_images.copy()
        
        # Emit the signal for the main chat handler (show user message by default)
        self.send_message_signal.emit(text, images, True)

        # Clear input box and temporary images after sending
        self.chat_line_edit.clear()
        self.pending_images.clear()

        # Update the position of the input container
        self.messages_count += 1
        self.adjust_input_height()
        self.update_input_container_position()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
        self.messages_count += 1
        self.adjust_input_height()
        self.update_input_container_position()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
    #-----------------------------------------------------------------------------

    #-----------------------------------------------------------------------------
    def send_external_message(self, text, show_user_message=True, skip_format_instruction=False):
        """
        Send a message programmatically from other parts of the application.
        
        Args:
            text (str): The message text to send.
            show_user_message (bool): If False, hides the user message bubble from the chat UI.
            skip_format_instruction (bool): If True, skip LaTeX format instructions (for PDF generation).
        """
        if not text:
            return

        # Ensure panel is visible
        if not self.is_visible:
            self.toggle_panel()
            
        # Store skip_format_instruction flag for controller to use
        # We need to pass this to the controller somehow
        # Option 1: Add it to the signal (requires modifying signal definition)
        # Option 2: Store it as an instance variable for the controller to read
        self._skip_format_instruction = skip_format_instruction
        
        # Emit signal to controller with show_user_message parameter
        self.send_message_signal.emit(text, [], show_user_message)
        
        # Add user bubble locally (controller might do this too, but usually UI updates immediately)
        # Note: The controller (Operation_Chat_Controller) usually handles adding the bubble 
        # via the signal connection. If we add it here AND the controller adds it, we get duplicates.
        # Let's check how on_send_clicked works. 
        # on_send_clicked emits signal, and clears input. It DOES NOT add bubble directly.
        # The controller (Operation_Chat_Controller.send_message) calls self.ui.add_message_bubble.
        # So we just need to emit the signal.
        
        # However, we might want to ensure the UI updates (scroll to bottom)
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
    #-----------------------------------------------------------------------------



    #-----------------------------------------------------------------------------
    def resizeEvent(self, event):
        """
        Handle window resize event
        Ensure input container adjusts correctly when window resizes
        """

        # Update the input container height first
        if hasattr(self, 'adjust_input_height'):
            self.adjust_input_height()

        # Then update its width and its position
        self.update_input_container_position()
        
        # Resize history panel if visible
        if hasattr(self, 'history_panel') and self.history_panel.is_visible:
            # Keep it full width and appropriate height
            panel_height = min(400, int(self.height() * 0.6))
            self.history_panel.setFixedSize(self.width(), panel_height)
            # Ensure it stays at top (0, 50) if it's fully shown
            if not self.history_panel.animation_in_progress:
                self.history_panel.move(0, 50) # Fixed: y=50 (below header)

        super().resizeEvent(event)
        
        # Use moderate delay (30ms) to coalesce continuous resize events
        # Avoids jitter from frequent updates while maintaining responsiveness
        # QTimer.singleShot(30, self.adjust_input_height)

    def showEvent(self, event):
        """Ensure correct layout when window is first shown"""
        super().showEvent(event)
        # Update position first, then height, ensuring correct initial display
        QTimer.singleShot(0, self.update_input_container_position)
        QTimer.singleShot(10, self.adjust_input_height)

    def eventFilter(self, obj, event):
        """Handle Enter key in text input"""
        if obj == self.chat_line_edit and event.type() == QEvent.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key_Enter, Qt.Key_Return):
                if key_event.modifiers() & Qt.ShiftModifier:
                    # Shift+Enter: insert newline
                    self.chat_line_edit.insertPlainText("\n")
                    return True
                else:
                    # Enter: send message
                    current_time = QDateTime.currentMSecsSinceEpoch()
                    if current_time - self._last_send_time >= self._send_debounce_ms:
                        self.on_send_clicked()
                        self._last_send_time = current_time
                    return True
        return super().eventFilter(obj, event)



    # ================= CHAT OPERATIONS =================
    # Insert image
    def insert_image(self):
        """Handle image insertion"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_name:
            self.pending_images.append(file_name)
            
            # Show thumbnail in text input
            cursor = self.chat_line_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            img_format = QTextImageFormat()
            img_format.setName(file_name)
            img_format.setWidth(60) # Thumbnail size
            img_format.setHeight(60)
            cursor.insertImage(img_format)
            cursor.insertText(" ")
            
            # Re-adjust height because image makes it taller
            self.adjust_input_height()

    def add_message_bubble(self, text, is_user=True):
        """Add a message bubble using BubbleMessage class"""
        # Ensure imports work, otherwise use fallback
        try:
            bubble = BubbleMessage(
                text=text,
                is_user=is_user,
                user_name="User",
                model_name=self.model_combo.currentText(),
                parent_width=self.chat_container.width()
            )
        except Exception:
            # Fallback if BubbleMessage is not fully compatible or imported
            bubble = QLabel(f"{'User' if is_user else 'AI'}: {text}")
            bubble.setWordWrap(True)
            bubble.setStyleSheet(f"background: {'#d1e7dd' if is_user else '#fff'}; padding: 10px; border-radius: 10px;")

        # Insert before the bottom_buffer
        # layout.count() - 1 is the index of bottom_buffer
        self.result_layout.insertWidget(self.result_layout.count() - 1, bubble)
        
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))


    def clear_all_messages(self):
        """Reset chat to initial state"""
        # Remove all widgets except bottom_buffer (which is last)
        # We iterate backwards from count-2 down to 0
        while self.result_layout.count() > 1:
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Reset position to center
        self.messages_count = 0
        self.update_input_container_position()

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
                self.full_width = 400
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
        
        # Store lang_manager for use in other methods
        self.lang_manager = lang_manager
        
        # Update title
        title_labels = self.findChildren(QLabel)
        if title_labels:
            title_labels[0].setText(lang_manager.get_text("AI Assistant"))
        
        # Update input placeholder
        if hasattr(self, 'input_text'):
            self.input_text.setPlaceholderText(lang_manager.get_text("Ask AI assistant"))
        
        # # Update send button
        # if hasattr(self, 'btn_send'):
        #     self.btn_send.setText(lang_manager.get_text("Send"))
        
        # Update new chat button tooltip
        new_chat_buttons = self.findChildren(QPushButton)
        for btn in new_chat_buttons:
            if btn.toolTip() in ["New chat", "新建对话"]:
                btn.setToolTip(lang_manager.get_text("New chat"))

            if btn.toolTip() in ["Chat history", "聊天记录"]:
                btn.setToolTip(lang_manager.get_text("Chat history"))

            if btn.toolTip() in ["New folder", "新建文件夹"]:
                btn.setToolTip(lang_manager.get_text("New folder"))

            if btn.toolTip() in ["Show/Hide Chat History", "显示/隐藏聊天记录"]:
                btn.setToolTip(lang_manager.get_text("Show/Hide Chat History"))
        
        # Update AI model combobox placeholder if it contains "No AI Models Configured"
        if hasattr(self, 'AI_engine_box'):
            current_text = self.AI_engine_box.currentText()
            if current_text in ["No AI Models Configured", "未配置 AI 模型"]:
                self.AI_engine_box.setItemText(0, lang_manager.get_text("No AI Models Configured"))

    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Slots for signals
    def on_chathistory_panel_clicked(self):
        print("Toolbar: emit show side panel signal")
        self.show_chathistory_panel_requested.emit()

    def get_current_AI_model(self):
        # Check if models list exists and has elements
        if not hasattr(self, 'models') or not self.models:
            print("[WARNING] No AI models configured")
            return None
        
        # Check if current index is valid
        idx = self.AI_engine_box.currentIndex()
        if 0 <= idx < len(self.models):
            print("[INFO] Current AI model selected:", self.models[idx])
            return self.models[idx]
        else:
            print(f"[WARNING] Invalid model index {idx}, using first model")
            return self.models[0] if self.models else None
    
    def get_current_AI_model_logo(self):
        if not hasattr(self, 'model_icons') or not self.model_icons:
            return QIcon()
        
        idx = self.AI_engine_box.currentIndex()
        if 0 <= idx < len(self.model_icons):
            return self.model_icons[idx]
        return QIcon()


    def emit_model_changed(self, new_model_index):
        if new_model_index < 0:
            return

        # Safety check: if models list is empty or index out of range (e.g. "No AI Models Configured" item)
        if not hasattr(self, 'models') or not self.models or new_model_index >= len(self.models):
            return

        new_model = self.models[new_model_index]
        
        # Safety check for icons
        if hasattr(self, 'model_icons') and self.model_icons and new_model_index < len(self.model_icons):
            model_icon = self.model_icons[new_model_index]
        else:
            model_icon = QIcon()

        print("[INFO] Tool_Bar: model changed to", new_model)
        self.model_changed_signal.emit(new_model, model_icon)
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    def load_AI_config(self, config_path):
        """
        Load OpenRouter configuration from a JSON file.
        Returns empty values if file is missing or invalid, instead of showing error boxes.
        
        Returns:
            tuple: (provider, base_url, api_key, models)
        """
        import json
        from pathlib import Path

        # Check if file exists
        if not Path(config_path).exists():
            print(f"[INFO] AI config file not found: {config_path}")
            return None, None, None, []

        # -------------------------------
        # Load JSON file
        # -------------------------------
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load account file: {e}")
            return None, None, None, []

        # -------------------------------
        # Extract fields safely
        # -------------------------------
        AI_provider = config.get("Provider")
        base_url = config.get("base_url")
        api_key = config.get("API-Key")
        models = config.get("models")

        if not isinstance(models, (list, set)):
            models = []

        return AI_provider, base_url, api_key, list(models)
    # ------------------------------------------------------------------




#--------------------------------------------------------------
# Test code
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    window = QWidget()
    layout = QHBoxLayout(window)
    layout.setContentsMargins(0,0,0,0)
    
    # Left dummy
    left = QLabel("Left Content")
    left.setStyleSheet("background: #ccc;")
    layout.addWidget(left, 1)
    
    # Right Panel
    panel = Right_AIChat_Panel()
    layout.addWidget(panel)
    
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())
