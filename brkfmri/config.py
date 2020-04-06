import os
import configparser
from PySide2 import QtWidgets
if os.name == 'nt':
    config_file = 'brkfmri.ini'
else:
    config_file = '.brkrc'


def build_config_obj():
    # Config for Dataset structure
    cfg = configparser.RawConfigParser()
    cfg.add_section('Environment')
    cfg.set('Environment', 'WorkingDirectory', os.path.expanduser('~'))

    cfg.add_section('QMainWindow')
    cfg.set('QMainWindow', 'x_position', 100)
    cfg.set('QMainWindow', 'y_position', 100)
    cfg.set('QMainWindow', 'width', 1700)
    cfg.set('QMainWindow', 'height', 1000)

    cfg.add_section('FileDialog')
    cfg.set('FileDialog', 'x_position', 100)
    cfg.set('FileDialog', 'y_position', 100)
    cfg.set('FileDialog', 'width', 800)
    cfg.set('FileDialog', 'height', 600)
    cfg.set('FileDialog', 'SideBarWidth', 250)
    cfg.set('FileDialog', 'SideBarMinimumWidth', 200)

    cfg.add_section('ScanList')
    cfg.set('ScanList', 'width', 500)
    cfg.set('ScanList', 'height', 800)

    cfg.add_section('ImageViewer')
    cfg.set('ImageViewer', 'size', 500)
    return cfg


def save_config_file(cfg: configparser.RawConfigParser, path: str):
    with open(path, 'w') as configfile:
        cfg.write(configfile)


# Load config
def load_cfg(reset: bool = False):
    cfg_path = os.path.join(os.path.expanduser("~"), config_file)
    cfg = configparser.RawConfigParser()
    default_cfg = build_config_obj()

    # create config file if it does not exist
    if not os.path.exists(cfg_path) or reset:
        save_config_file(default_cfg, cfg_path)
    cfg.read(cfg_path)
    if not reset:
        for section, options in default_cfg.items():
            if not cfg.has_section(section) and section is not 'DEFAULT':
                cfg.add_section(section)
            for option, value in options.items():
                if not cfg.has_option(section, option):
                    cfg.set(section, option, value)
    save_config_file(cfg, cfg_path)
    return cfg


def get_geometry(widget: QtWidgets.QWidget, item: str, reset: bool = False) -> (int, int, int, int):
    global config
    if reset:
        center = QtWidgets.QDesktopWidget().availableGeometry(widget).center()
        x, y = center.toTuple()
        width = int(config.get(item, 'width'))
        height = int(config.get(item, 'height'))
        x = x - int(width/2)
        y = y - int(height/2)
    else:
        x = config.get(item, 'x_position')
        y = config.get(item, 'y_position')
        width = config.get(item, 'width')
        height = config.get(item, 'height')
    return map(int, (x, y, width, height))


def set_geometry(widget: QtWidgets.QWidget, item: str):
    global config
    pos = widget.pos()
    config.set(item, 'x_position', pos.x())
    config.set(item, 'y_position', pos.y())
    # config.set(item, 'width', q_rect.width())
    # config.set(item, 'height', q_rect.height())

    cfg_path = os.path.join(os.path.expanduser("~"), config_file)
    save_config_file(config, cfg_path)


def get_home_dir():
    global config
    return config.get('Environment', 'WorkingDirectory')


def set_home_dir(path):
    global config
    config.set('Environment', 'WorkingDirectory', path)
    cfg_path = os.path.join(os.path.expanduser("~"), config_file)
    save_config_file(config, cfg_path)


if __name__ == '__main__':
    pass
else:
    config = load_cfg()