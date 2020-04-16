from PySide2 import QtCore, QtWidgets, QtGui


class SliceViewer(QtWidgets.QGraphicsView):
    pointed = QtCore.Signal(float, float, list)

    def __init__(self, parent=None):
        super(SliceViewer, self).__init__(parent)
        # namespace
        self._underlay = None
        self._overlay = None

        # setup Scene
        self._scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self._scene)
        self._scene.setBackgroundBrush(QtCore.Qt.black)

        # set attributes
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(True)

        # self.setLineWidth(0)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)

    def setPixmap(self, pixmap: QtGui.QPixmap):
        item_size = pixmap.copy().size()
        view_size = self.size()
        num_layer = len(self._scene.items())
        if num_layer:
            self._scene.removeItem(self._underlay)
            self._scene.removeItem(self._overlay)
        self._underlay = QtWidgets.QGraphicsPixmapItem(pixmap)
        if self._overlay is None:
            empty_pixmap = QtGui.QPixmap(item_size)
            empty_pixmap.fill(QtCore.Qt.transparent)
            self._overlay = QtWidgets.QGraphicsPixmapItem(empty_pixmap)

        move_x = (view_size.width() - item_size.width()) / 2.
        move_y = (view_size.height() - item_size.height()) / 2.

        self._scene.addItem(self._underlay)
        self._scene.addItem(self._overlay)
        # self._underlay.setPos(move_x, move_y)
        # self._overlay.setPos(move_x, move_y)
        # self._scene.sceneRect().setSize(view_size)

    # mouseEvent
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        pos_x = event.pos().x()
        pos_y = event.pos().y()
        min_x, min_y, width, height = self.get_overlay_pos()
        self.pointed.emit(float(pos_x-min_x)/width, float(pos_y-min_y)/height,
                          [pos_x, pos_y, min_x, min_y, width, height])
        self.draw_crossline(pos_x, pos_y)
        super(SliceViewer, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        super(SliceViewer, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super(SliceViewer, self).mouseMoveEvent(event)

    # def underMouse(self) -> bool:
    # def grabMouse(self):
    # def releaseMouse(self):
    # def setMouseTracking(self, enable:bool):
    # def hasMouseTracking(self) -> bool:

    def get_overlay_pos(self):
        qrect = self._overlay.pixmap().rect()
        min_x = qrect.x()
        width = qrect.width()
        min_y = qrect.y()
        height = qrect.height()
        return min_x, min_y, width, height

    def clean_overlay(self):
        self._overlay.pixmap().fill(QtCore.Qt.transparent)
        self._scene.update()

    def draw_crossline(self, pos_x, pos_y):
        min_x, min_y, width, height = self.get_overlay_pos()
        self._scene.removeItem(self._overlay)

        overlay = self._overlay.pixmap()
        overlay.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(overlay)
        pen = QtGui.QPen()
        pen.setColor(QtCore.Qt.gray)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(pos_x, min_y, pos_x, min_y)
        painter.drawLine(min_x, pos_y, min_x, pos_y)
        painter.end()

        self._overlay.setPixmap(overlay)
        self._overlay = QtWidgets.QGraphicsPixmapItem(overlay)
        self._scene.addItem(self._overlay)
        self._scene.update()
