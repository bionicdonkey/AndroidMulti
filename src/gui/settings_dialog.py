"""Settings dialog for configuring Android SDK paths and other settings"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QGroupBox, QFormLayout,
    QSpinBox, QCheckBox, QTabWidget, QWidget, QComboBox
)
from PyQt6.QtCore import Qt

from ..config_manager import ConfigManager
from .styles import ThemeStyles
from .widgets import PremiumSpinBox


class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""
    
    def __init__(self, parent, config: ConfigManager):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Tab widget for different setting categories
        tabs = QTabWidget()
        # Ensure it matches the main window style
        tabs.setDocumentMode(False)
        
        # Android SDK Settings Tab
        sdk_tab = QWidget()
        sdk_layout = QVBoxLayout()
        sdk_layout.setSpacing(15)
        
        sdk_group = QGroupBox("Android SDK Paths")
        sdk_form = QFormLayout()
        sdk_form.setSpacing(15)
        sdk_form.setContentsMargins(20, 30, 20, 20)
        sdk_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        sdk_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # SDK Root
        sdk_root_layout = QHBoxLayout()
        self.sdk_root_edit = QLineEdit()
        self.sdk_root_edit.setPlaceholderText("Auto-detected from ANDROID_SDK_ROOT or ANDROID_HOME")
        sdk_root_browse = QPushButton("Browse...")
        sdk_root_browse.clicked.connect(lambda: self.browse_path(self.sdk_root_edit, True))
        sdk_root_layout.addWidget(self.sdk_root_edit)
        sdk_root_layout.addWidget(sdk_root_browse)
        sdk_form.addRow("SDK Root:", sdk_root_layout)
        
        # Emulator path
        emulator_layout = QHBoxLayout()
        self.emulator_edit = QLineEdit()
        self.emulator_edit.setPlaceholderText("Path to emulator.exe")
        emulator_browse = QPushButton("Browse...")
        emulator_browse.clicked.connect(lambda: self.browse_file(self.emulator_edit, "emulator.exe"))
        emulator_layout.addWidget(self.emulator_edit)
        emulator_layout.addWidget(emulator_browse)
        sdk_form.addRow("Emulator:", emulator_layout)
        
        # ADB path
        adb_layout = QHBoxLayout()
        self.adb_edit = QLineEdit()
        self.adb_edit.setPlaceholderText("Path to adb.exe")
        adb_browse = QPushButton("Browse...")
        adb_browse.clicked.connect(lambda: self.browse_file(self.adb_edit, "adb.exe"))
        adb_layout.addWidget(self.adb_edit)
        adb_layout.addWidget(adb_browse)
        sdk_form.addRow("ADB:", adb_layout)
        
        # AVD Manager path
        avd_layout = QHBoxLayout()
        self.avd_edit = QLineEdit()
        self.avd_edit.setPlaceholderText("Path to avdmanager.bat")
        avd_browse = QPushButton("Browse...")
        avd_browse.clicked.connect(lambda: self.browse_file(self.avd_edit, "avdmanager.bat"))
        avd_layout.addWidget(self.avd_edit)
        avd_layout.addWidget(avd_browse)
        sdk_form.addRow("AVD Manager:", avd_layout)
        
        # Auto-detect button
        sdk_btn_layout = QHBoxLayout()

        auto_detect_btn = QPushButton("🔄 Auto-detect SDK Paths")
        auto_detect_btn.clicked.connect(self.auto_detect_paths)
        sdk_btn_layout.addWidget(auto_detect_btn)

        test_btn = QPushButton("Test Paths")
        test_btn.clicked.connect(self.test_paths)
        sdk_btn_layout.addWidget(test_btn)

        sdk_form.addRow("", sdk_btn_layout)
        
        sdk_group.setLayout(sdk_form)
        sdk_layout.addWidget(sdk_group)
        sdk_layout.addStretch()
        sdk_tab.setLayout(sdk_layout)
        
        # Emulator Settings Tab
        emulator_tab = QWidget()
        emulator_layout = QVBoxLayout()
        emulator_layout.setSpacing(15)
        
        emulator_group = QGroupBox("Default Emulator Settings")
        emulator_form = QFormLayout()
        emulator_form.setSpacing(15)
        emulator_form.setContentsMargins(15, 20, 15, 15)
        
        # Hardware acceleration
        self.hw_accel_checkbox = QCheckBox()
        self.hw_accel_checkbox.setChecked(True)
        emulator_form.addRow("Hardware Acceleration:", self.hw_accel_checkbox)
        
        # Default RAM
        self.ram_spin = PremiumSpinBox()
        self.ram_spin.setRange(512, 16384)
        self.ram_spin.setSuffix(" MB")
        self.ram_spin.setSingleStep(512)
        emulator_form.addRow("Default RAM:", self.ram_spin)
        
        # Default VM Heap
        self.vm_heap_spin = PremiumSpinBox()
        self.vm_heap_spin.setRange(16, 512)
        self.vm_heap_spin.setSuffix(" MB")
        self.vm_heap_spin.setSingleStep(16)
        emulator_form.addRow("Default VM Heap:", self.vm_heap_spin)
        
        emulator_group.setLayout(emulator_form)
        emulator_layout.addWidget(emulator_group)
        emulator_layout.addStretch()
        emulator_tab.setLayout(emulator_layout)
        
        # Input Sync Settings Tab
        sync_tab = QWidget()
        sync_layout = QVBoxLayout()
        sync_layout.setSpacing(15)
        
        sync_group = QGroupBox("Input Synchronization")
        sync_form = QFormLayout()
        sync_form.setSpacing(15)
        sync_form.setContentsMargins(15, 20, 15, 15)
        
        # Sync delay
        self.sync_delay_spin = PremiumSpinBox()
        self.sync_delay_spin.setRange(0, 1000)
        self.sync_delay_spin.setSuffix(" ms")
        sync_form.addRow("Sync Delay:", self.sync_delay_spin)
        
        # Sync options
        self.sync_touch_checkbox = QCheckBox()
        self.sync_touch_checkbox.setChecked(True)
        sync_form.addRow("Sync Touch:", self.sync_touch_checkbox)
        
        self.sync_keyboard_checkbox = QCheckBox()
        self.sync_keyboard_checkbox.setChecked(True)
        sync_form.addRow("Sync Keyboard:", self.sync_keyboard_checkbox)
        
        self.sync_scroll_checkbox = QCheckBox()
        self.sync_scroll_checkbox.setChecked(True)
        sync_form.addRow("Sync Scroll:", self.sync_scroll_checkbox)
        
        sync_group.setLayout(sync_form)
        sync_layout.addWidget(sync_group)
        sync_layout.addStretch()
        sync_tab.setLayout(sync_layout)
        
        # Appearance Settings Tab
        ui_tab = QWidget()
        ui_layout = QVBoxLayout()
        ui_layout.setSpacing(15)
        
        ui_group = QGroupBox("Appearance")
        ui_form = QFormLayout()
        ui_form.setSpacing(15)
        ui_form.setContentsMargins(20, 30, 20, 20)
        ui_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Auto (System)", "auto")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.setMinimumWidth(150)
        ui_form.addRow("Application Theme:", self.theme_combo)
        
        ui_group.setLayout(ui_form)
        ui_layout.addWidget(ui_group)
        ui_layout.addStretch()
        ui_tab.setLayout(ui_layout)
        
        # Add tabs
        tabs.addTab(sdk_tab, "Android SDK")
        tabs.addTab(emulator_tab, "Emulator")
        tabs.addTab(sync_tab, "Input Sync")
        tabs.addTab(ui_tab, "Appearance")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
               
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def browse_path(self, line_edit: QLineEdit, is_directory: bool = True):
        """Browse for a path"""
        current_path = line_edit.text() or str(Path.home())
        
        if is_directory:
            path = QFileDialog.getExistingDirectory(self, "Select Directory", current_path)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", current_path)
        
        if path:
            line_edit.setText(path)
    
    def browse_file(self, line_edit: QLineEdit, filter_name: str = ""):
        """Browse for a file"""
        current_path = line_edit.text() or str(Path.home())
        filter_str = f"{filter_name} (*{Path(filter_name).suffix});;All Files (*.*)" if filter_name else "All Files (*.*)"
        
        path, _ = QFileDialog.getOpenFileName(self, f"Select {filter_name}", current_path, filter_str)
        
        if path:
            line_edit.setText(path)
    
    def auto_detect_paths(self):
        """Auto-detect Android SDK paths"""
        # Trigger auto-detection on existing config
        self.config._detect_android_sdk()
        
        # Update UI with detected paths
        sdk_root = self.config.config.get('android_sdk', {}).get('root', '')
        emulator = self.config.config.get('android_sdk', {}).get('emulator', '')
        adb = self.config.config.get('android_sdk', {}).get('adb', '')
        avd_manager = self.config.config.get('android_sdk', {}).get('avd_manager', '')
        
        if sdk_root:
            self.sdk_root_edit.setText(sdk_root)
        if emulator:
            self.emulator_edit.setText(emulator)
        if adb:
            self.adb_edit.setText(adb)
        if avd_manager:
            self.avd_edit.setText(avd_manager)
        
        if sdk_root or emulator or adb:
            QMessageBox.information(self, "Auto-detection", "Android SDK paths have been auto-detected!")
        else:
            QMessageBox.warning(self, "Auto-detection", "Could not auto-detect Android SDK paths.\nPlease set them manually.")
    
    def test_paths(self):
        """Test if the configured paths are valid"""
        errors = []
        
        if self.emulator_edit.text() and not Path(self.emulator_edit.text()).exists():
            errors.append(f"Emulator path not found: {self.emulator_edit.text()}")
        
        if self.adb_edit.text() and not Path(self.adb_edit.text()).exists():
            errors.append(f"ADB path not found: {self.adb_edit.text()}")
        
        if self.avd_edit.text() and not Path(self.avd_edit.text()).exists():
            errors.append(f"AVD Manager path not found: {self.avd_edit.text()}")
        
        if errors:
            QMessageBox.warning(self, "Path Validation", "Some paths are invalid:\n\n" + "\n".join(errors))
        else:
            QMessageBox.information(self, "Path Validation", "All configured paths are valid!")
    
    def load_settings(self):
        """Load current settings into the UI"""
        # SDK paths
        sdk_config = self.config.config.get('android_sdk', {})
        self.sdk_root_edit.setText(sdk_config.get('root', ''))
        self.emulator_edit.setText(sdk_config.get('emulator', ''))
        self.adb_edit.setText(sdk_config.get('adb', ''))
        self.avd_edit.setText(sdk_config.get('avd_manager', ''))
        
        # Emulator settings
        emulator_config = self.config.config.get('emulator', {})
        self.hw_accel_checkbox.setChecked(emulator_config.get('hardware_acceleration', True))
        self.ram_spin.setValue(emulator_config.get('default_ram', 2048))
        self.vm_heap_spin.setValue(emulator_config.get('default_vm_heap', 256))
        
        # Input sync settings
        sync_config = self.config.config.get('input_sync', {})
        self.sync_delay_spin.setValue(sync_config.get('delay_ms', 0))
        self.sync_touch_checkbox.setChecked(sync_config.get('sync_touch', True))
        self.sync_keyboard_checkbox.setChecked(sync_config.get('sync_keyboard', True))
        self.sync_scroll_checkbox.setChecked(sync_config.get('sync_scroll', True))
        
        # UI settings
        ui_config = self.config.config.get('ui', {})
        theme = ui_config.get('theme', 'auto')
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
    
    def accept(self):
        """Save settings and close dialog"""
        # Save SDK paths
        self.config.config.setdefault('android_sdk', {})['root'] = self.sdk_root_edit.text()
        self.config.config.setdefault('android_sdk', {})['emulator'] = self.emulator_edit.text()
        self.config.config.setdefault('android_sdk', {})['adb'] = self.adb_edit.text()
        self.config.config.setdefault('android_sdk', {})['avd_manager'] = self.avd_edit.text()
        
        # Save emulator settings
        self.config.config.setdefault('emulator', {})['hardware_acceleration'] = self.hw_accel_checkbox.isChecked()
        self.config.config.setdefault('emulator', {})['default_ram'] = self.ram_spin.value()
        self.config.config.setdefault('emulator', {})['default_vm_heap'] = self.vm_heap_spin.value()
        
        # Save input sync settings
        self.config.config.setdefault('input_sync', {})['delay_ms'] = self.sync_delay_spin.value()
        self.config.config.setdefault('input_sync', {})['sync_touch'] = self.sync_touch_checkbox.isChecked()
        self.config.config.setdefault('input_sync', {})['sync_keyboard'] = self.sync_keyboard_checkbox.isChecked()
        self.config.config.setdefault('input_sync', {})['sync_scroll'] = self.sync_scroll_checkbox.isChecked()
        
        # Save UI settings
        self.config.config.setdefault('ui', {})['theme'] = self.theme_combo.currentData()
        
        # Save to file
        self.config.save_config()
        
        # Re-initialize emulator manager with new paths
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if hasattr(app, 'settings_changed'):
            app.settings_changed.emit()
        
        super().accept()
