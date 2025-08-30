import sys, os, importlib.util, inspect
from itertools import islice
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QComboBox, QLineEdit, QLabel, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- Load predefined functions from pipeline.py ---
def load_predefined_functions(filename="pipeline.py"):
    functions = {}
    if not os.path.exists(filename):
        print(f"{filename} not found.")
        return functions
    spec = importlib.util.spec_from_file_location("pipeline", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and getattr(obj, "_is_pipe", False):
            functions[name] = obj
    return functions

predefined_functions = load_predefined_functions("pipeline.py")

def load_custom_function(file, func_name):
    if not file or not func_name:
        return None
    if os.path.exists(file):
        spec = importlib.util.spec_from_file_location("custom_module", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, func_name):
            return getattr(module, func_name)
    return None

# --- Model ---
class Action:
    def __init__(self, name="", func_type='predefined', func_name='', param1=None, param2=None, user_file='', user_func=''):
        self.name = name
        self.step_number = 0
        self.active = True
        self.func_type = func_type
        self.func_name = func_name
        self.param1 = param1
        self.param2 = param2
        self.user_file = user_file
        self.user_func = user_func

class ActionList:
    def __init__(self):
        self.actions = []

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

# --- Step Widget ---
class StepWidget(QWidget):
    def __init__(self, action):
        super().__init__()
        self.action = action
        self.layout = QHBoxLayout()
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        # Drag handle
        self.handle = QLabel("≡")
        self.handle.setFixedWidth(20)
        self.handle.setAlignment(Qt.AlignCenter)
        self.handle.setStyleSheet("background-color: lightgray; border: 1px solid gray;")
        self.layout.addWidget(self.handle)

        # Step number
        self.number_label = QLabel(f"{self.action.step_number}")
        self.number_label.setFixedWidth(25)
        self.layout.addWidget(self.number_label)

        # Active checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(action.active)
        self.checkbox.stateChanged.connect(self.update_model)
        self.layout.addWidget(self.checkbox)

        # Function selector + params in vertical layout
        func_layout = QVBoxLayout()
        self.func_selector = QComboBox()
        self.func_selector.addItems(list(predefined_functions.keys()) + ["Custom"])
        if action.func_name in predefined_functions:
            self.func_selector.setCurrentText(action.func_name)
        else:
            self.func_selector.setCurrentText("Custom")
        self.func_selector.currentTextChanged.connect(self.on_func_change)
        func_layout.addWidget(self.func_selector)

        # Editable function name for custom
        self.user_func_input = QLineEdit(action.user_func)
        self.user_func_input.setFixedWidth(100)
        self.user_func_input.editingFinished.connect(self.update_model)
        self.user_func_input.setVisible(self.func_selector.currentText()=="Custom")
        func_layout.addWidget(self.user_func_input)

        # Load file button for custom
        self.load_file_btn = QPushButton("Load File" if not action.user_file else os.path.basename(action.user_file))
        self.load_file_btn.clicked.connect(self.load_custom_file)
        self.load_file_btn.setVisible(self.func_selector.currentText()=="Custom")
        func_layout.addWidget(self.load_file_btn)

        self.layout.addLayout(func_layout)

        # Parameters
        param_layout = QVBoxLayout()
        self.param1 = QLineEdit("" if action.param1 is None else str(action.param1))
        self.param1.setFixedWidth(50)
        self.param1.setStyleSheet("border:none; background: transparent;")
        self.param1.editingFinished.connect(self.update_model)
        p1_layout = QHBoxLayout()
        p1_layout.addWidget(QLabel("Param1:"))
        p1_layout.addWidget(self.param1)
        param_layout.addLayout(p1_layout)

        self.param2 = QLineEdit("" if action.param2 is None else str(action.param2))
        self.param2.setFixedWidth(50)
        self.param2.setStyleSheet("border:none; background: transparent;")
        self.param2.editingFinished.connect(self.update_model)
        p2_layout = QHBoxLayout()
        p2_layout.addWidget(QLabel("Param2:"))
        p2_layout.addWidget(self.param2)
        param_layout.addLayout(p2_layout)
        self.layout.addLayout(param_layout)

        # Matplotlib preview
        self.fig = Figure(figsize=(1.5,1))
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

        self.update_param_fields()
        self.update_preview()

    def load_custom_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select Python file", "", "Python Files (*.py)")
        if fname:
            self.action.user_file = fname
            self.load_file_btn.setText(os.path.basename(fname))
            self.update_param_fields()
            self.update_preview()

    def on_func_change(self, text):
        is_custom = (text=="Custom")
        self.user_func_input.setVisible(is_custom)
        self.load_file_btn.setVisible(is_custom)
        self.update_param_fields()
        self.update_preview()

    def update_model(self):
        self.action.active = self.checkbox.isChecked()
        self.action.func_name = self.func_selector.currentText()
        self.action.func_type = "custom" if self.action.func_name=="Custom" else "predefined"
        self.action.user_func = self.user_func_input.text() if self.action.func_type=="custom" else ""
        self.action.param1 = None if self.param1.text()=="" else float(self.param1.text())
        self.action.param2 = None if self.param2.text()=="" else float(self.param2.text())
        self.update_param_fields()
        self.update_preview()

    def update_param_fields(self):
        func = None
        if self.action.func_type=="predefined":
            func = predefined_functions.get(self.action.func_name)
        elif self.action.func_type=="custom":
            func = load_custom_function(self.action.user_file, self.action.user_func)
        if func:
            params = list(inspect.signature(func).parameters.values())
            # First param is input generator, remaining optional
            self.param1.setEnabled(len(params)>=2)
            if len(params)<2: self.param1.setText("")
            self.param2.setEnabled(len(params)>=3)
            if len(params)<3: self.param2.setText("")

    def update_preview(self):
        gen = None
        try:
            func = None
            if self.action.func_type=="predefined":
                func = predefined_functions.get(self.action.func_name)
            elif self.action.func_type=="custom":
                func = load_custom_function(self.action.user_file, self.action.user_func)
            if func:
                sig = list(inspect.signature(func).parameters.values())
                args = []
                if len(sig)>=2 and self.action.param1 is not None: args.append(self.action.param1)
                if len(sig)>=3 and self.action.param2 is not None: args.append(self.action2.param2)
                # First step: call without input
                gen = func(*args)
        except:
            gen = []
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.plot(list(islice(gen,10)))
        self.canvas.draw()

    def update_step_number(self, number):
        self.action.step_number = number
        self.number_label.setText(str(number))


# --- Pipeline GUI ---
class PipelineGUI(QWidget):
    def __init__(self, action_list):
        super().__init__()
        self.setWindowTitle("Pipeline GUI")
        self.action_list = action_list
        self.undo_stack = []
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Steps list
        self.step_list = QListWidget()
        self.step_list.setDragDropMode(QListWidget.InternalMove)
        self.layout.addWidget(self.step_list)

        # Add/remove buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Step")
        self.add_btn.clicked.connect(self.add_step)
        self.remove_btn = QPushButton("Remove Step")
        self.remove_btn.clicked.connect(self.remove_step)
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self.undo)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.undo_btn)
        self.layout.addLayout(btn_layout)

        # Run button
        self.run_btn = QPushButton("Run Pipeline")
        self.run_btn.clicked.connect(self.run_pipeline)
        self.layout.addWidget(self.run_btn)

        self.refresh_list()

    def refresh_list(self):
        self.step_list.clear()
        for idx, action in enumerate(self.action_list.actions):
            action.step_number = idx + 1
            widget = StepWidget(action)
            frame = QFrame()
            frame.setLayout(QVBoxLayout())
            frame.layout().setContentsMargins(0,0,0,0)
            frame.layout().addWidget(widget)
            frame.setStyleSheet("QFrame { border:1px solid gray; margin:2px; }")
            item = QListWidgetItem()
            item.setSizeHint(frame.sizeHint())
            self.step_list.addItem(item)
            self.step_list.setItemWidget(item, frame)

    def add_step(self):
        action = Action(name=f"Step {len(self.action_list.actions)+1}")
        self.action_list.add_action(action)
        self.undo_stack.append(('remove', len(self.action_list.actions)-1, action))
        self.refresh_list()

    def remove_step(self):
        index = self.step_list.currentRow()
        if index >=0:
            action = self.action_list.remove_action(index)
            self.undo_stack.append(('add', index, action))
            self.refresh_list()

    def undo(self):
        if not self.undo_stack:
            return
        op, index, action = self.undo_stack.pop()
        if op=='remove':
            self.action_list.remove_action(index)
        elif op=='add':
            self.action_list.actions.insert(index, action)
        self.refresh_list()

    def run_pipeline(self):
        gen = None
        for step in self.action_list.actions:
            if not step.active:
                continue
            func = None
            if step.func_type=="predefined":
                func = predefined_functions.get(step.func_name)
            elif step.func_type=="custom":
                func = load_custom_function(step.user_file, step.user_func)
            if func is None:
                continue
            sig = list(inspect.signature(func).parameters.values())
            args = []
            if gen is None:
                if len(sig)>=1 and step.param1 is not None: args.append(step.param1)
                if len(sig)>=2 and step.param2 is not None: args.append(step.param2)
                gen = func(*args)
            else:
                if len(sig)>=2 and step.param1 is not None: args.append(step.param1)
                if len(sig)>=3 and step.param2 is not None: args.append(step.param2)
                gen = func(gen, *args)
        # Consume final generator
        output = list(gen) if gen else []
        print("Pipeline output:", output)


# --- Main ---
def main():
    app = QApplication(sys.argv)
    actions = ActionList()
    gui = PipelineGUI(actions)
    gui.show()
    sys.exit(app.exec_())

if __name__=="__main__":
    main()
