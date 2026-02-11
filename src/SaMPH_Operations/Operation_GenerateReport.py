#--------------------------------------------------------------
# Report Generation Operations
# This file handles automatic report generation with AI assistance
# Programmer: Shanqin Jin (Fixed Version)
# Date: 2025-12-03
#--------------------------------------------------------------

import os
import time
import re
from pathlib import Path
from datetime import datetime
from html import escape

from PySide6.QtCore import QObject, Signal, QEventLoop, QTimer, Qt
from PySide6.QtWidgets import (QFileDialog, QMessageBox, QProgressDialog, QApplication, 
                               QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton)
from PySide6.QtGui import QFont, QIcon, QPixmap

# PDF generation checks
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepInFrame, HRFlowable, Frame, ListFlowable, ListItem, Preformatted
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[WARNING] reportlab not installed. PDF generation will not be available.")

# Assuming utils is available in your path
from SaMPH_Utils.Utils import utils


#==============================================================
# Modern Progress Dialog for Scientific Software
#==============================================================
class ModernProgressDialog(QDialog):
    """
    Modern, professional progress dialog for report generation.
    Designed to match scientific software aesthetics.
    Supports multilingual interface and uses custom icons.
    """
    
    def __init__(self, parent=None, lang_manager=None):

        super().__init__(parent)
        self._canceled = False
        self.lang_manager = lang_manager  # Store language manager for translations
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup modern UI with professional styling"""
        # Window title with translation support
        title = self.lang_manager.get_text("Report Generation") if self.lang_manager else "Report Generation"
        self.setWindowTitle(f"SaMPH - {title}")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(200)
        
        # Try to set window icon if available
        try:
            icon_path = utils.local_resource_path("SaMPH_Images/planing-hull-app-logo.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # Title label with translation support
        title_text = self.lang_manager.get_text("Generating Report") if self.lang_manager else "Generating Report"
        self.title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Status label with icon area
        status_container = QHBoxLayout()
        status_container.setSpacing(10)
        
        # Icon label - using QLabel with QIcon instead of emoji
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(24, 24)  # Icon size
        self.status_icon.setScaledContents(True)
        self._set_icon("default")  # Set default icon
        status_container.addWidget(self.status_icon)
        
        # Status text with translation support
        init_text = self.lang_manager.get_text("Initializing") if self.lang_manager else "Initializing"
        self.status_label = QLabel(f"{init_text}...")
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        self.status_label.setWordWrap(True)
        status_container.addWidget(self.status_label, 1)
        
        layout.addLayout(status_container)
        
        # Progress bar with modern styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(28)
        
        # Modern progress bar style
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #d0d0d0;
                border-radius: 8px;
                background-color: #f5f5f5;
                text-align: center;
                font-size: 11pt;
                font-weight: bold;
                color: #333333;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a90e2, 
                    stop:0.5 #5ca3f5, 
                    stop:1 #4a90e2
                );
                border-radius: 6px;
                margin: 1px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Spacer
        layout.addSpacing(10)
        
        # Cancel button with translation support
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_text = self.lang_manager.get_text("Cancel") if self.lang_manager else "Cancel"
        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setMinimumHeight(32)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 10pt;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Overall dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
            }
            QLabel {
                color: #333333;
            }
        """)
    
    def _set_icon(self, icon_type):
        """Set the status icon based on operation type using PNG files."""
        # Map operation types to icon files
        icon_map = {
            "ai": "SaMPH_Images/WIN11-Icons/icons8-generate-report-100.png",
            "chart": "SaMPH_Images/WIN11-Icons/icons8-combo-chart-100.png",
            "pdf": "SaMPH_Images/WIN11-Icons/icons8-pdf-100.png",
            "data": "SaMPH_Images/WIN11-Icons/icons8-analysis-100.png",
            "export": "SaMPH_Images/WIN11-Icons/icons8-export-101.png",
            "default": "SaMPH_Images/WIN11-Icons/icons8-gears-100.png"
        }
        
        icon_path = utils.local_resource_path(icon_map.get(icon_type, icon_map["default"]))
        
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Scale pixmap to icon size
                scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.status_icon.setPixmap(scaled_pixmap)
        else:
            # Fallback: use default gear icon
            default_icon_path = utils.local_resource_path(icon_map["default"])
            if os.path.exists(default_icon_path):
                pixmap = QPixmap(default_icon_path)
                scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.status_icon.setPixmap(scaled_pixmap)
    
    def setValue(self, value):
        """Set progress value (0-100)"""
        self.progress_bar.setValue(value)
        QApplication.processEvents()
        
    def setLabelText(self, text):

        """Set status text and update icon based on activity"""
        self.status_label.setText(text)
        
        # Dynamic icon based on activity (using keywords in both English and Chinese)
        if "AI" in text or "Analyzing" in text or "分析" in text:
            self._set_icon("ai")
        elif "Chart" in text or "Export" in text or "图表" in text or "导出" in text:
            self._set_icon("chart")
        elif "PDF" in text or "Building" in text or "生成" in text or "构建" in text:
            self._set_icon("pdf")
        elif "Collecting" in text or "Data" in text or "数据" in text or "收集" in text:
            self._set_icon("data")
        else:
            self._set_icon("default")
            
        QApplication.processEvents()
    
    def wasCanceled(self):
        """Check if user canceled the operation"""
        return self._canceled
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self._canceled = True
        # Update status text with translation support
        cancel_text = self.lang_manager.get_text("Canceling") if self.lang_manager else "Canceling"
        self.status_label.setText(f"{cancel_text}...")
        self.cancel_button.setEnabled(False)
        
    def closeEvent(self, event):
        """Handle window close event"""
        if not self._canceled:
            self._on_cancel()
        event.accept()
    
    def update_ui_texts(self, lang_manager):
        """Update all UI texts when language changes"""
        if not lang_manager:
            return
        
        # Update language manager reference
        self.lang_manager = lang_manager
        
        # Update window title
        title = lang_manager.get_text("Report Generation")
        self.setWindowTitle(f"SaMPH - {title}")
        
        # Update dialog title label
        title_text = lang_manager.get_text("Generating Report")
        self.title_label.setText(title_text)
        
        # Update cancel button text (if not already canceled)
        if not self._canceled:
            cancel_text = lang_manager.get_text("Cancel")
            self.cancel_button.setText(cancel_text)
        else:
            # If already canceling, update to new language
            cancel_text = lang_manager.get_text("Canceling")
            self.status_label.setText(f"{cancel_text}...")



