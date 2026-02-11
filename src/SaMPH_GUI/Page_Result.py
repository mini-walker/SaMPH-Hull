#--------------------------------------------------------------
# Result Page - displays calculation results in chart format
# Programmer: Shanqin Jin
# Email: sjin@mun.ca
# Date: 2025-11-30
#--------------------------------------------------------------

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMenu
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QAction, QGuiApplication, QDesktopServices
from PySide6.QtCore import Qt, QMargins, QSettings, QUrl
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QScatterSeries, QValueAxis
from pathlib import Path

import os


from SaMPH_Utils.Utils import utils 

#==============================================================
class CustomAxisFormatter:
    """Custom formatter for axis labels to always show 3 decimal places"""
    @staticmethod
    def format_value(value):
        """
        Format a value with 3 decimal places.
        Automatically switches between decimal and scientific notation.
        """
        # Use absolute value for comparison
        abs_value = abs(value)
        
        # If value is very large or very small, use scientific notation
        if abs_value >= 1e6 or (abs_value < 1e-3 and abs_value != 0):
            # Scientific notation with 3 significant figures
            return f"{value:.3e}"
        else:
            # Fixed decimal notation with 3 decimal places
            return f"{value:.3f}"

#==============================================================
class ChartStyleManager:

    """Manage chart styles from settings"""
    
    # Default global config for chart styles
    global_config = {
        "curve_style": "Solid",
        "curve_color": "#1F4788",
        "curve_width": 2.0,
        "scatter_style": "Circle",
        "axis_style": "Solid",
        "grid_style": "Solid",
        "bg_color": "#FAFAFA",
    }

    @classmethod
    def update_global_config(cls, new_cfg: dict):
        """
        Update global chart style config.
        Called when user changes settings.ini.
        """
        cls.global_config.update(new_cfg)
        print("[INFO] ChartStyleManager: Global configuration updated")

    def __init__(self):
        # Initialize with global config to ensure new pages get latest settings
        self.config = ChartStyleManager.global_config.copy()
        self.settings = self.load_settings()
        
        # If settings file exists, also try to load from there to be safe
        # But global_config should already be updated by Operation_Setting
        if self.settings:
            # We could optionally reload from settings here, but global_config is the source of truth
            # for the current session.
            pass
    
    #--------------------------------------------------------------
    # Load settings from settings.ini
    def load_settings(self):
        """Load settings from settings.ini"""
        try:
            usr_folder = utils.get_global_usr_dir()
            settings_path = usr_folder / "SaMPH" / "Settings" / "settings.ini"
            return QSettings(str(settings_path), QSettings.Format.IniFormat)
        except:
            return None
    
    #--------------------------------------------------------------
    # Get config values
    def get_curve_style(self):
        return self.config.get("curve_style", "Solid")

    def get_curve_color(self):
        return self.config.get("curve_color", "#1F4788")

    def get_curve_width(self):
        return self.config.get("curve_width", 2.0)

    def get_scatter_style(self):
        return self.config.get("scatter_style", "Circle")

    def get_axis_style(self):
        return self.config.get("axis_style", "Solid")

    def get_grid_style(self):
        return self.config.get("grid_style", "Solid")

    def get_bg_color(self):
        return self.config.get("bg_color", "#FAFAFA")
    #--------------------------------------------------------------
    
    def apply_pen_style(self, pen, style, width=1):
        """Apply line style to a pen"""
        style_map = {
            "Solid": Qt.PenStyle.SolidLine,
            "Dashed": Qt.PenStyle.DashLine,
            "Dotted": Qt.PenStyle.DotLine
        }
        pen.setStyle(style_map.get(style, Qt.PenStyle.SolidLine))
        pen.setWidth(width)
        return pen
    
    def apply_scatter_marker_shape(self, scatter_series, shape):
        """Apply marker shape to scatter series"""
        shape_map = {
            "Circle": QScatterSeries.MarkerShapeCircle,
            "Square": QScatterSeries.MarkerShapeRectangle,
            "Triangle": QScatterSeries.MarkerShapeTriangle
        }
        scatter_series.setMarkerShape(shape_map.get(shape, QScatterSeries.MarkerShapeCircle))

