#--------------------------------------------------------------
# This file contains operations for the main window
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-27  
#--------------------------------------------------------------

import webbrowser

from pathlib import Path
from urllib.parse import quote_plus

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication, QMessageBox



# Import here to avoid circular dependency
from SaMPH_GUI.Page_Input import InputPage
from SaMPH_GUI.Item_Central_TabWidget import SampleResultPage
from SaMPH_GUI.Page_Input import InputPage
from SaMPH_Utils.Utils import utils                            



#==============================================================
class MainWindow_Operations:
    """
    This class contains all the operation methods for the main window.
    It handles panel toggling, drag resizing, navigation, and other UI interactions.
    """
    
    def __init__(self, main_window):

        """Initialize with reference to the main window"""
        
        self.main_window = main_window
        
        # Connect Home page state change signal to update all buttons
        self.main_window.tab_widget.home_page_state_changed.connect(self.update_all_home_buttons)
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Drag resize handlers for left panel
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def start_left_drag(self, event):
        """Start dragging left panel separator"""
        self.main_window.left_drag_start_x = event.globalPosition().x()
        self.main_window.left_drag_start_width = self.main_window.left_panel.width()
        event.accept()
    
    def do_left_drag(self, event):
        """Handle dragging left panel separator"""
        dx = event.globalPosition().x() - self.main_window.left_drag_start_x
        new_width = self.main_window.left_drag_start_width + dx
        
        # Allow dragging to any width (including below threshold)
        # Clamp to reasonable bounds but allow going very small
        new_width = max(0, min(600, new_width))
        
        # Update panel width to follow mouse smoothly
        self.main_window.left_panel.setMaximumWidth(new_width)
        self.main_window.left_panel.setMinimumWidth(new_width)
        
        event.accept()
    
    def end_left_drag(self, event):
        """Finish dragging left panel separator"""
        final_width = self.main_window.left_panel.width()
        
        # Auto-hide if dragged below threshold
        if final_width < 50:
            # Collapse to 0
            self.main_window.left_panel.setMaximumWidth(0)
            self.main_window.left_panel.setMinimumWidth(0)
            self.main_window.left_panel.is_visible = False
            self.main_window.left_drag_handle.hide()
        else:
            # Keep the current width (don't force to minimum)
            # Just save it for restoration when reopening
            self.main_window.left_panel.full_width = final_width
            self.main_window.left_panel.is_visible = True
            self.main_window.left_panel.setVisible(True)
            self.main_window.left_drag_handle.show()
        
        # Emit visibility signal after drag completes
        self.main_window.left_panel_visible_changed.emit(self.main_window.left_panel.is_visible)
        event.accept()
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Drag resize handlers for right panel
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def start_right_drag(self, event):
        """Start dragging right panel separator"""
        self.main_window.right_drag_start_x = event.globalPosition().x()
        self.main_window.right_drag_start_width = self.main_window.right_panel.width()
        event.accept()
    
    def do_right_drag(self, event):
        """Handle dragging right panel separator"""
        dx = self.main_window.right_drag_start_x - event.globalPosition().x()
        new_width = self.main_window.right_drag_start_width + dx
        
        # Allow dragging to any width (including below threshold)
        # Clamp to reasonable bounds but allow going very small
        new_width = max(0, min(800, new_width))
        
        # Update panel width to follow mouse smoothly
        self.main_window.right_panel.setMaximumWidth(new_width)
        self.main_window.right_panel.setMinimumWidth(new_width)
        
        # *** Debounce mechanism during dragging ***
        # Use a timer to delay updates, avoiding stutter caused by frequent calls
        # Reference: Implementation in AIchat_Combo_V3
        if hasattr(self.main_window, 'drag_debounce_timer'):
            self.main_window.drag_debounce_timer.stop()
            self.main_window.drag_debounce_timer.start()
        
        event.accept()
    
    def end_right_drag(self, event):
        """Finish dragging right panel separator"""
        final_width = self.main_window.right_panel.width()
        
        # Auto-hide if dragged below threshold
        if final_width < 50:
            # Collapse to 0
            self.main_window.right_panel.setMaximumWidth(0)
            self.main_window.right_panel.setMinimumWidth(0)
            self.main_window.right_panel.is_visible = False
            self.main_window.right_drag_handle.hide()
        else:
            # Keep the current width (don't force to minimum)
            # Just save it for restoration when reopening
            self.main_window.right_panel.full_width = final_width
            self.main_window.right_panel.is_visible = True
            self.main_window.right_panel.setVisible(True)
            self.main_window.right_drag_handle.show()
        
        # Stop the debounce timer and execute the final update immediately
        if hasattr(self.main_window, 'drag_debounce_timer'):
            self.main_window.drag_debounce_timer.stop()
        
        # *** Update immediately after drag ends ***
        if hasattr(self.main_window.right_panel, 'update_input_container_position'):
            self.main_window.right_panel.update_input_container_position()

        # Force immediate update of bubble widths after drag completes
        self.update_bubbles_after_drag()
        
        # Emit visibility signal after drag completes
        self.main_window.right_panel_visible_changed.emit(self.main_window.right_panel.is_visible)

        event.accept()
    

    # ---------------------------------------------------------------------------------
    # Helper function to update bubble widths (called by debounce timer or mouse release)
    def update_bubbles_after_drag(self):

        """Update bubble widths and input container position after sidebar resize."""

        # Fix: operation_chat is an attribute of main_window, not self
        if hasattr(self.main_window, "operation_chat"):
            self.main_window.operation_chat.update_all_bubbles_width()
    # ---------------------------------------------------------------------------------


    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Public methods to toggle panels (can be called from toolbar)
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def toggle_home_panel(self, checked=None):

        """Show or hide the central tab widget (home view)."""
        desired = (not self.main_window.home_panel_visible) if checked is None else bool(checked)
        if desired == self.main_window.home_panel_visible:
            return

        self.main_window.home_panel_visible = desired
        if hasattr(self.main_window, "tab_widget"):
            self.main_window.tab_widget.setVisible(desired)
        self.main_window.home_panel_visible_changed.emit(desired)
        
    
    def toggle_left_panel(self, checked=None):
        """Toggle left navigation panel visibility"""
        desired = (not self.main_window.left_panel.is_visible) if checked is None else bool(checked)
        if desired == self.main_window.left_panel.is_visible:
            return

        self.main_window.left_panel.toggle_panel()
        if desired:
            self.main_window.left_drag_handle.show()
        else:
            self.main_window.left_drag_handle.hide()
        self.main_window.left_panel_visible_changed.emit(desired)
    
    def toggle_right_panel(self, checked=None):
        """Toggle right AI chat panel visibility"""
        desired = (not self.main_window.right_panel.is_visible) if checked is None else bool(checked)
        if desired == self.main_window.right_panel.is_visible:
            return

        self.main_window.right_panel.toggle_panel()
        if desired:
            self.main_window.right_drag_handle.show()
        else:
            self.main_window.right_drag_handle.hide()
        self.main_window.right_panel_visible_changed.emit(desired)
    
    def toggle_log_window(self, checked=None):
        """Toggle log window visibility"""
        desired = (not self.main_window.log_visible) if checked is None else bool(checked)
        
        # If we are trying to show it, but it's already "visible" (boolean true) 
        # yet the size is 0 (hidden by splitter), we still need to proceed to restore size.
        # So we relax the check: if desired is True, we always try to show/resize.
        if not desired and desired == self.main_window.log_visible:
            return

        if desired:
            self.main_window.log_window.show()
            
            # Check if the log window has 0 height (collapsed via splitter)
            # The log window is index 1 in the central_splitter
            sizes = self.main_window.central_splitter.sizes()
            if len(sizes) > 1 and sizes[1] == 0:
                # Restore to a default height (e.g., 150 or 20% of total)
                total_height = sum(sizes)
                new_log_height = 250
                new_tab_height = max(0, total_height - new_log_height)
                self.main_window.central_splitter.setSizes([new_tab_height, new_log_height])
            
            self.log_message("Log window shown")
        else:
            self.main_window.log_window.hide()
            # When hiding via button, we might want to set size to 0 explicitly if using splitter, 
            # but hide() usually does the job for the widget visibility. 
            # However, for QSplitter, sometimes setting size to 0 is better for "collapsing".
            # Let's stick to hide() first, as it sets isVisible() to false.
            self.log_message("Log window hidden")

        self.main_window.log_visible = desired
        self.main_window.log_window_visible_changed.emit(desired)
            
    def on_log_window_closed(self):
        """Handle log window close signal"""
        self.main_window.log_visible = False
        self.log_message("Log window closed")
        self.main_window.log_window_visible_changed.emit(False)

    def handle_splitter_moved(self, pos, index):
        """Handle splitter movement to detect if log window is collapsed"""
        sizes = self.main_window.central_splitter.sizes()
        # Assuming log window is the second widget (index 1)
        if len(sizes) > 1:
            log_height = sizes[1]
            if log_height == 0 and self.main_window.log_visible:
                # Log window collapsed by drag
                self.main_window.log_visible = False
                self.main_window.log_window_visible_changed.emit(False)
                self.log_message("Log window collapsed by drag")
            elif log_height > 0 and not self.main_window.log_visible:
                # Log window expanded by drag
                self.main_window.log_visible = True
                self.main_window.log_window_visible_changed.emit(True)
                self.log_message("Log window expanded by drag")

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Logging helper
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def log_message(self, message):
        """Log a message to the log window"""
        if hasattr(self.main_window, 'log_window') and self.main_window.log_window:
            self.main_window.log_window.log_message(message)
    



    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Navigation handler
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Unified Home toggle handler
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def toggle_home_page(self, show=True):
        """
        Unified handler for Home page toggle from toolbar or sidebar.
        Args:
            show: True=show/create Home, False=hide Home
        """
        # Check if Home page exists
        has_home = self.main_window.tab_widget.home_widget is not None

        if show and not has_home:
            # Create new Home page
            home_page = self.main_window.tab_widget.add_welcome_tab()
            
            # Connect HomePage signals
            if home_page is not None:
                home_page.log_signal.connect(self.log_message)
                home_page.add_input_window_signal.connect(self.on_home_add_input_requested)
            
            # Switch to Home tab
            self.main_window.tab_widget.tab_widget.setCurrentIndex(0)
            self.log_message("Home page created and shown")
            
        elif show and has_home:
            
            # Home exists, just switch to it
            for i in range(self.main_window.tab_widget.tab_widget.count()):
                if self.main_window.tab_widget.tab_widget.widget(i) == self.main_window.tab_widget.home_widget:
                    self.main_window.tab_widget.tab_widget.setCurrentIndex(i)
                    self.log_message("Switched to existing Home page")
                    break
                    
        elif not show and has_home:

            # Find and close Home tab
            for i in range(self.main_window.tab_widget.tab_widget.count()):
                if self.main_window.tab_widget.tab_widget.widget(i) == self.main_window.tab_widget.home_widget:
                    self.main_window.tab_widget.close_tab(i)
                    self.log_message("Home page closed")
                    break
    
    def update_all_home_buttons(self, is_visible):
        """
        Observer method: Update all Home button states when Home page visibility changes.
        This is called automatically when home_page_state_changed signal is emitted.
        """
        # Update toolbar Home button
        if hasattr(self.main_window, 'tool_bar'):
            self.main_window.tool_bar.update_home_toggle_state(is_visible)
        
        # Update sidebar Home button
        if hasattr(self.main_window, 'left_panel'):
            self.main_window.left_panel.update_home_icon(is_visible)
        
        self.log_message(f"All Home buttons updated: {'visible' if is_visible else 'hidden'}")
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Navigation handler (for Input and Results only, Home uses toggle_home_page)
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def handle_navigation(self, nav_item):

        """Handle navigation requests from left panel (Input/Results)"""
        self.log_message(f"Navigation requested: {nav_item}")
        

        # Handle navigation based on item clicked  
        if nav_item == "input":
            # Check if Input tab already exists
            input_tab_index = None
            for i in range(self.main_window.tab_widget.tab_widget.count()):
                if self.main_window.tab_widget.tab_widget.tabText(i) == "Input":
                    input_tab_index = i
                    break
            
            if input_tab_index is not None:
                # Switch to existing Input tab
                self.main_window.tab_widget.tab_widget.setCurrentIndex(input_tab_index)
                self.log_message("Switched to existing Input tab")
            else:
                # Create new Input tab
                input_page = InputPage()

                # Set reference in main window for operations access
                # Here we use self.main_window.page_input to store the input page reference
                self.main_window.page_input = input_page
                
                input_page.parameters_changed.connect(
                    lambda params: self.log_message(f"Parameters updated: {params}")
                )
                # Connect material change signal
                if hasattr(self.main_window, 'operations_input_page'):
                    input_page.material_combo_requested.connect(
                        self.main_window.operations_input_page.handle_material_change
                    )
                    
                self.main_window.tab_widget.add_tab(input_page, "Input")
                self.log_message("Created new Input tab")
                
        elif nav_item == "results":

            # Check if Results tab already exists
            results_tab_index = None

            for i in range(self.main_window.tab_widget.tab_widget.count()):
                if self.main_window.tab_widget.tab_widget.tabText(i) == "Results":
                    results_tab_index = i
                    break
            
            if results_tab_index is not None:

                # Switch to existing Results tab
                self.main_window.tab_widget.tab_widget.setCurrentIndex(results_tab_index)
                self.log_message("Switched to existing Results tab")

            else:

                # Create a sample Results tab for debug
                results_page = SampleResultPage()
                self.main_window.tab_widget.add_tab(results_page, "Results")
                self.log_message("Created new Results tab")
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Home page signal handler
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def on_home_add_input_requested(self, mode):
        
        """Handle request from Home page to add Input window with specific mode"""

        
        self.log_message(f"Home page requested Input page with mode: {mode}")
        
        # Check if Input tab already exists
        input_tab_index = None
        for i in range(self.main_window.tab_widget.tab_widget.count()):
            if self.main_window.tab_widget.tab_widget.tabText(i) == "Input":
                input_tab_index = i
                break
        
        if input_tab_index is not None:
            # Switch to existing Input tab
            self.main_window.tab_widget.tab_widget.setCurrentIndex(input_tab_index)
            self.log_message(f"Switched to existing Input tab (mode: {mode})")
        else:
            # Create new Input tab
            input_page = InputPage()
            # Set reference in main window for operations access
            self.main_window.page_input = input_page
            
            input_page.parameters_changed.connect(
                lambda params: self.log_message(f"Parameters updated: {params}")
            )
            # Connect material change signal
            if hasattr(self.main_window, 'operations_input_page'):
                input_page.material_combo_requested.connect(
                    self.main_window.operations_input_page.handle_material_change
                )
                
            # Add the input page to the tab widget (Input)
            self.main_window.tab_widget.add_tab(input_page, "Input")
            self.log_message(f"Created new Input tab (mode: {mode})")

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Tab state handlers
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def on_tab_closed_check_home(self, index):
        """Check if Home tab was closed and log"""
        # Icon update is now handled directly in close_tab
        if self.main_window.tab_widget.home_widget is None:
            self.log_message("Home tab was closed")
    
    def on_tabs_opened(self):
        """Handle when first tab is opened (from background)"""
        # Check if it's the Home tab
        if self.main_window.tab_widget.home_widget is not None:
            self.main_window.left_panel.update_home_icon(True)
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # AI message handler
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def handle_ai_message(self, message):
        """Handle AI chat messages from right panel"""
        self.log_message(f"AI message sent: {message}")
        
        # For now, just print the message
        # You can add API calls, model inference, etc.
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Toolbar search handler
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def handle_toolbar_search(self, query: str):

        """Handle toolbar search requests by opening the browser with the query."""

        #---------------------------------------------------------------------------------
        # Get the QSettings file path
        usr_folder = utils.get_global_usr_dir()    
        settings_file_path = usr_folder / "Settings/settings.ini"

        #---------------------------------------------------------------------------------
        # Check the settings
        settings   = QSettings(str(settings_file_path), QSettings.Format.IniFormat)
        use_baidu  = settings.value("Search/Baidu", True, type=bool)
        use_google = settings.value("Search/Google", False, type=bool)

        #---------------------------------------------------------------------------------
        # Connect signal from the search button based on search type
        if use_baidu and not use_google:
            self.perform_baidu_search()
        elif use_google and not use_baidu:
            self.perform_google_search()
        else:
            self.perform_baidu_search()  # default
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # The function to perform Baidu search
    def perform_baidu_search(self):
            
        query = self.main_window.tool_bar.search_input.text().strip()
        if query:
            encoded_query = quote_plus(query)
            url = f"https://www.baidu.com/s?wd={encoded_query}"
        else:
            url = "https://www.baidu.com"

        webbrowser.open(url)

        # self.main_window.close()  # Close dialog after search
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # The function to perform google search
    def perform_google_search(self):
        query = self.main_window.tool_bar.search_input.text().strip()
        if query:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        else:
            url = "https://www.google.com"

        webbrowser.open(url)


        # Close the window after search
        # self.main_window.close()
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Update visibility handlers (slots for signals)
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def update_home_panel_visibility(self, visible):
        """Update UI when home panel visibility changes"""
        self.log_message(f"Home panel visibility changed to: {visible}")
        pass

    def update_left_panel_visibility(self, visible):
        """Update UI when left panel visibility changes"""
        self.log_message(f"Left panel visibility changed to: {visible}")
        pass

    def update_right_panel_visibility(self, visible):
        """Update UI when right panel visibility changes"""
        self.log_message(f"Right panel visibility changed to: {visible}")
        pass

    def update_log_window_visibility(self, visible):
        """Update UI when log window visibility changes"""
        self.log_message(f"Log window visibility changed to: {visible}")
        pass

    #==============================================================
    # Help Menu Dialogs
    #==============================================================
    
    def show_about_dialog(self):
        """Show the About dialog with software information (supports i18n)."""
        # Get language manager
        lang_manager = self.main_window.language_manager
        current_lang = lang_manager.get_current_language()
        
        # Prepare multilingual content
        if current_lang == "Chinese":
            about_text = """
            <div style="line-height: 1.5; margin: 0; font-size: 13px;">
            <h2 style="margin: 8px 0 12px 0; color: #2c3e50;">SaMPH - 滑行艇运动姿态分析软件</h2>
            <p style="margin: 5px 0;"><b>版本：</b>1.0.0</p>
            <p style="margin: 5px 0;"><b>开发团队：</b>AMHL Team</p>
            <p style="margin: 5px 0;"><b>联系方式：</b>sjin@mun.ca</p>
            <p style="margin: 12px 0 10px 0; color: #34495e;">基于 Savitsky 方法的滑行艇运动性能分析工具。</p>
            <p style="margin: 10px 0 5px 0;"><b>主要功能：</b></p>
            <ul style="margin: 5px 0 5px 20px; padding: 0;">
                <li style="margin: 3px 0;">滑行艇运动姿态分析</li>
                <li style="margin: 3px 0;">离散和连续速度范围计算</li>
                <li style="margin: 3px 0;">详细的流体动力学性能评估</li>
                <li style="margin: 3px 0;">可视化结果展示和数据导出</li>
                <li style="margin: 3px 0;">人工智能辅助</li>
            </ul>
            <p style="margin: 12px 0 5px 0;"><b>参考文献：</b></p>
            <p style="margin: 5px 0; font-size: 12px; color: #555; line-height: 1.6;">
            Jin, S., Peng, H.H., Qiu, W., Hunter, R. and Thompson, S., 2023. 
            Numerical simulation of planing hull motions in calm water and waves with overset grid. 
            <i>Ocean Engineering</i>, 287, p.115858.
            </p>
            <p style="margin: 15px 0 8px 0; font-size: 11px; color: #7f8c8d;">© 2025 HydroX Team. 保留所有权利。</p>
            </div>
            """
            title = "关于 SaMPH"
        else:
            about_text = """
            <div style="line-height: 1.5; margin: 0; font-size: 13px;">
            <h2 style="margin: 8px 0 12px 0; color: #2c3e50;">SaMPH - Savitsky-based Motion of Planing Hulls</h2>
            <p style="margin: 5px 0;"><b>Version:</b> 1.0.0</p>
            <p style="margin: 5px 0;"><b>Developer:</b> AMHL Team</p>
            <p style="margin: 5px 0;"><b>Contact:</b> sjin@mun.ca</p>
            <p style="margin: 12px 0 10px 0; color: #34495e;">A modern tool for analyzing planing hull motion and performance based on the Savitsky method.</p>
            <p style="margin: 10px 0 5px 0;"><b>Features:</b></p>
            <ul style="margin: 5px 0 5px 20px; padding: 0;">
                <li style="margin: 3px 0;">Planing hull motion analysis</li>
                <li style="margin: 3px 0;">Discrete and continuous speed range calculations</li>
                <li style="margin: 3px 0;">Detailed hydrodynamic performance evaluation</li>
                <li style="margin: 3px 0;">Result visualization and data export</li>
                <li style="margin: 3px 0;">AI-powered assistance</li>
            </ul>
            <p style="margin: 12px 0 5px 0;"><b>Reference:</b></p>
            <p style="margin: 5px 0; font-size: 12px; color: #555; line-height: 1.6;">
            Jin, S., Peng, H.H., Qiu, W., Hunter, R. and Thompson, S., 2023. 
            Numerical simulation of planing hull motions in calm water and waves with overset grid. 
            <i>Ocean Engineering</i>, 287, p.115858.
            </p>
            <p style="margin: 15px 0 8px 0; font-size: 11px; color: #7f8c8d;">© 2025 HydroX Team. All rights reserved.</p>
            </div>
            """
            title = "About SaMPH"
        
        # Get current application font family
        app_font = QApplication.instance().font()
        font_family = app_font.family()
        
        # Create custom dialog
        dialog = QMessageBox(self.main_window)
        dialog.setWindowTitle(title)
        
        # Add font-family to the div container and h2 title to inherit app font
        about_text = about_text.replace(
            '<div style="line-height: 1.5; margin: 0; font-size: 13px;">',
            f'<div style="line-height: 1.5; margin: 0; font-size: 13px; font-family: {font_family};">'
        )
        about_text = about_text.replace(
            '<h2 style="margin: 8px 0 12px 0; color: #2c3e50;">',
            f'<h2 style="margin: 8px 0 12px 0; color: #2c3e50; font-family: {font_family};">'
        )
        
        dialog.setText(about_text)
        dialog.setTextFormat(Qt.RichText)
        dialog.setIcon(QMessageBox.NoIcon)
        dialog.setStandardButtons(QMessageBox.Close)
        
        # Set button text based on language
        close_btn = dialog.button(QMessageBox.Close)
        if current_lang == "Chinese":
            close_btn.setText("关闭")
        else:
            close_btn.setText("Close")
        
        dialog.exec()







    def show_license_dialog(self):
        """Show the License dialog with software license information (supports i18n)."""
        # Get language manager
        lang_manager = self.main_window.language_manager
        current_lang = lang_manager.get_current_language()
        
        # Prepare multilingual content
        if current_lang == "Chinese":
            license_text = """
            <div style="line-height: 1.5; margin: 0; font-size: 13px;">
            <h3 style="margin: 8px 0 12px 0; color: #2c3e50;">软件许可协议</h3>
            <p style="margin: 6px 0;"><b>SaMPH - 滑行艇运动姿态分析软件</b></p>
            <p style="margin: 5px 0;">版权所有 © 2025 AMHL Team</p>
            <p style="margin: 10px 0;">本软件仅供研究和教育目的使用。</p>
            <p style="margin: 10px 0 5px 0;"><b>MIT 许可证</b></p>
            <p style="margin: 5px 0; font-size: 12px; color: #555;">
            特此免费授予任何获得本软件副本及相关文档文件（"软件"）的人不受限制地
            处置该软件的权利，包括不受限制地使用、复制、修改、合并、发布、分发、再许可
            和/或出售该软件副本，以及再授权被配发了本软件的人如上的权利，须在以下条件下：
            </p>
            <p style="margin: 8px 0; font-size: 12px; color: #555;">
            上述版权声明和本许可声明应包含在该软件的所有副本或实质成分中。
            </p>
            <p style="margin: 8px 0; font-size: 11px; color: #666;">
            <b>本软件是"按原样"提供的，没有任何形式的明示或暗示的保证，包括但不限于
            对适销性、特定用途的适用性和不侵权的保证。在任何情况下，作者或版权持有人都
            不对任何索赔、损害或其他责任负责，无论这些追责来自合同、侵权或其它行为中，
            还是产生于、源于或有关于本软件以及本软件的使用或其它处置。</b>
            </p>
            </div>
            """
            title = "许可协议"
        else:
            license_text = """
            <div style="line-height: 1.5; margin: 0; font-size: 13px;">
            <h3 style="margin: 8px 0 12px 0; color: #2c3e50;">Software License Agreement</h3>
            <p style="margin: 6px 0;"><b>SaMPH - Savitsky-based Motion of Planing Hulls</b></p>
            <p style="margin: 5px 0;">Copyright © 2025 AMHL Team</p>
            <p style="margin: 10px 0;">This software is provided for research and educational purposes.</p>
            <p style="margin: 10px 0 5px 0;"><b>MIT License</b></p>
            <p style="margin: 5px 0; font-size: 12px; color: #555;">
            Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:
            </p>
            <p style="margin: 8px 0; font-size: 12px; color: #555;">
            The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.
            </p>
            <p style="margin: 8px 0; font-size: 11px; color: #666;">
            <b>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.</b>
            </p>
            </div>
            """
            title = "License Agreement"
        
        # Get current application font family
        app_font = QApplication.instance().font()
        font_family = app_font.family()
        
        # Create custom dialog
        dialog = QMessageBox(self.main_window)
        dialog.setWindowTitle(title)
        
        # Add font-family to the div container and h3 title to inherit app font
        license_text = license_text.replace(
            '<div style="line-height: 1.5; margin: 0; font-size: 13px;">',
            f'<div style="line-height: 1.5; margin: 0; font-size: 13px; font-family: {font_family};">'
        )
        license_text = license_text.replace(
            '<h3 style="margin: 8px 0 12px 0; color: #2c3e50;">',
            f'<h3 style="margin: 8px 0 12px 0; color: #2c3e50; font-family: {font_family};">'
        )
        
        dialog.setText(license_text)
        dialog.setTextFormat(Qt.RichText)
        dialog.setIcon(QMessageBox.NoIcon)
        dialog.setStandardButtons(QMessageBox.Close)
        
        # Set button text based on language
        close_btn = dialog.button(QMessageBox.Close)
        if current_lang == "Chinese":
            close_btn.setText("关闭")
        else:
            close_btn.setText("Close")
        
        dialog.exec()
#==============================================================
