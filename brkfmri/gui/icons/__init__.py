import os


def get_curpath(path):
    return os.path.join(os.path.dirname(__file__), path)


icon_sets = dict(
    win_icon=get_curpath("WindowsIcon.ico"),
    file_exit=get_curpath("file_exit.ico"),
    file_setpath=get_curpath("file_setpath.ico"),
    file_load=get_curpath("file_load.ico"),
    data_refresh=get_curpath("data_refresh.ico"),
    data_scanlist=get_curpath("data_scanlist.ico"),
    data_layer=get_curpath("data_layer.ico"),
    data_analysis=get_curpath("data_analysis.ico"),
    window_center=get_curpath("window_center.ico"),
)
