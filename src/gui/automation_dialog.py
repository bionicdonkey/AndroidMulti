from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, 
    QTextEdit, QComboBox, QGroupBox, QRadioButton, QButtonGroup, QCheckBox,
    QTabWidget, QWidget, QFileDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import shutil
import subprocess
import os
import re
from pathlib import Path
import urllib.request
import ssl
import json
from .styles import ThemeStyles

def _get_latest_magisk_url(progress_callback=None):
    """Dynamically find the latest Magisk download URL from GitHub API"""
    api_url = "https://api.github.com/repos/topjohnwu/Magisk/releases/latest"
    
    # Use unverified SSL context to avoid certificate issues on some systems
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        if progress_callback:
            progress_callback("Checking GitHub for latest Magisk version...")
        
        # GitHub API requires a User-Agent
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
            
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                # Find the main Magisk APK (e.g., Magisk-v28.1.apk)
                if name.startswith("Magisk-") and name.endswith(".apk"):
                    return asset.get("browser_download_url")
            
            # Fallback if specific pattern not found
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".apk") and "debug" not in asset.get("name", "").lower():
                    return asset.get("browser_download_url")
                    
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error fetching latest Magisk metadata: {e}")
    
    # Absolute fallback (last resort, might be stale but better than failing)
    return "https://github.com/topjohnwu/Magisk/releases/latest/download/Magisk.apk"


class RootAVDWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, cache_dir: Path):
        super().__init__()
        self.cache_dir = cache_dir
        self.repo_url = "https://gitlab.com/newbit/rootAVD.git"
        self.download_magisk = False
        
    def set_download_magisk(self, enabled: bool):
        self.download_magisk = enabled
        
    def run(self):
        try:
            target_dir = self.cache_dir / "rootAVD"
            
            # Check for git
            if not shutil.which("git"):
                self.finished.emit(False, "Git is not installed or not in PATH. Please install Git.")
                return

            if target_dir.exists():
                self.progress.emit("Updating RootAVD repository...")
                subprocess.run(["git", "pull"], cwd=target_dir, check=True, capture_output=True)
            else:
                self.progress.emit("Cloning RootAVD repository...")
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "clone", self.repo_url], cwd=self.cache_dir, check=True, capture_output=True)
                
            if self.download_magisk:
                self.progress.emit("Resolving latest Magisk download URL...")
                magisk_url = _get_latest_magisk_url(self.progress.emit)
                self.progress.emit(f"Downloading Magisk from: {magisk_url}")
                magisk_dest = target_dir / "Magisk.zip"
                
                # Use unverified SSL context to avoid certificate issues on some systems
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                try:
                    with urllib.request.urlopen(magisk_url, context=ctx) as response, open(magisk_dest, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                    self.progress.emit("Magisk downloaded and saved as Magisk.zip")
                except Exception as e:
                    self.progress.emit(f"Warning: Failed to download Magisk: {e}")
                    # Don't fail the whole process, script might still work with old magisk
            
            self.finished.emit(True, str(target_dir))
            
        except subprocess.CalledProcessError as e:
            self.finished.emit(False, f"Git command failed: {e}")
        except Exception as e:
            self.finished.emit(False, f"Error: {e}")

class MagiskSideloadWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, cache_dir: Path, target_devices: list):
        super().__init__()
        self.cache_dir = cache_dir
        self.target_devices = target_devices # List of device IDs (serial)
        
    def run(self):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            magisk_dest = self.cache_dir / "Magisk.apk"
            
            # Download if not exists or just always download latest?
            # User said "one click animation to download and sideload"
            self.progress.emit("Resolving latest Magisk download URL...")
            magisk_url = _get_latest_magisk_url(self.progress.emit)
            self.progress.emit(f"Downloading Magisk from: {magisk_url}")
            
            import urllib.request
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            try:
                with urllib.request.urlopen(magisk_url, context=ctx) as response, open(magisk_dest, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                self.progress.emit("Magisk downloaded successfully.")
            except Exception as e:
                self.finished.emit(False, f"Failed to download Magisk: {e}")
                return

            if not self.target_devices:
                self.finished.emit(False, "No target devices provided.")
                return

            for serial in self.target_devices:
                self.progress.emit(f"Installing Magisk on {serial}...")
                # Run adb install -r -d magisk_dest
                result = subprocess.run(
                    ["adb", "-s", serial, "install", "-r", "-d", str(magisk_dest)],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.progress.emit(f"Successfully installed on {serial}")
                else:
                    self.progress.emit(f"Error on {serial}: {result.stderr}")

            self.finished.emit(True, "Magisk installation finished.")
            
        except Exception as e:
            self.finished.emit(False, str(e))

class APKSideloadWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, apk_path: Path, target_devices: list):
        super().__init__()
        self.apk_path = apk_path
        self.target_devices = target_devices
        
    def run(self):
        try:
            if not self.apk_path.exists():
                self.finished.emit(False, f"APK file not found: {self.apk_path}")
                return

            if not self.target_devices:
                self.finished.emit(False, "No target devices provided.")
                return

            for serial in self.target_devices:
                self.progress.emit(f"Installing {self.apk_path.name} on {serial}...")
                # Run adb install -r -d magisk_dest
                result = subprocess.run(
                    ["adb", "-s", serial, "install", "-r", "-d", str(self.apk_path)],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.progress.emit(f"Successfully installed on {serial}")
                else:
                    self.progress.emit(f"Error on {serial}: {result.stderr}")

            self.finished.emit(True, f"Installation of {self.apk_path.name} finished.")
            
        except Exception as e:
            self.finished.emit(False, str(e))

class FilePushWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, local_path: Path, remote_path: str, target_devices: list):
        super().__init__()
        self.local_path = local_path
        self.remote_path = remote_path
        self.target_devices = target_devices
        
    def run(self):
        try:
            if not self.local_path.exists():
                self.finished.emit(False, f"Local file not found: {self.local_path}")
                return

            if not self.target_devices:
                self.finished.emit(False, "No target devices provided.")
                return

            for serial in self.target_devices:
                self.progress.emit(f"Pushing {self.local_path.name} to {serial}:{self.remote_path}...")
                result = subprocess.run(
                    ["adb", "-s", serial, "push", str(self.local_path), self.remote_path],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.progress.emit(f"Successfully pushed to {serial}")
                else:
                    self.progress.emit(f"Error on {serial}: {result.stderr}")

            self.finished.emit(True, f"Push of {self.local_path.name} finished.")
            
        except Exception as e:
            self.finished.emit(False, str(e))

class AccountAutomationWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, target_devices: list, action: str, data: str = ""):
        super().__init__()
        self.target_devices = target_devices
        self.action = action # 'launch' or 'type'
        self.data = data
        
    def run(self):
        try:
            if not self.target_devices:
                self.finished.emit(False, "No target devices provided.")
                return

            for serial in self.target_devices:
                if self.action == 'launch':
                    self.progress.emit(f"Launching Add Account screen on {serial}...")
                    # Standard Android intent for adding a Google account
                    subprocess.run([
                        "adb", "-s", serial, "shell", "am", "start", 
                        "-a", "android.settings.ADD_ACCOUNT_SETTINGS", 
                        "--es", "account_types", '["com.google"]'
                    ], capture_output=True)
                elif self.action == 'type':
                    self.progress.emit(f"Typing text to {serial}...")
                    # Note: We escape spaces with %s for adb input text
                    safe_text = self.data.replace(" ", "%s")
                    subprocess.run([
                        "adb", "-s", serial, "shell", "input", "text", safe_text
                    ], capture_output=True)

            self.finished.emit(True, "Account operation finished.")
            
        except Exception as e:
            self.finished.emit(False, str(e))

class AutomationDialog(QDialog):
    def __init__(self, parent=None, emulator_manager=None, selected_instance=None, initial_tab=0):
        super().__init__(parent)
        self.emulator_manager = emulator_manager
        self.selected_instance = selected_instance
        self.setWindowTitle("Tools - Root Device (RootAVD)")
        self.resize(600, 550)
        self.setup_ui()
        
        if initial_tab < self.tabs.count():
            self.tabs.setCurrentIndex(initial_tab)
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        
        # Tab 1: Root System
        self.root_tab = QWidget()
        self.setup_root_tab()
        self.tabs.addTab(self.root_tab, "Root System (RootAVD)")
        
        # Tab 2: Install Magisk App
        self.magisk_tab = QWidget()
        self.setup_sideload_tab()
        self.tabs.addTab(self.magisk_tab, "Install Magisk App")
        
        # Tab 3: Sideload Any APK
        self.apk_tab = QWidget()
        self.setup_apk_tab()
        self.tabs.addTab(self.apk_tab, "Sideload any APK")
        
        # Tab 4: Push File
        self.push_tab = QWidget()
        self.setup_push_tab()
        self.tabs.addTab(self.push_tab, "Push File to Device")
        
        # Tab 5: Account Setup
        self.account_tab = QWidget()
        self.setup_account_tab()
        self.tabs.addTab(self.account_tab, "Account Setup (Beta)")
        
        main_layout.addWidget(self.tabs)
        
        self.status_log = QTextEdit()
        self.status_log.setObjectName("logView")
        self.status_log.setReadOnly(True)
        self.status_log.setMinimumHeight(120)
        main_layout.addWidget(self.status_log, 1) # Give it stretch
        
        self.setLayout(main_layout)

    def setup_root_tab(self):
        layout = QVBoxLayout(self.root_tab)
        
        title = QLabel("Root with RootAVD")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        info = QLabel(
            "This tool will download and run 'RootAVD' to patch your AVD's ramdisk.img.\n"
            "After patching, you will still need to install the Magisk APK (see next tab)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Instance Selection
        instance_group = QGroupBox("Target Emulator")
        instance_layout = QVBoxLayout()
        self.instance_combo = QComboBox()
        
        instances = self.emulator_manager.list_instances() if self.emulator_manager else []
        active_index = 0
        
        running_found = False
        for i, inst in enumerate(instances):
            if inst.state.value == "running":
                self.instance_combo.addItem(f"{inst.name} ({inst.avd_name})", inst.name)
                running_found = True
                if self.selected_instance and inst.name == self.selected_instance:
                    active_index = self.instance_combo.count() - 1
        
        if not running_found:
            self.instance_combo.addItem("No running emulators found")
            self.instance_combo.setEnabled(False)
        else:
            self.instance_combo.setCurrentIndex(active_index)
            
        instance_layout.addWidget(self.instance_combo)
        instance_group.setLayout(instance_layout)
        layout.addWidget(instance_group)
        
        # Argument Selection
        args_group = QGroupBox("Rooting Command / Arguments")
        args_layout = QVBoxLayout()
        
        self.args_combo = QComboBox()
        self.args_combo.addItem("(Default) Install Magisk", "")
        self.args_combo.addItem("Install Magisk + FAKEBOOTIMG", "FAKEBOOTIMG")
        self.args_combo.addItem("Install Magisk (DEBUG PATCHFSTAB GetUSBHPmodZ)", "DEBUG PATCHFSTAB GetUSBHPmodZ")
        self.args_combo.addItem("Restore Original Boot", "restore")
        self.args_combo.addItem("Install Kernel Modules", "InstallKernelModules")
        self.args_combo.addItem("Install Prebuilt Kernel Modules", "InstallPrebuiltKernelModules")
        self.args_combo.addItem("Custom...", "CUSTOM")
        
        self.args_combo.currentIndexChanged.connect(self.update_preview)
        args_layout.addWidget(self.args_combo)
        
        self.custom_args_edit = QTextEdit()
        self.custom_args_edit.setPlaceholderText("Enter custom arguments here...")
        self.custom_args_edit.setMaximumHeight(50)
        self.custom_args_edit.setVisible(False)
        args_layout.addWidget(self.custom_args_edit)

        # Magisk Option
        self.magisk_check = QCheckBox("Download Latest Magisk (Fixes 'ignoring selection' issue)")
        self.magisk_check.setChecked(True)
        self.magisk_check.setToolTip("Downloads the latest stable Magisk APK and overwrites the local Magisk.zip used by RootAVD.")
        args_layout.addWidget(self.magisk_check)
        
        args_group.setLayout(args_layout)
        layout.addWidget(args_group)
        
        # Preview
        layout.addWidget(QLabel("Command Preview:"))
        self.preview_label = QLabel("rootAVD.bat [ramdisk] ...")
        self.preview_label.setObjectName("previewLabel")
        layout.addWidget(self.preview_label)
        
        self.run_btn = QPushButton("Run RootAVD")
        self.run_btn.setObjectName("primaryButton")
        self.run_btn.clicked.connect(self.start_rooting)
        if not running_found:
             self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)
        self.update_preview()

    def setup_sideload_tab(self):
        layout = QVBoxLayout(self.magisk_tab)
        
        title = QLabel("Install Magisk App (Sideload)")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        info = QLabel(
            "Quickly download and install the latest Magisk APK to your running emulators.\n"
            "This is required to manage root permissions after patching the ramdisk."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        target_group = QGroupBox("Target Emulators")
        target_layout = QVBoxLayout()
        
        self.sideload_all_radio = QRadioButton("All Running Emulators")
        self.sideload_selected_radio = QRadioButton("Selected Emulator in previous tab")
        self.sideload_group = QButtonGroup()
        self.sideload_group.addButton(self.sideload_all_radio)
        self.sideload_group.addButton(self.sideload_selected_radio)
        self.sideload_all_radio.setChecked(True)
        
        target_layout.addWidget(self.sideload_all_radio)
        target_layout.addWidget(self.sideload_selected_radio)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        self.sideload_btn = QPushButton("🚀 Download & Install Magisk APK")
        self.sideload_btn.setObjectName("primaryButton")
        self.sideload_btn.setMinimumHeight(40)
        self.sideload_btn.clicked.connect(self.start_sideload)
        layout.addWidget(self.sideload_btn)
        
        layout.addStretch()

    def setup_apk_tab(self):
        layout = QVBoxLayout(self.apk_tab)
        
        title = QLabel("Sideload Any APK File")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        info = QLabel(
            "Select a local .apk file and install it to your running emulators.\n"
            "The app will be updated if it already exists (-r) and allowed to downgrade (-d)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # File selector
        file_group = QGroupBox("Select APK")
        file_layout = QHBoxLayout()
        self.apk_path_edit = QLineEdit()
        self.apk_path_edit.setPlaceholderText("Select or drop APK file here...")
        self.apk_browse_btn = QPushButton("Browse...")
        self.apk_browse_btn.clicked.connect(self.browse_apk)
        
        file_layout.addWidget(self.apk_path_edit)
        file_layout.addWidget(self.apk_browse_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        target_group = QGroupBox("Target Emulators")
        target_layout = QVBoxLayout()
        
        self.apk_all_radio = QRadioButton("All Running Emulators")
        self.apk_selected_radio = QRadioButton("Selected Emulator in first tab")
        self.apk_group = QButtonGroup()
        self.apk_group.addButton(self.apk_all_radio)
        self.apk_group.addButton(self.apk_selected_radio)
        self.apk_all_radio.setChecked(True)
        
        target_layout.addWidget(self.apk_all_radio)
        target_layout.addWidget(self.apk_selected_radio)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        self.apk_btn = QPushButton("🚀 Install APK")
        self.apk_btn.setObjectName("primaryButton")
        self.apk_btn.setMinimumHeight(40)
        self.apk_btn.clicked.connect(self.start_apk_sideload)
        layout.addWidget(self.apk_btn)
        
        layout.addStretch()

    def setup_push_tab(self):
        layout = QVBoxLayout(self.push_tab)
        
        title = QLabel("Push File to Remote Device")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        info = QLabel(
            "Push any local file to the internal storage of your running emulators.\n"
            "Typical location is /sdcard/ (internal storage root)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # File selector
        file_group = QGroupBox("Source File")
        file_layout = QHBoxLayout()
        self.push_local_edit = QLineEdit()
        self.push_local_edit.setPlaceholderText("Select file to push...")
        self.push_browse_btn = QPushButton("Browse...")
        self.push_browse_btn.clicked.connect(self.browse_push_file)
        
        file_layout.addWidget(self.push_local_edit)
        file_layout.addWidget(self.push_browse_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Destination
        dest_group = QGroupBox("Destination Path")
        dest_layout = QVBoxLayout()
        self.push_remote_edit = QLineEdit("/sdcard/")
        self.push_remote_edit.setPlaceholderText("Remote path (e.g. /sdcard/file.txt or /sdcard/)")
        dest_layout.addWidget(self.push_remote_edit)
        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)
        
        target_group = QGroupBox("Target Emulators")
        target_layout = QVBoxLayout()
        
        self.push_all_radio = QRadioButton("All Running Emulators")
        self.push_selected_radio = QRadioButton("Selected Emulator in first tab")
        self.push_group = QButtonGroup()
        self.push_group.addButton(self.push_all_radio)
        self.push_group.addButton(self.push_selected_radio)
        self.push_all_radio.setChecked(True)
        
        target_layout.addWidget(self.push_all_radio)
        target_layout.addWidget(self.push_selected_radio)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        self.push_btn = QPushButton("🚀 Push File")
        self.push_btn.setObjectName("primaryButton")
        self.push_btn.setMinimumHeight(40)
        self.push_btn.clicked.connect(self.start_file_push)
        layout.addWidget(self.push_btn)
        
        layout.addStretch()

    def browse_push_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Push", "", "All Files (*.*)"
        )
        if file_path:
            self.push_local_edit.setText(file_path)

    def start_file_push(self):
        local_path = Path(self.push_local_edit.text().strip())
        if not local_path.exists() or not local_path.is_file():
            QMessageBox.warning(self, "Invalid File", "Please select a valid local file first.")
            return

        remote_path = self.push_remote_edit.text().strip()
        if not remote_path:
            QMessageBox.warning(self, "Invalid Path", "Please specify a destination path.")
            return

        target_devices = []
        if self.push_all_radio.isChecked():
            instances = self.emulator_manager.list_instances() if self.emulator_manager else []
            for inst in instances:
                if inst.state.value == "running" and inst.device_id:
                    target_devices.append(inst.device_id)
        else:
            instance_name = self.instance_combo.currentData()
            if instance_name:
                inst = self.emulator_manager.get_instance(instance_name)
                if inst and inst.device_id:
                    target_devices.append(inst.device_id)
        
        if not target_devices:
            self.log("Error: No running emulators found with device IDs.")
            return
            
        self.push_btn.setEnabled(False)
        self.log(f"Starting push of {local_path.name} to {len(target_devices)} device(s)...")
        
        self.push_worker = FilePushWorker(local_path, remote_path, target_devices)
        self.push_worker.progress.connect(self.log)
        self.push_worker.finished.connect(self.on_push_finished)
        self.push_worker.start()

    def on_push_finished(self, success, message):
        self.push_btn.setEnabled(True)
        if success:
            self.log(f"Success: {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self.log(f"Error: {message}")
            QMessageBox.critical(self, "Error", f"Failed to push file:\n{message}")

    def setup_account_tab(self):
        layout = QVBoxLayout(self.account_tab)
        
        title = QLabel("Semi-Automated Account Setup")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        info = QLabel(
            "Use this tool to speed up Google account provisioning across your farm.\n"
            "1. Launch the screen on target devices.\n"
            "2. Use 'Type to All' to paste credentials into the focused fields."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        target_group = QGroupBox("Target Emulators")
        target_layout = QVBoxLayout()
        
        self.acc_all_radio = QRadioButton("All Running Emulators")
        self.acc_selected_radio = QRadioButton("Selected Emulator in first tab")
        self.acc_group = QButtonGroup()
        self.acc_group.addButton(self.acc_all_radio)
        self.acc_group.addButton(self.acc_selected_radio)
        self.acc_all_radio.setChecked(True)
        
        target_layout.addWidget(self.acc_all_radio)
        target_layout.addWidget(self.acc_selected_radio)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # Actions
        action_group = QGroupBox("Provisions")
        action_layout = QVBoxLayout()
        
        self.launch_account_btn = QPushButton("🚀 Launch Add Account Screen on Targeted Devices")
        self.launch_account_btn.setObjectName("secondaryButton")
        self.launch_account_btn.clicked.connect(self.launch_account_flow)
        action_layout.addWidget(self.launch_account_btn)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Batch Typing
        type_group = QGroupBox("Batch Text Injection (Type to All)")
        type_layout = QHBoxLayout()
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("Enter text/password to type into all devices...")
        self.type_btn = QPushButton("⌨️ Type to All")
        self.type_btn.clicked.connect(self.type_to_all)
        
        type_layout.addWidget(self.type_edit)
        type_layout.addWidget(self.type_btn)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        

        
        layout.addStretch()

    def _get_acc_targets(self):
        target_devices = []
        if self.acc_all_radio.isChecked():
            instances = self.emulator_manager.list_instances() if self.emulator_manager else []
            for inst in instances:
                if inst.state.value == "running" and inst.device_id:
                    target_devices.append(inst.device_id)
        else:
            instance_name = self.instance_combo.currentData()
            if instance_name:
                inst = self.emulator_manager.get_instance(instance_name)
                if inst and inst.device_id:
                    target_devices.append(inst.device_id)
        return target_devices

    def launch_account_flow(self):
        targets = self._get_acc_targets()
        if not targets:
            self.log("Error: No running emulators found.")
            return
            
        self.log(f"Launching account flow on {len(targets)} device(s)...")
        self.acc_worker = AccountAutomationWorker(targets, 'launch')
        self.acc_worker.progress.connect(self.log)
        self.acc_worker.start()

    def type_to_all(self):
        text = self.type_edit.text()
        if not text:
            return
            
        targets = self._get_acc_targets()
        if not targets:
            self.log("Error: No running emulators found.")
            return
            
        self.log(f"Typing text to {len(targets)} device(s)...")
        self.acc_worker = AccountAutomationWorker(targets, 'type', text)
        self.acc_worker.progress.connect(self.log)
        self.acc_worker.start()
        self.type_edit.clear()

    def browse_apk(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select APK File", "", "Android Package (*.apk)"
        )
        if file_path:
            self.apk_path_edit.setText(file_path)

    def start_apk_sideload(self):
        apk_path = Path(self.apk_path_edit.text().strip())
        if not apk_path.exists() or not apk_path.is_file():
            QMessageBox.warning(self, "Invalid File", "Please select a valid .apk file first.")
            return

        target_devices = []
        if self.apk_all_radio.isChecked():
            instances = self.emulator_manager.list_instances() if self.emulator_manager else []
            for inst in instances:
                if inst.state.value == "running" and inst.device_id:
                    target_devices.append(inst.device_id)
        else:
            instance_name = self.instance_combo.currentData()
            if instance_name:
                inst = self.emulator_manager.get_instance(instance_name)
                if inst and inst.device_id:
                    target_devices.append(inst.device_id)
        
        if not target_devices:
            self.log("Error: No running emulators found with device IDs.")
            return
            
        self.apk_btn.setEnabled(False)
        self.log(f"Starting sideload of {apk_path.name} to {len(target_devices)} device(s)...")
        
        self.apk_worker = APKSideloadWorker(apk_path, target_devices)
        self.apk_worker.progress.connect(self.log)
        self.apk_worker.finished.connect(self.on_apk_finished)
        self.apk_worker.start()

    def on_apk_finished(self, success, message):
        self.apk_btn.setEnabled(True)
        if success:
            self.log(f"Success: {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self.log(f"Error: {message}")
            QMessageBox.critical(self, "Error", f"Failed to install APK:\n{message}")

    def start_sideload(self):
        target_devices = []
        if self.sideload_all_radio.isChecked():
            instances = self.emulator_manager.list_instances() if self.emulator_manager else []
            for inst in instances:
                if inst.state.value == "running" and inst.device_id:
                    target_devices.append(inst.device_id)
        else:
            instance_name = self.instance_combo.currentData()
            if instance_name:
                inst = self.emulator_manager.get_instance(instance_name)
                if inst and inst.device_id:
                    target_devices.append(inst.device_id)
        
        if not target_devices:
            self.log("Error: No running emulators found with device IDs.")
            return
            
        self.sideload_btn.setEnabled(False)
        self.log(f"Starting sideload to {len(target_devices)} device(s)...")
        
        cache_dir = Path.home() / ".android_multi_emulator" / "cache"
        self.sideload_worker = MagiskSideloadWorker(cache_dir, target_devices)
        self.sideload_worker.progress.connect(self.log)
        self.sideload_worker.finished.connect(self.on_sideload_finished)
        self.sideload_worker.start()

    def on_sideload_finished(self, success, message):
        self.sideload_btn.setEnabled(True)
        if success:
            self.log(f"Success: {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self.log(f"Error: {message}")
            QMessageBox.critical(self, "Error", f"Failed to sideload Magisk:\n{message}")
        
    def update_preview(self):
        arg_val = self.args_combo.currentData()
        if arg_val == "CUSTOM":
            self.custom_args_edit.setVisible(True)
            args = "<custom_args>"
        else:
            self.custom_args_edit.setVisible(False)
            args = arg_val
            
        self.preview_label.setText(f"rootAVD.bat [path/to/ramdisk.img] {args}")

    def log(self, message):
        self.status_log.append(message)
        
    def find_ramdisk_path(self, instance_name):
        """Find ramdisk.img path for the instance"""
        if not self.emulator_manager:
            return None
            
        inst = self.emulator_manager.get_instance(instance_name)
        if not inst:
            return None
            
        # Get AVD directory
        avd_dir = self.emulator_manager.get_avd_dir(inst.avd_name)
        config_ini = avd_dir / "config.ini"
        
        if not config_ini.exists():
            self.log(f"Error: AVD config not found at {config_ini}")
            return None
            
        # Parse config.ini for image.sysdir.1
        sys_dir_rel = None
        try:
            with open(config_ini, 'r') as f:
                for line in f:
                    if line.strip().startswith("image.sysdir.1"):
                        # image.sysdir.1 = system-images\android-33\google_apis\x86_64\
                        parts = line.split("=", 1)
                        if len(parts) > 1:
                            sys_dir_rel = parts[1].strip()
                        break
        except Exception as e:
            self.log(f"Error reading config: {e}")
            return None
            
        if not sys_dir_rel:
            self.log("Error: Could not find 'image.sysdir.1' in config.ini")
            return None
            
        # Construct full path. SDK root + sys_dir_rel + ramdisk.img
        # We need SDK root. It's usually parent of .android or in env.
        # But wait, sys_dir_rel is relative to SDK root.
        # Where is SDK root? We can try to infer or get from config if stored.
        # self.emulator_manager.config doesn't explicitly store SDK_ROOT yet, usually inferred.
        # We can check common env vars.
        
        sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        if not sdk_root:
            # Fallback: check config.emulator_path
             if self.emulator_manager.config.emulator_path:
                 # emulator path is usually SDK/emulator/emulator.exe
                 sdk_root = str(Path(self.emulator_manager.config.emulator_path).parent.parent)
        
        if not sdk_root:
            self.log("Error: ANDROID_SDK_ROOT not set and could not infer from emulator path")
            return None
            
        ramdisk_path = Path(sdk_root) / sys_dir_rel / "ramdisk.img"
        # Normalize separators
        ramdisk_path = Path(str(ramdisk_path).replace("\\", os.sep).replace("/", os.sep))
        
        if not ramdisk_path.exists():
             self.log(f"Warning: ramdisk.img not found at {ramdisk_path}")
             # Check if it has a different name? Usually not for this purpose.
             return None
             
        # Return tuple: (sdk_root, relative_path_string)
        # sys_dir_rel is like "system-images\android-33\google_apis\x86_64\"
        # we append ramdisk.img
        rel_path = Path(sys_dir_rel) / "ramdisk.img"
        rel_path_str = str(rel_path).replace("\\", os.sep).replace("/", os.sep)
        
        return str(sdk_root), rel_path_str

    def start_rooting(self):
        instance_name = self.instance_combo.currentData()
        if not instance_name:
            self.log("Error: No instance selected")
            return

        ramdisk_info = self.find_ramdisk_path(instance_name)
        if not ramdisk_info:
            self.log("Failed to resolve ramdisk.img path. Cannot proceed.")
            return
            
        sdk_root, rel_path = ramdisk_info
        self.log(f"SDK Root: {sdk_root}")
        self.log(f"Target Ramdisk (Relative): {rel_path}")

        self.run_btn.setEnabled(False)
        self.log("Checking prerequisites...")
        
        cache_dir = Path.home() / ".android_multi_emulator" / "cache"
        self.worker = RootAVDWorker(cache_dir)
        self.worker.set_download_magisk(self.magisk_check.isChecked())
        self.worker.progress.connect(self.log)
        
        # Prepare valid arguments
        arg_val = self.args_combo.currentData()
        if arg_val == "CUSTOM":
            extra_args = self.custom_args_edit.toPlainText().strip()
        else:
            extra_args = arg_val
            
        self.worker.finished.connect(lambda s, r: self.on_worker_finished(s, r, sdk_root, rel_path, extra_args))
        self.worker.start()
        
    def on_worker_finished(self, success, result, sdk_root=None, rel_path=None, extra_args=""):
        self.run_btn.setEnabled(True)
        if success:
            self.log(f"RootAVD ready at: {result}")
            self.log("Launching script...")
            
            script_dir = Path(result)
            script_path = script_dir / "rootAVD.bat"
            
            # Strategy: Set ANDROID_HOME and pass relative path
            
            wrapper_path = script_dir / "run_root.bat"
            try:
                with open(wrapper_path, "w") as f:
                    f.write("@echo off\n")
                    f.write(f'title RootAVD\n')
                    f.write("echo ---------------------------------------------------\n")
                    f.write("echo SETTING ANDROID_HOME...\n")
                    f.write(f'set "ANDROID_HOME={sdk_root}"\n')
                    f.write("echo EXECUTING RootAVD...\n")
                    f.write(f'echo Path: {rel_path}\n')
                    f.write(f'call rootAVD.bat {rel_path} {extra_args}\n')
                    f.write("if %errorlevel% neq 0 echo Error occurred.\n")
                    f.write("pause\n")
                    f.write("exit\n")
            except Exception as e:
                self.log(f"Failed to create wrapper script: {e}")
                return

            self.log(f"Created wrapper: {wrapper_path}")
            
            try:
                # Execute the wrapper
                subprocess.Popen(
                    f'start "" "{wrapper_path}"', 
                    shell=True,
                    cwd=script_dir
                )
                self.accept()
            except Exception as e:
                self.log(f"Failed to launch script: {e}")
        else:
            self.log(f"Error: {result}")
            QMessageBox.critical(self, "Error", result)