#==============================================================
# Data Collection Module
#==============================================================
class ReportDataCollector:
    """Collects all necessary data for report generation"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def collect_ship_info(self):
        """Collect ship basic information and calculation parameters."""
        input_page = getattr(self.main_window, 'page_input', None)
        
        ship_info = {
            'constants': {},
            'hull_parameters': {},
            'speed_configuration': {}
        }
        
        # Collect constants
        constants_keys = ['acceleration_of_gravity', 'density_of_water', 'kinematic_viscosity_of_water']
        for key in constants_keys:
            if key in input_page.inputs:
                try:
                    ship_info['constants'][key] = float(input_page.inputs[key].text())
                except ValueError:
                    ship_info['constants'][key] = None
        
        # Collect hull parameters
        hull_keys = ['ship_length', 'ship_beam', 'mean_draft', 'displacement', 
                     'deadrise_angle', 'frontal_area_of_ship', 
                     'longitudinal_center_of_gravity', 'vertical_center_of_gravity']
        for key in hull_keys:
            if key in input_page.inputs:
                try:
                    ship_info['hull_parameters'][key] = float(input_page.inputs[key].text())
                except ValueError:
                    ship_info['hull_parameters'][key] = None
        
        # Collect speed configuration
        try:
            speeds = input_page.speed_input.get_speed_values()
            ship_info['speed_configuration']['speeds'] = speeds
            ship_info['speed_configuration']['mode'] = 'discrete' if input_page.radio_discrete.isChecked() else 'continuous'
        except:
            ship_info['speed_configuration']['speeds'] = []
            ship_info['speed_configuration']['mode'] = 'unknown'
        
        return ship_info
    
    def collect_calculation_results(self):
        """Collect calculation results."""
        if not hasattr(self.main_window, 'operations_result_page'):
            return {}
        
        result_ops = self.main_window.operations_result_page
        if hasattr(result_ops, 'results_data'):
            return result_ops.results_data.copy()
        return {}
    
    def collect_result_charts(self, output_dir):
        """
        Export result charts as image files.
        FIX: Ensures layout is processed before grabbing, handles off-screen widgets.
        """
        chart_paths = {}
        
        if not hasattr(self.main_window, 'operations_result_page'):
            print("[WARNING] No operations_result_page found in main_window")
            return chart_paths
            
        result_ops = self.main_window.operations_result_page
        os.makedirs(output_dir, exist_ok=True)
        print(f"[INFO] Chart export directory: {output_dir}")
        
        # Check if we have any results data
        if not hasattr(result_ops, 'results_data') or not result_ops.results_data:
            print("[WARNING] No results_data found, charts will be empty")
        
        for result_type, label in result_ops.result_config.items():
            print(f"[INFO] Processing chart for {result_type}...")
            
            # Force create/get the page
            page = result_ops.create_or_get_result_page(result_type)
            
            if not page:
                print(f"[WARNING] Failed to create page for {result_type}")
                continue
                
            if not hasattr(page, 'chart_view'):
                print(f"[WARNING] Page for {result_type} has no chart_view")
                continue
            
            chart_path = os.path.join(output_dir, f"{result_type}_chart.png")
            
            try:
                # Check if page has data
                has_data = result_type in result_ops.results_data and len(result_ops.results_data[result_type]) > 0
                print(f"[DEBUG] {result_type} has data: {has_data}")
                
                if not has_data:
                    print(f"[WARNING] {result_type} has no data, skipping chart export")
                    continue
                
                # CRITICAL FIX for silent off-screen rendering:
                # 1. Ensure page and chart_view have valid sizes
                print(f"[DEBUG] Original page size: {page.size().width()}x{page.size().height()}")
                
                # 2. Use WA_DontShowOnScreen to render without physical display
                # This allows layout and painting events to process without popping up a window
                page.setAttribute(Qt.WA_DontShowOnScreen, True)
                
                # 3. Set explicit sizes and show (virtually)
                page.resize(800, 600)
                page.chart_view.resize(780, 580)
                page.show() # Triggers layout/polish but won't appear on screen due to attribute
                
                # 4. Process events multiple times to ensure rendering
                for i in range(3):
                    QApplication.processEvents()
                
                print(f"[DEBUG] After resize - page: {page.size().width()}x{page.size().height()}")
                
                # 5. Grab the pixmap
                pixmap = page.chart_view.grab()
                print(f"[DEBUG] Grabbed pixmap size: {pixmap.width()}x{pixmap.height()}, isNull: {pixmap.isNull()}")
                
                # 6. Hide and cleanup
                page.hide()
                page.setAttribute(Qt.WA_DontShowOnScreen, False)
                
                # 7. Validate and save
                if not pixmap.isNull() and pixmap.width() > 10 and pixmap.height() > 10:
                    success = pixmap.save(chart_path, 'PNG')
                    if success:
                        chart_paths[result_type] = chart_path
                        print(f"[SUCCESS] Exported chart for {result_type} to {chart_path}")
                    else:
                        print(f"[ERROR] Failed to save pixmap for {result_type}")
                else:
                    print(f"[WARNING] Invalid pixmap for {result_type} (size: {pixmap.width()}x{pixmap.height()})")
                    
            except Exception as e:
                print(f"[ERROR] Failed to export chart for {result_type}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"[INFO] Successfully exported {len(chart_paths)}/{len(result_ops.result_config)} charts")
        return chart_paths
    
#==============================================================
# AI Interaction Module  
#==============================================================
class ReportAIAssistant:
    """Handles AI communication for report generation."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_response = None
        self.event_loop = None
        self.response_timeout = False
        
        # Note: We do NOT connect signals here anymore to avoid persistent connections
        # that might conflict during multiple analysis runs.
        # We connect temporarily in _send_and_wait_for_ai.
    
    def request_ship_info_analysis(self, ship_data):
        prompt = self._format_ship_info_prompt(ship_data)
        return self._send_and_wait_for_ai(prompt, 'ship_info_analysis')
    
    def request_result_analysis(self, result_type, result_data, hull_params):
        prompt = self._format_result_analysis_prompt(result_type, result_data, hull_params)
        return self._send_and_wait_for_ai(prompt, f'result_analysis_{result_type}')
    
    def request_design_summary(self, all_data):
        prompt = self._format_design_summary_prompt(all_data)
        return self._send_and_wait_for_ai(prompt, 'design_summary')
    

    def _format_ship_info_prompt(self, ship_data):
        """
        Optimized prompt for generating ship information analysis
        that is directly compatible with Python ReportLab text rendering.
        """

        prompt = (
            "You are a naval architecture expert writing a technical PDF report. "
            "Your output will be inserted directly into a Python ReportLab Paragraph. "
            "Follow ALL formatting rules strictly.\n\n"

            "[REPORTLAB TEXT RULES]\n"
            "1. Write ONLY continuous paragraphs. No bullet points, no numbered lists, no section titles.\n"
            "2. Use plain Unicode characters only. ReportLab-safe text only.\n"
            "3. Degrees: use the ° symbol (example: 12°).\n"
            "4. Superscripts: write directly as m², m³ without caret symbols.\n"
            "5. Subscripts: write as plain text (Cd, Fr). Never use underscores.\n"
            "6. Greek letters: use Unicode forms ρ, Δ, α, λ, μ directly. No LaTeX commands.\n"
            "7. Absolutely NO LaTeX, no $, no markdown, no backslashes.\n"
            "8. No special formatting tags. Plain text only.\n"
            "9. Write in a formal academic tone suitable for a naval architecture technical report.\n\n"

            "TASK:\n"
            "Analyze the provided ship design parameters and produce three continuous paragraphs:\n"
            "• Paragraph 1: Hull form characteristics and implications for resistance and seakeeping.\n"
            "• Paragraph 2: Assessment of the selected operating speeds and corresponding Froude numbers.\n"
            "• Paragraph 3: Design implications including stability, loading, and resistance behavior.\n"
            "Write smoothly and integrate all numerical values directly into sentences.\n\n"

            "DATA (use inline):\n"
        )

        if 'constants' in ship_data:
            const_text = ', '.join(f"{k} = {v}" for k, v in ship_data['constants'].items())
            prompt += f"Physical constants: {const_text}.\n"

        if 'hull_params' in ship_data:
            hull_text = ', '.join(f"{k} = {v}" for k, v in ship_data['hull_params'].items())
            prompt += f"Hull parameters: {hull_text}.\n"

        if 'speeds' in ship_data:
            speeds_list = ', '.join(str(s) for s in ship_data['speeds'])
            prompt += (
                f"Speed configuration (mode = {ship_data.get('speed_mode', 'N/A')}): "
                f"speeds = {speeds_list}.\n"
            )

        return prompt



    def _format_result_analysis_prompt(self, result_type, result_data, hull_params):
        """
        Optimized prompt for generating a single ReportLab-safe paragraph
        for resistance, trim, or sinkage analysis.
        """

        type_names = {
            "Rw": "Hydrodynamic Resistance",
            "Rs": "Spray Resistance",
            "Ra": "Air Resistance",
            "Rt": "Total Resistance",
            "Trim": "Trim Angle",
            "Sinkage": "Sinkage"
        }

        type_units = {
            "Rw": "N",
            "Rs": "N",
            "Ra": "N",
            "Rt": "N",
            "Trim": "degrees",
            "Sinkage": "m"
        }

        name = type_names.get(result_type, result_type)
        unit = type_units.get(result_type, "")

        prompt = (
            f"You are a naval architecture expert writing an engineering PDF report. "
            f"Your response will be inserted directly into a Python ReportLab paragraph. "
            f"Analyze the following {name} data in one single continuous paragraph. "
            f"All values are in {unit}.\n\n"

            "[REPORTLAB TEXT RULES]\n"
            "1. Output must be ONE paragraph only, no line breaks, no lists.\n"
            "2. Use only plain text compatible with ReportLab.\n"
            "3. Degrees: use ° symbol directly (example: 5.4°).\n"
            "4. Superscripts must use natural Unicode (m², m³).\n"
            "5. Subscripts must be plain text (Cd, Fr). No underscores.\n"
            "6. Greek letters must be Unicode characters (ρ, Δ, α). No LaTeX.\n"
            "7. No mathematical markup, no $, no **, no backslashes.\n"
            "8. Integrate numerical data smoothly into professional engineering prose.\n"
            "9. Focus on physical interpretation and trends, not on listing values.\n\n"

            f"{name} data (for inline reference): "
        )

        # Inline data
        fn_vals = [f"Fn {fn:.4f}: {val:.4f}" for fn, val in result_data.items()]
        prompt += "; ".join(fn_vals) + ". "

        # Hull context
        if hull_params:
            hull_text = ', '.join(f"{k} = {v}" for k, v in hull_params.items())
            prompt += f"Hull parameters: {hull_text}. "

        return prompt



    def _format_design_summary_prompt(self, all_data):
        return (
            "You are a naval architecture expert. Provide a concise overall summary of the design based on parameters and results. "
            "Highlight strengths, optimization areas, and suitability. Write in professional tone without LaTeX math."
        )

    def _handle_timeout(self):
        """Handle response timeout"""
        self.response_timeout = True
        if self.event_loop and self.event_loop.isRunning():
            self.event_loop.quit()



    def _format_ai_text(self, text: str) -> str:
        """
        [BACKUP METHOD - Currently not in use]
        
        Convert AI-generated text into clean, PDF-safe HTML markup for ReportLab.
        
        NOTE: This method is preserved as a backup/alternative text formatting solution.
              Currently, the PDF generation uses parse_markdown_to_flowables() directly,
              which works well for the simple paragraph format returned by AI prompts.
              
        Use cases for this method (if needed in future):
            - When AI returns complex Markdown that needs aggressive cleaning
            - When switching to a different AI model with different output formats
            - When enhanced LaTeX/Math symbol processing is required
        
        Features:
            - FULL removal of Markdown, LaTeX, and Unicode unsupported symbols
            - Converts Unicode superscripts/subscripts into <sup>/<sub>
            - Converts scientific notation correctly: 1 × 10⁻⁶ -> 1 × 10<sup>-6</sup>
            - Converts m² -> m<sup>2</sup>, m³ -> m<sup>3</sup>
            - Converts Greek letters to Unicode supported by ReportLab
            - Supports headings (#, ##, ###)
            - Generates clean HTML paragraphs using Times font
            - NEVER outputs bullets/lists; all are converted into continuous sentences
            
        To use this method, modify add_chapter_X methods to call:
            cleaned_text = self._format_ai_text(ai_analysis)
            flowables = self.parse_markdown_to_flowables(cleaned_text)
        """

        if not text:
            return ""

        # Normalize input
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split paragraphs on blank lines
        paragraphs = re.split(r"\n\s*\n+", text)
        formatted = []

        # =====================================================
        # Helper: Greek letters + special symbol replacements
        # =====================================================
        def replace_latex_symbols(s):
            greek = {
                r"\rho": "ρ", r"\alpha": "α", r"\beta": "β", r"\gamma": "γ",
                r"\theta": "θ", r"\lambda": "λ", r"\mu": "μ", r"\pi": "π",
                r"\sigma": "σ", r"\omega": "ω", r"\phi": "φ", r"\Delta": "Δ"
            }
            for k, v in greek.items():
                s = re.sub(k, v, s)

            # Remove remaining LaTeX commands like \cdot \sqrt etc.
            s = re.sub(r"\\[A-Za-z]+", "", s)

            # Fractions: \frac{a}{b} → (a)/(b)
            s = re.sub(r"\\frac\{(.+?)\}\{(.+?)\}", r"(\1)/(\2)", s)

            return s

        # =====================================================
        # Helper: Replace Unicode superscripts with <sup>
        # =====================================================
        superscript_map = {
            "⁰": "<sup>0</sup>", "¹": "<sup>1</sup>", "²": "<sup>2</sup>", "³": "<sup>3</sup>",
            "⁴": "<sup>4</sup>", "⁵": "<sup>5</sup>", "⁶": "<sup>6</sup>",
            "⁷": "<sup>7</sup>", "⁸": "<sup>8</sup>", "⁹": "<sup>9</sup>",
            "⁻": "-",  # negative sign for scientific notation
        }

        def normalize_superscripts(s):
            for k, v in superscript_map.items():
                s = s.replace(k, v)
            return s

        # =====================================================
        # Helper: normalize scientific notation
        # =====================================================
        def normalize_scientific_notation(s):
            # Pattern: "10-6"
            s = re.sub(r"10<sup>-(\d+)</sup>", r"10<sup>-\1</sup>", s)

            # Pattern: 10⁻6
            s = re.sub(r"10-?(\d+)", r"10<sup>\1</sup>", s)

            # Full scientific: "1 × 10⁻6" or "1 x 10^-6"
            s = re.sub(
                r"(\d+)\s*[x×]\s*10[-⁻]?(\d+)",
                r"\1 × 10<sup>-\2</sup>",
                s
            )
            return s

        # =====================================================
        # Helper: clean headings
        # =====================================================
        def convert_heading(line):
            line = line.strip()
            if line.startswith("### "):
                return f"<b><font size='12'>{line[4:].strip()}</font></b><br/><br/>"
            if line.startswith("## "):
                return f"<b><font size='14'>{line[3:].strip()}</font></b><br/><br/>"
            if line.startswith("# "):
                return f"<b><font size='16'>{line[2:].strip()}</font></b><br/><br/>"
            return None

        # =====================================================
        # Main paragraph loop
        # =====================================================
        for para in paragraphs:

            original = para

            # Escape HTML, then selectively restore
            para = escape(para, quote=False)

            # Restore basic symbols
            para = para.replace("&lt;", "<").replace("&gt;", ">")

            # Remove Markdown emphasis
            para = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", para)
            para = re.sub(r"\*(.+?)\*", r"<i>\1</i>", para)
            para = re.sub(r"_(.+?)_", r"<i>\1</i>", para)

            # Remove Markdown lists
            lines = para.split("\n")
            cleaned_lines = []
            for line in lines:
                if re.match(r"^\s*[-*+]\s+", line):
                    cleaned_lines.append(line.split(" ", 1)[1])
                elif re.match(r"^\s*\d+\.\s+", line):
                    cleaned_lines.append(line.split(" ", 1)[1])
                else:
                    cleaned_lines.append(line)
            para = " ".join(cleaned_lines)

            # Remove LaTeX math $...$
            para = re.sub(r"\$([^$]+)\$", r"\1", para)

            # Apply symbol conversions
            para = replace_latex_symbols(para)
            para = normalize_superscripts(para)
            para = normalize_scientific_notation(para)

            # Convert remaining ^2 → <sup>
            para = re.sub(r"(\w)\^(\d+)", r"\1<sup>\2</sup>", para)

            # Convert _d → <sub>d</sub>
            para = re.sub(r"([A-Za-z])_([A-Za-z0-9]+)", r"\1<sub>\2</sub>", para)

            # Convert m², m³
            para = para.replace("m²", "m<sup>2</sup>").replace("m³", "m<sup>3</sup>")

            # Check for headings
            heading = None
            for l in original.split("\n"):
                h = convert_heading(l)
                if h:
                    heading = h
                    break
            if heading:
                formatted.append(f"<font face='Times'>{heading}</font>")
            else:
                formatted.append(f"<font face='Times'>{para}</font>")

        return "<br/><br/>".join(formatted)







    def _on_ai_response_received(self, reply_dict, bubble=None):
        """
        Callback when AI worker finished signal is emitted.
        Stores the raw AI response for later processing by the report generator.
        """
        try:
            print(f"[DEBUG] _on_ai_response_received called. event_loop exists: {self.event_loop is not None}")

            if not reply_dict:
                print("[WARNING] reply_dict is empty or None.")
                self.current_response = ""
                return

            # Extract raw_text robustly
            raw_text = ''
            if isinstance(reply_dict, dict):
                raw_text = reply_dict.get('raw_text') or reply_dict.get('text') or ''
            elif isinstance(reply_dict, str):
                raw_text = reply_dict
            else:
                try:
                    raw_text = reply_dict.get('raw_text', '')
                except Exception:
                    raw_text = ''

            if raw_text:
                print(f"[DEBUG] Got raw_text length: {len(raw_text)}")
                # Basic cleanup only - remove conversational fillers
                text = raw_text.strip()
                text = re.sub(r'^Here is the analysis.*?:\s*', '', text, flags=re.IGNORECASE)
                text = re.sub(r'^Here are.*?:\s*', '', text, flags=re.IGNORECASE)
                
                self.current_response = text
                print(f"[DEBUG] Stored response length: {len(self.current_response)}")
            else:
                print("[WARNING] No raw_text found in reply_dict.")
                self.current_response = ""

            # Quit event loop if running
            try:
                if self.event_loop and getattr(self.event_loop, "isRunning", lambda: False)():
                    print("[DEBUG] Quitting event loop now.")
                    self.event_loop.quit()
                else:
                    print("[DEBUG] Event loop not running or not available.")
            except Exception as e:
                print(f"[ERROR] While trying to quit event loop: {e}")

        except Exception as e:
            print(f"[ERROR] Unexpected error in _on_ai_response_received: {e}")


    def _send_and_wait_for_ai(self, prompt, response_key, timeout=60):
        """
        Send prompt to AI and WAIT synchronously for response.
        FIX: Ensures signals are cleanly connected/disconnected to prevent duplicates.
        """
        if not hasattr(self.main_window, 'right_panel') or not hasattr(self.main_window, 'operation_chat'):
            return "[AI analysis not available - AI components not initialized]"
        
        worker = self.main_window.operation_chat.worker
        if not worker:
            return "[Error: Chat worker not ready]"

        # 1. Setup Signal - CRITICAL FIX
        # Always disconnect first, then connect fresh to avoid stale connections
        try:
            # Try to disconnect any existing connection (may fail if not connected)
            worker.finished.disconnect(self._on_ai_response_received)
            print(f"[DEBUG] Disconnected existing signal for {response_key}")
        except (RuntimeError, TypeError):
            # No existing connection, which is fine
            pass
        
        # Now connect fresh (without UniqueConnection to avoid Qt warnings)
        worker.finished.connect(self._on_ai_response_received)
        print(f"[DEBUG] Connected signal for {response_key}")

        self.current_response = None
        self.response_timeout = False
        
        # 2. Send Message
        if hasattr(self.main_window, 'log_window'):
            self.main_window.log_window.log_message(f"AI Request: Analyzing {response_key}...", level="INFO")
        
        # Send message with skip_format_instruction=True to avoid LaTeX rendering conflicts
        self.main_window.right_panel.send_external_message(
            prompt, 
            show_user_message=False,
            skip_format_instruction=True  # Skip LaTeX rules for PDF generation
        )
        print(f"[DEBUG] Sent AI request for {response_key}")
        
        # 3. Wait loop
        self.event_loop = QEventLoop()
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(self._handle_timeout)
        timeout_timer.start(timeout * 1000)
        
        print(f"[DEBUG] Entering event loop, waiting for response...")
        try:
            self.event_loop.exec() # BLOCKING WAIT
            print(f"[DEBUG] Event loop exited")
        finally:
            # FIX: ALWAYS disconnect signal to prevent future double-triggering
            try:
                worker.finished.disconnect(self._on_ai_response_received)
                print(f"[DEBUG] Cleaned up signal for {response_key}")
            except (RuntimeError, TypeError) as e:
                print(f"[DEBUG] Signal cleanup note: {e}")
            timeout_timer.stop()
            self.event_loop = None

        if self.response_timeout:
            print(f"[WARNING] AI timeout for {response_key}")
            return f"[AI response timeout for {response_key}]"
        
        result = self.current_response if self.current_response else "[No valid AI response]"
        print(f"[DEBUG] Returning result for {response_key}: {len(result) if result else 0} chars")
        return result


