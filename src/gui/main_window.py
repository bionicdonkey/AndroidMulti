"""Main GUI window for Android Multi-Emulator Manager"""

import sys
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QComboBox, QCheckBox,
    QGroupBox, QMessageBox, QDialog, QLineEdit, QSpinBox, QProgressDialog,
    QTabWidget, QSplitter, QTextEdit, QStatusBar, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QAction

from ..config_manager import ConfigManager
from ..emulator_manager import EmulatorManager, EmulatorInstance, EmulatorState
from ..input_synchronizer import InputSynchronizer
from ..logger import AppLogger, get_logger
from .emulator_worker import EmulatorCreationWorker
from .automation_dialog import AutomationDialog
from .settings_dialog import SettingsDialog
from .styles import ThemeStyles, VectorIcon
from .widgets import PremiumSpinBox, CollapsibleSidebar


class EmulatorRefreshThread(QThread):
    """Background thread for refreshing emulator states"""
    refreshed = pyqtSignal()
    
    def __init__(self, emulator_manager: EmulatorManager):
        super().__init__()
        self.emulator_manager = emulator_manager
        self.running = True
    
    def run(self):
        """Run refresh loop"""
        while self.running:
            self.emulator_manager.refresh_instances()
            self.refreshed.emit()
            self.msleep(2000)  # Refresh every 2 seconds
    
    def stop(self):
        """Stop the thread"""
        self.running = False


