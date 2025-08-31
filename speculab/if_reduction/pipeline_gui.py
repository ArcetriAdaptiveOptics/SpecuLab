import sys
import yaml
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QListWidgetItem,
    QToolBar, QAction, QFileDialog, QPushButton, QWidget,
    QVBoxLayout, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import PyQt5.QtGui as QtGui
from pipeline_lib import run_pipeline

from step_widget import StepWidget


class EmittingStream(QObject):
    textWritten = pyqtSignal(str)

    def write(self, text):
        if text:
            self.textWritten.emit(str(text))

    def flush(self):
        pass


class FunctionRunner(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(object)  # optional: return value

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        # Redirect stdout/stderr in this thread
        class Stream:
            def write(self_inner, text):
                if text:
                    self.log_signal.emit(text)
            def flush(self_inner):
                pass

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = Stream()

        try:
            self.result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            self.finished_signal.emit(self.result)


class MainWindow(QMainWindow):

    callback_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Editor")
        self.setGeometry(200, 200, 1200, 600)

        self.undo_stack = []
        self.redo_stack = []

        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # List of steps
        self.step_list = QListWidget()
        self.step_list.setDragDropMode(QListWidget.InternalMove)

        size_policy = self.step_list.sizePolicy()
        size_policy.setVerticalPolicy(QSizePolicy.Expanding)
        self.step_list.setSizePolicy(size_policy)
        
        layout.addWidget(self.step_list)

        # Run buttons
        self.run_preview_btn = QPushButton("Run Preview")
        self.run_pipeline_btn = QPushButton("Run Pipeline")
        self.run_preview_btn.clicked.connect(self.run_preview)
        self.run_pipeline_btn.clicked.connect(self.run_pipeline)
        layout.addWidget(self.run_preview_btn)
        layout.addWidget(self.run_pipeline_btn)

        self.interrupt_btn = QPushButton("Interrupt")
        self.interrupt_btn.setEnabled(False)  # initially disabled
        self.interrupt_btn.clicked.connect(self._interrupt_pipeline)
        layout.addWidget(self.interrupt_btn)

        self.setCentralWidget(central_widget)

        # Toolbar
        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)

        add_action = QAction("Add Step", self)
        add_action.triggered.connect(self.add_step)
        toolbar.addAction(add_action)

        remove_action = QAction("Remove Step", self)
        remove_action.triggered.connect(self.remove_step)
        toolbar.addAction(remove_action)

        toolbar.addSeparator()

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_state)
        toolbar.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.triggered.connect(self.load_state)
        toolbar.addAction(load_action)

        toolbar.addSeparator()

        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undo)
        toolbar.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.redo)
        toolbar.addAction(redo_action)

        # Add log text widget at the bottom
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget)

        layout.setStretchFactor(self.step_list, 3)
        layout.setStretchFactor(self.log_widget, 1)

        # Create streams
        self.stdout_stream = EmittingStream()
        self.stderr_stream = EmittingStream()
        self.stdout_stream.textWritten.connect(self._append_log)
        self.stderr_stream.textWritten.connect(self._append_log)

        self.callback_signal.connect(self._update_step_previews)
        # Start with one default step
        self.add_step()
        self._append_log('Pipeline editor initialized.\n')

    def _append_log(self, text):
        """Append text to the log widget and auto-scroll."""
        self.log_widget.moveCursor(QtGui.QTextCursor.End)
        self.log_widget.insertPlainText(text)
        self.log_widget.moveCursor(QtGui.QTextCursor.End)
        self.log_widget.ensureCursorVisible()

    def run_any_function(self, func, *args, **kwargs):
        """
        Runs an arbitrary function in the background and logs stdout/stderr.
        """
        self.runner = FunctionRunner(func, *args, **kwargs)
        self.runner.log_signal.connect(self._append_log)
        self.runner.finished_signal.connect(lambda res: print("Function finished:", res))
        self.runner.finished_signal.connect(lambda: self.run_pipeline_btn.setEnabled(True))
        self.runner.finished_signal.connect(lambda: self.run_preview_btn.setEnabled(True))
        self.runner.finished_signal.connect(lambda: self.interrupt_btn.setEnabled(False))
        self.runner.start()

    def _interrupt_pipeline(self):
        if self.runner.isRunning():
            self.runner.requestInterruption()

    def check_interrupt_callback(self):
        return self.runner.isInterruptionRequested()
    
    def add_step(self, state=None, row=None):
        step = StepWidget(initial_file='pipeline.py')
        if state:
            step.set_state(state)

        item = QListWidgetItem()
        item.setSizeHint(step.sizeHint())

        if row is None:
            self.step_list.addItem(item)
            self.step_list.setItemWidget(item, step)
            row = self.step_list.row(item)
        else:
            self.step_list.insertItem(row, item)
            self.step_list.setItemWidget(item, step)

        # Record action for undo
        self.undo_stack.append(("add", row))
        self.redo_stack.clear()

    def get_all_states(self):
        states = []
        for i in range(self.step_list.count()):
            item = self.step_list.item(i)
            step = self.step_list.itemWidget(item)
            states.append(step.get_state())
        return states

    def set_all_states(self, states):
        self.step_list.clear()
        for state in states:
            self.add_step(state)

    def save_state(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Pipeline", "", "YAML Files (*.yml)")
        if not path:
            return

        with open(path, "w") as f:
            yaml.dump(self.get_all_states(), f)

    def load_state(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Pipeline", "", "YAML Files (*.yml)")
        if not path:
            return

        with open(path, "r") as f:
            states = yaml.safe_load(f)

        self.set_all_states(states)

    def remove_step(self):
        current_row = self.step_list.currentRow()
        if current_row < 0:
            return

        item = self.step_list.item(current_row)
        step = self.step_list.itemWidget(item)
        if step is None:
            return  # Safety fallback

        state = step.get_state()

        # Now remove safely
        self.step_list.takeItem(current_row)

        # Record for undo
        self.undo_stack.append(("remove", (current_row, state)))
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return

        action, data = self.undo_stack.pop()

        if action == "add":
            row = data
            item = self.step_list.item(row)
            step = self.step_list.itemWidget(item)
            state = step.get_state() if step else None

            # Remove the step safely
            self.step_list.takeItem(row)
            self.redo_stack.append(("add", (row, state)))

        elif action == "remove":
            row, state = data
            self.add_step(state=state, row=row)
            self.redo_stack.append(("remove", row))

    def redo(self):
        if not self.redo_stack:
            return

        action, data = self.redo_stack.pop()

        if action == "add":
            row, state = data
            self.add_step(state=state, row=row)
            self.undo_stack.append(("add", row))

        elif action == "remove":
            row = data
            item = self.step_list.item(row)
            step = self.step_list.itemWidget(item)
            state = step.get_state() if step else None

            # Remove safely
            self.step_list.takeItem(row)
            self.undo_stack.append(("remove", (row, state)))

    def get_pipeline_functions_and_args(self):
        funcs = []
        args_list = []
        flag_list = []

        for i in range(self.step_list.count()):
            item = self.step_list.item(i)
            step = self.step_list.itemWidget(item)

            if not step.enable_checkbox.isChecked():
                continue  # skip disabled steps

            func_name = step.function_selector.get_selected_function()
            func_obj = step.function_selector.get_function_object(func_name)
            mp_enabled = step.function_selector.get_mp_enabled()
            if func_obj is None:
                continue

            # Get the arguments from the form corresponding to this function
            form = step.forms.get(func_name)
            if form is None:
                continue

            args = form.get_values()

            funcs.append(func_obj)
            args_list.append(args)
            flag_list.append({'mp_enabled': mp_enabled})

        return funcs, args_list, flag_list

    def update_step_previews(self, preview_results):
        """
        Update the preview plots for each step based on function objects.

        Parameters
        ----------
        preview_results : dict
            Keys are function objects, values are preview data (list or array).
            Example: {func_obj_0: [1,2,3], func_obj_1: [4,5,6]}
        """
        self.callback_signal.emit(preview_results)

    def _update_step_previews(self, preview_results):

        for i in range(self.step_list.count()):
            item = self.step_list.item(i)
            step = self.step_list.itemWidget(item)
            if step is None:
                continue

            func_name = step.function_selector.get_selected_function()
            func_obj = step.function_selector.get_function_object(func_name)
            if func_obj in preview_results:
                step.update_preview(preview_results[func_obj])

    def _run_pipeline(self, preview=False):
        func_list, args_list, flag_list = window.get_pipeline_functions_and_args()
        run_pipeline(func_list, args_list, flag_list, preview=preview,
                     callback=self.update_step_previews,
                     check_interrupt_callback=self.check_interrupt_callback)

    def run_preview(self):
        """Run the pipeline preview using the background runner."""
        # Disable the buttons while running
        self.run_preview_btn.setEnabled(False)
        self.run_pipeline_btn.setEnabled(False)
        self.interrupt_btn.setEnabled(True)
        for i in range(self.step_list.count()):
            item = self.step_list.item(i)
            step = self.step_list.itemWidget(item)
            step.clear_preview()
        self.run_any_function(lambda: self._run_pipeline(preview=True))

    def run_pipeline(self):
        """Run the full pipeline using the background runner."""
        # Disable the buttons while running
        self.run_preview_btn.setEnabled(False)
        self.run_pipeline_btn.setEnabled(False)
        self.interrupt_btn.setEnabled(True)
        self.run_any_function(lambda: self._run_pipeline(preview=False))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())