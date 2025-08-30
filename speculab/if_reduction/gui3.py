
import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QComboBox, QLineEdit, QLabel, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import inspect

import numpy as np

from pipeline_lib import load_custom_function, load_predefined_functions, run_pipeline


# --- Model ---
class Action:
    def __init__(self, name="", func_type='predefined', func_name='Multiply',
                 params=None, user_file='', user_func=''):
        self.name = name
        self.step_number = 0
        self.active = True
        self.func_type = func_type
        self.func_name = func_name
        self.params = params or {}
        self.user_file = user_file
        self.user_func = user_func



class ActionList:
    def __init__(self, predefined_functions):
        self.actions = []
        self.functions = predefined_functions

    def add_action(self, action):
        self.actions.append(action)

    def remove_action(self, index):
        if 0 <= index < len(self.actions):
            return self.actions.pop(index)
        return None

    def move_action(self, from_index, to_index):
        if 0 <= from_index < len(self.actions) and 0 <= to_index <= len(self.actions):
            action = self.actions.pop(from_index)
            if to_index > from_index:
                to_index -= 1
            self.actions.insert(to_index, action)

    def get_available_functions(self):
        return list(self.functions.keys())

    def get_function(self, name):
        return self.functions.get(name)

# --- Step Widget ---
import os
import inspect
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QFileDialog
)
from typing import get_type_hints