#==============================================================
# PDF Report Generator
#==============================================================
class PDFReportGenerator:
    """Generates PDF reports using reportlab"""
    
    def __init__(self, output_path):
        self.output_path = output_path
        self.story = []
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._setup_chinese_fonts()
            self._setup_custom_styles()
    
    def _setup_chinese_fonts(self):
        """Setup Chinese font support safely."""
        try:
            # Windows font paths
            font_paths = [
                r"C:\Windows\Fonts\simsun.ttc",
                r"C:\Windows\Fonts\msyh.ttc",
            ]
            registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        registered = True
                        break
                    except:
                        continue
            
            if not registered:
                print("[WARNING] No compatible Chinese font found.")
        except Exception as e:
            print(f"[WARNING] Font setup error: {e}")
    
    def _setup_custom_styles(self):
        # ... [Styles remain largely the same, just ensuring base styles exist] ...
        if 'Heading1' not in self.styles: return

        self.styles.add(ParagraphStyle(
            name='CustomTitle', parent=self.styles['Heading1'],
            fontSize=28, leading=34, textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30, alignment=TA_CENTER, fontName='Times-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='ChapterHeading', parent=self.styles['Heading1'],
            fontSize=16, spaceAfter=12, spaceBefore=24, fontName='Times-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeading', parent=self.styles['Heading2'],
            fontSize=12, spaceAfter=10, fontName='Times-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='ReportBody', parent=self.styles['Normal'],
            fontSize=11, leading=14, alignment=TA_JUSTIFY, fontName='Times-Roman'
        ))
        self.styles.add(ParagraphStyle(
            name='TableCaption', parent=self.styles['Normal'],
            fontSize=10, alignment=TA_CENTER, fontName='Times-Roman', spaceAfter=6
        ))

    def parse_markdown_to_flowables(self, text: str):
        """
        Parse AI text into a list of ReportLab Flowables (paragraphs, headers, etc.).
        
        PRIMARY USE: Processing simple paragraph text from AI (as per current prompts).
        SECONDARY CAPABILITY: Can handle basic Markdown if AI output deviates from prompts.
        
        Current AI prompts request PURE PARAGRAPH OUTPUT without Markdown formatting.
        However, this method retains Markdown parsing capabilities for robustness:
            - Headers (#, ##, ###) - in case AI adds section markers
            - Lists (*, -, 1.) - converted to continuous text
            - Code blocks (```) - should not appear but handled gracefully
            - Inline formatting (bold, italic, math) - basic support
        
        The method ensures all output is compatible with ReportLab PDF rendering.
        """
        if not text:
            return []
            
        flowables = []
        
        # Helper to format inline text (bold, italic, math)
        def format_inline(content):
            # Escape HTML first
            content = escape(content, quote=False)
            
            # LaTeX symbols replacement
            replacements = {
                r'\\rho': 'ρ', r'\\Delta': 'Δ', r'\\alpha': 'α', r'\\beta': 'β',
                r'\\gamma': 'γ', r'\\theta': 'θ', r'\\lambda': 'λ', r'\\mu': 'μ',
                r'\\pi': 'π', r'\\sigma': 'σ', r'\\omega': 'ω', r'\\phi': 'φ',
                r'\\nabla': '∇', r'\\partial': '∂', r'\\infty': '∞',
                r'\\cdot': '·', r'\\times': '×', r'\\approx': '≈',
                r'\\le': '≤', r'\\ge': '≥', r'\\pm': '±', r'\\ne': '≠'
            }
            for latex, char in replacements.items():
                content = re.sub(latex, char, content)
            
            # Fractions and Sqrt
            content = re.sub(r'\\frac\{(.+?)\}\{(.+?)\}', r'(\1)/(\2)', content)
            content = re.sub(r'\\sqrt\{(.+?)\}', r'√(\1)', content)
            
            # Math formatting
            # Display math $$...$$ -> monospace
            content = re.sub(r'\$\$(.*?)\$\$', r"<font face='Courier'>\1</font>", content, flags=re.S)
            # Inline math $...$ -> monospace
            def _imath_repl(m):
                inner = m.group(1).strip()
                inner = re.sub(r'_(\{(.*?)\}|(\w))', lambda x: f"<sub>{x.group(2) or x.group(3)}</sub>", inner)
                inner = re.sub(r'\^(\{(.*?)\}|(\w))', lambda x: f"<sup>{x.group(2) or x.group(3)}</sup>", inner)
                return f"<font face='Courier'>{inner}</font>"
            content = re.sub(r'\$([^\$\n]+)\$', _imath_repl, content)
            
            # Naked math (sub/sup) - FIX: Capture base character too
            content = re.sub(r'\b([A-Za-z])_([A-Za-z0-9]+)\b', r'\1<sub>\2</sub>', content)
            content = re.sub(r'\b([A-Za-z])\^([0-9]+)\b', r'\1<sup>\2</sup>', content)
            
            # Bold and Italic
            content = re.sub(r'\*\*(.+?)\*\*', r"<b>\1</b>", content)
            content = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r"<i>\1</i>", content)
            content = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r"<i>\1</i>", content)
            
            return content

        # Normalize
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split by double newlines for blocks
        blocks = re.split(r'\n\s*\n+', text)
        
        for block in blocks:
            block = block.strip()
            if not block: continue
            
            # Header detection
            header_match = re.match(r'^(#{1,6})\s+(.*)', block, flags=re.DOTALL)
            if header_match:
                level = len(header_match.group(1))
                content = header_match.group(2).strip()
                # Map to Heading1, Heading2, etc. (ReportLab usually has Heading1-6)
                # We map # -> Heading1, ## -> Heading2, etc.
                # Adjust style based on available styles
                style_name = 'Heading2' if level == 1 else 'Heading3' if level == 2 else 'Heading4'
                # If style doesn't exist, fallback to Heading2
                if style_name not in self.styles: style_name = 'Heading2'
                
                content = format_inline(content)
                flowables.append(Paragraph(content, self.styles[style_name]))
                flowables.append(Spacer(1, 0.2*cm))
                continue
                
            # List detection (simple block-level list)
            # Check if block starts with list marker
            if re.match(r'^(\*|-|\d+\.)\s+', block):
                lines = block.split('\n')
                for line in lines:
                    line = line.strip()
                    # Check if list item
                    match = re.match(r'^(\*|-|\d+\.)\s+(.*)', line)
                    if match:
                        content = match.group(2)
                        content = format_inline(content)
                        # Use bullet char for unordered, number for ordered?
                        # For simplicity, use bullet for all or just text
                        # ReportLab ListFlowable is good but Paragraph with bullet is easier
                        flowables.append(Paragraph(content, self.styles['ReportBody'], bulletText='•'))
                    else:
                        # Continuation line? Treat as text
                        content = format_inline(line)
                        flowables.append(Paragraph(content, self.styles['ReportBody']))
                flowables.append(Spacer(1, 0.2*cm))
                continue
                    
            # Code block
            if block.startswith('```'):
                content = block.strip('`').strip()
                # Preformatted style
                style = self.styles['Code'] if 'Code' in self.styles else self.styles['Normal']
                flowables.append(Preformatted(content, style))
                flowables.append(Spacer(1, 0.2*cm))
                continue
                
            # Normal Paragraph
            content = format_inline(block)
            flowables.append(Paragraph(content, self.styles['ReportBody']))
            flowables.append(Spacer(1, 0.2*cm))
                
        return flowables


    def add_cover_page(self, title, project_name, date_str):


        if not REPORTLAB_AVAILABLE:
            return


        # ---------- Top space ----------
        self.story.append(Spacer(1, 2*cm))

        # ---------- Branding LOGO ----------
        try:
            logo_path = utils.local_resource_path("SaMPH_Images/planing-hull-app-logo.png")
            logo_img = Image(logo_path, width=4*cm, height=4*cm)
            logo_img.hAlign = 'CENTER'
            self.story.append(logo_img)
            self.story.append(Spacer(1, 0.5*cm))
        except Exception as e:
            print(f"[WARNING] Logo image not found: {e}")

        # ---------- Subtitle (SaMPH) ----------
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontSize=12,
            alignment=TA_CENTER,
            fontName='Times-Bold',
            textColor=colors.HexColor('#222222')
        )
        self.story.append(Paragraph("SaMPH", subtitle_style))
        self.story.append(Spacer(1, 1*cm))

        # ---------- Divider line ----------
        self.story.append(
            HRFlowable(width="65%", thickness=1, color=colors.black,
                    spaceBefore=0.3*cm, spaceAfter=0.3*cm, hAlign='CENTER')
        )

        # ---------- Main Title ----------
        title_style = ParagraphStyle(
            'CoverTitle',
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            fontName='Times-Bold',
            textColor=colors.HexColor('#111111'),
            spaceAfter=1*cm
        )
        self.story.append(Paragraph(title, title_style))

        # ---------- Version ----------
        version_style = ParagraphStyle(
            'Version',
            fontSize=11,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )
        self.story.append(Paragraph("Version 1.0", version_style))

        # ---------- Spacer to push Prepared into vertical center ----------
        self.story.append(Spacer(1, 4*cm))  # Reduce top spacing, push content down

        # ---------- Prepared by SaMPH (Center) ----------
        prepared_style = ParagraphStyle(
            'Prepared',
            fontSize=12,
            alignment=TA_CENTER,
            fontName='Times-Italic',  # Italic
            textColor=colors.HexColor('#000000')
        )
        self.story.append(Paragraph("Prepared by SaMPH", prepared_style))

        # ---------- Spacer between Prepared and Date - Push to bottom ----------
        self.story.append(Spacer(1, 6*cm))  # Increase spacing, push date to bottom

        # ---------- Date (Bottom) ----------
        date_style = ParagraphStyle(
            'Date',
            fontSize=10,
            alignment=TA_CENTER,
            fontName='Times-Roman',
            textColor=colors.HexColor('#000000')
        )
        self.story.append(Paragraph(str(date_str), date_style))

        # ---------- Next page ----------
        self.story.append(PageBreak())



    def add_table_of_contents(self):
        """Add table of contents with page numbers and subsection support"""
        
        if not REPORTLAB_AVAILABLE: return
        
        # 1. Title Configuration
        toc_title_style = ParagraphStyle(
            'TOCTitle',
            parent=self.styles['Normal'],
            fontName='Times-Bold',
            fontSize=16,
            alignment=1,  # center
            spaceAfter=12
        )
        self.story.append(Paragraph("Table of Contents", toc_title_style))
        self.story.append(Spacer(1, 0.8*cm))
        
        # 2. TOC Entries
        # [Title, Page, Indent Level (0=chapter, 1=section)]
        toc_data = [
            ["Chapter 1: Ship Basic Information", "3", 0],
            ["1.1 Physical Constants", "3", 1],
            ["1.2 Hull Parameters", "3", 1],
            ["1.3 Design Analysis", "4", 1],
            ["Chapter 2: Calculation Results", "5", 0],
            ["2.1 Total Resistance", "5", 1],
            ["2.2 Trim Angle", "6", 1],
            ["2.3 Sinkage", "6", 1],
            ["2.4 Hydrodynamic Resistance", "7", 1],
            ["2.5 Spray Resistance", "7", 1],
            ["2.6 Air Resistance", "8", 1],
            ["Chapter 3: Design Summary", "9", 0],
            ["Chapter 4: References", "10", 0]
        ]
        
        

        # 3. Build the Table Flowables
        for title, page_num, indent_level in toc_data:

            # Dynamic Styling Variables based on indentation
            is_chapter = (indent_level == 0)
            current_font = 'Times-Bold' if is_chapter else 'Times-Roman'
            current_size = 11 if is_chapter else 10
            left_indent = 0.5*cm + indent_level * 0.5*cm
            padding = 4 if is_chapter else 2

            # Define the Paragraph Style for the Title (Left Column)
            entry_para_style = ParagraphStyle(
                f'TOCLevel{indent_level}',
                parent=self.styles['Normal'],
                fontName=current_font,
                fontSize=current_size,
                leftIndent=left_indent, 
                rightIndent=0,
            )
            
            # Define the Paragraph Style for the Page Number (Right Column)
            page_num_style = ParagraphStyle(
                'PageNum', 
                parent=self.styles['Normal'],
                fontName='Times-Roman', 
                fontSize=current_size, 
                alignment=2  # right aligned
            )

            # Create the Table Row
            # Column 1: Title (Paragraph), Column 2: Page Number (Paragraph)
            row_data = [
                Paragraph(title, entry_para_style), 
                Paragraph(page_num, page_num_style)
            ]
            
            entry_table = Table(
                [row_data],
                colWidths=[14*cm, 2*cm]
            )
            
            # Apply Table Styling
            entry_table.setStyle(TableStyle([
                # Alignment
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'), # Ensures text aligns at top if title wraps
                
                # Padding (visual separation between rows)
                ('BOTTOMPADDING', (0,0), (-1,-1), padding),
                ('TOPPADDING', (0,0), (-1,-1), padding),
                
                # Note: We rely on the Paragraph styles for Font/Size, 
                # but setting table grid lines to transparent is often good practice:
                # ('GRID', (0,0), (-1,-1), 0, colors.white),
            ]))
            
            self.story.append(entry_table)
        
        self.story.append(Spacer(1, 1*cm))
        self.story.append(PageBreak())


    def add_chapter_1_ship_info(self, ship_data, ai_analysis):
        if not REPORTLAB_AVAILABLE: return
        self.story.append(Paragraph("Chapter 1: Ship Basic Information", self.styles['ChapterHeading']))
        self.story.append(Spacer(1, 0.5*cm))
        
        # Section 1.1: Physical Constants
        self.story.append(Paragraph("1.1 Physical Constants", self.styles['SectionHeading']))
        
        if ship_data and 'constants' in ship_data:
            # Table caption
            caption = Paragraph("<b>Table 1.1:</b> Physical Constants", self.styles['TableCaption'])
            self.story.append(caption)
            self.story.append(Spacer(1, 0.2*cm))
            
            # Define units for constants
            const_units = {
                'acceleration_of_gravity': 'm/s²',
                'density_of_water': 'kg/m³',
                'kinematic_viscosity_of_water': 'm²/s'
            }
            
            constants_data = [['Parameter', 'Value']]
            for key, value in ship_data['constants'].items():
                param_name = str(key).replace('_', ' ').title()
                unit = const_units.get(key, '')
                if unit:
                    param_name += f" ({unit})"
                val_str = f"{value:.6f}" if isinstance(value, float) else str(value)
                constants_data.append([param_name, val_str])
            
            t = Table(constants_data, colWidths=[10*cm, 4*cm])
            t.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
                ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
                ('LINEBELOW', (0,0), (-1,0), 0.5, colors.black),
                ('LINEBELOW', (0,-1), (-1,-1), 1.5, colors.black),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            self.story.append(t)
        self.story.append(Spacer(1, 0.8*cm))
        
        # Section 1.2: Hull Parameters
        self.story.append(Paragraph("1.2 Hull Parameters", self.styles['SectionHeading']))
        
        if ship_data and 'hull_parameters' in ship_data:
            # Table caption
            caption = Paragraph("<b>Table 1.2:</b> Hull Parameters", self.styles['TableCaption'])
            self.story.append(caption)
            self.story.append(Spacer(1, 0.2*cm))
            
            # Define units for hull parameters
            hull_units = {
                'ship_length': 'm',
                'ship_beam': 'm',
                'mean_draft': 'm',
                'displacement': 'kg',
                'deadrise_angle': '°',
                'frontal_area_of_ship': 'm²',
                'longitudinal_center_of_gravity': 'm',
                'vertical_center_of_gravity': 'm'
            }
            
            hull_data = [['Parameter', 'Value']]
            for key, value in ship_data['hull_parameters'].items():
                param_name = str(key).replace('_', ' ').title()
                unit = hull_units.get(key, '')
                if unit:
                    param_name += f" ({unit})"
                val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                hull_data.append([param_name, val_str])
            
            t = Table(hull_data, colWidths=[10*cm, 4*cm])
            t.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
                ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
                ('LINEBELOW', (0,0), (-1,0), 0.5, colors.black),
                ('LINEBELOW', (0,-1), (-1,-1), 1.5, colors.black),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            self.story.append(t)
        self.story.append(Spacer(1, 0.8*cm))

        # Section 1.3: AI Analysis
        # Note: AI analysis usually includes headers like "## 1.3 ...", so we parse it directly
        if ai_analysis:
            flowables = self.parse_markdown_to_flowables(str(ai_analysis))
            self.story.extend(flowables)
        self.story.append(PageBreak())

    def add_chapter_2_results(self, results_data, chart_paths, ai_comments):
        if not REPORTLAB_AVAILABLE: return
        self.story.append(Paragraph("Chapter 2: Calculation Results", self.styles['ChapterHeading']))
        self.story.append(Spacer(1, 0.5*cm))
        
        # Result type names for figure captions
        result_names = {
            'Rt': 'Total Resistance',
            'Trim': 'Trim Angle',
            'Sinkage': 'Sinkage',
            'Rw': 'Hydrodynamic Resistance',
            'Rs': 'Spray Resistance',
            'Ra': 'Air Resistance'
        }
        
        for idx, (result_type, data) in enumerate(results_data.items(), 1):
            result_name = result_names.get(result_type, result_type)
            
            # Section heading
            self.story.append(Paragraph(f"2.{idx} {result_name}", self.styles['SectionHeading']))
            self.story.append(Spacer(1, 0.3*cm))
            
            # Add Chart with caption
            if result_type in chart_paths and os.path.exists(chart_paths[result_type]):
                try:
                    img = Image(chart_paths[result_type], width=14*cm, height=10*cm)
                    self.story.append(img)
                    
                    # Figure caption below image
                    caption_text = f"<b>Figure 2.{idx}:</b> {result_name} vs Froude Number"
                    caption = Paragraph(caption_text, self.styles['TableCaption'])
                    self.story.append(Spacer(1, 0.2*cm))
                    self.story.append(caption)
                except Exception as e:
                    print(f"Image error: {e}")
            
            # Add AI Comment
            if result_type in ai_comments:
                self.story.append(Spacer(1, 0.4*cm))
                flowables = self.parse_markdown_to_flowables(str(ai_comments[result_type]))
                self.story.extend(flowables)
            
            self.story.append(Spacer(1, 0.8*cm))
        self.story.append(PageBreak())

    def add_chapter_3_summary(self, ai_summary):
        if not REPORTLAB_AVAILABLE: return
        self.story.append(Paragraph("Chapter 3: Design Summary", self.styles['ChapterHeading']))
        if ai_summary:
            flowables = self.parse_markdown_to_flowables(str(ai_summary))
            self.story.extend(flowables)
        self.story.append(PageBreak())

    def add_chapter_references(self):
        if not REPORTLAB_AVAILABLE: return
        self.story.append(Paragraph("Chapter 4: References", self.styles['ChapterHeading']))
        self.story.append(Spacer(1, 0.5*cm))
        
        # Reference 1: Software
        ref1 = Paragraph(
            "[1] SaMPH - Savitsky-based Motion of Planing Hulls, Version 1.0, AMHL Team, 2025.",
            self.styles['ReportBody']
        )
        self.story.append(ref1)
        self.story.append(Spacer(1, 0.3*cm))
        
        # Reference 2: Jin et al. 2023 paper
        ref2 = Paragraph(
            "[2] Jin, S., Peng, H.H., Qiu, W., Hunter, R. and Thompson, S., 2023. "
            "Numerical simulation of planing hull motions in calm water and waves with overset grid. "
            "<i>Ocean Engineering</i>, 287, p.115858.",
            self.styles['ReportBody']
        )
        self.story.append(ref2)


    def _add_page_number(self, canvas, doc):
        """Add header and footer to each page (skip cover page)."""
        canvas.saveState()
        
        page_num = canvas.getPageNumber()
        page_width, page_height = A4
        
        # Skip header/footer on cover page (page 1)
        if page_num > 1:
            # Header - Report title on left, horizontal line below
            canvas.setFont('Times-Italic', 9)
            canvas.setFillColor(colors.HexColor('#555555'))
            canvas.drawString(2.5*cm, page_height - 2*cm, "Planing Hull Analysis Report")
            
            # Header line
            canvas.setStrokeColor(colors.HexColor('#333333'))
            canvas.setLineWidth(0.5)
            canvas.line(2.5*cm, page_height - 2.2*cm, page_width - 2.5*cm, page_height - 2.2*cm)
            
            # Footer - Centered page number (just number, no "Page" prefix)
            canvas.setFont('Times-Roman', 10)
            canvas.setFillColor(colors.black)
            canvas.drawCentredString(page_width / 2, 1.5*cm, str(page_num))
            
            # Footer line
            canvas.setStrokeColor(colors.HexColor('#333333'))
            canvas.setLineWidth(0.5)
            canvas.line(2.5*cm, 2*cm, page_width - 2.5*cm, 2*cm)
        
        canvas.restoreState()

    def build(self):
        if not REPORTLAB_AVAILABLE: return False
        try:
            from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
            doc = BaseDocTemplate(self.output_path, pagesize=A4, 
                                rightMargin=2.5*cm, leftMargin=2.5*cm, 
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
            frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
            template = PageTemplate(id='main', frames=[frame], onPage=self._add_page_number)
            doc.addPageTemplates([template])
            doc.build(self.story)
            return True
        except Exception as e:
            print(f"[ERROR] Build PDF failed: {e}")
            return False

#==============================================================
# Markdown Report Generator (Simplified for brevity - Logic was OK)
#==============================================================
class MarkdownReportGenerator:
    """Generates Markdown reports"""
    def __init__(self, output_path):
        self.output_path = output_path
        self.content = []
    
    def add_cover_page(self, title, project_name, date_str):
        self.content.append(f"# {title}\n\n**Ship Length:** {project_name}m\n**Date:** {date_str}\n\n---\n")

    def add_chapter_1_ship_info(self, ship_data, ai_analysis):
        self.content.append("## 1. Ship Info\n\n")
        # ... logic similar to PDF ...
        self.content.append(f"### Analysis\n{ai_analysis}\n\n")

    def add_chapter_2_results(self, results, charts, comments):
        self.content.append("## 2. Results\n\n")
        
        # Get markdown directory once
        try:
            md_dir = os.path.dirname(self.output_path)
        except:
            md_dir = ""

        for k, v in results.items():
            self.content.append(f"### {k}\n")
            if k in charts:
                # Calculate relative path from markdown file to image for better portability
                try:
                    if md_dir:
                        rel_path = os.path.relpath(charts[k], md_dir)
                    else:
                        rel_path = os.path.basename(charts[k])
                    
                    image_path = str(rel_path).replace('\\', '/')
                    
                    # Add ./ prefix for clarity
                    if not image_path.startswith('.') and not image_path.startswith('/'):
                        image_path = './' + image_path
                        
                except Exception as e:
                    print(f"[WARN] Failed to calculate relative path for {k}: {e}")
                    image_path = str(charts[k]).replace('\\', '/')

                self.content.append(f"![Chart]({image_path})\n\n")
            if k in comments:
                self.content.append(f"{comments[k]}\n\n")

    def add_chapter_3_summary(self, summary):
        self.content.append(f"## 3. Summary\n\n{summary}\n")

    def build(self):
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(self.content))
            return True
        except Exception as e:
            print(f"MD Build failed: {e}")
            return False