#==============================================================
class ResultPage(QWidget):
    """
    Result page for displaying calculation results as a chart.
    Shows a plot with Froude Number (x-axis) vs. result values (y-axis) that updates in real-time.
    Supports mouse hover to display coordinates.
    """
    
    def __init__(self, result_type, result_label, parent=None):
        """
        Initialize result page.
        
        Args:
            result_type: Type identifier (e.g., "Rt", "Trim", "Sinkage")
            result_label: Display label (e.g., "Total Resistance - Rt (N)")
        """
        super().__init__(parent)

        self.result_type = result_type
        self.result_label = result_label

        self.style_manager = ChartStyleManager() 
        
        # Store data points {fn: value}
        self.data_points = {}
        
        # Store hull parameters for AI evaluation
        self.hull_params = {}


        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        
        # Create chart
        self.chart = QChart()
        self.chart.setTitle(f"{self.result_label} vs. Froude Number")
        # Academic paper style - serif font
        title_font = QFont("Times New Roman", 13, QFont.Bold)
        self.chart.setTitleFont(title_font)
        self.chart.setAnimationOptions(QChart.NoAnimation)  # Disable animation for scientific look
        
        # Create line series
        self.series = QLineSeries()
        self.series.setName(self.result_label)
        
        # Create scatter series for hollow markers
        self.scatter_series = QScatterSeries()
        self.scatter_series.setName(self.result_label + " Points")
        self.scatter_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        self.scatter_series.setMarkerSize(6)  # Smaller size as requested
        
        # Style the line - clean and scientific
        pen = QPen(QColor("#1F4788"))  # Dark professional blue
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.series.setPen(pen)
        
        # Style the scatter points (Hollow circles)
        self.scatter_series.setPen(pen)  # Same blue border
        self.scatter_series.setBrush(QColor("white"))  # White fill = hollow look
        
        # Enable hover events for tooltips
        self.series.hovered.connect(self.on_point_hovered)
        self.scatter_series.hovered.connect(self.on_point_hovered)
        
        # Add series to chart
        self.chart.addSeries(self.series)
        self.chart.addSeries(self.scatter_series)
        
        # Create axes with Times New Roman font (standard in academic papers)
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Froude Number (Fn)")
        axis_title_font = QFont("Times New Roman", 11, QFont.Bold)
        self.axis_x.setTitleFont(axis_title_font)
        axis_label_font = QFont("Times New Roman", 10)
        self.axis_x.setLabelsFont(axis_label_font)
        self.axis_x.setLabelFormat("%.2f")
        self.axis_x.setRange(0, 1)
        
        # Grid styling - professional appearance
        self.axis_x.setGridLineVisible(True)
        self.axis_x.setMinorGridLineVisible(True)
        grid_pen = QPen(QColor("#E0E0E0"))
        grid_pen.setWidth(1)
        self.axis_x.setGridLinePen(grid_pen)
        
        minor_grid_pen = QPen(QColor("#F0F0F0"))
        minor_grid_pen.setWidth(1)
        minor_grid_pen.setStyle(Qt.DotLine)
        self.axis_x.setMinorGridLinePen(minor_grid_pen)
        
        # Tick lines
        self.axis_x.setLinePenColor(QColor("#333333"))
        
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText(self.result_label)
        self.axis_y.setTitleFont(axis_title_font)
        self.axis_y.setLabelsFont(axis_label_font)
        # Use custom label format - will be handled via setLabelsFormat
        self.axis_y.setLabelFormat("%.3f")  # Default format, will override
        self.axis_y.setRange(0, 1)
        self.axis_y.setGridLineVisible(True)
        self.axis_y.setMinorGridLineVisible(True)
        self.axis_y.setGridLinePen(grid_pen)
        self.axis_y.setMinorGridLinePen(minor_grid_pen)
        self.axis_y.setLinePenColor(QColor("#333333"))
        
        # Attach axes to series
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)
        self.scatter_series.attachAxis(self.axis_x)
        self.scatter_series.attachAxis(self.axis_y)
        
        # Top Axis (no labels, for box style)
        self.axis_top = QValueAxis()
        self.axis_top.setLabelsVisible(False)
        self.axis_top.setGridLineVisible(False)
        self.axis_top.setMinorGridLineVisible(False)
        self.axis_top.setLinePenColor(QColor("#333333"))
        self.axis_top.setRange(0, 1)
        self.axis_top.setTickCount(self.axis_x.tickCount()) # Try to sync ticks
        
        # Right Axis (no labels, for box style)
        self.axis_right = QValueAxis()
        self.axis_right.setLabelsVisible(False)
        self.axis_right.setGridLineVisible(False)
        self.axis_right.setMinorGridLineVisible(False)
        self.axis_right.setLinePenColor(QColor("#333333"))
        self.axis_right.setRange(0, 1)
        self.axis_right.setTickCount(self.axis_y.tickCount()) # Try to sync ticks
        
        self.chart.addAxis(self.axis_top, Qt.AlignTop)
        self.chart.addAxis(self.axis_right, Qt.AlignRight)
        
        # Attach to series to ensure they follow data range (though we set manually too)
        self.series.attachAxis(self.axis_top)
        self.series.attachAxis(self.axis_right)
        self.scatter_series.attachAxis(self.axis_top)
        self.scatter_series.attachAxis(self.axis_right)
        
        # Create chart view
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Style chart - clean scientific look with proper margins
        self.chart.setBackgroundBrush(QColor("#FAFAFA"))  # Subtle off-white instead of pure white
        self.chart.setBackgroundRoundness(0)  # Square corners (academic style)
        self.chart.setMargins(QMargins(15, 20, 20, 15))  # More generous margins
        self.chart.setPlotAreaBackgroundVisible(True)
        self.chart.setPlotAreaBackgroundBrush(QColor("#FFFFFF"))
        
        # Title styling
        self.chart.setTitleBrush(QColor("#1F1F1F"))
        
        # Legend - hidden for cleaner look (typical in scientific papers)
        self.chart.legend().setVisible(False)
        
        # Chart view styling
        self.chart_view.setStyleSheet("""
            QChartView {
                border: 1px solid #CCCCCC;
                background-color: #FAFAFA;
                border-radius: 1.5px;
            }
        """)
        
        main_layout.addWidget(self.chart_view)
        
        # Apply style after all components are initialized
        self.apply_chart_settings()
    
    def apply_chart_settings(self):

        """Apply chart style settings from settings.ini"""
        
        if not self.style_manager.settings:
            return
        
        # Apply curve style
        curve_style = self.style_manager.get_curve_style()
        curve_color = self.style_manager.get_curve_color()
        curve_width = self.style_manager.get_curve_width()
        
        pen = QPen(QColor(curve_color))
        pen = self.style_manager.apply_pen_style(pen, curve_style, int(curve_width))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.series.setPen(pen)
        
        # Apply scatter marker style
        scatter_style = self.style_manager.get_scatter_style()
        self.style_manager.apply_scatter_marker_shape(self.scatter_series, scatter_style)
        self.scatter_series.setPen(pen)
        
        # Apply axis style
        axis_style = self.style_manager.get_axis_style()
        axis_pen = QPen(QColor("#333333"))
        axis_pen = self.style_manager.apply_pen_style(axis_pen, axis_style, 1)
        self.axis_x.setLinePenColor(QColor("#333333"))
        self.axis_y.setLinePenColor(QColor("#333333"))
        
        # Apply grid style
        grid_style = self.style_manager.get_grid_style()
        grid_pen = QPen(QColor("#E0E0E0"))
        grid_pen = self.style_manager.apply_pen_style(grid_pen, grid_style, 1)
        self.axis_x.setGridLinePen(grid_pen)
        self.axis_y.setGridLinePen(grid_pen)
        
        # Apply background color
        bg_color = self.style_manager.get_bg_color()
        self.chart.setBackgroundBrush(QColor(bg_color))
        
        # Refresh chart
        self.chart.update()
        
    def on_point_hovered(self, point, state):
        """
        Handle mouse hover over data points to show tooltip.
        
        Args:
            point: QPointF containing (x, y) coordinates
            state: bool indicating hover state (True = hovering, False = left)
        """
        if state:
            # Show tooltip with coordinates
            tooltip_text = f"Fn = {point.x():.4f}\nValue = {point.y():.6f}"
            self.chart.setToolTip(tooltip_text)
        else:
            # Clear tooltip
            self.chart.setToolTip("")
    
    def set_chart_style(self, mode="continuous"):
        """
        Set chart style based on calculation mode.
        
        Args:
            mode: "scatter" (discrete speeds) or "continuous" (range)
        """
        if mode == "scatter":
            # Scatter mode: Line + Hollow Circles
            self.series.setVisible(True)
            self.series.setPointsVisible(False) # Disable built-in points of line series
            self.scatter_series.setVisible(True)
        else:
            # Continuous mode: Line only
            self.series.setVisible(True)
            self.series.setPointsVisible(False)
            self.scatter_series.setVisible(False)
            
    def update_result(self, fn, value):
        """
        Add or update a result point.
        
        Args:
            fn: Froude number
            value: Result value
        """
        # Store data point
        self.data_points[fn] = value
        
        # Rebuild series with sorted data
        self.series.clear()
        self.scatter_series.clear()
        sorted_points = sorted(self.data_points.items())
        
        for fn_val, result_val in sorted_points:
            self.series.append(fn_val, result_val)
            self.scatter_series.append(fn_val, result_val)
        
        # Auto-adjust axes
        if sorted_points:
            fn_values = [p[0] for p in sorted_points]
            result_values = [p[1] for p in sorted_points]
            
            fn_min, fn_max = min(fn_values), max(fn_values)
            val_min, val_max = min(result_values), max(result_values)
            
            # Add 10% padding for better visualization
            fn_range = fn_max - fn_min if fn_max != fn_min else 0.1
            val_range = val_max - val_min if val_max != val_min else 0.1
            
            self.axis_x.setRange(fn_min - 0.1 * fn_range, fn_max + 0.1 * fn_range)
            self.axis_y.setRange(val_min - 0.1 * val_range, val_max + 0.1 * val_range)
            
            # Sync top and right axes
            self.axis_top.setRange(fn_min - 0.1 * fn_range, fn_max + 0.1 * fn_range)
            self.axis_right.setRange(val_min - 0.1 * val_range, val_max + 0.1 * val_range)
    
    def clear_results(self):
        """Clear all results from the chart"""
        self.data_points.clear()
        self.series.clear()
        self.scatter_series.clear()
        self.axis_x.setRange(0, 1)
        self.axis_y.setRange(0, 1)
        self.axis_top.setRange(0, 1)
        self.axis_right.setRange(0, 1)
        self.axis_right.setRange(0, 1)

    def update_ui_texts(self, lang_manager):
        """Update UI texts based on current language."""
        if not lang_manager:
            return
            
        # Result pages use scientific notation and symbols, minimal translation needed
        # Chart titles and axis labels are already set during initialization
        pass

    def set_hull_params(self, params):
        """Set hull parameters for AI evaluation context."""
        self.hull_params = params

    # ---------------------------------------------------------------------------------
    def contextMenuEvent(self, event):
        """
        Create context menu for the chart.
        """
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction, QGuiApplication, QIcon
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from SaMPH_Utils.Utils import utils
        
        menu = QMenu(self)
        
        # Apply modern stylesheet
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 5px 0px;
            }
            QMenu::item {
                padding: 8px 32px 8px 36px;
                background-color: transparent;
                color: #333333;
                font-size: 13px;
                border-radius: 4px;
                margin: 2px 5px;
            }
            QMenu::item:selected {
                background-color: #F0F0F0;           /* Very light gray */
                color: #212121;
                border-left: 2px solid #757575;      /* Subtle gray accent */
            }
            QMenu::item:hover {
                background-color: #F0F0F0;
                color: #000000;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E0E0E0;
                margin: 5px 10px;
            }
            QMenu::icon {
                padding-left: 10px;
            }
        """)
        
        # Action 1: Copy file result path
        action_copy_path = QAction(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-copy-file-path-100.png")), "Copy result file path", self)
        action_copy_path.triggered.connect(lambda: self.copy_result_file_path(utils))
        menu.addAction(action_copy_path)
        
        # Action 2: Open result storage folder
        action_open_folder = QAction(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-file-explorer-100.png")), "Open result folder", self)
        action_open_folder.triggered.connect(lambda: self.open_result_folder(utils))
        menu.addAction(action_open_folder)
        
        menu.addSeparator()
        
        # Action 3: Open/Hide AI Chat Panel
        # Determine icon based on current state
        is_chat_visible = False
        main_window = self.window()
        
        if hasattr(main_window, 'right_panel'):
            # Use custom is_visible attribute instead of Qt's isVisible()
            # because the panel might be collapsed (width=0) but still "visible" in Qt terms
            if hasattr(main_window.right_panel, 'is_visible'):
                is_chat_visible = main_window.right_panel.is_visible
            else:
                is_chat_visible = main_window.right_panel.isVisible()
            
        chat_icon_path = "SaMPH_Images/WIN11-Icons/icons8-claude-ai-100.png" if is_chat_visible else "SaMPH_Images/WIN11-Icons/icons8-claude-ai-deactive-100.png"
        
        action_toggle_chat = QAction(QIcon(utils.local_resource_path(chat_icon_path)), "Toggle AI chat", self)
        action_toggle_chat.triggered.connect(self.toggle_ai_chat)
        menu.addAction(action_toggle_chat)
        
        # Action 4: Open Chat History
        action_chat_history = QAction(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-order-history-100.png")), "Open chat history", self)
        action_chat_history.triggered.connect(self.open_chat_history)
        menu.addAction(action_chat_history)
        
        # Action 5: New AI Chat
        action_new_chat = QAction(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-computer-chat-100.png")), "New chat", self)
        action_new_chat.triggered.connect(self.start_new_chat)
        menu.addAction(action_new_chat)

        menu.addSeparator()

        # Action 6: Evaluate with AI
        action_evaluate = QAction(QIcon(utils.local_resource_path("SaMPH_Images/WIN11-Icons/icons8-evaluate-100.png")), "Evaluate with AI", self)
        action_evaluate.triggered.connect(self.evaluate_result_with_ai)
        menu.addAction(action_evaluate)
        
        menu.exec(event.globalPos())

    def copy_result_file_path(self, utils):
        
        """Find the latest result file and copy its path to clipboard."""
        results_dir = utils.get_results_dir()
        if not results_dir.exists():
            return
            
        # Find latest xlsx file
        files = list(results_dir.glob("Savitsky_Results_*.xlsx"))
        if not files:
            return
            
        latest_file = max(files, key=os.path.getctime)
        
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(str(latest_file))
        print(f"[INFO] Copied to clipboard: {latest_file}")

    def open_result_folder(self, utils):
        """Open the result folder in file explorer."""
        results_dir = utils.get_results_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(results_dir)))

    def toggle_ai_chat(self):
        """Toggle the right AI chat panel."""
        main_window = self.window()
        if hasattr(main_window, 'operations_main_window'):
            main_window.operations_main_window.toggle_right_panel()

    def open_chat_history(self):
        """Open the chat history panel."""
        main_window = self.window()
        if hasattr(main_window, 'right_panel') and hasattr(main_window.right_panel, 'history_panel'):
            # Ensure right panel is visible first
            if not main_window.right_panel.isVisible():
                main_window.operations_main_window.toggle_right_panel()
            
            # Then toggle history if it's not already visible
            # Or just toggle it. The user asked to "Open Chat History page", usually implies showing it.
            # But toggle is safer if it's already open.
            main_window.right_panel.history_panel.toggle_panel()

    def start_new_chat(self):
        """Start a new AI chat."""
        main_window = self.window()
        if hasattr(main_window, 'right_panel'):
            # Ensure right panel is visible
            if not main_window.right_panel.isVisible():
                main_window.operations_main_window.toggle_right_panel()
            
            main_window.right_panel.new_chat_request.emit()

    def evaluate_result_with_ai(self):
        """
        Send the current calculation results to the AI chat for evaluation.
        """
        if not self.data_points:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Data", "There are no calculation results to evaluate.")
            return

        # Format data into a readable string
        data_str = "Froude Number (Fn) | Value\n"
        data_str += "-------------------|-------\n"
        
        # Sort points by Fn
        sorted_points = sorted(self.data_points.items())
        for fn, val in sorted_points:
            data_str += f"{fn:.4f}             | {val:.6f}\n"
            
        # Format hull parameters
        hull_info = ""
        if self.hull_params:
            hull_info = "**Hull Parameters:**\n"
            hull_info += f"- Length (L): {self.hull_params.get('ship_length', 'N/A')} m\n"
            hull_info += f"- Beam (B): {self.hull_params.get('ship_beam', 'N/A')} m\n"
            hull_info += f"- Deadrise Angle (Beta): {self.hull_params.get('beta', 'N/A')} deg\n"
            mass = self.hull_params.get('mass', 0)
            g = self.hull_params.get('g', 9.81)
            hull_info += f"- Displacement: {mass * g:.2f} N\n"
            hull_info += f"- LCG: {self.hull_params.get('lcg', 'N/A')} m\n"
            hull_info += f"- VCG: {self.hull_params.get('vcg', 'N/A')} m\n"
            hull_info += "\n"

        # Construct the prompt
        prompt = (
            f"Please evaluate the following calculation results for **{self.result_label}**:\n\n"
            f"{hull_info}"
            f"**Calculation Data:**\n"
            f"```\n{data_str}```\n\n"
            "**Background:**\n"
            "This is a planing hull resistance/performance calculation based on Savitsky's method.\n"
            "**Request:**\n"
            "1. Analyze the trend of the data and identify any potential anomalies.\n"
            "2. Evaluate if the design is reasonable based on the hull parameters and performance.\n"
            "3. Provide engineering optimization directions to improve performance."
        )
        
        # Send to AI chat (hide the detailed prompt from user view)
        main_window = self.window()
        if hasattr(main_window, 'right_panel') and hasattr(main_window.right_panel, 'send_external_message'):
            main_window.right_panel.send_external_message(prompt, show_user_message=False)
        else:
            print("[ERROR] Cannot access AI chat panel to send message.")


