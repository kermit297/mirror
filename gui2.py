from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class Application(QApplication):
    def __init__(self):
        QApplication.__init__(self, [])

        self.window = QWidget()

        p = self.window.palette()
        p.setColor(self.window.backgroundRole(), Qt.red)
        self.window.setPalette(p)

        frame1 = Frame()

        layout_window = QVBoxLayout()
        layout_window.addWidget(frame1)

        self.window.setLayout(layout_window)
        self.window.show()


class Frame(QFrame):

    def __init__(self):
        QFrame.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QPushButton('Top'))

        canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(canvas)
        self.ax = canvas.figure.subplots()

        self.data = np.arange(1,100,1)

        self.plt_timer = QTimer()
        self.plt_timer.timeout.connect(self.update_plt)
        self.plt_timer.start(500)

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def tick(self):
        pass
        #print("tick")

    def update_plt(self):
        #print(self.data)
        self.ax.clear()
        self.ax.plot(self.data)
        self.ax.figure.canvas.draw()
        self.data = np.roll(self.data, 1, 0)

app = Application()
app.exec_()
