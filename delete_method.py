    def delete_selected_emulator(self):
        """Delete the selected emulator"""
        selected = self.emulator_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        instance_name = self.emulator_table.item(row, 0).text()
        
        msg = f"Are you sure you want to PERMANENTLY delete emulator '{instance_name}'?\n\n" \
              f"This will stop the emulator if running and DELETE all associated files (clone AVD)."
        
        if QMessageBox.question(self, "Confirm Delete", msg, 
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                              QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            
            self.logger.info(f"Deleting emulator '{instance_name}'")
            if self.emulator_manager.delete_instance(instance_name):
                self.input_synchronizer.remove_from_sync(instance_name)
                self.logger.info(f"Emulator '{instance_name}' deleted successfully")
                self.refresh_emulator_list()
                self.statusBar().showMessage(f"Deleted emulator '{instance_name}'")
            else:
                self.logger.warning(f"Failed to delete emulator '{instance_name}'")
                QMessageBox.warning(self, "Error", f"Failed to delete emulator '{instance_name}'. Check logs for details.")
