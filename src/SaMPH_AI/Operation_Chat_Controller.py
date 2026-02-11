#-----------------------------------------------------------------------------------------
# Purpouse: This file contains the Operation_Chat_Controller class
#           It is used to control the chat operations between GUI and AI backend
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-23 
#----------------------------------------------------------------------------------------- 


import json
import re
import io
import base64
import requests
import matplotlib
import matplotlib.pyplot as plt
import markdown
import mimetypes

from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from PySide6.QtCore import QTimer, QThread, Signal, Qt
from PySide6.QtGui import QImageReader 

from SaMPH_AI.Operation_Bubble_Message import BubbleMessage, HTML_WRAPPER
from SaMPH_Utils.Utils import utils


# Import rendering utilities from Utils
latex_to_base64_block = utils.latex_to_base64_block
latex_to_mathml_inline = utils.latex_to_mathml_inline
wrap_code_with_table = utils.wrap_code_with_table
unicode_to_latex = utils.unicode_to_latex

# ============================================================
# Backend rendering configuration and markdown converter setup
# ============================================================
QImageReader.setAllocationLimit(0)
matplotlib.use('Agg')
plt.rcParams['mathtext.fontset'] = 'cm' 
plt.rcParams['font.serif'] = ['DejaVu Serif']

md_converter = markdown.Markdown(extensions=[
    'fenced_code', 'tables', 'nl2br', 'codehilite'
], extension_configs={
    'codehilite': {'css_class': 'codehilite', 'noclasses': False, 'use_pygments': True}
})

# ============================================================================
# Process Mixed Content - LaTeX and Markdown Rendering
# ============================================================================
def process_mixed_content(raw_text):
    # [Added] Remove <think> tags and their content
    text = re.sub(r'<think>.*?</think>\s*', '', raw_text, flags=re.DOTALL)
    
    # [Key Fix] Convert Unicode math symbols to LaTeX first
    text = unicode_to_latex(text)
    
    text = re.sub(r'([^\n])\n\s*-\s+', r'\1\n\n- ', text)
    text = re.sub(r'(?m)^(\s*)(\d+)\.\s+(.*)', r'\1**\2.** \3', text)
    
    ph_map = {}; ctr = 0
    def rep_blk(m):
        nonlocal ctr; k = f"MB{ctr}P"; ctr+=1
        # Support both $$...$$ and \[...\] syntax
        latex_code = m.group(1) or m.group(2)
        ph_map[k] = latex_to_base64_block(latex_code.strip(), max_width_px=600)
        return k
        
    def rep_inl(m):
        nonlocal ctr; k = f"MI{ctr}P"; ctr+=1
        # Support both $...$ and \(...\) syntax
        latex_code = m.group(1) or m.group(2)
        latex_stripped = latex_code.strip()
        
        # [Key Fix] Use image rendering for subscript(_) or superscript(^)
        # Because QTextBrowser cannot properly display MathML <msup> and <msub>
        if '_' in latex_stripped or '^' in latex_stripped:
            # inline=True: Use inline style, aligned with text
            ph_map[k] = latex_to_base64_block(latex_stripped, font_size=11, dpi=120, max_width_px=400, inline=True)
        else:
            ph_map[k] = latex_to_mathml_inline(latex_stripped)
        return k

    # [Key Enhancement] Apply regex patterns for block and inline math 
    text = re.sub(r'(?:\$\$([\s\S]*?)\$\$)|(?:\\\[([\s\S]*?)\\\])', rep_blk, text)
    text = re.sub(r'(?:(?<!\\)\$([^\$\n]+?)(?<!\\)\$)|(?:\\\((.*?)\\\))', rep_inl, text)
    
    md_converter.reset()
    html = md_converter.convert(text)
    
    html = wrap_code_with_table(html)
    
    for k, v in ph_map.items(): html = html.replace(k, v)
    return HTML_WRAPPER.format(content=html)



