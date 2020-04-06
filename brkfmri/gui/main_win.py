from .. import __version__
from .icons import icon_sets
from .browser import DataBrowserMain
from .toolbars.select_scan import ScanSelectDialog
from .io import HomeDirDialog, PvDatasetFileDialog
from ..config import set_geometry, get_geometry, set_home_dir, get_home_dir
import sys
from PySide2 import QtWidgets, QtGui, QtCore


class MainWindow(QtWidgets.QMainWindow):
    dataRefreshed = QtCore.Signal()
    dataSelected = QtCore.Signal(list)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.brkraw_obj = None
        self.scanlist = None
        self.init_ui()
        self.set_statusbar()
        self.set_actions()
        self.set_menubar()
        self.set_toolbar()
        self.set_centerwidget()
        self.set_geometry()
        self.show()

    def init_ui(self):
        self.setWindowTitle('Bruker-fMRI v{} - CAMRI at UNC-CH'.format(__version__))
        self.setWindowIcon(QtGui.QIcon(icon_sets['win_icon']))
        self.setObjectName('main_window')

    # initiate environments
    def set_statusbar(self):
        self.statusBar().showMessage('Ready')

    def set_actions(self):
        # File
        self.exit_action = QtWidgets.QAction(QtGui.QIcon(icon_sets['file_exit']),
                                             'Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(QtCore.QCoreApplication.instance().quit)

        self.dfpath_action = QtWidgets.QAction(QtGui.QIcon(icon_sets['file_setpath']),
                                               'SetPath', self)
        self.dfpath_action.setStatusTip('Set default working directory')
        self.dfpath_action.triggered.connect(self.open_setpath_dialog)

        self.load_action = QtWidgets.QAction(QtGui.QIcon(icon_sets['file_load']),
                                             'Load', self)
        self.load_action.setShortcut('Ctrl+O')
        self.load_action.setStatusTip('Open file dialog')
        self.load_action.triggered.connect(self.load_dataset_dialog)

        # Data
        self.refresh_action = QtWidgets.QAction(QtGui.QIcon(icon_sets['data_refresh']),
                                                'Refresh', self)
        self.refresh_action.setShortcut('Ctrl+R')
        self.refresh_action.setStatusTip('Refresh loaded dataset')
        self.refresh_action.triggered.connect(self.refresh_dataset)

        self.scanlist_action = QtWidgets.QAction(QtGui.QIcon(icon_sets['data_scanlist']),
                                                 'Show ScanList', self)
        self.scanlist_action.setShortcut('Ctrl+L')
        self.scanlist_action.setStatusTip('Toggle ScanList dialog')
        self.scanlist_action.triggered.connect(self.toggle_scanlist_dialog)

        self.analysis_action = QtWidgets.QAction(QtGui.QIcon(icon_sets['data_analysis']),
                                                 'Get Timecourse', self)
                                                 # 'Analysis', self)
        self.analysis_action.setShortcut('Ctrl+T')
        # self.analysis_action.setStatusTip('Open analysis dialog')
        self.analysis_action.setStatusTip('Extract timecourse and plot')
        self.analysis_action.triggered.connect(self.open_analysis_dialog)

        # Disable when data is not loaded
        self.scanlist_action.setDisabled(True)
        self.refresh_action.setDisabled(True)
        self.analysis_action.setDisabled(True)

        # Window
        self.movecenter_action = QtWidgets.QAction(QtGui.QIcon(icon_sets['window_center']),
                                             'Move Center', self)
        self.movecenter_action.setStatusTip('Move window to screen center')
        self.movecenter_action.triggered.connect(self.movecenter)

    def set_menubar(self):
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)
        self.filemenu = self.menubar.addMenu('&File')
        self.filemenu.addAction(self.load_action)
        self.filemenu.addSeparator()
        self.filemenu.addAction(self.exit_action)

        self.datamenu = self.menubar.addMenu('&Data')
        self.datamenu.addAction(self.refresh_action)
        self.datamenu.addSeparator()
        self.datamenu.addAction(self.scanlist_action)
        self.datamenu.addAction(self.analysis_action)

        self.windowmenu = self.menubar.addMenu('&Window')
        self.windowmenu.addAction(self.movecenter_action)

    def set_scanlist(self):
        self.scanlist = ScanSelectDialog(self)
        # self.scanlist.setWindowFlags(QtCore.Qt.Popup)  # this is not suitable
        # signal received that when scanlist dialog is shows, then toggle the menu text
        self.scanlist.showed.connect(self.toggle_scanlist_text)
        # when item in scanlist selected, corespond scan_id and reco_id will emit
        self.scanlist.lvobj.data_selected.connect(self.transmit_data_to_browser)

    def transmit_data_to_browser(self, scan_id, reco_id):
        self.analysis_action.setEnabled(True)
        scan_id = int(scan_id)
        reco_id = int(reco_id)

        # load data
        dataobj = self.brkraw_obj.get_dataobj(scan_id, reco_id)
        # affine = self.brkraw_obj.get_affine(scan_id, reco_id)
        visu_pars = self.brkraw_obj.get_visu_pars(scan_id, reco_id)
        resol = self.brkraw_obj._get_spatial_info(visu_pars)['spatial_resol'][0]
        # fov = self.brkraw_obj._get_spatial_info(visu_pars)['fov_size']
        tr = self.brkraw_obj._get_temp_info(visu_pars)['temporal_resol']
        n_slicep = self.brkraw_obj._get_slice_info(visu_pars)['num_slice_packs']
        n_slicepp = self.brkraw_obj._get_slice_info(visu_pars)['num_slices_each_pack'][0]

        if n_slicep > 1 and n_slicepp == 1:
            is_localizer = True
        else:
            is_localizer = False

        # deliver to data browser
        delivery_package = [dataobj, resol, tr, is_localizer]
        self.dataSelected.emit(delivery_package)

    def set_toolbar(self):
        file_toolbar = self.addToolBar('File')
        file_toolbar.addAction(self.exit_action)
        file_toolbar.addAction(self.dfpath_action)
        file_toolbar.addAction(self.load_action)

        data_toolbar = self.addToolBar('Data')
        data_toolbar.addAction(self.refresh_action)
        data_toolbar.addAction(self.scanlist_action)
        data_toolbar.addAction(self.analysis_action)

    def set_centerwidget(self):
        self.browser = DataBrowserMain(self)
        self.setCentralWidget(self.browser)
        self.browser.adjustSize()

    def set_geometry(self):
        x, y, width, height = get_geometry(self, 'QMainWindow', reset=False)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width+1000, height)
        self.setGeometry(x, y, width, height)

    # slots
    def open_setpath_dialog(self):
        self.dir_dialog = HomeDirDialog(self, directory=get_home_dir())
        self.dir_dialog.datasetLoaded.connect(self.set_homedir)
        self.dir_dialog.open()

    def set_homedir(self):
        homedir = self.dir_dialog.homedir
        if homedir is None:
            pass
        else:
            set_home_dir(homedir)

    def toggle_scanlist_dialog(self):
        if self.scanlist_action.text() == 'Show ScanList':
            self.scanlist.show()
        else:
            self.scanlist.hide()

    def toggle_scanlist_text(self, event):
        if event:
            self.scanlist_action.setText('Hide ScanList')
        else:
            self.scanlist_action.setText('Show ScanList')

    def open_analysis_dialog(self):
        from ..lib.utils import get_cluster_coordinates
        import numpy as np

        browser = self.centralWidget()
        x, y, z = browser.get_coord()

        dataobj = browser.selectedScan
        coord_set = get_cluster_coordinates((x, y, z))
        ts_data = dataobj[tuple(np.transpose(coord_set).tolist())].mean(0)
        if isinstance(ts_data, np.float):
            browser.plot_timecourse(x=None, y=ts_data)
        else:
            print(ts_data.max())
            num_points = ts_data.shape[0]
            x = np.linspace(0, num_points*(browser.selectedScanTR - 1), num_points)
            browser.plot_timecourse(x=x, y=ts_data)

    def refresh_dataset(self):
        import brkraw
        path = self.brkraw_obj.pvobj.filename
        self.brkraw_obj = brkraw.load(path)
        self.dataRefreshed.emit()

    def load_dataset_dialog(self):
        self.fd = PvDatasetFileDialog(self)
        self.fd.datasetLoaded.connect(self.dataLoaded)
        self.fd.open()

    def dataLoaded(self):
        if self.fd.brkraw_obj is not None:
            self.brkraw_obj = self.fd.brkraw_obj
            self.set_scanlist()
            self.scanlist_action.setEnabled(True)
            self.refresh_action.setEnabled(True)
            # self.analysis_action.setEnabled(True)
        else:
            self.brkraw_obj = None
            self.scanlist_action.setDisabled(True)
            self.refresh_action.setDisabled(True)
            self.analysis_action.setDisabled(True)

    def movecenter(self):
        self.setGeometry(*get_geometry(self, 'QMainWindow', reset=True))

    def remember_geometry(self):
        set_geometry(self, 'QMainWindow')

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.remember_geometry()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    exe = MainWindow()
    sys.exit(app.exec_())