import os
import inspect
import importlib.util
from PyQt5.QtCore import pyqtSignal, QFileSystemWatcher
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox,
    QVBoxLayout, QHBoxLayout, QFileDialog
)

class FunctionSelector(QWidget):
    functionSelected = pyqtSignal(str, object)  # (func_name, func_obj)

    def __init__(self, initial_file=None, parent=None):
        super().__init__(parent)

        self.current_file = None
        self.functions = {}
        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self._on_file_changed)

        self._build_ui()

        if initial_file and os.path.isfile(initial_file):
            self.set_selected_file(initial_file)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Top bar: file label + browse button
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.browse_btn)

        # ComboBox for functions
        self.func_combo = QComboBox()
        self.func_combo.currentTextChanged.connect(self._on_function_selected)

        layout.addLayout(file_layout)
        layout.addWidget(self.func_combo)

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Python File", "", "Python Files (*.py)")
        if path:
            self.set_selected_file(path)

    def set_selected_file(self, file_path):
        """Sets the selected file, loads its functions, updates UI, and emits if possible."""
        if not os.path.isfile(file_path):
            return

        # Stop watching old file
        if self.current_file and self.current_file in self.watcher.files():
            self.watcher.removePath(self.current_file)

        self.current_file = os.path.abspath(file_path)
        self.file_label.setText(os.path.basename(self.current_file))

        # Start watching new file
        self.watcher.addPath(self.current_file)

        self._load_functions()

        if self.func_combo.count() > 0:
            self.func_combo.setCurrentIndex(0)
            self._emit_selected_function()

    def get_selected_file(self):
        return self.current_file

    def _load_functions(self):
        """Dynamically import the module and list all top-level functions."""
        self.functions.clear()
        self.func_combo.clear()

        if not self.current_file:
            return

        spec = importlib.util.spec_from_file_location("_dynamic_module", self.current_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # list functions sorted by name
        for name, obj in sorted(inspect.getmembers(module, inspect.isfunction), key=lambda x: x[0]):
            # Only include top-level functions defined in this file
            if obj.__module__ == module.__name__ and not name.startswith("_"):
                self.functions[name] = obj
                self.func_combo.addItem(name)

    def get_function_object(self, func_name):
        return self.functions.get(func_name)

    def _on_function_selected(self, func_name):
        if func_name in self.functions:
            self._emit_selected_function()

    def _emit_selected_function(self):
        func_name = self.func_combo.currentText()
        func_obj = self.functions.get(func_name)
        if func_obj:
            self.functionSelected.emit(func_name, func_obj)

    def get_selected_function(self):
        return self.func_combo.currentText()

    def set_selected_function(self, func_name):
        """Sets the combo selection and emits signal."""
        index = self.func_combo.findText(func_name)
        if index >= 0:
            self.func_combo.setCurrentIndex(index)
            self._emit_selected_function()

    def _on_file_changed(self):
        """Auto-refresh functions when file changes."""
        previous_func = self.func_combo.currentText()
        self._load_functions()

        # Try to restore selection if possible
        index = self.func_combo.findText(previous_func)
        if index >= 0:
            self.func_combo.setCurrentIndex(index)
            self._emit_selected_function()
        elif self.func_combo.count() > 0:
            self.func_combo.setCurrentIndex(0)
            self._emit_selected_function()

# Example usage
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    def on_func_selected(name, func):
        print(f"Selected function: {name} -> {func}")

    app = QApplication(sys.argv)
    w = FunctionSelector(initial_file=__file__)
    w.functionSelected.connect(on_func_selected)
    w.show()
    sys.exit(app.exec_())