# ============================================================
# AIChatWorker (unchanged behavior, kept for context)
# ============================================================
class AIChatWorker(QThread):
    """
    Generic AI chat worker thread.
    Supports all OpenAI-compatible APIs: OpenRouter, DeepSeek, OpenAI, Ollama, etc.
    """
    # Signal: Send processed content back to UI
    finished = Signal(dict, object) 
    # Signal: Send token usage statistics
    stats_updated = Signal(int)

    def __init__(self, api_key, model, base_url, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.model = model
        self.base_url = base_url  # Dynamic API address
        self.queue = Queue()
        self._running = True

    # ------------------------------------------------------------------------
    # Add Task to Queue
    # ------------------------------------------------------------------------
    def add_task(self, msgs, bubble):
        """Add task to queue"""
        self.queue.put((msgs, bubble))

    # ------------------------------------------------------------------------
    # Worker Thread Main Loop
    # ------------------------------------------------------------------------
    def run(self):
        while self._running:
            try:
                # Get task from queue, timeout prevents blocking thread exit
                task = self.queue.get(timeout=0.5)
            except Empty:
                continue
            
            if task is None:
                break
                
            msgs, bubble = task
            try:
                # print(f"[INFO] Worker sending request to: {self.base_url} | Model: {self.model}")
                
                # Send request (using dynamic Base URL)
                resp = requests.post(
                    self.base_url, 
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model, 
                        "messages": msgs, 
                        "temperature": 0.7
                    }, 
                    timeout=60
                )
                resp.raise_for_status()
                
                # Parse response
                response_data = resp.json()
                content = response_data['choices'][0]['message']['content']
                
                # Extract token statistics
                if 'usage' in response_data:
                    total_tokens = response_data['usage']['total_tokens']
                    self.stats_updated.emit(total_tokens)

                if self._running:
                    # [Key Recovery] Render in background thread!
                    # ------------------------------------------------------
                    # process_mixed_content includes: latex to image, markdown to HTML
                    # Time-consuming operations done here, won't freeze UI
                    html_output = process_mixed_content(content)
                    
                    # Send result (including rendered HTML)
                    # ------------------------------------------------------
                    self.finished.emit(
                        {"html": html_output, "raw_text": content, "images": None}, 
                        bubble
                    )
                    
            except Exception as e:
                print(f"[Error] AI Worker Failed: {e}")
                if self._running:
                    self.finished.emit(
                        {"html": f"<p style='color:red'>Error: {e}</p>", "raw_text": str(e), "images": None}, 
                        bubble
                    )
            finally:
                self.queue.task_done()

    # ------------------------------------------------------------------------
    # Stop Worker Thread
    # ------------------------------------------------------------------------
    def stop(self):
        self._running = False
        self.queue.put(None)
        self.quit()
        self.wait()

    # ------------------------------------------------------------------------
    # Update Configuration Dynamically
    # ------------------------------------------------------------------------
    def update_config(self, new_api_key, new_base_url, new_model):

        """Dynamically update config without restarting thread"""

        self.api_key = new_api_key
        self.base_url = new_base_url
        self.model = new_model

        print(f"[INFO] Worker config updated: {self.model} @ {self.base_url}")



# ============================================================
# Operation_Chat_Controller
# - adds a robust file resolution helper `resolve_chat_file`
# - uses that helper when opening chat files so UI/disk name mismatch is tolerated
# ============================================================