#==============================================================
# Main Report Generator Controller
#==============================================================
class ReportGenerator_Operations(QObject):
    """Main controller for report generation"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.data_collector = ReportDataCollector(main_window)
        self.ai_assistant = ReportAIAssistant(main_window)
        self.progress_dialog = None  # Reference to current progress dialog (if open)

    def _wait_non_blocking(self, seconds):
        """
        FIX: Wait without freezing the GUI.
        Replaces time.sleep()
        """
        loop = QEventLoop()
        QTimer.singleShot(int(seconds * 1000), loop.quit)
        # Check cancellation during wait if attached to a progress dialog
        loop.exec()

    def generate_report(self):
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self.main_window, "Error", "ReportLab not installed.")
            return

        default_filename = f"SaMPH_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Save Report", 
            str(utils.get_results_dir() / default_filename), 
            "PDF Files (*.pdf);;Markdown Files (*.md)"
        )
        
        if not file_path: return
        
        # Determine paths
        base_path = Path(file_path)
        pdf_path = str(base_path.with_suffix('.pdf'))
        md_path = str(base_path.with_suffix('.md'))

        # Create modern progress dialog with language support
        lang_manager = getattr(self.main_window, 'language_manager', None)
        self.progress_dialog = ModernProgressDialog(self.main_window, lang_manager)
        progress = self.progress_dialog  # Keep backward compatibility with existing code
        progress.show()
        QApplication.processEvents()

        try:
            # 1. Collect Data
            progress.setLabelText("Collecting data...")
            progress.setValue(10)
            ship_info = self.data_collector.collect_ship_info()
            results_data = self.data_collector.collect_calculation_results()
            
            if not ship_info or not results_data:
                QMessageBox.warning(self.main_window, "No Data", "Please run calculations first.")
                return

            # 2. Charts
            progress.setLabelText("Exporting charts...")
            progress.setValue(30)
            # Create a dedicated charts folder alongside report
            charts_dir = base_path.parent / (base_path.stem + "_charts")
            chart_paths = self.data_collector.collect_result_charts(str(charts_dir))
            
            # 3. AI Analysis
            progress.setLabelText("AI: Analyzing hull parameters...")
            progress.setValue(40)
            ai_ship_analysis = self.ai_assistant.request_ship_info_analysis(ship_info)
            
            self._wait_non_blocking(2.0) # Non-blocking wait

            ai_result_comments = {}
            count = len(results_data)
            for i, result_type in enumerate(results_data.keys()):
                if progress.wasCanceled(): return
                progress.setLabelText(f"AI: Analyzing {result_type}...")
                
                comment = self.ai_assistant.request_result_analysis(
                    result_type, results_data[result_type], ship_info.get('hull_parameters', {})
                )
                ai_result_comments[result_type] = comment
                progress.setValue(40 + int(30 * (i+1)/count))
                self._wait_non_blocking(2.0)

            progress.setLabelText("AI: Generating Summary...")
            ai_summary = self.ai_assistant.request_design_summary({'ship': ship_info, 'res': results_data})
            progress.setValue(80)

            # 4. Build Files
            progress.setLabelText("Building PDF...")
            pdf_gen = PDFReportGenerator(pdf_path)
            hull_params = ship_info.get('hull_parameters', {})
            pdf_gen.add_cover_page("Planing Hull Analysis Report", hull_params.get('ship_length', 'N/A'), datetime.now().strftime('%Y-%m-%d'))
            pdf_gen.add_table_of_contents()
            pdf_gen.add_chapter_1_ship_info(ship_info, ai_ship_analysis)
            pdf_gen.add_chapter_2_results(results_data, chart_paths, ai_result_comments)
            pdf_gen.add_chapter_3_summary(ai_summary)
            pdf_gen.add_chapter_references()
            pdf_gen.build()
            
            progress.setLabelText("Building Markdown...")
            md_gen = MarkdownReportGenerator(md_path)
            md_gen.add_cover_page("Planing Hull Analysis Report", hull_params.get('ship_length', 'N/A'), datetime.now().strftime('%Y-%m-%d'))
            md_gen.add_chapter_1_ship_info(ship_info, ai_ship_analysis)
            md_gen.add_chapter_2_results(results_data, chart_paths, ai_result_comments)
            md_gen.add_chapter_3_summary(ai_summary)
            md_gen.build()

            progress.setValue(100)
            QMessageBox.information(self.main_window, "Success", f"Report saved to:\n{pdf_path}\n{md_path}")

        except Exception as e:
            print(f"Main Error: {e}")
            QMessageBox.critical(self.main_window, "Error", f"Generation failed: {e}")
        finally:
            progress.close()
            self.progress_dialog = None  # Clear reference after closing
    
    
    def update_ui_texts(self, lang_manager):
        """Update UI texts when language changes"""
        # Update progress dialog if it's currently open
        if self.progress_dialog and hasattr(self.progress_dialog, 'update_ui_texts'):
            print("[INFO] Updating progress dialog language (dialog is open)")
            self.progress_dialog.update_ui_texts(lang_manager)
        else:
            print("[DEBUG] Progress dialog not open, will use new language when created")


