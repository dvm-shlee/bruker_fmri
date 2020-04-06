from ..config import config
from PySide2.QtCore import Qt, QSize, QMetaObject, Signal, QTimer
from PySide2.QtGui import QPalette, QBrush, QColor, QFont
from PySide2.QtWidgets import \
    QWidget, QGridLayout, QFrame, QLabel, QVBoxLayout, \
    QHBoxLayout, QGroupBox, QSlider, QSpinBox, QPushButton, QListView
import pyqtgraph as pg
import numpy as np
from ..lib.utils import convert_arr2qpixmap, popup_error_dialog
from shleeh.errors import *
from .viewer.sliceviewer import ImageViewer


class DataBrowserMain(QWidget):
    sliceUpdated = Signal(int, int, int, int)

    def __init__(self, parent):
        super(DataBrowserMain, self).__init__(parent)

        # data import
        self.brkraw_obj = self.parent().brkraw_obj
        self.selectedScan = None
        self.selectedScanTR = None

        self.set_viewer_frame()
        self.set_controller_frame()
        self.set_gridlayouts()
        self.set_font()
        # self.set_palette()  # TODO
        self.set_size()
        self.set_objectnames()
        self.set_texts()
        self.ratio_container = []
        self.init_connection()
        self.inactivate_widgets()  # Inactivate during startup

    def init_connection(self):
        self.parent().dataSelected.connect(self.selectScanEvent)  # run selectScanEvent when data selected
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self.sliceUpdateEvent)  #
        self.sliceUpdated.connect(self.updateImage)

        self.xaxis_slider.valueChanged.connect(self.xaxis_spinbox.setValue)
        self.xaxis_spinbox.valueChanged.connect(self.xaxis_slider.setValue)
        self.yaxis_slider.valueChanged.connect(self.yaxis_spinbox.setValue)
        self.yaxis_spinbox.valueChanged.connect(self.yaxis_slider.setValue)
        self.zaxis_slider.valueChanged.connect(self.zaxis_spinbox.setValue)
        self.zaxis_spinbox.valueChanged.connect(self.zaxis_slider.setValue)
        self.frame_slider.valueChanged.connect(self.frame_spinbox.setValue)
        self.frame_spinbox.valueChanged.connect(self.frame_slider.setValue)

        self.axial_view.pointed.connect(self.axialview_pointing_event)
        self.sagittal_view.pointed.connect(self.sagittalview_pointing_event)
        self.coronal_view.pointed.connect(self.coronalview_pointing_event)

        self.connect_sliders_to_update()

    def axialview_pointing_event(self, pos_x, pos_y, meta):
        max_x = self.zaxis_slider.maximum()
        max_y = self.yaxis_slider.maximum()

        # print(pos_x, pos_y, max_x, max_y)
        self.zaxis_slider.setValue(int(max_x * pos_x))
        self.yaxis_slider.setValue(int(max_y * pos_y))
        # print(int(max_x * pos_x), int(max_y * pos_y))

    def sagittalview_pointing_event(self, pos_x, pos_y, meta):
        max_x = self.zaxis_slider.maximum()
        max_y = self.xaxis_slider.maximum()

        # print(pos_x, pos_y, max_x, max_y)
        self.zaxis_slider.setValue(int(max_x * pos_x))
        self.xaxis_slider.setValue(max_y - int(max_y * pos_y))
        # print(int(max_x * pos_x), int(max_y * pos_y))

    def coronalview_pointing_event(self, pos_x, pos_y, meta):
        max_x = self.yaxis_slider.maximum()
        max_y = self.xaxis_slider.maximum()

        # print(pos_x, pos_y, max_x, max_y)
        self.yaxis_slider.setValue(int(max_x * pos_x))
        self.xaxis_slider.setValue(max_y - int(max_y * pos_y))
        # print(int(max_x * pos_x), int(max_y * pos_y))

    def sliderChangeEvent(self):
        self.event_timer.start(10)

    def sliceUpdateEvent(self):
        # This will executed only when timer timeout
        x = self.xaxis_slider.value()
        y = self.yaxis_slider.value()
        z = self.zaxis_slider.value()
        t = self.frame_slider.value()
        self.sliceUpdated.emit(x, y, z, t)
        self.event_timer.stop()

    @staticmethod
    def slice_data(dataobj, slice_orient, slice_num):
        if slice_orient == 'axial':
            sliced_data = dataobj[:, :, slice_num]
        elif slice_orient == 'sagittal':
            sliced_data = dataobj[:, slice_num, ::-1]
        elif slice_orient == 'coronal':
            sliced_data = dataobj[slice_num, :, ::-1]
        else:
            popup_error_dialog(UnexpectedError.message)
            return None
        return sliced_data

    def updateImage(self, x, y, z, frame):
        if len(self.selectedScan.shape) == 4:
            dataobj = self.selectedScan[:,:,:,frame]
        else:
            dataobj = self.selectedScan[...]

        data_xy = self.slice_data(dataobj, 'axial', x)
        data_yz = self.slice_data(dataobj, 'sagittal', y)
        data_xz = self.slice_data(dataobj, 'coronal', z)
        ratio_xy, ratio_yz, ratio_xz = self.ratio_container

        qm_xy = convert_arr2qpixmap(data_xy, ratio_xy)
        qm_yz = convert_arr2qpixmap(data_yz, ratio_yz)
        qm_xz = convert_arr2qpixmap(data_xz, ratio_xz)

        if self.axial_view._overlay is not None:
            overlay = self.axial_view._overlay_item.pixmap()
            self.axial_view.setPixmap(qm_xy)
            self.axial_view._overlay_item.setPixmap(overlay)
        else:
            self.axial_view.setPixmap(qm_xy)
        self.sagittal_view.setPixmap(qm_yz)
        self.coronal_view.setPixmap(qm_xz)

    def selectScanEvent(self, delivery_package: list):
        """ this event is occurring when a scan selected on scanlist """
        self.axial_view.setEnabled(True)
        self.sagittal_view.setEnabled(True)
        self.coronal_view.setEnabled(True)
        self.selectedScan, resol, self.selectedScanTR, is_localizer = delivery_package
        self.selectedScanTR /= 1000

        if is_localizer:
            # localizer will show on each view
            data_xy = self.selectedScan[..., 0]
            data_yz = self.selectedScan[..., 1]
            data_xz = self.selectedScan[..., 2]
            self.ratio_container = [1.0, 1.0, 1.0]

            qm_xy = convert_arr2qpixmap(data_xy, self.ratio_container[0])
            qm_yz = convert_arr2qpixmap(data_yz, self.ratio_container[1])
            qm_xz = convert_arr2qpixmap(data_xz, self.ratio_container[2])

            self.update_axisview(qm_xy, qm_yz, qm_xz)
        else:
            # other than localizer
            self.init_data(self.selectedScan)
            matrix_size = np.asarray(self.selectedScan.shape)
            resol = np.asarray(resol)
            fov = matrix_size[:3] * resol
            self.ratio_container = [fov[0] / fov[1],
                                    fov[1] / fov[2],
                                    fov[0] / fov[2]]
            # reset value
            init_x, init_y, init_z = (np.asarray(self.selectedScan.shape[:3])/2.0).astype(int)
            init_f = 0

            self.disconnect_sliders_to_update()
            self.xaxis_slider.setValue(init_x)
            self.yaxis_slider.setValue(init_y)
            self.zaxis_slider.setValue(init_z)
            self.frame_slider.setValue(init_f)
            self.connect_sliders_to_update()
            self.updateImage(init_x, init_y, init_z, init_f)

    def connect_sliders_to_update(self):
        # connect to check slice update
        self.xaxis_slider.valueChanged.connect(self.sliderChangeEvent)
        self.yaxis_slider.valueChanged.connect(self.sliderChangeEvent)
        self.zaxis_slider.valueChanged.connect(self.sliderChangeEvent)
        self.frame_slider.valueChanged.connect(self.sliderChangeEvent)

    def disconnect_sliders_to_update(self):
        # disconnect to check slice update
        self.xaxis_slider.valueChanged.disconnect(self.sliderChangeEvent)
        self.yaxis_slider.valueChanged.disconnect(self.sliderChangeEvent)
        self.zaxis_slider.valueChanged.disconnect(self.sliderChangeEvent)
        self.frame_slider.valueChanged.disconnect(self.sliderChangeEvent)

    def init_data(self, dataobj):
        self.slicecontrol_pane.setEnabled(True)
        dim = len(dataobj.shape)
        if dim == 3:
            size_x, size_y, size_z = dataobj.shape
            size_frame = None
        elif dim == 4:
            size_x, size_y, size_z, size_frame = dataobj.shape
        else:
            popup_error_dialog(UnexpectedError.message)
            return None

        # init sliders and spinboxes
        self.xaxis_slider.setRange(0, size_x-1)
        self.yaxis_slider.setRange(0, size_y-1)
        self.zaxis_slider.setRange(0, size_z-1)

        self.xaxis_spinbox.setRange(0, size_x-1)
        self.yaxis_spinbox.setRange(0, size_y-1)
        self.zaxis_spinbox.setRange(0, size_z-1)

        if dim == 3:
            self.frame_label.setDisabled(True)
            self.frame_slider.setDisabled(True)
            self.frame_spinbox.setDisabled(True)
        else:
            self.frame_label.setEnabled(True)
            self.frame_slider.setEnabled(True)
            self.frame_spinbox.setEnabled(True)
            self.frame_slider.setRange(0, size_frame-1)
            self.frame_spinbox.setRange(0, size_frame-1)

    def update_axisview(self, axial_img, sagittal_img, coronal_img):
        self.axial_view.setPixmap(axial_img)
        self.sagittal_view.setPixmap(sagittal_img)
        self.coronal_view.setPixmap(coronal_img)

    def inactivate_widgets(self):
        self.slicecontrol_pane.setDisabled(True)
        self.graph_frame.setDisabled(True)

    def set_navigationmode(self):
        # mouse click will navigate slice.
        pass

    def set_drawingmode(self):
        # roi drawing function
        pass

    def mask_data_handler(self):
        # mask later handler
        pass

    def slider_event_related(self):
        # slider for slicing.
        pass

    def set_viewer_frame(self):
        self.imageframe = QFrame(self)
        self.axial_view = ImageViewer(self.imageframe)
        self.axial_view.setDisabled(True)
        self.sagittal_view = ImageViewer(self.imageframe)
        self.sagittal_view.setDisabled(True)
        self.coronal_view = ImageViewer(self.imageframe)
        self.coronal_view.setDisabled(True)

        # TODO: Will reactivate these on later version
        # self.axial_title = QLabel(self.imageframe)
        # self.coronal_title = QLabel(self.imageframe)
        # self.sagittal_title = QLabel(self.imageframe)
        #
        # self.axialL_label = QLabel(self.imageframe)
        # self.axialA_label = QLabel(self.imageframe)
        # self.axialR_label = QLabel(self.imageframe)
        # self.axialP_label = QLabel(self.imageframe)
        #
        # self.sagittalS_label = QLabel(self.imageframe)
        # self.sagittalA_label = QLabel(self.imageframe)
        # self.sagittalI_label = QLabel(self.imageframe)
        # self.sagittalP_label = QLabel(self.imageframe)
        #
        # self.coronalL_label = QLabel(self.imageframe)
        # self.coronalS_label = QLabel(self.imageframe)
        # self.coronalR_label = QLabel(self.imageframe)
        # self.coronalI_label = QLabel(self.imageframe)
        #
        # self.axial_title.setTextFormat(Qt.MarkdownText)
        # self.axialL_label.setTextFormat(Qt.MarkdownText)
        # self.axialA_label.setTextFormat(Qt.MarkdownText)
        # self.axialR_label.setTextFormat(Qt.MarkdownText)
        # self.axialP_label.setTextFormat(Qt.MarkdownText)
        #
        # self.sagittal_title.setTextFormat(Qt.MarkdownText)
        # self.sagittalS_label.setTextFormat(Qt.MarkdownText)
        # self.sagittalA_label.setTextFormat(Qt.MarkdownText)
        # self.sagittalI_label.setTextFormat(Qt.MarkdownText)
        # self.sagittalP_label.setTextFormat(Qt.MarkdownText)
        #
        # self.coronal_title.setTextFormat(Qt.MarkdownText)
        # self.coronalL_label.setTextFormat(Qt.MarkdownText)
        # self.coronalS_label.setTextFormat(Qt.MarkdownText)
        # self.coronalR_label.setTextFormat(Qt.MarkdownText)
        # self.coronalI_label.setTextFormat(Qt.MarkdownText)
        #
        # self.axial_title.setAlignment(Qt.AlignCenter)
        # self.axialL_label.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        # self.axialA_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        # self.axialR_label.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        # self.axialP_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        #
        # self.sagittal_title.setAlignment(Qt.AlignCenter)
        # self.sagittalS_label.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        # self.sagittalA_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        # self.sagittalI_label.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        # self.sagittalP_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        #
        # self.coronal_title.setAlignment(Qt.AlignCenter)
        # self.coronalL_label.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        # self.coronalS_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        # self.coronalR_label.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        # self.coronalI_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

    def set_controller_frame(self):
        self.controller_frame = QFrame(self)
        self.slicecontrol_pane = QGroupBox(self.controller_frame)
        self.frame_spinbox = QSpinBox(self.slicecontrol_pane)

        self.xaxis_label = QLabel(self.slicecontrol_pane)
        self.yaxis_label = QLabel(self.slicecontrol_pane)
        self.zaxis_label = QLabel(self.slicecontrol_pane)
        self.frame_label = QLabel(self.slicecontrol_pane)

        self.xaxis_slider = QSlider(self.slicecontrol_pane)
        self.yaxis_slider = QSlider(self.slicecontrol_pane)
        self.zaxis_slider = QSlider(self.slicecontrol_pane)
        self.frame_slider = QSlider(self.slicecontrol_pane)

        self.xaxis_spinbox = QSpinBox(self.slicecontrol_pane)
        self.yaxis_spinbox = QSpinBox(self.slicecontrol_pane)
        self.zaxis_spinbox = QSpinBox(self.slicecontrol_pane)

        self.graph_frame = QFrame(self)
        self.graph_view = pg.PlotWidget(self.graph_frame)
        self.graph_view.setBackground('w')

        # TODO: Will reactivate these on later version
        # self.graph_view = QGraphicsView(self.graph_frame)
        # self.graphcontrol_pane = QGroupBox(self.graph_frame)
        # self.addmask_button = QPushButton(self.graphcontrol_pane)
        # self.removemask_button = QPushButton(self.graphcontrol_pane)
        # self.mask_listview = QListView(self.graphcontrol_pane)
        # self.savepng_button = QPushButton(self.graphcontrol_pane)
        # self.savecsv_button = QPushButton(self.graphcontrol_pane)

        self.axial_view.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.sagittal_view.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.coronal_view.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.xaxis_slider.setOrientation(Qt.Horizontal)
        self.yaxis_slider.setOrientation(Qt.Horizontal)
        self.zaxis_slider.setOrientation(Qt.Horizontal)
        self.frame_slider.setOrientation(Qt.Horizontal)

        self.slicecontrol_pane.setAlignment(Qt.AlignCenter)
        self.xaxis_label.setAlignment(Qt.AlignCenter)
        self.yaxis_label.setAlignment(Qt.AlignCenter)
        self.zaxis_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setAlignment(Qt.AlignCenter)
        # TODO: Will reactivate these on later version
        # self.graphcontrol_pane.setAlignment(Qt.AlignCenter)

    def set_size(self):
        size = int(config.get('ImageViewer', 'size'))
        self.imageframe.setLineWidth(0)
        self.axial_view.setMinimumSize(QSize(size, size))
        self.axial_view.setMaximumSize(QSize(size, size))
        self.axial_view.setLineWidth(0)
        self.sagittal_view.setMinimumSize(QSize(size, size))
        self.sagittal_view.setMaximumSize(QSize(size, size))
        self.sagittal_view.setLineWidth(0)
        self.coronal_view.setMinimumSize(QSize(size, size))
        self.coronal_view.setMaximumSize(QSize(size, size))
        self.coronal_view.setLineWidth(0)

        # TODO: Will reactivate these on later version
        # self.axialL_label.setMinimumSize(QSize(20, 0))
        # self.axialA_label.setMinimumSize(QSize(0, 20))
        # self.axialR_label.setMinimumSize(QSize(20, 0))
        # self.axialP_label.setMinimumSize(QSize(0, 20))
        # self.sagittalS_label.setMinimumSize(QSize(20, 0))
        # self.sagittalA_label.setMinimumSize(QSize(0, 20))
        # self.sagittalI_label.setMinimumSize(QSize(20, 0))
        # self.sagittalP_label.setMinimumSize(QSize(0, 20))
        # self.coronalL_label.setMinimumSize(QSize(20, 0))
        # self.coronalS_label.setMinimumSize(QSize(0, 20))
        # self.coronalR_label.setMinimumSize(QSize(20, 0))
        # self.coronalI_label.setMinimumSize(QSize(0, 20))

        self.controller_frame.setMinimumSize(QSize(300, 300))
        self.controller_frame.setMaximumSize(QSize(400, 300))
        self.graph_frame.setMinimumSize(QSize(0, 300))
        self.graph_frame.setMaximumSize(QSize(4000, 4000))
        self.graph_view.setMaximumSize(QSize(4000, 600))

        # TODO: Will reactivate these on later version
        # self.graphcontrol_pane.setMinimumSize(QSize(300, 0))
        # self.graphcontrol_pane.setMaximumSize(QSize(300, 4000))
        # self.addmask_button.setMinimumSize(QSize(30, 0))
        # self.addmask_button.setMaximumSize(QSize(30, 4000))
        # self.removemask_button.setMinimumSize(QSize(30, 0))
        # self.removemask_button.setMaximumSize(QSize(30, 4000))

    def set_font(self):
        self.arial_8 = QFont()
        self.arial_8.setFamily(u"Arial")
        self.arial_8.setPointSize(8)
        self.setFont(self.arial_8)
        # TODO: Will reactivate these on later version
        # self.axial_title.setFont(self.arial_8)
        # self.coronal_title.setFont(self.arial_8)
        # self.sagittal_title.setFont(self.arial_8)
        # self.axialL_label.setFont(self.arial_8)
        # self.axialA_label.setFont(self.arial_8)
        # self.axialR_label.setFont(self.arial_8)
        # self.axialP_label.setFont(self.arial_8)
        # self.sagittalS_label.setFont(self.arial_8)
        # self.sagittalA_label.setFont(self.arial_8)
        # self.sagittalI_label.setFont(self.arial_8)
        # self.sagittalP_label.setFont(self.arial_8)
        # self.coronalL_label.setFont(self.arial_8)
        # self.coronalS_label.setFont(self.arial_8)
        # self.coronalR_label.setFont(self.arial_8)
        # self.coronalI_label.setFont(self.arial_8)
        self.slicecontrol_pane.setFont(self.arial_8)

        # TODO: Will reactivate these on later version
        # self.xaxis_label.setFont(self.arial_8)
        # self.yaxis_label.setFont(self.arial_8)
        # self.zaxis_label.setFont(self.arial_8)
        # self.frame_label.setFont(self.arial_8)
        # self.graphcontrol_pane.setFont(self.arial_8)
        # self.addmask_button.setFont(self.arial_8)
        # self.removemask_button.setFont(self.arial_8)
        # self.savepng_button.setFont(self.arial_8)
        # self.savecsv_button.setFont(self.arial_8)

    def set_palette(self):
        # Brush
        gray_text = QBrush(QColor(171, 171, 171, 255))
        gray_text.setStyle(Qt.SolidPattern)
        black_background = QBrush(QColor(0, 0, 0, 255))
        black_background.setStyle(Qt.SolidPattern)

        self.orientation_label_palette = QPalette()
        self.orientation_label_palette.setBrush(QPalette.Active, QPalette.WindowText, gray_text)
        self.orientation_label_palette.setBrush(QPalette.Inactive, QPalette.WindowText, gray_text)
        self.orientation_label_palette.setBrush(QPalette.Disabled, QPalette.WindowText, gray_text)
        self.ortho_viewer_palette = QPalette()
        self.ortho_viewer_palette.setBrush(QPalette.Active, QPalette.Base, black_background)
        self.ortho_viewer_palette.setBrush(QPalette.Inactive, QPalette.Base, black_background)
        self.ortho_viewer_palette.setBrush(QPalette.Disabled, QPalette.Base, black_background)

        self.axialA_label.setPalette(self.orientation_label_palette)
        self.axialL_label.setPalette(self.orientation_label_palette)
        self.axialR_label.setPalette(self.orientation_label_palette)
        self.axialP_label.setPalette(self.orientation_label_palette)
        self.axial_view.setPalette(self.ortho_viewer_palette)
        self.sagittalS_label.setPalette(self.orientation_label_palette)
        self.sagittalA_label.setPalette(self.orientation_label_palette)
        self.sagittalI_label.setPalette(self.orientation_label_palette)
        self.sagittalP_label.setPalette(self.orientation_label_palette)
        self.sagittal_view.setPalette(self.ortho_viewer_palette)
        self.coronalL_label.setPalette(self.orientation_label_palette)
        self.coronalS_label.setPalette(self.orientation_label_palette)
        self.coronalR_label.setPalette(self.orientation_label_palette)
        self.coronalI_label.setPalette(self.orientation_label_palette)
        self.coronal_view.setPalette(self.ortho_viewer_palette)

    def set_gridlayouts(self):
        self.axial_gridLayout = QGridLayout()
        self.coronal_gridLayout = QGridLayout()
        self.sagittal_gridLayout = QGridLayout()
        self.imagecont_gridLayout = QGridLayout(self.slicecontrol_pane)
        self.imageframe_gridLayout = QGridLayout(self.imageframe)
        # self.graphcontrol_gridLayout = QGridLayout(self.graphcontrol_pane)
        self.verticalLayout = QVBoxLayout(self.controller_frame)
        self.horizontalLayout = QHBoxLayout(self.graph_frame)
        self.main_gridLayout = QGridLayout(self)
        # TODO: Will reactivate these on later version
        # self.imageframe_gridLayout.addWidget(self.axial_title, 0, 1, 1, 1)
        # self.imageframe_gridLayout.addWidget(self.coronal_title, 0, 2, 1, 1)
        # self.imageframe_gridLayout.addWidget(self.sagittal_title, 0, 0, 1, 1)
        # self.axial_gridLayout.addWidget(self.axialL_label, 1, 0, 1, 1)
        # self.axial_gridLayout.addWidget(self.axialA_label, 0, 1, 1, 1)
        # self.axial_gridLayout.addWidget(self.axialR_label, 1, 2, 1, 1)
        # self.axial_gridLayout.addWidget(self.axialP_label, 2, 1, 1, 1)
        self.axial_gridLayout.addWidget(self.axial_view, 1, 1, 1, 1)
        # self.sagittal_gridLayout.addWidget(self.sagittalS_label, 1, 0, 1, 1)
        # self.sagittal_gridLayout.addWidget(self.sagittalA_label, 0, 1, 1, 1)
        # self.sagittal_gridLayout.addWidget(self.sagittalI_label, 1, 2, 1, 1)
        # self.sagittal_gridLayout.addWidget(self.sagittalP_label, 2, 1, 1, 1)
        self.sagittal_gridLayout.addWidget(self.sagittal_view, 1, 1, 1, 1)
        # self.coronal_gridLayout.addWidget(self.coronalL_label, 1, 0, 1, 1)
        # self.coronal_gridLayout.addWidget(self.coronalS_label, 0, 1, 1, 1)
        # self.coronal_gridLayout.addWidget(self.coronalR_label, 1, 2, 1, 1)
        # self.coronal_gridLayout.addWidget(self.coronalI_label, 2, 1, 1, 1)
        self.coronal_gridLayout.addWidget(self.coronal_view, 1, 1, 1, 1)
        self.imagecont_gridLayout.addWidget(self.xaxis_label, 0, 0, 1, 1)
        self.imagecont_gridLayout.addWidget(self.xaxis_slider, 0, 1, 1, 1)
        self.imagecont_gridLayout.addWidget(self.xaxis_spinbox, 0, 2, 1, 1)
        self.imagecont_gridLayout.addWidget(self.yaxis_label, 1, 0, 1, 1)
        self.imagecont_gridLayout.addWidget(self.yaxis_slider, 1, 1, 1, 1)
        self.imagecont_gridLayout.addWidget(self.yaxis_spinbox, 1, 2, 1, 1)
        self.imagecont_gridLayout.addWidget(self.zaxis_label, 2, 0, 1, 1)
        self.imagecont_gridLayout.addWidget(self.zaxis_slider, 2, 1, 1, 1)
        self.imagecont_gridLayout.addWidget(self.zaxis_spinbox, 2, 2, 1, 1)
        self.imagecont_gridLayout.addWidget(self.frame_label, 3, 0, 1, 1)
        self.imagecont_gridLayout.addWidget(self.frame_slider, 3, 1, 1, 1)
        self.imagecont_gridLayout.addWidget(self.frame_spinbox, 3, 2, 1, 1)
        self.imageframe_gridLayout.addLayout(self.axial_gridLayout, 1, 1, 1, 1)
        self.imageframe_gridLayout.addLayout(self.coronal_gridLayout, 1, 2, 1, 1)
        self.imageframe_gridLayout.addLayout(self.sagittal_gridLayout, 1, 0, 1, 1)
        # self.graphcontrol_gridLayout.addWidget(self.addmask_button, 3, 0, 1, 1)
        # self.graphcontrol_gridLayout.addWidget(self.removemask_button, 3, 1, 1, 1)
        # self.graphcontrol_gridLayout.addWidget(self.mask_listview, 0, 0, 1, 5)
        # self.graphcontrol_gridLayout.addWidget(self.savepng_button, 3, 4, 1, 1)
        # self.graphcontrol_gridLayout.addWidget(self.savecsv_button, 3, 3, 1, 1)
        self.verticalLayout.addWidget(self.slicecontrol_pane)
        self.horizontalLayout.addWidget(self.graph_view)
        # self.horizontalLayout.addWidget(self.graphcontrol_pane)
        self.main_gridLayout.addWidget(self.imageframe, 0, 0, 1, 2)
        self.main_gridLayout.addWidget(self.controller_frame, 1, 0, 1, 1)
        self.main_gridLayout.addWidget(self.graph_frame, 1, 1, 1, 1)

    def set_objectnames(self):
        self.setObjectName(u"data_browser")
        self.imageframe.setObjectName(u"image_frame")
        self.axial_gridLayout.setObjectName(u"axial_gridLayout")
        self.coronal_gridLayout.setObjectName(u"coronal_gridLayout")
        self.sagittal_gridLayout.setObjectName(u"sagittal_gridLayout")
        # TODO: Will reactivate these on later version
        # self.axial_title.setObjectName(u"axial_label")
        # self.coronal_title.setObjectName(u"coronal_label")
        # self.sagittal_title.setObjectName(u"sagittal_label")
        self.axial_view.setObjectName(u"axial_view")
        self.sagittal_view.setObjectName(u"sagittal_view")
        self.coronal_view.setObjectName(u"coronal_view")
        # self.axialL_label.setObjectName(u"axialL_label")
        # self.axialR_label.setObjectName(u"axialR_label")
        # self.axialA_label.setObjectName(u"axialA_label")
        # self.axialP_label.setObjectName(u"axialP_label")
        # self.sagittalS_label.setObjectName(u"sagittalS_label")
        # self.sagittalA_label.setObjectName(u"sagittalA_label")
        # self.sagittalI_label.setObjectName(u"sagittalI_label")
        # self.sagittalP_label.setObjectName(u"sagittalP_label")
        # self.coronalL_label.setObjectName(u"coronalL_label")
        # self.coronalS_label.setObjectName(u"coronalS_label")
        # self.coronalR_label.setObjectName(u"coronalR_label")
        # self.coronalI_label.setObjectName(u"coronalI_label")
        self.controller_frame.setObjectName(u"controller_frame")
        self.slicecontrol_pane.setObjectName(u"slicecontrol_pane")
        self.xaxis_label.setObjectName(u"xaxis_label")
        self.xaxis_slider.setObjectName(u"xaxis_slider")
        self.xaxis_spinbox.setObjectName(u"xaxis_spinbox")
        self.yaxis_label.setObjectName(u"yaxis_label")
        self.yaxis_slider.setObjectName(u"yaxis_slider")
        self.yaxis_spinbox.setObjectName(u"yaxis_spinbox")
        self.zaxis_label.setObjectName(u"zaxis_label")
        self.zaxis_slider.setObjectName(u"zaxis_slider")
        self.zaxis_spinbox.setObjectName(u"zaxis_spinbox")
        self.frame_label.setObjectName(u"frame_label")
        self.frame_slider.setObjectName(u"frame_slider")
        self.frame_spinbox.setObjectName(u"frame_spinbox")
        self.graph_frame.setObjectName(u"graph_frame")
        self.graph_view.setObjectName(u"graph_view")
        # TODO: Will reactivate these on later version
        # self.graphcontrol_pane.setObjectName(u"graphcontrol_pane")
        # self.addmask_button.setObjectName(u"addmask_button")
        # self.removemask_button.setObjectName(u"removemask_button")
        # self.mask_listview.setObjectName(u"mask_listview")
        # self.savepng_button.setObjectName(u"savepng_button")
        # self.savecsv_button.setObjectName(u"savecsv_button")
        self.imagecont_gridLayout.setObjectName(u"imagecont_gridLayout")
        self.imageframe_gridLayout.setObjectName(u"imageframe_gridLayout")
        # self.graphcontrol_gridLayout.setObjectName(u"graphcontrol_gridLayout")
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.main_gridLayout.setObjectName(u"main_gridLayout")
        QMetaObject.connectSlotsByName(self)

    def set_texts(self):
        self.setWindowTitle(u"Data Browser")
        # TODO: Will reactivate these on later version
        # self.axial_title.setText(u"**Axial**")
        # self.coronal_title.setText(u"**Coronal**")
        # self.sagittal_title.setText(u"**Sagittal**")
        # self.sagittalS_label.setText(u"**S**")
        # self.sagittalA_label.setText(u"**A**")
        # self.sagittalI_label.setText(u"**I**")
        # self.sagittalP_label.setText(u"**P**")
        # self.axialL_label.setText(u"**L**")
        # self.axialA_label.setText(u"**A**")
        # self.axialR_label.setText(u"**R**")
        # self.axialP_label.setText( u"**P**")
        # self.coronalL_label.setText(u"**L**")
        # self.coronalS_label.setText(u"**S**")
        # self.coronalR_label.setText(u"**R**")
        # self.coronalI_label.setText(u"**I**")
        self.slicecontrol_pane.setTitle(u"Slice Control Pane")
        self.xaxis_label.setText(u"x")
        self.yaxis_label.setText(u"y")
        self.zaxis_label.setText(u"z")
        self.frame_label.setText(u"Frame")
        # TODO: Will reactivate these on later version
        # self.graphcontrol_pane.setTitle(u"Graph Control Pane")
        # self.addmask_button.setText(u"+")
        # self.removemask_button.setText(u"-")
        # self.savepng_button.setText(u"toPNG")
        # self.savecsv_button.setText(u"toCSV")

    def plot_timecourse(self, x, y):
        self.graph_frame.setEnabled(True)
        self.graph_view.clear()
        pen = pg.mkPen(color=(255, 0, 0))
        if x is None:
            x = [0]
            y = [y]
            self.graph_view.plot(x, y, pen=pen, symbol='o')
        else:
            self.graph_view.plot(x, y, pen=pen)

    def get_coord(self):
        x = self.xaxis_slider.value()
        y = self.yaxis_slider.value()
        z = self.zaxis_slider.value()
        return (x, y, z)

