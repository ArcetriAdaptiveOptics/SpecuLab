import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QStackedWidget,
    QSizePolicy, QDialog
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from function_selector import FunctionSelector
from function_form import FunctionForm

class StepWidget(QWidget):
    def __init__(self, initial_file=None, parent=None):
        super().__init__(parent)

        self.forms = {}  # {func_name: FunctionForm}
        self.preview_data = None

        self._build_ui(initial_file)

    def _build_ui(self, initial_file):
        layout = QHBoxLayout(self)

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable")
        self.enable_checkbox.setChecked(True)
        layout.addWidget(self.enable_checkbox)

        # Function selector
        self.function_selector = FunctionSelector(initial_file=initial_file)
        self.function_selector.functionSelected.connect(self._on_function_selected)
        layout.addWidget(self.function_selector)

        # Stack of forms (only one visible at a time)
        self.form_stack = QStackedWidget()
        self.form_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.form_stack)

        # Matplotlib preview
        self.figure = Figure(figsize=(1, 1))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.canvas.setFixedSize(100, 100)
        self.canvas.mpl_connect("button_press_event", self._on_preview_clicked)
        layout.addWidget(self.canvas)

    def clear_preview(self):
        """
        Clear the small preview plot.
        """
        self.figure.clf()
        self.canvas.draw()

    def _on_function_selected(self, func_name, func_obj):
        if func_obj is None:
            return
        if func_name not in self.forms:
            form = FunctionForm(func_obj)
            self.forms[func_name] = form
            self.form_stack.addWidget(form)

        # Switch to the correct form
        form = self.forms[func_name]
        index = self.form_stack.indexOf(form)
        self.form_stack.setCurrentIndex(index)

    def _plot_to_ax(self, ax, data):
        """Helper function to plot data to a given matplotlib axis."""
        ax.clear()
        if isinstance(data, np.ndarray):
            if data.ndim == 1:
                ax.plot(data)
            elif data.ndim == 2:
                ax.imshow(data)
        ax.figure.canvas.draw()

    def update_preview(self, data):
        """Updates the small matplotlib preview."""
        self.preview_data = data
        ax = self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._plot_to_ax(ax, data)
#        self.canvas.draw()

    def _on_preview_clicked(self, event):
        print('Preview clicked')
        if self.preview_data is None:
            return
        self._open_large_preview()

    def _open_large_preview(self):
        """Opens a non-modal larger view of the same data."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Preview")
        dlg.setModal(False)
        dlg.resize(800, 600)

        vbox = QVBoxLayout(dlg)
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        vbox.addWidget(canvas)

        ax = fig.add_subplot(111)
        data = self.preview_data
        self._plot_to_ax(ax, data)
#        canvas.draw()

        dlg.show()

    def get_state(self):
        return {
            "enabled": self.enable_checkbox.isChecked(),
            "file": self.function_selector.get_selected_file(),
            "function": self.function_selector.get_selected_function(),
            "forms": {
                fname: form.get_values()
                for fname, form in self.forms.items()
            }
        }

    def set_state(self, state):
        # Restore enabled state
        self.enable_checkbox.setChecked(state.get("enabled", True))

        # Restore selected file & function
        file_path = state.get("file")
        func_name = state.get("function")

        # Set file and update available functions
        self.function_selector.set_selected_file(file_path)
        self.function_selector.set_selected_function(func_name)

        # Restore all form states if present
        form_states = state.get("forms", {})

        for fname, fstate in form_states.items():
            # Create the form if it doesn't exist yet
            if fname not in self.forms:
                func_obj = self.function_selector.get_function_object(fname)
                if func_obj:
                    form = FunctionForm(func_obj)
                    self.forms[fname] = form
                    self.form_stack.addWidget(form)

            # If we have the form now, set its state
            if fname in self.forms:
                self.forms[fname].set_values(fstate)

        # Show the selected form
        self._on_function_selected(func_name, self.function_selector.get_function_object(func_name))

# Example usage
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    w = StepWidget(initial_file=__file__)
    w.update_preview([1, 3, 2, 5, 4, 6])
    w.show()

    sys.exit(app.exec_())
