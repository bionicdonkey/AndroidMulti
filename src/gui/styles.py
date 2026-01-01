import winreg
from PyQt6.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter, QPainterPath, QPen, QBrush, QTransform
from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtWidgets import QApplication

class ThemeStyles:
    # --- SAPPHIRE DARK PALETTE ---
    DARK_BG = "#12141d"           # Midnight
    DARK_SURFACE = "#1b1e2b"      # Deep Sapphire
    DARK_SURFACE_LIGHT = "#242938" # Muted Blue
    DARK_BORDER = "#2f354a"       # Soft border
    DARK_ACCENT = "#5d5fef"       # Indigo
    DARK_ACCENT_SOFT = "#4338ca"  
    DARK_TEXT = "#f1f5f9"         
    DARK_TEXT_DIM = "#94a3b8"     
    DARK_DANGER = "#ef4444"       
    DARK_SUCCESS = "#22c55e"      

    # --- ARCTIC LIGHT PALETTE ---
    LIGHT_BG = "#f5f7f9"          # Soft gray-white
    LIGHT_SURFACE = "#ffffff"     # White
    LIGHT_SURFACE_LIGHT = "#f1f5f9" # Slate 100
    LIGHT_BORDER = "#d1d9e6"      # Soft blue-gray border
    LIGHT_ACCENT = "#3b82f6"      # Modern Blue
    LIGHT_ACCENT_SOFT = "#2563eb" 
    LIGHT_TEXT = "#1a202c"        # Deep slate text
    LIGHT_TEXT_DIM = "#718096"    # Muted Slate
    LIGHT_DANGER = "#e53e3e"      
    LIGHT_SUCCESS = "#38a169"     

    @staticmethod
    def is_dark_mode(preference="auto"):
        """Detect theme based on preference and Windows registry."""
        if preference == "dark":
            return True
        if preference == "light":
            return False
            
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except Exception:
            return True

    @classmethod
    def apply_theme(cls, app: QApplication, preference="auto"):
        """Apply theme and force consistent style engine"""
        is_dark = cls.is_dark_mode(preference)
        app.setStyle("Fusion")
        
        palette = app.palette()
        if is_dark:
            palette.setColor(QPalette.ColorRole.Window, QColor(cls.DARK_BG))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.DARK_TEXT))
            palette.setColor(QPalette.ColorRole.Base, QColor(cls.DARK_SURFACE))
            palette.setColor(QPalette.ColorRole.Button, QColor(cls.DARK_SURFACE))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.DARK_TEXT))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.DARK_ACCENT))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(cls.LIGHT_BG))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.LIGHT_TEXT))
            palette.setColor(QPalette.ColorRole.Base, QColor(cls.LIGHT_SURFACE))
            palette.setColor(QPalette.ColorRole.Button, QColor(cls.LIGHT_SURFACE))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.LIGHT_TEXT))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.LIGHT_ACCENT))
        
        app.setPalette(palette)
        app.setStyleSheet(cls.get_style_sheet(is_dark))

    @classmethod
    def get_style_sheet(cls, dark=True):
        bg = cls.DARK_BG if dark else cls.LIGHT_BG
        surface = cls.DARK_SURFACE if dark else cls.LIGHT_SURFACE
        surface_light = cls.DARK_SURFACE_LIGHT if dark else cls.LIGHT_SURFACE_LIGHT
        text = cls.DARK_TEXT if dark else cls.LIGHT_TEXT
        text_dim = cls.DARK_TEXT_DIM if dark else cls.LIGHT_TEXT_DIM
        accent = cls.DARK_ACCENT if dark else cls.LIGHT_ACCENT
        accent_soft = cls.DARK_ACCENT_SOFT if dark else cls.LIGHT_ACCENT_SOFT
        border = cls.DARK_BORDER if dark else cls.LIGHT_BORDER
        danger = cls.DARK_DANGER if dark else cls.LIGHT_DANGER
        success = cls.DARK_SUCCESS if dark else cls.LIGHT_SUCCESS

        # Pre-calculating hover tints for robust cross-platform rendering
        def get_rgba_tint(hex_color, alpha=0.12):
            c = QColor(hex_color)
            return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"

        accent_hover_bg = get_rgba_tint(accent)
        danger_hover_bg = get_rgba_tint(danger)

        # SVG Escaping for data URIs
        svg_text_dim = text_dim.replace("#", "%23")
        svg_accent = accent.replace("#", "%23")

        # Base64 encoded SVGs for maximum reliability
        import base64
        def get_b64_svg(path_d, color):
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><path d="{path_d}" fill="{color}"/></svg>'
            return base64.b64encode(svg.encode()).decode()

        svg_up = get_b64_svg("M5 2L1 8h8z", text_dim)
        svg_up_hover = get_b64_svg("M5 2L1 8h8z", accent)
        svg_down = get_b64_svg("M5 8L1 2h8z", text_dim)
        svg_down_hover = get_b64_svg("M5 8L1 2h8z", accent)
        svg_check = get_b64_svg("M2 5l2 2 4-4", "#ffffff")
        svg_radio_dot = get_b64_svg("M5 3a2 2 0 100 4 2 2 0 000-4z", "#ffffff")

        return f"""
            /* Global Container Defaults */
            QMainWindow, QDialog, QWidget#centralWidget {{
                background-color: {bg};
                color: {text};
                font-family: 'Segoe UI', system-ui, sans-serif;
            }}

            QWidget {{
                color: {text};
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 13px;
                outline: none;
            }}

            /* Headers & Typography */
            QLabel {{
                background-color: transparent;
            }}
            QDialog QLabel {{
                padding-top: 5px; /* Vertical alignment for form fields in dialogs */
            }}
            QLabel#titleLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {text};
                padding: 5px 0 15px 0;
            }}

            /* Tables */
            QTableWidget {{
                background-color: {surface};
                gridline-color: {border};
                border: 1px solid {border};
                border-radius: 10px;
                selection-background-color: {surface_light};
                selection-color: {text};
                padding: 2px;
            }}
            QHeaderView::section {{
                background-color: {surface_light};
                color: {text_dim};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {border};
                font-weight: bold;
                text-transform: uppercase;
                font-size: 10px;
            }}
            QHeaderView::section:vertical {{
                border-bottom: 1px solid {border};
                border-right: 1px solid {border};
                padding: 5px 10px;
                min-width: 40px;
            }}
            QTableWidget::item {{
                padding: 10px;
            }}

            /* TABS */
            QTabWidget {{
                border: none;
            }}
            QTabWidget::tab-bar {{
                left: 10px;
            }}
            QTabWidget::pane {{
                border: 1px solid {border};
                background: {surface};
                border-radius: 10px;
                top: -1px;
                padding: 0px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {text_dim};
                padding: 12px 24px;
                margin-right: 4px;
                border-bottom: 3px solid transparent;
                font-weight: bold;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                color: {accent};
                background: {surface};
                border-bottom: 3px solid {accent};
            }}

            /* Buttons */
            QPushButton {{
                background-color: {surface};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 600;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background-color: {surface_light};
                border-color: {text_dim};
            }}
            QPushButton:disabled {{
                color: {text_dim};
                background-color: {surface};
                border: 1px solid {border};
            }}
            QPushButton#primaryButton {{
                background-color: transparent;
                color: {accent};
                border: 1px solid {accent};
            }}
            QPushButton#primaryButton:hover {{
                background-color: {accent_hover_bg};
                border-color: {accent_soft};
            }}
            QPushButton#primaryButton:disabled {{
                color: {text_dim};
                border: 1px solid {border};
            }}
            QPushButton#dangerButton {{
                background-color: transparent;
                color: {danger};
                border: 1px solid {danger};
            }}
            QPushButton#dangerButton:hover {{
                background-color: {danger_hover_bg};
                border-color: {danger};
            }}
            QPushButton#dangerButton:disabled {{
                color: {text_dim};
                border: 1px solid {border};
            }}

            /* Inputs */
            QLineEdit, QComboBox, QTextEdit {{
                background-color: {surface_light};
                border: 2px solid {border};
                border-radius: 8px;
                padding: 10px 12px;
                color: {text};
                min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border-color: {accent};
            }}

            /* PremiumSpinBox Wrapper Styling */
            QWidget#spinBoxContainer {{
                background-color: {surface_light};
                border: 2px solid {border};
                border-radius: 8px;
                min-height: 20px;
            }}
            QWidget#spinBoxContainer:focus-within {{
                border-color: {accent};
            }}
            QLineEdit#spinBoxEdit {{
                background: transparent;
                border: none;
                padding: 10px;
                color: {text};
            }}
            QWidget#spinBoxButtons {{
                border-left: 1px solid {border};
            }}
            QPushButton#spinBoxUp, QPushButton#spinBoxDown {{
                background-color: transparent;
                border: none;
                margin: 0;
                padding: 0;
                color: {text_dim};
                font-size: 7px;
                border-radius: 0;
                margin-right: 1px;
            }}
            QPushButton#spinBoxUp {{
                border-top-right-radius: 5px;
                border-bottom: 1px solid {border};
                border-left: 1px solid {border};
                margin-top: 1px;
            }}
            QPushButton#spinBoxDown {{
                border-bottom-right-radius: 5px;
                border-left: 1px solid {border};
                margin-bottom: 1px;
            }}
            QPushButton#spinBoxUp:hover, QPushButton#spinBoxDown:hover {{
                background-color: {surface};
                color: {accent};
            }}

            /* Native SpinBox Fallback (Simplified) */
            QSpinBox {{
                background-color: {surface_light};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0;
                height: 0;
                border: none;
            }}

            /* Checkboxes & Radios */
            QCheckBox, QRadioButton {{
                spacing: 12px;
                background: transparent;
            }}
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {border};
                background-color: {surface_light};
                border-radius: 5px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                image: url("data:image/svg+xml;base64,{svg_check}");
            }}
            QRadioButton::indicator {{
                border-radius: 10px;
                border: 2px solid {border};
            }}
            QRadioButton::indicator:checked {{
                background-color: {accent};
                border: 2px solid {accent};
                image: url("data:image/svg+xml;base64,{svg_radio_dot}");
            }}
            QRadioButton::indicator:hover {{
                border-color: {accent};
            }}

            /* Group Box */
            QGroupBox {{
                border: 2px solid {border};
                border-radius: 12px;
                margin-top: 30px;
                padding-top: 6px;
                font-weight: bold;
                background-color: {surface};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                top: 5px;
                padding: 0 10px;
                color: {accent};
            }}

            /* Collapsible Sidebar */
            QPushButton#sidebarHandle {{
                background-color: {surface};
                border: 1px solid {border};
                border-radius: 6px;
                color: {accent};
                font-weight: bold;
                font-size: 10px;
                padding: 10px 0;
            }}
            QPushButton#sidebarHandle:hover {{
                background-color: {accent};
                color: #ffffff;
            }}
            QLabel#sidebarTitle {{
                color: {accent};
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }}
            QWidget#sidebarContent {{
                background-color: transparent;
            }}

            /* Logs Dashboard */
            QTextEdit#logView {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 10px;
                min-height: 150px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }}
        """

