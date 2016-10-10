# Standard library
import os
import sys

# Pyblish libraries
import pyblish.api

# Host libraries
import nuke
import nukescripts

# Local libraries
from . import plugins

try:
    from .vendor.Qt import QtWidgets, QtGui
except ImportError:
    raise ImportError("Pyblish requires either PySide or PyQt bindings.")

cached_process = None


self = sys.modules[__name__]
self._has_been_setup = False
self._has_menu = False
self._registered_gui = None
self._dock = False


def setup(console=False, port=None, menu=True, dock=False):
    """Setup integration

    Registers Pyblish for Maya plug-ins and appends an item to the File-menu

    Arguments:
        console (bool): Display console with GUI
        port (int, optional): Port from which to start looking for an
            available port to connect with Pyblish QML, default
            provided by Pyblish Integration.

    """

    if self._has_been_setup:
        teardown()

    register_plugins()
    register_host()

    if menu:
        add_to_filemenu()
        self._has_menu = True

    if dock:
        self._dock = True
    else:
        self._dock = False

    self._has_been_setup = True
    print("pyblish: Loaded successfully.")


def show():
    """Try showing the most desirable GUI

    This function cycles through the currently registered
    graphical user interfaces, if any, and presents it to
    the user.

    """

    window = (_discover_gui() or _show_no_gui)()

    if self._dock:
        dock_window(window)

    return window


def _discover_gui():
    """Return the most desirable of the currently registered GUIs"""

    # Prefer last registered
    guis = reversed(pyblish.api.registered_guis())

    for gui in guis:
        try:
            gui = __import__(gui).show
        except (ImportError, AttributeError):
            continue
        else:
            return gui


def teardown():
    """Remove integration"""
    if not self._has_been_setup:
        return

    deregister_plugins()
    deregister_host()

    if self._has_menu:
        remove_from_filemenu()
        self._has_menu = False

    self._has_been_setup = False
    print("pyblish: Integration torn down successfully")


def remove_from_filemenu():
    menubar = nuke.menu('Nuke')
    menu = menubar.menu('File')

    menu.removeItem("Publish")


def deregister_plugins():
    # De-register accompanying plugins
    plugin_path = os.path.dirname(plugins.__file__)
    pyblish.api.deregister_plugin_path(plugin_path)
    print("pyblish: Deregistered %s" % plugin_path)


def register_host():
    """Register supported hosts"""
    pyblish.api.register_host("nuke")


def deregister_host():
    """De-register supported hosts"""
    pyblish.api.deregister_host("nuke")


def register_plugins():
    # Register accompanying plugins
    plugin_path = os.path.dirname(plugins.__file__)
    pyblish.api.register_plugin_path(plugin_path)


def filemenu_publish():
    """DEPRECATED"""


def add_to_filemenu():
    menubar = nuke.menu('Nuke')
    menu = menubar.menu('File')

    menu.addSeparator(index=8)

    cmd = 'import pyblish_nuke;pyblish_nuke.show()'
    menu.addCommand('Publish', cmd, index=9)

    menu.addSeparator(index=10)


def _show_no_gui():
    """Popup with information about how to register a new GUI

    In the event of no GUI being registered or available,
    this information dialog will appear to guide the user
    through how to get set up with one.

    """

    messagebox = QtWidgets.QMessageBox()
    messagebox.setIcon(messagebox.Warning)
    messagebox.setWindowIcon(QtGui.QIcon(os.path.join(
        os.path.dirname(pyblish.__file__),
        "icons",
        "logo-32x32.svg"))
    )

    spacer = QtWidgets.QWidget()
    spacer.setMinimumSize(400, 0)
    spacer.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                         QtWidgets.QSizePolicy.Expanding)

    layout = messagebox.layout()
    layout.addWidget(spacer, layout.rowCount(), 0, 1, layout.columnCount())

    messagebox.setWindowTitle("Uh oh")
    messagebox.setText("No registered GUI found.")

    if not pyblish.api.registered_guis():
        messagebox.setInformativeText(
            "In order to show you a GUI, one must first be registered. "
            "Press \"Show details...\" below for information on how to "
            "do that.")

        messagebox.setDetailedText(
            "Pyblish supports one or more graphical user interfaces "
            "to be registered at once, the next acting as a fallback to "
            "the previous."
            "\n"
            "\n"
            "For example, to use Pyblish Lite, first install it:"
            "\n"
            "\n"
            "$ pip install pyblish-lite"
            "\n"
            "\n"
            "Then register it, like so:"
            "\n"
            "\n"
            ">>> import pyblish.api\n"
            ">>> pyblish.api.register_gui(\"pyblish_lite\")"
            "\n"
            "\n"
            "The next time you try running this, Lite will appear."
            "\n"
            "See http://api.pyblish.com/register_gui.html for "
            "more information.")

    else:
        messagebox.setInformativeText(
            "None of the registered graphical user interfaces "
            "could be found."
            "\n"
            "\n"
            "Press \"Show details\" for more information.")

        messagebox.setDetailedText(
            "These interfaces are currently registered."
            "\n"
            "%s" % "\n".join(pyblish.api.registered_guis()))

    messagebox.setStandardButtons(messagebox.Ok)
    messagebox.exec_()


def where(program):
    """DEPRECATED"""


def _nuke_set_zero_margins(widget_object):
    """Remove Nuke margins when docked UI
    .. _More info:
        https://gist.github.com/maty974/4739917
    """
    parentApp = QtWidgets.QApplication.allWidgets()
    parentWidgetList = []
    for parent in parentApp:
        for child in parent.children():
            if widget_object.__class__.__name__ == child.__class__.__name__:
                parentWidgetList.append(
                    parent.parentWidget())
                parentWidgetList.append(
                    parent.parentWidget().parentWidget())
                parentWidgetList.append(
                    parent.parentWidget().parentWidget().parentWidget())

                for sub in parentWidgetList:
                        for tinychild in sub.children():
                            try:
                                tinychild.setContentsMargins(0, 0, 0, 0)
                            except:
                                pass


class pyblish_nuke_dockwidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        QtWidgets.QVBoxLayout(self)
        self.setObjectName("pyblish_nuke.dock")


def dock_window(widget):

    # delete existing dock
    for obj in QtWidgets.QApplication.allWidgets():
        if obj.objectName() == "pyblish_nuke.dock":
            obj.deleteLater()

    pane = nuke.getPaneFor("Properties.1")
    widget_path = "pyblish_nuke.lib.pyblish_nuke_dockwidget"
    panel = nukescripts.panels.registerWidgetAsPanel(widget_path,
                                                     "Pyblish",
                                                     "pyblish_nuke.dock",
                                                     True).addToPane(pane)

    panel_widget = panel.customKnob.getObject().widget
    _nuke_set_zero_margins(panel_widget)
    panel_widget.layout().addWidget(widget)