class StepWidget(QWidget):
    def __init__(self, action, parent=None):
        super().__init__(parent)
        self.action = action
        self.layout = QHBoxLayout()
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        # Step number
        self.number_label = QLabel(f"{self.action.step_number}")
        self.number_label.setFixedWidth(25)
        self.layout.addWidget(self.number_label)

        # Active checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(action.active)
        self.checkbox.stateChanged.connect(self.update_model)
        self.layout.addWidget(self.checkbox)

        # Vertical layout for function selection and custom file
        func_layout = QVBoxLayout()

        # Combobox
        self.func_selector = QComboBox()
        self.func_selector.addItems(list(predefined_functions.keys()) + ["Custom"])
        self.func_selector.setCurrentText(action.func_name)
        self.func_selector.currentTextChanged.connect(self.on_func_change)
        func_layout.addWidget(self.func_selector)

        # Editable function name
        self.user_func_input = QLineEdit(action.user_func)
        self.user_func_input.setFixedWidth(100)
        self.user_func_input.editingFinished.connect(self.update_model)
        self.user_func_input.setVisible(self.func_selector.currentText() == "Custom")
        func_layout.addWidget(self.user_func_input)

        # Load File button
        self.load_file_btn = QPushButton("Load File" if not action.user_file else os.path.basename(action.user_file))
        self.load_file_btn.clicked.connect(self.load_custom_file)
        self.load_file_btn.setVisible(self.func_selector.currentText() == "Custom")
        func_layout.addWidget(self.load_file_btn)

        # --- Parameters area
        self.params_layout = QVBoxLayout()
        self.layout.addLayout(self.params_layout)


        # Build initial parameters for the first selected function
        self.on_function_changed(self.func_combo.currentText())

    # -------------------------------------------------
    # 1) Load custom functions from user-provided file
    # -------------------------------------------------
    def load_custom_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Python File", "", "Python Files (*.py)"
        )
        if not file_path:
            return

        # Import dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("custom_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Add any callable functions from module
        self.loaded_functions.clear()
        for name in dir(module):
            attr = getattr(module, name)
            if callable(attr):
                self.loaded_functions[name] = attr
                self.func_combo.addItem(name)

    # -------------------------------------------------
    # 2) When function changes, rebuild parameter widgets
    # -------------------------------------------------
    def on_function_changed(self, func_name):
        # Clear previous widgets
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.param_editors.clear()

        # Get the callable from either predefined or loaded
        print(self.action_list.functions)
        func = self.loaded_functions.get(func_name) or self.action_list.get_function(func_name)
        if func is None:
            return

        sig = inspect.signature(func)
        hints = get_type_hints(func)

        for param_name, param in sig.parameters.items():
            param_type = hints.get(param_name, str)
            default_value = (
                "" if param.default is inspect.Parameter.empty else param.default
            )

            row_layout = QHBoxLayout()
            label = QLabel(param_name)
            row_layout.addWidget(label)

            # If it's a path-like parameter → QLineEdit + Browse
            if param_type in (os.PathLike, Path, str) and "path" in param_name.lower():
                editor = QLineEdit(str(default_value))
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda _, e=editor: self.browse_file(e))
                row_layout.addWidget(editor)
                row_layout.addWidget(browse_btn)
                self.param_editors[param_name] = editor
            else:
                # Default → just a QLineEdit
                editor = QLineEdit(str(default_value))
                row_layout.addWidget(editor)
                self.param_editors[param_name] = editor

            self.params_layout.addLayout(row_layout)
        self.update_model()

    # -------------------------------------------------
    # 3) Open file dialog for path parameters
    # -------------------------------------------------
    def browse_file(self, editor: QLineEdit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            editor.setText(file_path)

    # -------------------------------------------------
    # 4) Collect current parameter values for pipeline run
    # -------------------------------------------------
    def get_parameters(self):
        params = {}
        for name, editor in self.param_editors.items():
            params[name] = editor.text()
        return params


    def update_model(self):
        self.action.active = self.checkbox.isChecked()
        self.action.func_name = self.func_selector.currentText()
        self.action.func_type = "custom" if self.action.func_name == "Custom" else "predefined"
        self.action.user_func = self.user_func_input.text() if self.action.func_type == "custom" else ""
        try:
            self.action.param1 = float(self.param1.text())
            self.action.param2 = float(self.param2.text())
        except ValueError:
            pass
        #self.update_preview()

    def update_step_number(self, number):
        self.action.step_number = number
        self.number_label.setText(str(number))

    def set_preview(self, data):
        """Update the matplotlib preview with provided data (list)."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        print('Data:', data)
        if isinstance(data, np.ndarray):
            if len(data.shape) == 2:
                ax.imshow(data)
                print(data.sum())
            elif len(data.shape) == 1:
                ax.plot(data)
        self.canvas.draw()

# --- Main GUI ---
class PipelineGUI(QWidget):
    def __init__(self, action_list):
        super().__init__()
        self.setWindowTitle("Pipeline GUI Complete")
        self.resize(1000, 600)

        self.action_list = action_list
        self.undo_stack = []
        self.redo_stack = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.step_list = QListWidget()
        self.step_list.setDragDropMode(QListWidget.InternalMove)
        self.layout.addWidget(self.step_list)

        # Buttons
        self.add_button = QPushButton("Add Step")
        self.remove_button = QPushButton("Remove Selected Step")
        self.undo_button = QPushButton("Undo")
        self.redo_button = QPushButton("Redo")
        self.run_button = QPushButton("Run Pipeline")
        self.run_preview = QPushButton("Run Preview")
        for btn in [self.add_button, self.remove_button, self.undo_button, self.redo_button, self.run_button, self.run_preview]:
            self.layout.addWidget(btn)

        # Connections
        self.add_button.clicked.connect(self.add_step)
        self.remove_button.clicked.connect(self.remove_step)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.run_button.clicked.connect(self.run_pipeline)
        self.run_preview.clicked.connect(self.update_all_previews)
        self.step_list.model().rowsMoved.connect(self.on_rows_moved)

        self.refresh_list()

    # --- GUI Refresh ---
    def refresh_list(self):
        self.step_list.clear()
        for idx, action in enumerate(self.action_list.actions):
            action.step_number = idx + 1
            widget = StepWidget(self.action_list, idx+1)
            widget.update_step_number(idx+1)
            frame = QFrame()
            frame.setLayout(QVBoxLayout())
            frame.layout().setContentsMargins(0,0,0,0)
            frame.layout().addWidget(widget)
            frame.setStyleSheet("QFrame { border:1px solid gray; margin:2px; }")
            item = QListWidgetItem()
            item.setSizeHint(frame.sizeHint())
            self.step_list.addItem(item)
            self.step_list.setItemWidget(item, frame)

    # --- Step Operations ---
    def add_step(self):
        action = Action(name=f"Step {len(self.action_list.actions)+1}")
        self.action_list.add_action(action)
        self.undo_stack.append(('remove', len(self.action_list.actions)-1, action))
        self.redo_stack.clear()
        self.refresh_list()

    def remove_step(self):
        selected_items = self.step_list.selectedItems()
        for item in reversed(selected_items):
            row = self.step_list.row(item)
            action = self.action_list.remove_action(row)
            self.undo_stack.append(('add', row, action))
        self.redo_stack.clear()
        self.refresh_list()

    def undo(self):
        if not self.undo_stack: return
        op, index, action = self.undo_stack.pop()
        if op == 'remove':
            self.action_list.remove_action(index)
            self.redo_stack.append(('add', index, action))
        elif op == 'add':
            self.action_list.actions.insert(index, action)
            self.redo_stack.append(('remove', index, action))
        self.refresh_list()

    def redo(self):
        if not self.redo_stack: return
        op, index, action = self.redo_stack.pop()
        if op == 'remove':
            self.action_list.remove_action(index)
            self.undo_stack.append(('add', index, action))
        elif op == 'add':
            self.action_list.actions.insert(index, action)
            self.undo_stack.append(('remove', index, action))
        self.refresh_list()

    def on_rows_moved(self, parent, start, end, dest, row):
        self.action_list.move_action(start, row)
        self.refresh_list()

    def update_step_preview(self, step_name, data):
        """Callback to update the preview of a specific step."""
        for idx, action in enumerate(self.action_list.actions):
            if action.func_name == step_name:
                step_widget = self.get_step_widget(idx)
                step_widget.set_preview(data)
                break

    def get_func_and_param_lists(self):
        '''Generate function and parameter lists from current actions'''
        func_list = []
        param_list = []
        for idx, action in enumerate(self.action_list.actions):
            if not action.active:
                continue
            func = None
            if action.func_type == "predefined":
                func = predefined_functions.get(action.func_name)
            elif action.func_type == "custom" and action.user_file and action.user_func:
                func = load_custom_function(action.user_file, action.user_func)

            if func is None:
                print(f"Warning: Function for step {idx+1} is not defined.")
                continue

            params = []
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            # Skip first parameter (assumed to be generator input)
            if len(param_names) >= 2:
                params.append(action.param1)
            if len(param_names) >= 3:
                params.append(action.param2)

            func_list.append(func)
            param_list.append(params)

    def update_all_previews(self):
        """Run the pipeline in preview mode and update all step previews."""

        func_list, param_list = self.get_func_and_param_lists()

        for step_widget in self.step_list:
            step_widget.set_preview([])

        run_pipeline(func_list, param_list, preview=True, callback=self.update_step_preview)

    def run_pipeline(self):
        """Run the full pipeline without preview."""
        func_list, param_list = self.get_func_and_param_lists()
        run_pipeline(func_list, param_list, preview=False)

    def get_step_widget(self, index):
        """Retrieve the StepWidget from QListWidget item"""
        item = self.step_list.item(index)
        frame = self.step_list.itemWidget(item)
        return frame.layout().itemAt(0).widget()

predefined_functions= load_predefined_functions()
print(predefined_functions)

# --- Main ---
def main():
    app = QApplication(sys.argv)
    actions = ActionList(predefined_functions)
    actions.add_action(Action(name="Step 1"))
    actions.add_action(Action(name="Step 2"))
    gui = PipelineGUI(actions)
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()