class Operation_Chat_Controller:

    def __init__(self, main_window, model="openai/gpt-4o"):

        # References to main window components
        self.chat_window     = main_window.right_panel
        self.scroll_area     = main_window.right_panel.scroll_area
        self.result_display  = main_window.right_panel.result_layout
        self.side_panel      = main_window.right_panel.history_panel
        self.setting_window  = main_window.setting_page


        # Get the initial model from the tool bar
        self.model           = main_window.right_panel.get_current_AI_model()
        
        # If no model configured, use a default placeholder
        if self.model is None:
            self.model = "No AI Model Configured"
            print("[WARNING] No AI model configured, using placeholder")
            
        self.model_logo      = main_window.right_panel.get_current_AI_model_logo()                                              


        # Get the API Key and base URL from settings
        self.api_key  = self.setting_window.get_api_key()
        self.base_url = self.setting_window.get_base_url()  


        self.current_chat_file = None
        self.active_chat_path = None
        self.chat_history = []
        

        # 2. Initialize Worker
        print(f"[INFO] Initializing AIChatWorker with model: {self.model}, base_url: {self.base_url}")
        print(f"[INFO] Using API Key: {self.api_key}")
        self.worker = AIChatWorker(self.api_key, self.model, self.base_url)

        # 3. Connect Signals
        # worker.finished emits (reply_dict, bubble_widget)
        self.worker.finished.connect(self.on_ai_reply)
        
        
        self.worker.start()
        



    # Update the model for chat controller
    # ========================================================================
    # Update Model Configuration
    # ========================================================================
    def update_model_for_chat_controller(self, new_model, new_model_icon):

        print("[INFO] Operation_Chat_Controller: model updated to", new_model)

        self.model = new_model
        self.model_logo = new_model_icon

        # Also update worker's model
        # Get the new API Key and base URL from settings
        # If the worker exists, update its config
        new_key = self.setting_window.get_api_key()
        new_url = self.setting_window.get_base_url()

        print(f"[INFO] Updating AIChatWorker with model: {self.model}, new_url: {new_url}")
        print(f"[INFO] Updating API Key: {new_key}")

        if self.worker:
            self.worker.update_config(new_key, new_url, new_model)


    # =========================================================================
    # File helpers: robust chat file resolution
    # - resolve_chat_file will attempt exact and fuzzy matches before giving up.
    # =========================================================================
    # ========================================================================
    # Resolve Chat File Path with Fuzzy Matching
    # ========================================================================
    def resolve_chat_file(self, folder: str, chat_title: str) -> Path:
        """
        Try to find the correct chat JSON file on disk for the requested folder + chat_title.
        Returns a Path if found, else a Path that doesn't exist (so caller can act).
        Resolution strategy:
          1. Exact match: folder/chat_title.json
          2. Sanitized match: folder/sanitize(chat_title).json
          3. Case-insensitive stems: compare sanitized stems
          4. Inspect JSON 'title' field inside files for matches
        This helps when UI title and filesystem filename drift apart (e.g. manual rename or encoding).
        """
        usr_dir = utils.get_global_usr_dir()

        folder_path = usr_dir / Path("ChatHistory") / folder

        if not folder_path.exists() or not folder_path.is_dir():
            return folder_path / f"{chat_title}.json"  # non-existing path

        # helper sanitization
        def _sanitize(s: str):
            if not isinstance(s, str):
                s = str(s)
            s = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', s)
            s = re.sub(r'\s+', ' ', s).strip()
            s = s.rstrip(' .')
            return s

        cand_exact = folder_path / f"{chat_title}.json"
        if cand_exact.exists():
            return cand_exact

        cand_sanitized = folder_path / f"{_sanitize(chat_title)}.json"
        if cand_sanitized.exists():
            return cand_sanitized

        # list all jsons and try to match sanitized stems
        all_jsons = list(folder_path.glob("*.json"))
        target_norm = _sanitize(chat_title).lower()
        for p in all_jsons:
            if _sanitize(p.stem).lower() == target_norm:
                return p

        # last resort: inspect 'title' field inside JSON files
        for p in all_jsons:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data.get("title", "") == chat_title:
                        return p
            except Exception:
                continue

        # not found
        return folder_path / f"{chat_title}.json"


    # ========================================================================
    # Ensure Chat File Exists
    # ========================================================================
    def ensure_chat_file(self):
        """
        Ensures a chat JSON file exists for the current chat window.
        If current_chat_file already exists on disk, keep it.
        Otherwise create a new file under active folder.
        """
        # 1. If file exists, return
        if self.current_chat_file and Path(self.current_chat_file).exists():
            return

        # 2. Create new file logic
        usr_dir = utils.get_global_usr_dir()
        folder = self.side_panel.active_folder or "Default folder"
        base_path = usr_dir / "ChatHistory" / folder
        base_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = base_path / f"Chat {timestamp}.json"

        init_data = {
            "title": f"Chat {timestamp}",
            "folder": folder,
            "messages": []
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(init_data, f, ensure_ascii=False, indent=2)

        self.current_chat_file = str(file_path)
        self.side_panel.save_chat_to_folder(folder, title=init_data["title"])


    # ---------------------------------------------------------
    # send_message, _get_image_data_uri, _history_to_messages unchanged
    # (we keep your original behavior; only the file resolution was enhanced)
    # ---------------------------------------------------------
    # ========================================================================
    # Send Message to AI
    # ========================================================================
    def send_message(self, text: str, images: list = None, show_user_message: bool = True):
        """
        Send message to AI.
        :param text: Text content
        :param images: Image list (Base64 string list or file path list)
        :param show_user_message: If False, hides the user message bubble from the chat UI (but still sends to AI)
        """
        # 1. Modified validation: return only if no text AND no images
        # This allows users to send images without text
        if not text.strip() and not images: 
            return
            
        self.ensure_chat_file()

        w = max(100, self.scroll_area.viewport().width() - 40)
        
        # 2. Modified record saving: pass real images data, not hardcoded None
        self.append_record("user", {"text": text, "images": images})

        # 3. Modified UI creation: conditionally add user bubble based on show_user_message
        if show_user_message:
            user_bubble = BubbleMessage(
                text=text, 
                images=images,  # <--- Key: Pass images here so UI will display them
                is_user=True, 
                parent_width=w
            )
            self.result_display.insertWidget(self.result_display.count()-1, user_bubble)

        # 4. AI bubble stays unchanged
        ai_bubble = BubbleMessage(
            text="Thinking...", 
            is_user=False, 
            ai_logo=self.model_logo, 
            model_name=self.model, 
            parent_width=w
        )
        self.result_display.insertWidget(self.result_display.count()-1, ai_bubble)

        QTimer.singleShot(0, self.update_all_bubbles_width)
        
        # 5. Check if skip_format_instruction flag is set (for PDF report generation)
        skip_format = getattr(self.chat_window, '_skip_format_instruction', False)
        
        # 6. Send to Worker with skip_format_instruction parameter
        # Worker reads saved records via history_to_messages
        self.worker.add_task(self.history_to_messages(skip_format_instruction=skip_format), ai_bubble)
        
        # 7. Reset the flag after use
        if hasattr(self.chat_window, '_skip_format_instruction'):
            self.chat_window._skip_format_instruction = False
        
        self.scroll_to_bottom()


    # ========================================================================
    # Scroll Chat View to Bottom
    # ========================================================================
    def scroll_to_bottom(self):
        QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))


    # ========================================================================
    # Handle AI Reply
    # ========================================================================
    def on_ai_reply(self, reply: dict, ai_bubble: BubbleMessage):
        """
        Handle AI reply.
        Fixed empty content issue: added raw_text processing logic.
        """
        # 1. Persist and save record
        raw_text = reply.get("raw_text", "")
        
        # [Key Fix] Remove <think> tags before saving to avoid persisting thinking content
        clean_text = re.sub(r'<think>.*?</think>\s*', '', raw_text, flags=re.DOTALL)
        
        self.append_record("assistant", 
                            {"text": clean_text, "images": None}, 
                            model_name=self.model)

        # 2. Defensive programming: create new bubble if missing
        if ai_bubble is None:
            w = max(100, self.scroll_area.viewport().width() - 40)
            ai_bubble = BubbleMessage(
                text="Thinking...", is_user=False,
                ai_logo=self.model_logo, 
                model_name=self.model,
                parent_width=w
            )
            self.result_display.insertWidget(self.result_display.count()-1, ai_bubble)

        # 3. Connect scroll signal
        try:
            ai_bubble.content_updated.connect(
                lambda: QTimer.singleShot(0, self.scroll_to_bottom),
                Qt.SingleShotConnection
            )
        except Exception:
            pass

        # 4. [Core Fix] Set content display
        html_content = reply.get("html")
        
        if html_content:
            # If Worker already rendered HTML (old mode), set directly
            ai_bubble.set_pre_rendered_content(html_content)
        else:
            # If Worker only passed plain text (new mode), call bubble's own renderer
            # set_content will auto-handle Markdown and LaTeX
            ai_bubble.set_content(clean_text)

        # 5. Scroll to bottom
        QTimer.singleShot(0, self.scroll_to_bottom)


    # ========================================================================
    # Append Message Record to Chat History
    # ========================================================================
    def append_record(self, role, content, model_name=None):
        """
        Save message to JSON. Added model_name parameter to record model name.
        """
        if self.current_chat_file: 
            # Build message dictionary
            msg_data = {"role": role, **content}
            
            # If model name provided (usually AI reply), save it
            if model_name:
                msg_data["model"] = model_name
                
            self.chat_history.append(msg_data)
            
            try:
                Path(self.current_chat_file).write_text(
                    json.dumps(self.chat_history, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            except Exception as e:
                print(f"[ERR] Failed to write chat history: {e}")

    # ... helper for images (unchanged) ...
    # ========================================================================
    # Get Image Data URI
    # ========================================================================
    def get_image_data_uri(self, image_source):
        """
        Helper function: Convert image source (path or Base64) to Data URI format required by API.
        Format example: data:image/png;base64,iVBORw0K...
        """
        # 1. If already Data URI (data:image/...), return directly
        if image_source.startswith("data:"):
            return image_source

        # 2. If local file path, read file and convert
        path = Path(image_source)
        if path.is_file():
            try:
                mime_type, _ = mimetypes.guess_type(path)
                if not mime_type: mime_type = "image/png"  # Default fallback
                
                with open(path, "rb") as image_file:
                    base64_encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    return f"data:{mime_type};base64,{base64_encoded}"
            except Exception as e:
                print(f"[ERR] Failed to load image file: {e}")
                return None

        # 3. If pure Base64 string (no prefix), assume PNG and add prefix
        # Simple check: Base64 is usually long and has no path separators
        if len(image_source) > 200 and "/" not in image_source[:50]: 
             return f"data:image/png;base64,{image_source}"

        # 4. Other cases (possibly invalid path), return None
        return None

    # ========================================================================
    # Convert Chat History to API Message Format
    # ========================================================================
    def history_to_messages(self, skip_format_instruction=False):
        """
        Convert chat history to OpenRouter/OpenAI API standard format.
        Contains robust image processing logic to prevent 400 errors.
        
        :param skip_format_instruction: If True, skip LaTeX rendering rules (for PDF report generation)
        """

        # 1. Get user's System Prompt from settings (persona)
        # Default might be "You are a helpful assistant."
        user_persona = self.setting_window.get_system_prompt()

        # 2. Define [Mandatory format instructions]
        # This tells AI: must use LaTeX, must wrap with $ and $$
        # SKIP this when generating PDF reports (skip_format_instruction=True)
        if skip_format_instruction:
            # For PDF reports: no special formatting instructions
            final_system_message = user_persona
        else:
            # For Qt display: add LaTeX rendering rules
            latex_instruction = (
                "\n\n[IMPORTANT: LATEX RENDERING RULES]\n"
                "1. All math MUST be valid LaTeX. No Unicode symbols (e.g., use $x^2$ NOT x²).\n"
                "2. Inline math delimiter: single $ only. Forbidden: \\( ... \\).\n"
                "3. Block math delimiter: double $$ only. Forbidden: \\[ ... \\].\n"
                "4. Do NOT wrap equations in markdown code blocks (```).\n"
                "5. Do NOT escape the dollar signs.\n"
                "6. Ensure block math ($$) starts and ends on its own line."
            )
            final_system_message = user_persona + latex_instruction

        # 4. Build message list
        msgs = [
            {"role": "system", "content": final_system_message}
        ]
        
        for x in self.chat_history:
            role = x["role"]
            text = x.get("text", "")
            images = x.get("images", [])

            # --- Case A: Pure text ---
            if not images:
                msgs.append({"role": role, "content": text})
            
            # --- Case B: Contains images (Vision Request) ---
            else:
                content_list = []
                
                # 1. Add text (if not empty)
                if text and str(text).strip():
                    content_list.append({"type": "text", "text": str(text)})
                
                # 2. Process and add images
                for img in images:
                    # Use helper function to get correct format
                    data_uri = self.get_image_data_uri(img)
                    
                    if data_uri:
                        content_list.append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_uri
                            }
                        })
                    else:
                        print(f"[WARN] Skipping invalid image source in history.")

                # Only add message when content_list not empty, prevent errors from sending empty content
                if content_list:
                    msgs.append({"role": role, "content": content_list})
                
        return msgs
    



    # ========================================================================
    # Clear Chat History
    # ========================================================================
    def clear_history(self):
        if self.active_chat_path: self.active_chat_path.unlink(missing_ok=True)
        self.active_chat_path = None; self.chat_history = []

    # ========================================================================
    # Cleanup Resources
    # ========================================================================
    def cleanup(self): 
        if self.worker: self.worker.stop()

    # ========================================================================
    # Update All Bubble Widths on Window Resize
    # ========================================================================
    def update_all_bubbles_width(self):
        try:
            w = max(100, self.scroll_area.viewport().width() - 40)
            for i in range(self.result_display.count()):
                item = self.result_display.itemAt(i)
                if item is None: continue
                wid = item.widget()
                if isinstance(wid, BubbleMessage):
                    wid.update_max_width(w)
            QTimer.singleShot(0, self.scroll_to_bottom)
        except Exception:
            pass

    # ========================================================================
    # Handle New Chat Creation
    # ========================================================================
    def handle_new_chat(self):

        # Fix: use current_chat_file consistently
        self.chat_window.clear_all_messages()
        self.current_chat_file = None 

        now = datetime.now()
        chat_title = f"Chat {now.strftime('%Y-%m-%d %H-%M-%S')}"
        folder_name = self.side_panel.active_folder or "Default folder"

        folder_path = self.side_panel.storage_root / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        chat_file = folder_path / f"{chat_title}.json"
        chat_data = {"title": chat_title, "folder": folder_name, "messages": []}

        try:
            with open(chat_file, "w", encoding="utf-8") as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
            self.current_chat_file = str(chat_file) # Fix: Update the main tracker
            print(f"[INFO] New chat file created at: {chat_file}")
        except Exception as e:
            print(f"Failed to create new chat file: {e}")

        self.side_panel.save_chat_to_folder(folder_name, title=chat_title, save_json=False)
        self.side_panel.refresh_chat_list()

        # Adjust the chat input container position
        self.chat_window.messages_count = 0     # Update the message count in chat_window
        self.chat_window.adjust_input_height()
        self.chat_window.update_input_container_position()

    # ========================================================================
    # Handle Opening Existing Chat File
    # ========================================================================
    def handle_open_chat_file(self, folder, chat_title):
        """
        Open a chat file and render its messages into the chat window.
        Enhanced: uses resolve_chat_file to handle mismatches between UI title and actual filename.
        """
        # Try to resolve the file robustly
        chat_file = self.resolve_chat_file(folder, chat_title)

        if not chat_file.exists():
            print(f"[WARN] Chat file not found (after fallback search): {chat_file}")
            return

        self.current_chat_file = str(chat_file)
        self.chat_history = [] 
        self.chat_window.clear_all_messages()

        try:
            with open(chat_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        if isinstance(data, dict):
            messages = data.get("messages", [])
        elif isinstance(data, list):
            messages = data
        else:
            return

        w = max(100, self.scroll_area.viewport().width() - 40)
        
        for msg in messages:
            # 1. Parse basic fields
            role = msg.get("role", "user")
            text = msg.get("text", "")
            images = msg.get("images", [])
            
            # [Key Fix] Remove <think> tags when loading history
            if role == "assistant":
                original_text = text
                text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)
                if '<think>' in original_text:
                    print(f"[DEBUG handle_open_chat_file] Removed <think> tags, original length: {len(original_text)}, cleaned length: {len(text)}")
            
            # 2. [Key Modification] Try to read 'model' field
            # If old history record lacks this field, default to current selected model or "AI"
            saved_model_name = msg.get("model", self.model)

            self.chat_history.append({"role": role, "text": text, "images": images, "model": saved_model_name})

            # 3. Create bubble
            bubble = BubbleMessage(
                text=text,
                images=images,
                is_user=(role=="user"),
                parent_width=w,
                # If assistant, pass the read saved_model_name
                model_name=saved_model_name if role=="assistant" else "User", 
                # Note: ai_logo might still use current default logo, or you can dynamically search logo by name
                ai_logo=self.model_logo if role=="assistant" else None
            )
            self.result_display.insertWidget(self.result_display.count()-1, bubble)


        QTimer.singleShot(0, self.scroll_to_bottom)

        print(f"[INFO] Loaded chat '{chat_title}' from folder '{folder}'")

        if hasattr(self.chat_window, 'messages_count'):
            self.chat_window.messages_count = len(messages)
        
        if hasattr(self.chat_window, 'chat_line_edit'):
            self.chat_window.chat_line_edit.clear()
            self.chat_window.chat_line_edit.setFocus()
            self.chat_window.pending_images.clear()
            self.chat_window.update_input_container_position()
            
        QTimer.singleShot(20, self.update_all_bubbles_width)