class CreateEmulatorDialog(QDialog):
    """Dialog for creating a new emulator instance"""
    
    def __init__(self, parent, avds: List[dict], emulator_manager: EmulatorManager):
        super().__init__(parent)
        self.emulator_manager = emulator_manager
        self.avds = avds
        self.instance_name = None
        self.selected_avd = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Create Emulator Instance")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # AVD selection
        avd_label = QLabel("Select AVD Template:")
        layout.addWidget(avd_label)
        
        self.avd_combo = QComboBox()
        for avd in self.avds:
            display_text = f"{avd.get('name', 'Unknown')} (API {avd.get('api_level', '?')})"
            self.avd_combo.addItem(display_text, avd.get('name'))
        layout.addWidget(self.avd_combo)
        
        # Instance name
        name_label = QLabel("Instance Name (optional):")
        layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Auto-generated if left empty")
        layout.addWidget(self.name_edit)
        
        # Clone checkbox
        self.clone_checkbox = QCheckBox("Create as clone (allows multiple instances)")
        self.clone_checkbox.setChecked(True)
        layout.addWidget(self.clone_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create & Start")
        create_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def accept(self):
        """Handle accept"""
        if self.avd_combo.currentData():
            self.selected_avd = self.avd_combo.currentData()
            self.instance_name = self.name_edit.text().strip() or None
            super().accept()
        else:
            QMessageBox.warning(self, "Error", "Please select an AVD template")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def apply_icons(self):
        """Update button icons with current theme colors"""
        color = self.icon_color
        # Button Icons
        self.create_btn.setIcon(VectorIcon.get_icon("plus", color))
        self.refresh_btn.setIcon(VectorIcon.get_icon("refresh", color))
        self.settings_btn.setIcon(VectorIcon.get_icon("settings", color))
        self.tools_btn.setIcon(VectorIcon.get_icon("tools", self.accent_color))
        
        self.start_all_btn.setIcon(VectorIcon.get_icon("play", color))
        self.stop_all_btn.setIcon(VectorIcon.get_icon("stop", self.danger_color))
        self.stop_btn.setIcon(VectorIcon.get_icon("stop", color))
        self.restart_btn.setIcon(VectorIcon.get_icon("refresh", color))
        self.rename_btn.setIcon(VectorIcon.get_icon("edit", color))
        self.delete_btn.setIcon(VectorIcon.get_icon("trash", self.danger_color))
        
        # Menu Actions
        self.root_action.setIcon(VectorIcon.get_icon("shield", color))
        self.sideload_magisk_action.setIcon(VectorIcon.get_icon("box-arrow", color))
        self.apk_sideload_action.setIcon(VectorIcon.get_icon("box-arrow", color))
        self.push_file_action.setIcon(VectorIcon.get_icon("file-push", color))
        self.account_setup_action.setIcon(VectorIcon.get_icon("user", color))

    def __init__(self):
        super().__init__()
        self.logger = AppLogger()
        self.config = ConfigManager()
        self.emulator_manager = EmulatorManager(self.config)
        self.input_synchronizer = InputSynchronizer(self.config, self.emulator_manager)
        
        self.refresh_thread = EmulatorRefreshThread(self.emulator_manager)
        self.refresh_thread.refreshed.connect(self.refresh_emulator_list)
        self.refresh_thread.start()
        
        # Apply Theme
        from PyQt6.QtWidgets import QApplication
        theme_pref = self.config.get('ui.theme', 'auto')
        ThemeStyles.apply_theme(QApplication.instance(), theme_pref)
        
        self.init_ui()
        
        # Determine theme colors for icons
        is_dark = ThemeStyles.is_dark_mode(self.config.get('ui.theme', 'auto'))
        self.icon_color = QColor(ThemeStyles.DARK_TEXT if is_dark else ThemeStyles.LIGHT_TEXT)
        self.danger_color = QColor(ThemeStyles.DARK_DANGER if is_dark else ThemeStyles.LIGHT_DANGER)
        self.accent_color = QColor(ThemeStyles.DARK_ACCENT if is_dark else ThemeStyles.LIGHT_ACCENT)
        self.apply_icons()
        
        # Setup logging UI integration AFTER UI is initialized
        qt_handler = self.logger.get_qt_handler()
        if qt_handler and qt_handler.emitter:
            qt_handler.emitter.log_message.connect(self.on_log_message)
        
        self.logger.info("Application started")
        
        # Validate Android SDK paths after UI is initialized
        if not self._validate_sdk_paths():
            QTimer.singleShot(500, self._show_sdk_warning)  # Show after window appears
        
        self.refresh_avd_list()
        self.refresh_emulator_list()
    
    def _validate_sdk_paths(self) -> bool:
        """Validate that Android SDK paths are configured"""
        from pathlib import Path
        
        emulator_path = self.config.emulator_path
        adb_path = self.config.adb_path
        
        if not emulator_path or not Path(emulator_path).exists():
            return False
        if not adb_path or not Path(adb_path).exists():
            return False
        return True
    
    def _show_sdk_warning(self):
        """Show warning about missing Android SDK paths"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Android SDK Not Found")
        msg.setText("Android SDK paths are not configured or invalid.")
        msg.setInformativeText(
            "Please configure the paths in Settings or set ANDROID_SDK_ROOT environment variable.\n\n"
            "Required paths:\n"
            "- Emulator executable\n"
            "- ADB (Android Debug Bridge)\n\n"
            "The application will still start, but emulator operations may fail."
        )
        settings_btn = msg.addButton("Open Settings", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("OK", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        
        if msg.clickedButton() == settings_btn:
            self.show_settings()
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self, self.config)
        if dialog.exec():
            # Reload config and reinitialize managers if paths changed
            self.config.load_config()
            self.emulator_manager = EmulatorManager(self.config)
            self.input_synchronizer = InputSynchronizer(self.config, self.emulator_manager)
            self.logger.info("Settings saved and managers reloaded")
            # Re-apply theme in case it changed
            from PyQt6.QtWidgets import QApplication
            theme_pref = self.config.get('ui.theme', 'auto')
            ThemeStyles.apply_theme(QApplication.instance(), theme_pref)
            self.refresh_all()
    
    def show_tools(self, initial_tab=0):
        """Show tools/automation dialog"""
        selected_instance = None
        names = self.get_selected_instances()
        if names:
            selected_instance = names[0]
            
        dialog = AutomationDialog(self, self.emulator_manager, selected_instance, initial_tab)
        dialog.exec()
    
    def on_log_message(self, message: str, level: str):
        """Handle log message from logger"""
        # Check if log_text widget exists (UI might not be initialized yet)
        if not hasattr(self, 'log_text') or self.log_text is None:
            return
        
        color_map = {
            'INFO': '#ffffff',
            'DEBUG': '#888888',
            'WARNING': '#ffaa00',
            'ERROR': '#ff4444',
            'CRITICAL': '#ff0000'
        }
        color = color_map.get(level, '#ffffff')
        formatted_message = f'<span style="color: {color};">{message}</span>'
        self.log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Android Multi-Emulator Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Toolbar section
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 10)
        toolbar_layout.setSpacing(10)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        create_btn = QPushButton(" Create Emulator")
        self.create_btn = create_btn # Store for icon update
        create_btn.clicked.connect(self.show_create_dialog)
        toolbar_layout.addWidget(create_btn)
        
        refresh_btn = QPushButton(" Refresh")
        self.refresh_btn = refresh_btn
        refresh_btn.clicked.connect(self.refresh_all)
        toolbar_layout.addWidget(refresh_btn)
        
        settings_btn = QPushButton(" Settings")
        self.settings_btn = settings_btn
        settings_btn.clicked.connect(self.show_settings)
        toolbar_layout.addWidget(settings_btn)
        
        tools_btn = QPushButton(" Tools")
        self.tools_btn = tools_btn
        tools_btn.setObjectName("primaryButton") # Primary color for tools
        tools_menu = QMenu(self)
        self.root_action = QAction("Root Device (RootAVD)", self)
        self.root_action.triggered.connect(lambda: self.show_tools(initial_tab=0))
        tools_menu.addAction(self.root_action)
        
        self.sideload_magisk_action = QAction("Install Magisk App", self)
        self.sideload_magisk_action.triggered.connect(lambda: self.show_tools(initial_tab=1))
        tools_menu.addAction(self.sideload_magisk_action)
        
        self.apk_sideload_action = QAction("Sideload APK", self)
        self.apk_sideload_action.triggered.connect(lambda: self.show_tools(initial_tab=2))
        tools_menu.addAction(self.apk_sideload_action)
        
        self.push_file_action = QAction("Push File to Device", self)
        self.push_file_action.triggered.connect(lambda: self.show_tools(initial_tab=3))
        tools_menu.addAction(self.push_file_action)
        
        self.account_setup_action = QAction("Google Account Setup", self)
        self.account_setup_action.triggered.connect(lambda: self.show_tools(initial_tab=4))
        tools_menu.addAction(self.account_setup_action)
        
        tools_btn.setMenu(tools_menu)
        toolbar_layout.addWidget(tools_btn)
        
        toolbar_layout.addStretch()
        
        # Sync controls
        sync_group = QGroupBox("Input Synchronization")
        sync_layout = QHBoxLayout()
        sync_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.sync_enable_checkbox = QCheckBox("Enable Sync")
        self.sync_enable_checkbox.stateChanged.connect(self.toggle_sync)
        sync_layout.addWidget(self.sync_enable_checkbox)
        
        sync_layout.addWidget(QLabel("Delay (ms):"))
        self.sync_delay_spin = PremiumSpinBox(min_val=0, max_val=1000)
        self.sync_delay_spin.setValue(self.config.get('input_sync.delay_ms', 0))
        self.sync_delay_spin.valueChanged.connect(self.update_sync_delay)
        sync_layout.addWidget(self.sync_delay_spin)
        
        sync_group.setLayout(sync_layout)
        toolbar_layout.addWidget(sync_group)
        
        main_layout.addLayout(toolbar_layout)
        
        # Main content area with tabs
        main_tabs = QTabWidget()
        main_tabs.setObjectName("mainTabs")
        
        # Tab 1: Emulator Management
        management_tab = QWidget()
        management_layout = QVBoxLayout()
        management_layout.setContentsMargins(20, 20, 20, 20)
        management_layout.setSpacing(15)
        
        self.management_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Emulator instances
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 10, 0) # Spacer from splitter
        left_layout.setSpacing(10)
        
        instances_label = QLabel("Running Emulators:")
        instances_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(instances_label)
        
        self.emulator_table = QTableWidget()
        self.emulator_table.setColumnCount(5)
        self.emulator_table.setHorizontalHeaderLabels([
            "Instance Name", "AVD", "Port", "State", "Sync"
        ])
        self.emulator_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.emulator_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.emulator_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.emulator_table.customContextMenuRequested.connect(self.show_context_menu)
        self.emulator_table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.emulator_table)
        
        # Instance controls
        instance_controls = QHBoxLayout()
        
        self.start_all_btn = QPushButton(" Start All")
        self.start_all_btn.clicked.connect(self.start_all_emulators)
        instance_controls.addWidget(self.start_all_btn)

        self.stop_all_btn = QPushButton(" Stop All")
        self.stop_all_btn.setObjectName("dangerButton")
        self.stop_all_btn.clicked.connect(self.stop_all_emulators)
        instance_controls.addWidget(self.stop_all_btn)

        self.stop_btn = QPushButton(" Stop")
        self.stop_btn.clicked.connect(self.stop_selected_emulator)
        self.stop_btn.setEnabled(False)
        instance_controls.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton(" Restart")
        self.restart_btn.clicked.connect(self.restart_selected_emulator)
        self.restart_btn.setEnabled(False)
        instance_controls.addWidget(self.restart_btn)
        
        self.rename_btn = QPushButton(" Rename")
        self.rename_btn.clicked.connect(self.rename_selected_emulator)
        self.rename_btn.setEnabled(False)
        instance_controls.addWidget(self.rename_btn)
        
        self.delete_btn = QPushButton(" Delete")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.clicked.connect(self.delete_selected_emulator)
        self.delete_btn.setEnabled(False)
        instance_controls.addWidget(self.delete_btn)
        
        instance_controls.addStretch()
        
        left_layout.addLayout(instance_controls)
        
        left_panel.setLayout(left_layout)
        self.management_splitter.addWidget(left_panel)
        
        # Right panel: AVD templates (Collapsible Sidebar)
        self.avd_sidebar = CollapsibleSidebar("Available AVD Templates", collapsed=True)
        
        self.avd_table = QTableWidget()
        self.avd_table.setColumnCount(3)
        self.avd_table.setHorizontalHeaderLabels(["Name", "Target", "API Level"])
        self.avd_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.avd_sidebar.addWidget(self.avd_table)
        self.avd_sidebar.toggled.connect(self._on_sidebar_toggled)
        
        self.management_splitter.addWidget(self.avd_sidebar)
        
        self.management_splitter.setStretchFactor(0, 2)
        self.management_splitter.setStretchFactor(1, 1)
        
        management_layout.addWidget(self.management_splitter)
        management_tab.setLayout(management_layout)
        
        # Tab 2: Logs
        logs_tab = QWidget()
        logs_layout = QVBoxLayout()
        logs_layout.setContentsMargins(20, 20, 20, 20)
        logs_layout.setSpacing(15)
        
        logs_label = QLabel("Application Logs:")
        logs_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        logs_layout.addWidget(logs_label)
        
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logView")
        self.log_text.setReadOnly(True)
        logs_layout.addWidget(self.log_text)
        
        log_controls = QHBoxLayout()
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.log_text.clear)
        log_controls.addWidget(clear_logs_btn)
        log_controls.addStretch()
        logs_layout.addLayout(log_controls)
        
        logs_tab.setLayout(logs_layout)
        
        # Add tabs
        main_tabs.addTab(management_tab, "Emulators")
        main_tabs.addTab(logs_tab, "Logs")
        
        main_layout.addWidget(main_tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        central_widget.setLayout(main_layout)
    
    def _on_sidebar_toggled(self, is_collapsed):
        """Update splitter sizes when sidebar is toggled"""
        if is_collapsed:
            # Force splitter to minimize right pane
            self.management_splitter.setSizes([10000, 24])
        else:
            # Give reasonable space to templates
            self.management_splitter.setSizes([700, 300])
    
    def refresh_avd_list(self):
        """Refresh the AVD template list"""
        avds = self.emulator_manager.list_avds()
        self.avd_table.setRowCount(len(avds))
        
        for row, avd in enumerate(avds):
            self.avd_table.setItem(row, 0, QTableWidgetItem(avd.get('name', 'Unknown')))
            self.avd_table.setItem(row, 1, QTableWidgetItem(avd.get('target', 'Unknown')))
            self.avd_table.setItem(row, 2, QTableWidgetItem(str(avd.get('api_level', '?'))))
        
        self.avd_table.resizeColumnsToContents()
    
    def refresh_emulator_list(self):
        """Refresh the emulator instance list"""
        instances = self.emulator_manager.list_instances()
        self.emulator_table.setRowCount(len(instances))
        
        for row, instance in enumerate(instances):
            self.emulator_table.setItem(row, 0, QTableWidgetItem(instance.name))
            self.emulator_table.setItem(row, 1, QTableWidgetItem(instance.avd_name))
            self.emulator_table.setItem(row, 2, QTableWidgetItem(str(instance.port)))
            
            state_item = QTableWidgetItem(instance.state.value.capitalize())
            if instance.state == EmulatorState.RUNNING:
                state_item.setForeground(QColor(0, 255, 0))
            elif instance.state == EmulatorState.STARTING:
                state_item.setForeground(QColor(255, 255, 0))
            elif instance.state == EmulatorState.STOPPED:
                state_item.setForeground(QColor(128, 128, 128))
            else:
                state_item.setForeground(QColor(255, 0, 0))
            self.emulator_table.setItem(row, 3, state_item)
            
            # Sync checkbox (Centered)
            sync_container = QWidget()
            sync_layout = QHBoxLayout(sync_container)
            sync_checkbox = QCheckBox()
            sync_checkbox.setChecked(instance.name in self.input_synchronizer.synced_instances)
            sync_checkbox.stateChanged.connect(
                lambda state, name=instance.name: self.toggle_instance_sync(name, state)
            )
            sync_layout.addWidget(sync_checkbox)
            sync_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sync_layout.setContentsMargins(0, 0, 0, 0)
            self.emulator_table.setCellWidget(row, 4, sync_container)
        
        self.emulator_table.resizeColumnsToContents()
        running_count = sum(1 for instance in instances if instance.state == EmulatorState.RUNNING)
        self.statusBar().showMessage(f"{running_count} emulator(s) running")
    
    def refresh_all(self):
        """Refresh both lists"""
        self.refresh_avd_list()
        self.refresh_emulator_list()
    
    def show_create_dialog(self):
        """Show create emulator dialog"""
        avds = self.emulator_manager.list_avds()
        if not avds:
            QMessageBox.warning(self, "No AVDs", "No AVD templates found. Please create one using Android Studio's AVD Manager.")
            self.logger.warning("No AVD templates found")
            return
        
        dialog = CreateEmulatorDialog(self, avds, self.emulator_manager)
        if dialog.exec():
            avd_name = dialog.selected_avd
            instance_name = dialog.instance_name
            create_clone = dialog.clone_checkbox.isChecked()
            
            # Check if AVD is already running (warn if not cloning)
            running_same_avd = [inst for inst in self.emulator_manager.list_instances()
                               if inst.avd_name == avd_name and inst.state == EmulatorState.RUNNING]
            if running_same_avd and not create_clone:
                reply = QMessageBox.question(
                    self,
                    "AVD Already Running",
                    f"Another instance of '{avd_name}' is already running.\n\n"
                    f"The emulator will use -read-only mode automatically, but creating a clone is recommended.\n\n"
                    f"Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Show progress dialog
            self.progress_dialog = QProgressDialog("Creating emulator instance...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowTitle("Creating Emulator")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.setCancelButton(None)  # Don't allow canceling for now
            self.progress_dialog.show()
            
            self.logger.info(f"Starting emulator creation: AVD={avd_name}, Clone={create_clone}, Name={instance_name}")
            
            # Create worker thread for emulator creation
            self.creation_worker = EmulatorCreationWorker(
                self.emulator_manager, avd_name, instance_name, create_clone
            )
            self.creation_worker.progress.connect(self.on_creation_progress)
            self.creation_worker.error.connect(self.on_creation_error)
            self.creation_worker.finished.connect(self.on_creation_finished)
            self.creation_worker.start()
    
    def on_creation_progress(self, message: str):
        """Handle progress updates from creation worker"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setLabelText(message)
        self.logger.info(message)
    
    def on_creation_error(self, error: str):
        """Handle errors from creation worker"""
        self.logger.error(error)
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
    
    def on_creation_finished(self, instance: Optional[EmulatorInstance]):
        """Handle completion of emulator creation"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        
        if instance:
            self.logger.info(f"Emulator instance '{instance.name}' created successfully on port {instance.port}")
            QMessageBox.information(self, "Success", 
                f"Emulator instance '{instance.name}' is starting...\n\n"
                f"It may take 1-2 minutes to fully boot. Check the Logs tab for progress.")
            self.refresh_emulator_list()
        else:
            self.logger.error("Failed to create emulator instance")
            QMessageBox.warning(self, "Error", 
                "Failed to start emulator. Check if Android SDK paths are configured correctly.\n\n"
                "See the Logs tab for more details.")
    
    def on_selection_changed(self):
        """Handle emulator selection change"""
        selected = self.emulator_table.selectedItems()
        enabled = len(selected) > 0
        self.stop_btn.setEnabled(enabled)
        self.restart_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        # Rename only enabled for single selection
        self.rename_btn.setEnabled(enabled and len(set(item.row() for item in selected)) == 1)
    
    def get_selected_instances(self):
        """Get list of selected instance names"""
        selected = self.emulator_table.selectedItems()
        if not selected:
            return []
        
        # Get unique rows
        rows = sorted(list(set(item.row() for item in selected)))
        names = []
        for row in rows:
            item = self.emulator_table.item(row, 0)
            if item:
                names.append(item.text())
        return names

    def stop_selected_emulator(self):
        """Stop selected emulators"""
        names = self.get_selected_instances()
        if not names:
            return
        
        count = len(names)
        msg = f"Stop emulator '{names[0]}'?" if count == 1 else f"Stop {count} emulators?"
        
        if QMessageBox.question(self, "Confirm", msg) == QMessageBox.StandardButton.Yes:
            # Show progress for multiple
            progress = None
            if count > 1:
                progress = QProgressDialog("Stopping emulators...", None, 0, count, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()
            
            for i, instance_name in enumerate(names):
                self.logger.info(f"Stopping emulator '{instance_name}'")
                if progress:
                    progress.setLabelText(f"Stopping {instance_name}...")
                    progress.setValue(i)
                
                if self.emulator_manager.stop_emulator(instance_name):
                    self.input_synchronizer.remove_from_sync(instance_name)
                    self.logger.info(f"Emulator '{instance_name}' stopped")
                else:
                    self.logger.warning(f"Failed to stop '{instance_name}'")
            
            if progress:
                progress.setValue(count)
            
            self.refresh_emulator_list()
            self.statusBar().showMessage(f"Stopped {count} emulator(s)")
    
    def restart_selected_emulator(self):
        """Restart selected emulators"""
        names = self.get_selected_instances()
        if not names:
            return
            
        count = len(names)
        msg = f"Restart emulator '{names[0]}'?" if count == 1 else f"Restart {count} emulators?"
        
        if QMessageBox.question(self, "Confirm", msg) == QMessageBox.StandardButton.Yes:
            for instance_name in names:
                self.logger.info(f"Restarting emulator '{instance_name}'")
                # Stop
                self.emulator_manager.stop_emulator(instance_name)
                self.input_synchronizer.remove_from_sync(instance_name)
                
                # Start (find avd name)
                instance = self.emulator_manager.get_instance(instance_name)
                if instance:
                    # Small delay to ensure cleanup
                    QTimer.singleShot(1000, 
                        lambda name=instance_name, avd=instance.avd_name: 
                        self.emulator_manager.start_emulator(avd, name)
                    )
            
            self.statusBar().showMessage(f"Restarting {count} emulator(s)...")
            # Refresh will happen on timer or next update
            QTimer.singleShot(2000, self.refresh_emulator_list)
            
    def rename_selected_emulator(self):
        """Rename selected emulator"""
        names = self.get_selected_instances()
        if not names or len(names) != 1:
            QMessageBox.information(self, "Info", "Please select exactly one emulator to rename.")
            return
        
        old_name = names[0]
        instance = self.emulator_manager.get_instance(old_name)
        if not instance:
            return
        
        # Create a simple dialog for renaming
        dialog = QDialog(self)
        dialog.setWindowTitle("Rename Emulator")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        label = QLabel(f"Enter new name for '{old_name}':")
        layout.addWidget(label)
        
        name_input = QLineEdit()
        name_input.setText(old_name)
        name_input.selectAll()  # Select all for easy replacement
        layout.addWidget(name_input)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Rename")
        cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        def do_rename():
            new_name = name_input.text().strip()
            
            if not new_name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
            
            if new_name == old_name:
                dialog.accept()
                return
            
            if self.emulator_manager.rename_instance(old_name, new_name):
                # Update sync group if instance was in sync
                if old_name in self.input_synchronizer.synced_instances:
                    self.input_synchronizer.synced_instances.discard(old_name)
                    self.input_synchronizer.synced_instances.add(new_name)
                
                self.statusBar().showMessage(f"Renamed '{old_name}' to '{new_name}'")
                self.refresh_emulator_list()
                dialog.accept()
            else:
                QMessageBox.critical(self, "Error", f"Failed to rename emulator to '{new_name}'.")
        
        ok_btn.clicked.connect(do_rename)
        cancel_btn.clicked.connect(dialog.reject)
        name_input.returnPressed.connect(do_rename)
        
        dialog.exec()
            
    def delete_selected_emulator(self):
        """Delete selected emulators"""
        names = self.get_selected_instances()
        if not names:
            return
            
        count = len(names)
        msg = f"permanently DELETE emulator '{names[0]}'?" if count == 1 else f"permanently DELETE {count} emulators?"
        warning = "\n\nFiles will be removed!"
        
        if QMessageBox.question(self, "Confirm", msg + warning) == QMessageBox.StandardButton.Yes:
            for instance_name in names:
                if self.emulator_manager.delete_instance(instance_name):
                     self.statusBar().showMessage(f"Deleted '{instance_name}'")
                else:
                     self.logger.warning(f"Failed to delete '{instance_name}'")
            
            self.refresh_emulator_list()
            
    def start_all_emulators(self):
        """Start all stopped emulators"""
        stopped = [
            inst for inst in self.emulator_manager.list_instances() 
            if inst.state == EmulatorState.STOPPED
        ]
        
        if not stopped:
            QMessageBox.information(self, "Info", "No stopped emulators to start.")
            return
            
        count = len(stopped)
        if QMessageBox.question(self, "Start All", f"Start {count} stopped emulators?") == QMessageBox.StandardButton.Yes:
            for inst in stopped:
                self.emulator_manager.start_emulator(inst.avd_name, inst.name, inst.port)
            
            self.statusBar().showMessage(f"Starting {count} emulators...")
            QTimer.singleShot(1000, self.refresh_emulator_list)

    def stop_all_emulators(self):
        """Stop all running emulators"""
        running = [
            inst for inst in self.emulator_manager.list_instances() 
            if inst.state == EmulatorState.RUNNING
        ]
        
        if not running:
            QMessageBox.information(self, "Info", "No running emulators to stop.")
            return
            
        count = len(running)
        if QMessageBox.question(self, "Stop All", f"Stop all {count} running emulators?") == QMessageBox.StandardButton.Yes:
            # Show progress
            progress = QProgressDialog("Stopping all emulators...", None, 0, count, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            for i, inst in enumerate(running):
                progress.setLabelText(f"Stopping {inst.name}...")
                progress.setValue(i)
                self.emulator_manager.stop_emulator(inst.name)
                self.input_synchronizer.remove_from_sync(inst.name)
            
            progress.setValue(count)
            self.refresh_emulator_list()
            self.statusBar().showMessage(f"Stopped {count} emulator(s)")

    def show_context_menu(self, position):
        """Show context menu for emulator table"""
        menu = QMenu()
        names = self.get_selected_instances()
        
        if not names:
            return
            
        start_action = QAction("Start", self)
        start_action.setIcon(VectorIcon.get_icon("play", self.icon_color))
        stop_action = QAction("Stop", self)
        stop_action.setIcon(VectorIcon.get_icon("stop", self.icon_color))
        restart_action = QAction("Restart", self)
        restart_action.setIcon(VectorIcon.get_icon("refresh", self.icon_color))
        rename_action = QAction("Rename", self)
        rename_action.setIcon(VectorIcon.get_icon("edit", self.icon_color))
        delete_action = QAction("Delete", self)
        delete_action.setIcon(VectorIcon.get_icon("trash", self.danger_color))
        root_action = QAction("Root Device (RootAVD)", self)
        root_action.setIcon(VectorIcon.get_icon("shield", self.icon_color))
        sideload_magisk_action = QAction("Install Magisk App", self)
        sideload_magisk_action.setIcon(VectorIcon.get_icon("box-arrow", self.icon_color))
        apk_sideload_action = QAction("Sideload APK", self)
        apk_sideload_action.setIcon(VectorIcon.get_icon("box-arrow", self.icon_color))
        push_file_action = QAction("Push File to Device", self)
        push_file_action.setIcon(VectorIcon.get_icon("file-push", self.icon_color))
        account_setup_action = QAction("Google Account Setup", self)
        account_setup_action.setIcon(VectorIcon.get_icon("user", self.icon_color))
        
        # Check states to enable/disable
        has_running = any(self.emulator_manager.get_instance(n).state == EmulatorState.RUNNING for n in names if self.emulator_manager.get_instance(n))
        has_stopped = any(self.emulator_manager.get_instance(n).state == EmulatorState.STOPPED for n in names if self.emulator_manager.get_instance(n))
        
        if has_stopped:
            menu.addAction(start_action)
        if has_running:
            menu.addAction(stop_action)
            menu.addAction(restart_action)
            menu.addAction(root_action)
            menu.addAction(sideload_magisk_action)
            menu.addAction(apk_sideload_action)
            menu.addAction(push_file_action)
            menu.addAction(account_setup_action)
        
        menu.addSeparator()
        # Rename action is available for single selection only
        if len(names) == 1:
            menu.addAction(rename_action)
        menu.addAction(delete_action)
        
        action = menu.exec(self.emulator_table.viewport().mapToGlobal(position))
        
        if action == start_action:
            for name in names:
                inst = self.emulator_manager.get_instance(name)
                if inst and inst.state == EmulatorState.STOPPED:
                    self.emulator_manager.start_emulator(inst.avd_name, inst.name, inst.port)
            self.refresh_emulator_list()
        elif action == stop_action:
            self.stop_selected_emulator()
        elif action == restart_action:
            self.restart_selected_emulator()
        elif action == rename_action:
            self.rename_selected_emulator()
        elif action == delete_action:
            self.delete_selected_emulator()
        elif action == root_action:
            if len(names) == 1:
                self.show_tools(initial_tab=0) 
            else:
                 QMessageBox.information(self, "Info", "Please select only one emulator to root.")
        elif action == sideload_magisk_action:
            self.show_tools(initial_tab=1)
        elif action == apk_sideload_action:
            self.show_tools(initial_tab=2)
        elif action == push_file_action:
            self.show_tools(initial_tab=3)
        elif action == account_setup_action:
            self.show_tools(initial_tab=4)
    

    
    def toggle_sync(self, state):
        """Toggle input synchronization"""
        if state == Qt.CheckState.Checked.value or state == 2:
            # Get all running instances
            running_instances = [
                inst.name for inst in self.emulator_manager.list_instances()
                if inst.state == EmulatorState.RUNNING
            ]
            if running_instances:
                self.input_synchronizer.enable_sync(running_instances)
                self.statusBar().showMessage("Input synchronization enabled")
            else:
                self.sync_enable_checkbox.setChecked(False)
                QMessageBox.information(self, "No Emulators", "No running emulators to sync.")
        else:
            self.input_synchronizer.disable_sync()
            self.statusBar().showMessage("Input synchronization disabled")
        self.refresh_emulator_list()
    
    def toggle_instance_sync(self, instance_name: str, state):
        """Toggle sync for a specific instance"""
        if state == Qt.CheckState.Checked.value or state == 2:
            self.input_synchronizer.add_to_sync(instance_name)
        else:
            self.input_synchronizer.remove_from_sync(instance_name)
    
    def update_sync_delay(self, value):
        """Update sync delay"""
        self.config.set('input_sync.delay_ms', value)
        self.config.save_config()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.refresh_thread.stop()
        self.refresh_thread.wait()
        
        # Stop all running emulators
        running_instances = [
            inst.name for inst in self.emulator_manager.list_instances()
            if inst.state == EmulatorState.RUNNING
        ]
        
        if running_instances:
            # Show shutting down dialog
            progress = QProgressDialog("Shutting down emulators...", None, 0, len(running_instances), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Exiting")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.setCancelButton(None)  # Disable cancel
            progress.show()
            
            # Process events to show dialog
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            for i, name in enumerate(running_instances):
                progress.setLabelText(f"Stopping {name}...")
                QApplication.processEvents()
                
                self.emulator_manager.stop_emulator(name)
                self.input_synchronizer.remove_from_sync(name)
                progress.setValue(i + 1)
        
        # Clean up logger handlers to avoid Qt object deletion errors
        if hasattr(self.logger, '_qt_handler') and self.logger._qt_handler:
            try:
                # Disconnect signal first
                qt_handler = self.logger._qt_handler
                if hasattr(qt_handler, 'log_message'):
                    try:
                        qt_handler.log_message.disconnect()
                    except:
                        pass
                
                # Remove handler from logger
                import logging
                logger = logging.getLogger('AndroidMultiEmulator')
                logger.removeHandler(qt_handler)
                
                # Close the handler
                qt_handler.close()
            except Exception as e:
                # Ignore cleanup errors
                pass
        
        event.accept()


def main():
    """Main entry point for the GUI application"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("Android Multi-Emulator Manager")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
