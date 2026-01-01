"""Background worker thread for emulator operations"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional

from ..emulator_manager import EmulatorManager, EmulatorInstance


class EmulatorCreationWorker(QThread):
    """Worker thread for creating emulator instances without blocking UI"""
    
    finished = pyqtSignal(object)  # Emits EmulatorInstance or None on completion
    progress = pyqtSignal(str)  # Emits progress messages
    error = pyqtSignal(str)  # Emits error messages
    
    def __init__(self, emulator_manager: EmulatorManager, avd_name: str, 
                 instance_name: Optional[str] = None, create_clone: bool = True):
        super().__init__()
        self.emulator_manager = emulator_manager
        self.avd_name = avd_name
        self.instance_name = instance_name
        self.create_clone = create_clone
    
    def run(self):
        """Run the emulator creation in background thread"""
        try:
            if self.create_clone:
                self.progress.emit(f"Preparing to clone AVD '{self.avd_name}'...")
                import time
                clone_name = f"{self.avd_name}_clone_{int(time.time())}"
                
                self.progress.emit(f"Copying AVD files for '{clone_name}'...")
                if not self.emulator_manager.create_clone_avd(self.avd_name, clone_name):
                    self.error.emit(f"Failed to clone AVD '{self.avd_name}'")
                    self.finished.emit(None)
                    return
                
                self.progress.emit(f"Clone created successfully. Starting emulator '{clone_name}'...")
                # Clones should not need -read-only since they're different AVDs
                instance = self.emulator_manager.start_emulator(clone_name, self.instance_name or clone_name, use_readonly=False)
                # Store the original AVD name for reference
                if instance:
                    instance.created_from = self.avd_name
                    self.progress.emit(f"Emulator '{instance.name}' is booting (this may take 1-2 minutes)...")
            else:
                self.progress.emit(f"Starting emulator from AVD '{self.avd_name}'...")
                instance = self.emulator_manager.start_emulator(self.avd_name, self.instance_name)
                if instance:
                    self.progress.emit(f"Emulator '{instance.name}' is booting...")
            
            if instance:
                self.progress.emit(f"Emulator '{instance.name}' started successfully on port {instance.port}")
                self.finished.emit(instance)
            else:
                self.error.emit(f"Failed to start emulator from AVD '{self.avd_name}'")
                self.finished.emit(None)
                
        except Exception as e:
            self.error.emit(f"Error creating emulator: {str(e)}")
            self.finished.emit(None)
