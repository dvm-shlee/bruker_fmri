from PySide2 import QtGui, QtCore, QtWidgets
from ..icons import icon_sets
from ...config import config


class ScanTreeView(QtWidgets.QTreeView):
    clicked = QtCore.Signal(QtCore.QModelIndex)
    data_selected = QtCore.Signal(str, str)

    def __init__(self, *args):
        super(ScanTreeView, self).__init__(*args)
        self.clicked.connect(self.emit_scanid)

    def emit_scanid(self, index):
        model = self.model()
        parent = model.itemFromIndex(index).parent()

        if parent is None:
            scanid_index = index.siblingAtColumn(0)
            scan_id = model.itemFromIndex(scanid_index).text().strip()
            recoid_index = model.index(0, 1, scanid_index)
            reco_id = model.itemFromIndex(recoid_index).text().strip()
        else:
            scan_id = model.item(parent.row(), 0).text().strip()
            recoid_index = index.siblingAtColumn(1)
            reco_id = model.itemFromIndex(recoid_index).text().strip()
        self.data_selected.emit(scan_id, reco_id)

    def mouseDoubleClickEvent(self, event:QtGui.QMouseEvent):
        pass


class ScanSelectDialog(QtWidgets.QWidget):
    showed = QtCore.Signal(bool)

    def __init__(self, parent):
        super(ScanSelectDialog, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowIcon(QtGui.QIcon(icon_sets['data_scanlist']))
        self.setWindowTitle('ScanList')
        # self.activateWindow()
        width = int(config.get('ScanList', 'Width'))
        height = int(config.get('ScanList', 'Height'))
        self.resize(width, height)
        self.lvobj = ScanTreeView()

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.addWidget(self.lvobj, 0, 1, 1, 1)
        self.update_list()
        for column in range(3):
            self.lvobj.resizeColumnToContents(column)

        self.parent().dataRefreshed.connect(self.refresh)

    def refresh(self):
        self.update_list()

    def update_list(self):
        model = self.create_model()
        self.import_scanlist(model)
        self.lvobj.setModel(model)

    def create_model(self):
        model = QtGui.QStandardItemModel(0, 3, self)
        model.setHorizontalHeaderLabels(['ScanID', 'RecoID', 'Description'])
        return model

    def import_scanlist(self, model):
        from brkraw.lib.utils import get_value
        brkraw_obj = self.parent().brkraw_obj
        for i, (scan_id, recos) in enumerate(brkraw_obj._avail.items()):
            visu_pars = brkraw_obj._get_visu_pars(scan_id, recos[0])
            protocol_name = get_value(visu_pars, 'VisuAcquisitionProtocol')
            scan_item = QtGui.QStandardItem(str(scan_id).rjust(3))
            empt_item = QtGui.QStandardItem('')
            desc_item = QtGui.QStandardItem(protocol_name)
            model.appendRow([scan_item, empt_item, desc_item])
            for reco_id in recos:
                frame_type = get_value(visu_pars, 'VisuCoreFrameType')
                reco_item = QtGui.QStandardItem(str(reco_id).rjust(3))
                matrix_size = brkraw_obj._get_matrix_size(visu_pars)
                type_item = QtGui.QStandardItem('{} ({})'.format(frame_type.lower(),
                                                                 'x'.join(map(str, matrix_size))))
                scan_item.appendRow([empt_item, reco_item, type_item])

    def hideEvent(self, event: QtGui.QHideEvent):
        self.showed.emit(False)

    def showEvent(self, arg__1: QtGui.QShowEvent):
        self.showed.emit(True)