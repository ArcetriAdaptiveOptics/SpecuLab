import inspect
import os
from typing import get_type_hints, Iterator
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QVBoxLayout, QHBoxLayout, QApplication, QPushButton, QFileDialog
)
from pipeline_lib import classify_function


from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout, QFileDialog

class PathInputWidget(QWidget):
    '''
    A widget that combines a QLineEdit and a "Browse" button to select file paths.
    '''
    def __init__(self, parent=None, file_filter="All Files (*)"):
        super().__init__(parent)
        self.file_filter = file_filter

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit()
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self._on_browse)

        layout.addWidget(self.line_edit)
        layout.addWidget(self.browse_btn)

    def _on_browse(self):

        # We always use getSaveFileName to allow selecting non-existing files,
        # removing the confirm overwrite check so that it works for opening files as well.
        path, _ = QFileDialog.getSaveFileName(None, "Select File", "", self.file_filter,
                                              options=QFileDialog.DontConfirmOverwrite)
        if path:
            self.line_edit.setText(path)

    def get_text(self):
        """Return the current text in the line edit."""
        return self.line_edit.text()

    def set_text(self, text):
        """Set the text in the line edit."""
        self.line_edit.setText(str(text))



class FunctionForm(QWidget):
    def __init__(self, func, parent=None):
        super().__init__(parent)
        self.func = func
        self.widgets = {}

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        ftype = classify_function(self.func)
        if ftype == 'generic':
            remove_first = True
        else:
            remove_first = False

        sig = inspect.signature(self.func)
        hints = get_type_hints(self.func)

        doc = inspect.getdoc(self.func)
        if doc:
            first_line = doc.strip().splitlines()[0]
            doc_label = QLabel(first_line)
            doc_label.setStyleSheet("font-style: italic; color: gray;")
            layout.addWidget(doc_label)

        for i, (name, param) in enumerate(sig.parameters.items()):
            if i == 0 and hints.get(name, None) is Iterator:
                continue
            if i == 0 and remove_first:
                continue
            if name == 'preview':
                continue
            field_layout = QHBoxLayout()
            label = QLabel(name)
            field_layout.addWidget(label)

            hint = hints.get(name, str)  # default to str if no type hint

            widget = self._create_widget_for_type(hint, param.default)
            self.widgets[name] = widget
            field_layout.addWidget(widget)

            layout.addLayout(field_layout)

        if layout.count() == 0:
            layout.addWidget(QLabel("No parameters"))

        layout.addStretch()

    def _create_widget_for_type(self, hint, default):
        # Decide widget type based on type hint
        if hint == int:
            widget = QSpinBox()
            widget.setMaximum(999999)
            if default is not inspect.Parameter.empty:
                widget.setValue(default)
            return widget

        elif hint == float:
            widget = QDoubleSpinBox()
            widget.setMaximum(1e9)
            widget.setDecimals(6)
            if default is not inspect.Parameter.empty:
                widget.setValue(default)
            return widget

        elif hint == bool:
            widget = QCheckBox()
            if default is not inspect.Parameter.empty:
                widget.setChecked(default)
            return widget

        elif hint == os.PathLike:
            widget = PathInputWidget()
            if default is not inspect.Parameter.empty:
                widget.set_text(str(default))
            return widget

        else:  # fallback: string
            widget = QLineEdit()
            if default is not inspect.Parameter.empty:
                widget.setText(str(default))
            return widget

    def get_values(self):
        values = {}
        for name, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, PathInputWidget):
                values[name] = widget.get_text()
        return values

    def set_values(self, values: dict):
        for name, value in values.items():
            widget = self.widgets.get(name)
            if widget is None:
                continue
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, PathInputWidget):
                widget.set_text(str(value))

# Example usage
def example_func(name: str, age: int = 30, score: float = 88.5, active: bool = True):
    pass

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    form = FunctionForm(example_func)
    form.show()

    sys.exit(app.exec_())