class VectorIcon:
    """Refined utility to generate professional QIcons using QPainter paths"""
    
    @staticmethod
    def get_icon(name: str, color: QColor, size: int = 24) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        
        path = QPainterPath()
        s = float(size)
        
        if name == "play":
            # Better weighted triangle
            path.moveTo(s * 0.32, s * 0.22)
            path.lineTo(s * 0.82, s * 0.5)
            path.lineTo(s * 0.32, s * 0.78)
            path.closeSubpath()
            
        elif name == "stop":
            # Balanced square with rounded corners
            path.addRoundedRect(QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56), s * 0.1, s * 0.1)
            
        elif name == "refresh":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(color, s * 0.1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            rect = QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64)
            path.arcMoveTo(rect, 45)
            path.arcTo(rect, 45, 275)
            painter.drawPath(path)
            
            # Use separate path for arrow head to avoid stroke issues
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            head = QPainterPath()
            head.moveTo(s * 0.62, s * 0.02)
            head.lineTo(s * 0.98, s * 0.25)
            head.lineTo(s * 0.68, s * 0.52)
            path = head
            
        elif name == "plus":
            w = s * 0.12
            path.addRect(QRectF((s - w)/2, s * 0.22, w, s * 0.56))
            path.addRect(QRectF(s * 0.22, (s - w)/2, s * 0.56, w))
            
        elif name == "settings":
            # Professional Gear: center hole and teeth
            outer_r = s * 0.38
            inner_r = s * 0.22
            hole_r = s * 0.12
            
            # Teeth
            for i in range(8):
                angle = i * 45
                p = QPainterPath()
                # Tooth shape
                p.addRoundedRect(QRectF((s - s*0.14)/2, s * 0.05, s*0.14, s*0.25), s*0.05, s*0.05)
                painter.save()
                painter.translate(s/2, s/2)
                painter.rotate(angle)
                painter.translate(-s/2, -s/2)
                painter.drawPath(p)
                painter.restore()
            
            # Core circle
            path.addEllipse(QRectF((s - outer_r*2)/2, (s - outer_r*2)/2, outer_r*2, outer_r*2))
            # Subtract inner hole
            hole = QPainterPath()
            hole.addEllipse(QRectF((s - hole_r*2)/2, (s - hole_r*2)/2, hole_r*2, hole_r*2))
            path = path.subtracted(hole)
            
        elif name == "trash":
            # Clean Bin Icon
            path.addRoundedRect(QRectF(s*0.28, s*0.3, s*0.44, s*0.58), s*0.05, s*0.05)
            path.addRect(QRectF(s*0.22, s*0.22, s*0.56, s*0.08))
            path.addRoundedRect(QRectF(s*0.4, s*0.14, s*0.2, s*0.08), s*0.02, s*0.02)
            
        elif name == "tools":
            # Hammer Icon
            # Hammer head (rectangle)
            head = QPainterPath()
            head.addRoundedRect(QRectF(s*0.2, s*0.1, s*0.6, s*0.35), s*0.05, s*0.05)
            path.addPath(head)
            
            # Handle (long thin rectangle)
            handle = QPainterPath()
            handle.addRoundedRect(QRectF(s*0.42, s*0.4, s*0.16, s*0.55), s*0.05, s*0.05)
            path.addPath(handle)
            
        elif name == "shield":
            # Root Shield
            path.moveTo(s*0.5, s*0.12)
            path.lineTo(s*0.82, s*0.22)
            path.lineTo(s*0.82, s*0.5)
            path.arcTo(QRectF(s*0.18, s*0.2, s*0.64, s*0.7), 0, -180)
            path.closeSubpath()
            
        elif name == "box-arrow":
            # Sideload/APK
            path.addRect(QRectF(s*0.2, s*0.4, s*0.6, s*0.45))
            path.moveTo(s*0.5, s*0.05)
            path.lineTo(s*0.75, s*0.35)
            path.lineTo(s*0.55, s*0.35)
            path.lineTo(s*0.55, s*0.55)
            path.lineTo(s*0.45, s*0.55)
            path.lineTo(s*0.45, s*0.35)
            path.lineTo(s*0.25, s*0.35)
            path.closeSubpath()
            
        elif name == "file-push":
            # Push File
            path.addRoundedRect(QRectF(s*0.2, s*0.2, s*0.45, s*0.6), s*0.05, s*0.05)
            # Arrow
            head = QPainterPath()
            head.moveTo(s*0.6, s*0.4)
            head.lineTo(s*0.9, s*0.1)
            head.lineTo(s*0.9, s*0.35)
            head.moveTo(s*0.9, s*0.1)
            head.lineTo(s*0.65, s*0.1)
            path.addPath(head)
            
        elif name == "user":
            # Account Setup
            path.addEllipse(QRectF(s*0.35, s*0.15, s*0.3, s*0.3))
            # Shoulder arc
            shoulder = QPainterPath()
            shoulder.moveTo(s*0.15, s*0.9)
            shoulder.arcTo(QRectF(s*0.15, s*0.55, s*0.7, s*0.7), 180, -180)
            shoulder.closeSubpath()
            path.addPath(shoulder)
        
        elif name == "edit":
            # Pencil/Edit Icon - Simple and clean
            # Pencil tip (triangle)
            tip = QPainterPath()
            tip.moveTo(s*0.1, s*0.9)
            tip.lineTo(s*0.18, s*0.82)
            tip.lineTo(s*0.18, s*0.98)
            tip.closeSubpath()
            path.addPath(tip)
            
            # Pencil body (rectangle rotated)
            body_trans = QTransform()
            body_trans.translate(s*0.5, s*0.5)
            body_trans.rotate(-45)
            body_trans.translate(-s*0.5, -s*0.5)
            
            body = QPainterPath()
            body.addRoundedRect(QRectF(s*0.15, s*0.3, s*0.7, s*0.15), s*0.05, s*0.05)
            path.addPath(body_trans.map(body))
        
        painter.drawPath(path)
        painter.end()
        return QIcon(pixmap)
