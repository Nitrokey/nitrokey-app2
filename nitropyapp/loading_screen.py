from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSortFilterProxyModel, QRect
from PyQt5.Qt import QLabel, QMovie, QProgressBar
import nitropyapp.ui.breeze_resources
#pyrcc5 -o gui_resources.py ui/resources.qrc
import nitropyapp.gui_resources

class LoadingScreen(QtWidgets.QWidget):
    # def __init__(self):
    #     super().__init__()
    #     self.setFixedSize(128,128)  #128 128
    #     self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

    #     self.label_animation = QLabel(self)
    #     self.qprogressbar = QProgressBar(self)
    #     self.setGeometry(QRect(650,300,0,0))
        #self.movie = QMovie(":/images/ProgressWheel.GIF")
        #self.label_animation.setMovie(self.movie)

        #timer = QTimer(self)
        #self.startAnimation()
        #timer.singleShot(1000, self.stopAnimation)

    #    self.show()

    def startAnimation(self):
        self.movie.start()

    def stopAnimation(self):
        #self.movie.stop()
        self.close()
        GUI.user_info("success","You now have a main key with the capability\n to sign and certify and a subkey for encryption.  ",title ="Key generation was successful", parent=self.label_animation)
