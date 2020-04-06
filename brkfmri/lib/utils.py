from ..config import config
from PySide2 import QtWidgets, QtGui, QtCore
from PIL import Image, ImageQt
import numpy as np
from shleeh.errors import *


def convert_arr2qpixmap(data: np.array, aspect: float = 1.0) -> QtGui.QPixmap:
    size = int(config.get('ImageViewer', 'size'))
    rescaled_data = data / data.max()* 255
    rescaled_data = rescaled_data.astype('uint8')
    imgobj = Image.fromarray(rescaled_data.T)
    qimgobj = ImageQt.ImageQt(imgobj)
    qpixmap = QtGui.QPixmap(qimgobj)

    if aspect > 1:  # aspect = width / height
        width = size
        height = size / aspect
    else:
        width = size * aspect
        height = size
    qpixmap = qpixmap.scaled(QtCore.QSize(width, height))
    return qpixmap


def popup_error_dialog(message: str):
    err_box = QtWidgets.QMessageBox()
    err_box.setWindowTitle('Error')
    err_box.setText(message)
    err_box.exec()


def get_cluster_coordinates(coord, size=1, NN=3, mask=None):
    n_voxel = size + 1
    x, y, z = coord
    X = sorted([x +i for i in range(n_voxel)] + [x - i for i in range(n_voxel) if i != 0])
    Y = sorted([y +i for i in range(n_voxel)] + [y - i for i in range(n_voxel) if i != 0])
    Z = sorted([z + i for i in range(n_voxel)] + [z - i for i in range(n_voxel) if i != 0])

    if NN == 1:
        thr = size
    elif NN == 2:
        thr = np.sqrt(np.square([size] * 2).sum())
    elif NN == 3:
        thr = np.sqrt(np.square([size] * 3).sum())
    else:
        raise UnexpectedError

    all_poss = [(i, j, k) for i in X for j in Y for k in Z]
    output_coord = [c for c in all_poss if cal_distance(coord, c) <= thr]

    if mask == None:
        return output_coord
    else:
        return [c for c in output_coord if c in mask]


def cal_distance(coordA, coordB):
    return np.sqrt(np.square(np.diff(np.asarray(list(zip(coordA, coordB))))).sum())
