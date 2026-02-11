#--------------------------------------------------------------
# Operations for Result Pages
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-30
#--------------------------------------------------------------

from PySide6.QtCore import QObject

from SaMPH_GUI.Page_Result import ResultPage

#==============================================================
class ResultPage_Operations(QObject):
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Dictionary to store result pages {result_type: ResultPage}
        self.result_pages = {}
        
        # Dictionary to store calculation data {result_type: {fn: value}}
        # This ensures we can repopulate pages if they are closed and reopened
        self.results_data = {}
        
        # Result type configuration
        self.result_config = {
            "Rw": "Bare hull resistance - Rw (N)",
            "Rs": "Spray resistance - Rs (N)",
            "Ra": "Air resistance - Ra (N)",
            "Rt": "Total resistance - Rt (N)",
            "Trim": "Trim angle (degree)",
            "Sinkage": "Sinkage (m)"
        }
    
    def set_mode(self, mode):
        """
        Set the chart style mode for all pages.
        
        Args:
            mode: "scatter" or "continuous"
        """
        self.current_mode = mode
        # Clean up deleted pages first
        self._cleanup_deleted_pages()
        
        for page in self.result_pages.values():
            page.set_chart_style(mode)

    def _cleanup_deleted_pages(self):
        """Remove references to deleted C++ objects"""
        keys_to_remove = []
        for key, page in self.result_pages.items():
            try:
                # Try to access objectName to check if C++ object still exists
                _ = page.objectName()
            except RuntimeError:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.result_pages[key]

    def create_or_get_result_page(self, result_type):
        """
        Create a result page if it doesn't exist, or return existing one.
        
        Args:
            result_type: Type identifier (e.g., "Rt", "Trim")
            
        Returns:
            ResultPage instance
        """
        # First, check if we have a reference but the object is deleted
        if result_type in self.result_pages:
            try:
                _ = self.result_pages[result_type].objectName()
            except RuntimeError:
                del self.result_pages[result_type]
        
        if result_type not in self.result_pages:
            # Create new page
            result_label = self.result_config.get(result_type, result_type)
            page = ResultPage(result_type, result_label)
            
            # Apply current mode if set
            if hasattr(self, 'current_mode'):
                page.set_chart_style(self.current_mode)
            
            # Apply hull params if set
            if hasattr(self, 'hull_params'):
                page.set_hull_params(self.hull_params)
            
            # Populate with existing data if available
            if result_type in self.results_data:
                for fn, value in self.results_data[result_type].items():
                    page.update_result(fn, value)
            
            self.result_pages[result_type] = page
        
        return self.result_pages[result_type]
    
    def handle_result_update(self, result_type, fn, value):
        """
        Update a specific result page with new data.
        
        Args:
            result_type: Type identifier (e.g., "Rt")
            fn: Froude number
            value: Result value
        """
        # 1. Store data persistently
        if result_type not in self.results_data:
            self.results_data[result_type] = {}
        self.results_data[result_type][fn] = value
        
        # 2. Update page if it exists and is valid
        if result_type in self.result_pages:
            try:
                self.result_pages[result_type].update_result(fn, value)
            except RuntimeError:
                # Page was deleted, remove reference
                del self.result_pages[result_type]
    
    def clear_all_results(self):
        """Clear all result pages and stored data"""
        # Clear stored data
        self.results_data.clear()
        
        # Clear active pages
        self._cleanup_deleted_pages()
        for page in self.result_pages.values():
            page.clear_results()
    
    def open_default_pages(self):
        """
        Open default result pages (Rt, Trim, Sinkage) and add them to tabs.
        """
        default_types = ["Rt", "Trim", "Sinkage"]
        
        last_added_page = None
        for result_type in default_types:
            
            page = self.create_or_get_result_page(result_type)
            
            # Add to tab widget if not already there
            # Note: main_window.tab_widget is Central_Tab_Widget, need .tab_widget for actual QTabWidget
            tab_widget = self.main_window.tab_widget.tab_widget
            
            # Check if page already exists in tabs
            page_exists = False
            for i in range(tab_widget.count()):
                if tab_widget.widget(i) == page:
                    page_exists = True
                    break
            
            if not page_exists:
                result_label = self.result_config[result_type]
                tab_widget.addTab(page, result_label)
                last_added_page = page
        
        # Activate the last added page (Sinkage)
        if last_added_page:
            tab_widget.setCurrentWidget(last_added_page)

    def set_hull_params(self, params):
        """
        Set hull parameters for all result pages.
        
        Args:
            params: Dictionary of hull parameters
        """
        self.hull_params = params
        
        # Update existing pages
        self._cleanup_deleted_pages()
        for page in self.result_pages.values():
            if hasattr(page, 'set_hull_params'):
                page.set_hull_params(params)
