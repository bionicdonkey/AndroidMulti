"""Custom UI widgets for a premium experience"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIntValidator

class PremiumSpinBox(QWidget):
    """
    A custom SpinBox implementation that avoids native rendering bugs 
    by using standard LineEdit and PushButtons.
    """
    valueChanged = pyqtSignal(int)
    
    def __init__(self, parent=None, min_val=0, max_val=99999, initial_val=0):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        
        self.init_ui()
        
    def init_ui(self):
        # Main horizontal layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Container to mimic the LineEdit look
        self.container = QWidget()
        self.container.setObjectName("spinBoxContainer")
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(1, 1, 1, 1) # Space for border
        self.container_layout.setSpacing(0)
        
        # Input field
        self.line_edit = QLineEdit(str(self.value))
        self.line_edit.setObjectName("spinBoxEdit")
        self.line_edit.setFrame(False)
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_edit.setValidator(QIntValidator(self.min_val, self.max_val))
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.container_layout.addWidget(self.line_edit)
        
        # Button container
        btn_container = QWidget()
        btn_container.setObjectName("spinBoxButtons")
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        
        self.up_btn = QPushButton("▲")
        self.up_btn.setObjectName("spinBoxUp")
        self.up_btn.setFixedWidth(24)
        self.up_btn.clicked.connect(self.increment)
        
        self.down_btn = QPushButton("▼")
        self.down_btn.setObjectName("spinBoxDown")
        self.down_btn.setFixedWidth(24)
        self.down_btn.clicked.connect(self.decrement)
        
        btn_layout.addWidget(self.up_btn)
        btn_layout.addWidget(self.down_btn)
        
        self.container_layout.addWidget(btn_container)
        self.main_layout.addWidget(self.container)
        
    def _on_text_changed(self, text):
        if not text:
            return
        try:
            val = int(text)
            if self.min_val <= val <= self.max_val:
                self.value = val
                self.valueChanged.emit(self.value)
        except ValueError:
            pass

    def setValue(self, value):
        val = max(self.min_val, min(self.max_val, value))
        self.value = val
        self.line_edit.setText(str(val))
        self.valueChanged.emit(self.value)
        
    def getValue(self):
        return self.value
        
    def value(self):
        """QSpinBox compatibility"""
        return self.value
        
    def setRange(self, min_val, max_val):
        """QSpinBox compatibility"""
        self.min_val = min_val
        self.max_val = max_val
        self.line_edit.setValidator(QIntValidator(self.min_val, self.max_val))
        self.setValue(self.value)

    def setSingleStep(self, step):
        """QSpinBox compatibility (stub)"""
        self.step = step

    def setSuffix(self, suffix):
        """QSpinBox compatibility (stub visually)"""
        # We could add a label inside for the suffix if needed
        pass
        
    def increment(self):
        step = getattr(self, 'step', 1)
        self.setValue(self.value + step)
        
    def decrement(self):
        step = getattr(self, 'step', 1)
        self.setValue(self.value - step)

class CollapsiblePanel(QWidget):
    """
    A collapsible panel with a title bar and toggle button.
    """
    def __init__(self, title="", parent=None, collapsed=True):
        super().__init__(parent)
        self.is_collapsed = collapsed
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        self.header = QWidget()
        self.header.setObjectName("collapsibleHeader")
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(10, 5, 10, 5)
        
        self.title_label = QPushButton(title)
        self.title_label.setObjectName("collapsibleTitle")
        self.title_label.setFlat(True)
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_label.clicked.connect(self.toggle)
        self.header_layout.addWidget(self.title_label)
        
        self.header_layout.addStretch()
        
        self.toggle_btn = QPushButton(self._get_toggle_icon())
        self.toggle_btn.setFixedWidth(30)
        self.toggle_btn.setObjectName("collapsibleToggle")
        self.toggle_btn.clicked.connect(self.toggle)
        self.header_layout.addWidget(self.toggle_btn)
        
        self.main_layout.addWidget(self.header)
        
        # Content area
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 10, 0, 0)
        self.main_layout.addWidget(self.content)
        
        if self.is_collapsed:
            self.content.hide()

    def _get_toggle_icon(self):
        return "▶️" if self.is_collapsed else "▼"

    def toggle(self):
        self.is_collapsed = not self.is_collapsed
        self.content.setVisible(not self.is_collapsed)
        self.toggle_btn.setText(self._get_toggle_icon())
        
    def addWidget(self, widget):
        self.content_layout.addWidget(widget)
        
    def setLayout(self, layout):
        self.content.setLayout(layout)

class CollapsibleSidebar(QWidget):
    """
    A right-side collapsible sidebar with a vertical toggle handle.
    """
    toggled = pyqtSignal(bool)
    
    def __init__(self, title="", parent=None, collapsed=True, min_content_width=300):
        super().__init__(parent)
        self.is_collapsed = collapsed
        self.min_content_width = min_content_width
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Toggle Handle (Vertical)
        self.handle = QPushButton()
        self.handle.setObjectName("sidebarHandle")
        self.handle.setFixedWidth(24)
        self.handle.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )
        self.handle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.handle.setText("◀\n\nA\nV\nD\ns\n\n◀" if self.is_collapsed else "▶\n\nA\nV\nD\ns\n\n▶")
        self.handle.clicked.connect(self.toggle)
        self.main_layout.addWidget(self.handle)
        
        # Content Panel
        self.content_container = QWidget()
        self.content_container.setObjectName("sidebarContent")
        self.content_container.setMinimumWidth(self.min_content_width)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(10, 0, 0, 0)
        
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("sidebarTitle")
            self.content_layout.addWidget(title_label)
            
        self.main_layout.addWidget(self.content_container)
        
        # Initialize visibility and constraint
        if self.is_collapsed:
            self.content_container.hide()
            self.setMaximumWidth(24)
        else:
            self.setMaximumWidth(16777215)

    def toggle(self):
        self.is_collapsed = not self.is_collapsed
        self.content_container.setVisible(not self.is_collapsed)
        self.handle.setText("◀\n\nA\nV\nD\ns\n\n◀" if self.is_collapsed else "▶\n\nA\nV\nD\ns\n\n▶")
        
        if self.is_collapsed:
            self.setMaximumWidth(24)
        else:
            self.setMaximumWidth(16777215)
            
        self.toggled.emit(self.is_collapsed)

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)
