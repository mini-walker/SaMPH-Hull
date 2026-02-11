import sys
import os
from pathlib import Path
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QGridLayout, QPushButton, QRadioButton, QButtonGroup,
    QGroupBox, QSizePolicy, QMessageBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QIcon

# Add the parent directory to the Python path for debugging
if __name__ == "__main__": 
    print("Debug mode!")   
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path: 
        sys.path.insert(0, project_root)

from SaMPH_Utils.Utils import utils


#==============================================================
class SpeedInputSection(QWidget):
    """
    Speed input section with discrete/continuous mode switching
    Maintains consistent height regardless of mode
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize with references to radio buttons (will be set by parent)
        self.radio_discrete = None
        self.radio_continuous = None
        self.init_ui()
    
    def init_ui(self):

        """Initialize speed input UI"""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ============ Stacked Input Fields (use fixed widget to maintain size) ============
        # Create a container that maintains consistent size
        self.container = QWidget()
        self.container.setMinimumHeight(150)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)
        
        # -- Discrete Mode Inputs --
        discrete_layout = QGridLayout()
        discrete_layout.setHorizontalSpacing(20)
        discrete_layout.setVerticalSpacing(6)
        discrete_layout.setContentsMargins(0, 0, 0, 0)
        
        # Discrete speed values
        label = QLabel("Speed Values (m/s):")
        label_font = QFont("Times New Roman", 11)
        label.setFont(label_font)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        discrete_layout.addWidget(label, 0, 0)
        
        self.discrete_speeds = QLineEdit()
        self.discrete_speeds.setPlaceholderText("e.g., 5, 10, 15, 20, 25")

        self.discrete_speeds.textChanged.connect(self.update_discrete_preview)
        discrete_layout.addWidget(self.discrete_speeds, 0, 1)
        
        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setFont(label_font)
        preview_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        discrete_layout.addWidget(preview_label, 1, 0)
        
        self.discrete_preview = QLabel("(No values entered)")
        self.discrete_preview.setStyleSheet(
            "color: #666; font-size: 10px; padding: 5px; "
            "background-color: #f5f5f5; border-radius: 3px;"
        )
        self.discrete_preview.setWordWrap(True)
        self.discrete_preview.setMinimumHeight(40)
        discrete_layout.addWidget(self.discrete_preview, 1, 1)
        
        self.discrete_widget = QWidget()
        self.discrete_widget.setLayout(discrete_layout)
        
        # -- Continuous Mode Inputs --
        continuous_layout = QGridLayout()
        continuous_layout.setHorizontalSpacing(20)
        continuous_layout.setVerticalSpacing(6)
        continuous_layout.setContentsMargins(0, 0, 0, 0)
        
        # Initial speed
        label = QLabel("Initial speed (m/s):")
        label.setFont(label_font)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        continuous_layout.addWidget(label, 0, 0)
        
        self.continuous_initial = QLineEdit()
        self.continuous_initial.setText("5")

        self.continuous_initial.textChanged.connect(self.update_continuous_preview)
        continuous_layout.addWidget(self.continuous_initial, 0, 1)
        
        # Final speed
        label = QLabel("Final speed (m/s):")
        label.setFont(label_font)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        continuous_layout.addWidget(label, 1, 0)
        
        self.continuous_final = QLineEdit()
        self.continuous_final.setText("25")

        self.continuous_final.textChanged.connect(self.update_continuous_preview)
        continuous_layout.addWidget(self.continuous_final, 1, 1)
        
        # Speed increment
        label = QLabel("Speed increment (m/s):")
        label.setFont(label_font)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        continuous_layout.addWidget(label, 2, 0)
        
        self.continuous_increment = QLineEdit()
        self.continuous_increment.setText("5")

        self.continuous_increment.textChanged.connect(self.update_continuous_preview)
        continuous_layout.addWidget(self.continuous_increment, 2, 1)
        
        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setFont(label_font)
        preview_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        continuous_layout.addWidget(preview_label, 3, 0)
        
        self.continuous_preview = QLabel()
        self.continuous_preview.setStyleSheet(
            "color: #666; font-size: 10px; padding: 5px; "
            "background-color: #f5f5f5; border-radius: 3px;"
        )
        self.continuous_preview.setWordWrap(True)
        self.continuous_preview.setMinimumHeight(40)
        continuous_layout.addWidget(self.continuous_preview, 3, 1)
        
        self.continuous_widget = QWidget()
        self.continuous_widget.setLayout(continuous_layout)
        
        # Add widgets to container
        container_layout.addWidget(self.discrete_widget)
        container_layout.addWidget(self.continuous_widget)
        self.continuous_widget.hide()
        
        layout.addWidget(self.container)
    
    def on_mode_changed(self):
        """Handle mode switching"""
        if self.radio_discrete and self.radio_discrete.isChecked():
            self.discrete_widget.show()
            self.continuous_widget.hide()
        else:
            self.discrete_widget.hide()
            self.continuous_widget.show()
            self.update_continuous_preview()
    
    def update_discrete_preview(self):
        """Update discrete mode preview"""
        text = self.discrete_speeds.text().strip()
        if not text:
            self.discrete_preview.setText("(No values entered)")
            return
        
        try:
            values = [float(v.strip()) for v in text.split(',')]
            for v in values:
                if v < 0 or v > 100:
                    self.discrete_preview.setText("⚠ Values should be 0-100 m/s")
                    self.discrete_preview.setStyleSheet(
                        "color: #d9534f; font-size: 10px; padding: 5px; "
                        "background-color: #ffe6e6; border-radius: 3px;"
                    )
                    return
            
            preview = f"✓ {len(values)} speed(s): " + ", ".join(f"{v:.1f}" for v in values)
            self.discrete_preview.setText(preview)
            self.discrete_preview.setStyleSheet(
                "color: #27ae60; font-size: 10px; padding: 5px; "
                "background-color: #e8f5e9; border-radius: 3px;"
            )
        except ValueError:
            self.discrete_preview.setText("⚠ Invalid input format")
            self.discrete_preview.setStyleSheet(
                "color: #d9534f; font-size: 10px; padding: 5px; "
                "background-color: #ffe6e6; border-radius: 3px;"
            )
    
    def update_continuous_preview(self):
        """Update continuous mode preview"""
        try:
            initial = float(self.continuous_initial.text().strip() or 0)
            final = float(self.continuous_final.text().strip() or 0)
            increment = float(self.continuous_increment.text().strip() or 0)
            
            if increment <= 0:
                self.continuous_preview.setText("⚠ Increment must be > 0")
                self.continuous_preview.setStyleSheet(
                    "color: #d9534f; font-size: 10px; padding: 5px; "
                    "background-color: #ffe6e6; border-radius: 3px;"
                )
                return
            
            if initial > final:
                self.continuous_preview.setText("⚠ Initial must be ≤ Final")
                self.continuous_preview.setStyleSheet(
                    "color: #d9534f; font-size: 10px; padding: 5px; "
                    "background-color: #ffe6e6; border-radius: 3px;"
                )
                return
            
            speeds = []
            current = initial
            while current <= final + 1e-9:
                speeds.append(current)
                current += increment
            
            preview = f"✓ {len(speeds)} speed(s): " + ", ".join(f"{v:.1f}" for v in speeds[:8])
            if len(speeds) > 8:
                preview += f", ... ({len(speeds)} total)"
            
            self.continuous_preview.setText(preview)
            self.continuous_preview.setStyleSheet(
                "color: #27ae60; font-size: 10px; padding: 5px; "
                "background-color: #e8f5e9; border-radius: 3px;"
            )
        except ValueError:
            self.continuous_preview.setText("⚠ Invalid numeric input")
            self.continuous_preview.setStyleSheet(
                "color: #d9534f; font-size: 10px; padding: 5px; "
                "background-color: #ffe6e6; border-radius: 3px;"
            )
    
    def get_speed_values(self):
        """Get speed values based on current mode"""
        if self.radio_discrete and self.radio_discrete.isChecked():
            text = self.discrete_speeds.text().strip()
            if not text:
                raise ValueError("No speed values entered")
            try:
                values = [float(v.strip()) for v in text.split(',')]
                for v in values:
                    if v < 0 or v > 100:
                        raise ValueError(f"Speed {v} out of range (0-100)")
                return sorted(values)
            except ValueError as e:
                raise ValueError(f"Invalid discrete speeds: {str(e)}")
        else:
            try:
                initial = float(self.continuous_initial.text().strip())
                final = float(self.continuous_final.text().strip())
                increment = float(self.continuous_increment.text().strip())
                
                if increment <= 0:
                    raise ValueError("Increment must be > 0")
                if initial > final:
                    raise ValueError("Initial must be ≤ Final")
                
                speeds = []
                current = initial
                while current <= final + 1e-9:
                    speeds.append(round(current, 1))
                    current += increment
                return speeds
            except ValueError as e:
                raise ValueError(f"Invalid continuous speeds: {str(e)}")


#==============================================================
class InputPage(QWidget):
    """
    Input page with organized parameter groups using QGroupBox
    - Constants section
    - Speed Mode selection (top level)
    - Speed Input section (within group)
    - Hull Parameters section
    """
    
    parameters_changed       = Signal(dict)     # Signal to emit when parameters change
    material_combo_requested = Signal(str)      # Signal to emit when material combo changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the input page UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) 
        main_layout.setSpacing(10)
        # ============ Top Section: Speed Mode Selection (Standalone) ============
        mode_group = QGroupBox("Speed Configuration Mode")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #333;
                font-size: 14px;
            }
        """)
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(15, 15, 15, 15)
        mode_layout.setSpacing(30)
        self.mode_group = QButtonGroup()
        self.radio_discrete = QRadioButton("Discrete Mode (Multiple speeds)")
        self.radio_discrete.setChecked(True)
        self.radio_continuous = QRadioButton("Continuous Mode (Range with increment)")
        self.mode_group.addButton(self.radio_discrete, 0)
        self.mode_group.addButton(self.radio_continuous, 1)
        mode_layout.addWidget(self.radio_discrete)
        mode_layout.addWidget(self.radio_continuous)
        mode_layout.addStretch()
        main_layout.addWidget(mode_group)
        # ============ Middle Section: Constants + Speed (Side by Side) ============
        middle_h_layout = QHBoxLayout()
        middle_h_layout.setSpacing(15)
        # -- Left: Constants Group --
        constants_group = QGroupBox("Constants")
        constants_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #333;
                font-size: 14px;
            }
        """)
        constants_layout = QGridLayout(constants_group)
        constants_layout.setHorizontalSpacing(15)
        constants_layout.setVerticalSpacing(10)
        constants_layout.setContentsMargins(15, 15, 15, 15)
        material_label = QLabel("Material preset:")
        material_label_font = QFont("Times New Roman", 11)
        material_label.setFont(material_label_font)
        material_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        constants_layout.addWidget(material_label, 0, 0)
        self.material_combo = QComboBox()
        self.material_combo.addItems(["", "Fresh water (20 °C)", "Sea water (20 °C)"])
        self.material_combo.setFixedHeight(25)
        constants_layout.addWidget(self.material_combo, 0, 1)
        material_label.setObjectName("material_combo_label")
        self.material_combo.setObjectName("material_combo")
        self.material_combo.currentTextChanged.connect(self.material_combo_requested)
        constants_data = [
            ("Acceleration of gravity", "g", "m/s^2"),                  # Acceleration of gravity, g (m/s^2)
            ("Density of water", "\u03C1", "kg/m^3"),                   # Density of water, \rho, (kg/m^3)
            ("Kinematic viscosity of water", "\u03BD", "m^2/s")        # Kinematic viscousity of water, \nu (m^2/s)
        ]
        self.inputs = {}
        label_font = QFont("Times New Roman", 11)
        for idx, (name, symbol, unit) in enumerate(constants_data):
            row_idx = idx + 1
            label = QLabel(f"{name}, <i>{self.parse_unit(symbol)}</i> ({self.parse_unit(unit)}):")
            label.setFont(label_font)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            constants_layout.addWidget(label, row_idx, 0)
            input_field = QLineEdit()
            input_field.setClearButtonEnabled(True)
            constants_layout.addWidget(input_field, row_idx, 1)
            self.inputs[name.lower().replace(" ", "_")] = input_field
            if name == "Acceleration of gravity":
                input_field.setText("9.81")
        # -- Right: Speed Input Group --
        speed_group = QGroupBox("Speed Configuration")
        speed_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #333;
                font-size: 14px;
            }
        """)
        speed_group_layout = QVBoxLayout(speed_group)
        speed_group_layout.setContentsMargins(15, 15, 15, 15)
        speed_group_layout.setSpacing(10)
        self.speed_input = SpeedInputSection()
        self.speed_input.radio_discrete = self.radio_discrete
        self.speed_input.radio_continuous = self.radio_continuous
        self.radio_discrete.toggled.connect(self.speed_input.on_mode_changed)
        speed_group_layout.addWidget(self.speed_input)
        middle_h_layout.addWidget(constants_group, 1)
        middle_h_layout.addWidget(speed_group, 1)
        main_layout.addLayout(middle_h_layout)
        # ============ Hull Parameters Group ============
        hull_group = QGroupBox("Particulars of Hull")
        hull_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #333;
                font-size: 14px;
            }
        """)
        hull_layout = QGridLayout(hull_group)
        hull_layout.setHorizontalSpacing(15)
        hull_layout.setVerticalSpacing(10)
        hull_layout.setContentsMargins(15, 15, 15, 15)
        hull_params = [
            ("Ship length", "L", "m"),
            ("Ship beam", "B", "m"),
            ("Mean draft", "T_m", "m"),
            ("Displacement", "\u0394", "N"),
            ("Deadrise angle", "\u03B2", "\u00BA"),
            ("Frontal area of ship", "A_h", "m^2"),
            ("Longitudinal center of gravity", "LCG", "m"),
            ("Vertical center of gravity", "VCG", "m")
        ]
        for idx, (name, symbol, unit) in enumerate(hull_params):
            row = idx // 2
            col = (idx % 2) * 2
            label = QLabel(f"{name}, <i>{self.parse_unit(symbol)}</i> ({self.parse_unit(unit)}):")
            label.setFont(label_font)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            hull_layout.addWidget(label, row, col)
            input_field = QLineEdit()
            input_field.setClearButtonEnabled(True)
            hull_layout.addWidget(input_field, row, col + 1)
            self.inputs[name.lower().replace(" ", "_")] = input_field
        main_layout.addWidget(hull_group)
    
    def parse_unit(self, unit_text):
        """Convert unit text with ^ and _ to HTML format"""
        unit_text = re.sub(r'\^(\w+)', r'<sup>\1</sup>', unit_text)
        unit_text = re.sub(r'_(\w+)', r'<sub>\1</sub>', unit_text)
        return unit_text
    
    def reset_parameters(self):
        """Clear all input fields"""
        for widget in self.inputs.values():
            widget.clear()
        self.speed_input.discrete_speeds.clear()
        self.speed_input.continuous_initial.setText("5")
        self.speed_input.continuous_final.setText("25")
        self.speed_input.continuous_increment.setText("5")
    
    def perform_calculation(self):
        """Perform calculation and emit results"""
        try:
            # Get speed values
            speeds = self.speed_input.get_speed_values()
            
            # Collect all input values
            result = {
                "speeds": speeds,
                "speed_mode": "discrete" if self.radio_discrete.isChecked() else "continuous",
                "parameters": {}
            }
            
            # Add all other parameters
            for key, widget in self.inputs.items():
                try:
                    value = float(widget.text().strip() or 0)
                    result["parameters"][key] = value
                except ValueError:
                    result["parameters"][key] = None
            
            self.parameters_changed.emit(result)
            
            QMessageBox.information(
                self,
                "Success",
                f"Calculation completed!\n"
                f"Speed Mode: {result['speed_mode']}\n"
                f"Speed Values: {len(speeds)}"
            )
        
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Invalid input: {str(e)}")
    
    def update_ui_texts(self, lang_manager):
        """Update UI texts based on current language."""
        if not lang_manager:
            return
        
        # Update group box titles
        group_boxes = self.findChildren(QGroupBox)
        for gb in group_boxes:
            title = gb.title()
            if "Speed Configuration Mode" in title or "速度配置模式" in title:
                gb.setTitle(lang_manager.get_text("Speed Configuration Mode"))
            elif "Constants" in title or "常量" in title:
                gb.setTitle(lang_manager.get_text("Constants"))
            elif "Speed Configuration" in title or "速度配置" in title:
                gb.setTitle(lang_manager.get_text("Speed Configuration"))
            elif "Particulars of Hull" in title or "船体参数" in title:
                gb.setTitle(lang_manager.get_text("Particulars of Hull"))
        
        # Update material combo if it exists
        if hasattr(self, 'material_combo'):
            current_index = self.material_combo.currentIndex()
            self.material_combo.clear()
            materials = lang_manager.get_text("material_combo")
            if isinstance(materials, list):
                self.material_combo.addItems(materials)
                if current_index < self.material_combo.count():
                    self.material_combo.setCurrentIndex(current_index)
    # ----------------------------------------------------------------





#--------------------------------------------------------------
# Test code
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = InputPage()
    window.setWindowTitle("Input Page")
    window.resize(900, 800)
    window.show()
    
    window.parameters_changed.connect(lambda r: print(f"Result: {r}"))
    
    sys.exit(app.exec())
