from PySide2 import QtWidgets, QtCore

from PySide2.QtWidgets import QFileDialog, QPushButton, QListView, QFileSystemModel
from PySide2.QtCore import Signal
from ..lib.utils import popup_error_dialog
from shleeh import *
from ..config import config, get_geometry
import brkraw
import pathlib


class BaseFileDialog(QtWidgets.QFileDialog):
    """ """
    datasetLoaded = Signal()

    def __init__(self, *args, **kwargs):
        super(BaseFileDialog, self).__init__(*args, **kwargs)
        # use config parser to handle geometry parameters
        self.setGeometry(*get_geometry(self, 'FileDialog', reset=True))


class HomeDirDialog(BaseFileDialog):
    def __init__(self, *args, **kwargs):
        super(HomeDirDialog, self).__init__(*args, **kwargs)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)
        self.setViewMode(self.List)
        self.homedir = None

        # Update Sidebar width (original width is too narrow)
        self.sbobj = [x for x in self.findChildren(QListView) if 'sidebar' == x.objectName()][0]
        minimum_width = int(config.get('FileDialog', 'SideBarMinimumWidth'))
        self.sbobj.setMinimumWidth(minimum_width)

    def accept(self):
        """ override accept slot. regular action of this slot function
        hides the modal dialog and sets the result code to Accepted
        """
        list_dirs = self.selectedFiles()
        if len(list_dirs) == 0:
            super(HomeDirDialog, self).accept()
        else:
            self.homedir = list_dirs[0]
            self.datasetLoaded.emit()
            self.hide()


class PvDatasetFileDialog(BaseFileDialog):
    def __init__(self, *args, **kwargs):
        super(PvDatasetFileDialog, self).__init__(*args, **kwargs)
        self.brkraw_obj = None

        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFile)
        self.setViewMode(self.Detail)
        self.setNameFilter("All Files (*)")

        # Update listView object double click response
        self.lvobj = [x for x in self.findChildren(QListView) if 'listView' == x.objectName()][0]
        self.lvobj.doubleClicked.connect(self.double_clicked)

        # Update Sidebar width (original width is too narrow)
        self.sbobj = [x for x in self.findChildren(QListView) if 'sidebar' == x.objectName()][0]
        minimum_width = int(config.get('FileDialog', 'SideBarMinimumWidth'))
        self.sbobj.setMinimumWidth(minimum_width)

        # Update Open button object double click response
        self.obobj = [x for x in self.findChildren(QPushButton) if 'open' in str(x.text().lower())][0]
        self.obobj.clicked.disconnect()
        self.obobj.clicked.connect(self.open_clicked)

    def _try_load_pvdataset(self, pathname):
        pathname = pathlib.Path(pathname)
        err = FileNotValidError(pathname, DataType.PVDATASET).message
        try:
            data = brkraw.load(pathname)
            if data.is_pvdataset:
                self.brkraw_obj = data
                self.datasetLoaded.emit()
                self.hide()
            else:
                self.brkraw_obj = None
                popup_error_dialog(err)
        except FileNotValidError as e:
            self.brkraw_obj = None
            popup_error_dialog(e.message)

    def accept(self):
        """ override accept slot. regular action of this slot function
        hides the modal dialog and sets the result code to Accepted
        """
        list_files = self.selectedFiles()
        if len(list_files) == 0:
            super(PvDatasetFileDialog, self).accept()
        else:
            self._try_load_pvdataset(list_files[0])

    def double_clicked(self, event):
        if QFileSystemModel.isDir(event.model(), event):
            pass
        else:
            pathname = self.selectedFiles()[0]
            self._try_load_pvdataset(pathname)

    def open_clicked(self):
        pathname = self.selectedFiles()[0]
        self._try_load_pvdataset(pathname)
