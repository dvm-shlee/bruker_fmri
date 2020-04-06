from PySide2 import QtCore, QtWidgets, QtGui


class ImageViewer(QtWidgets.QGraphicsView):
    pointed = QtCore.Signal(float, float, list)

    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self._scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self._scene)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setLineWidth(0)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self._background = None
        self._overlay = None
        self._overlay_item = None

    def setPixmap(self, pixmap: QtGui.QPixmap):
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        self._scene.addItem(item)
        self._background = item
        self._overlay = QtGui.QPixmap(pixmap.size())
        self._overlay.fill(QtCore.Qt.transparent)  # this will make overlay pixmap transparent
        self._overlay_item = self._scene.addPixmap(self._overlay)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        pos_x = event.pos().x()
        pos_y = event.pos().y()
        _, min_x, min_y, width, height = self.get_overlay_pos()
        # self.clean_crossline()
        self.pointed.emit(float(pos_x-min_x)/width, float(pos_y-min_y)/height,
                          [pos_x, pos_y, min_x, min_y, width, height])
        # self.draw_crossline(pos_x, pos_y)

    def get_overlay_pos(self):
        overlay = self._overlay_item.pixmap()
        qrect = overlay.rect()
        min_x = qrect.x()
        width = qrect.width()
        min_y = qrect.y()
        height = qrect.height()
        return overlay, min_x, min_y, width, height

    def clean_crossline(self):
        overlay = self._overlay_item.pixmap()
        overlay.fill(QtCore.Qt.transparent)  # clear previous drawing
        self._overlay_item.setPixmap(overlay)

    def draw_crossline(self, pos_x, pos_y):
        overlay, min_x, min_y, width, height = self.get_overlay_pos()
        painter = QtGui.QPainter(overlay)
        pen = QtGui.QPen()
        pen.setColor(QtCore.Qt.gray)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(pos_x, min_y, pos_x, height + min_y)
        painter.drawLine(min_x, pos_y, width + min_x, pos_y)
        painter.end()
        self._overlay_item.setPixmap(overlay)
        self.update()
