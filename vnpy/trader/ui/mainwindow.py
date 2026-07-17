"""
Implements main window of the trading platform.
"""

from types import ModuleType
import webbrowser
from functools import partial
from importlib import import_module
from typing import TypeVar, cast
from collections.abc import Callable

import vnpy
from vnpy.event import EventEngine

from .qt import QtCore, QtGui, QtWidgets
from .widget import (
    BaseMonitor,
    TickMonitor,
    OrderMonitor,
    TradeMonitor,
    PositionMonitor,
    AccountMonitor,
    LogMonitor,
    ActiveOrderMonitor,
    ConnectDialog,
    ContractManager,
    HotMoneyWidget,
    TradingWidget,
    AboutDialog,
    GlobalDialog,
    WechatDialog
)
from ..engine import MainEngine, BaseApp, EmailEngine
from ..utility import get_icon_path, TRADER_DIR
from ..locale import _


WidgetType = TypeVar("WidgetType", bound="QtWidgets.QWidget")


class MainWindow(QtWidgets.QMainWindow):
    """
    Main window of the trading platform.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.window_title: str = _("VeighNa Trader 社区版 - {}   [{}]").format(vnpy.__version__, TRADER_DIR)

        self.widgets: dict[str, QtWidgets.QWidget] = {}
        self.monitors: dict[str, BaseMonitor] = {}
        self._docks: list[QtWidgets.QDockWidget] = []

        self.trading_widget: TradingWidget
        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(self.window_title)
        self.init_dock()
        self.init_toolbar()
        self.init_menu()
        self.init_central()
        self.load_window_setting("custom")

    def init_central(self) -> None:
        """"""
        # 中心总容器
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_h_layout = QtWidgets.QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(4, 4, 4, 4)
        main_h_layout.setSpacing(4)

        # ====================== 1. 左侧垂直工具栏 ======================
        self.toolbar.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.toolbar.setFixedWidth(40)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QtCore.QSize(32, 32))
        main_h_layout.addWidget(self.toolbar)

        # ====================== 外层横向分割器：左工具栏 | 中间区 | 右侧区 ======================
        outer_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        outer_splitter.setHandleWidth(4)
        main_h_layout.addWidget(outer_splitter)

        # ---------------------- 2. 中间整体区域（上绘图 + 下表格） ----------------------
        mid_container = QtWidgets.QWidget()
        mid_vlay = QtWidgets.QVBoxLayout(mid_container)
        mid_vlay.setContentsMargins(0,0,0,0)
        mid_vlay.setSpacing(4)

        # 上部 pyqtgraph 图表
        hot_money_widget: HotMoneyWidget = HotMoneyWidget(self.main_engine, self.event_engine)
        mid_vlay.addWidget(hot_money_widget, stretch=3)

        # 下部表格
        # mid_table = QtWidgets.QTableWidget()
        # mid_table.setRowCount(10)
        # mid_table.setColumnCount(6)
        # mid_vlay.addWidget(mid_table, stretch=2)

        outer_splitter.addWidget(mid_container)

        # ---------------------- 3. 右侧整体区域（右上交易+行情，右下Tab表格） ----------------------
        right_container = QtWidgets.QWidget()
        right_vlay = QtWidgets.QVBoxLayout(right_container)
        right_vlay.setContentsMargins(0,0,0,0)
        right_vlay.setSpacing(4)

        # 右上横向分割：交易面板 | 行情表格
        right_top_split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        right_top_split.setHandleWidth(4)

        # 交易面板
        self.trading_widget, trading_dock = self.create_dock(
            TradingWidget, _("交易"), QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
        )
        right_top_split.addWidget(self.trading_widget)

        self.monitors[_("行情")].itemDoubleClicked.connect(self.trading_widget.update_with_cell)
        self.monitors[_("持仓")].itemDoubleClicked.connect(self.trading_widget.update_with_cell)

        # 行情表格
        right_top_split.addWidget(self.monitors[_("行情")])

        right_vlay.addWidget(right_top_split)

        # 右下Tab标签页，每个标签都是表格
        tab_widget = QtWidgets.QTabWidget()
        tab_names = [_("活动"), _("委托"), _("成交"), _("日志"), _("持仓"), _("资金")]
        for name in tab_names:
            tab_widget.addTab(self.monitors[name], name)
        tab_widget.setMaximumHeight(500)
        right_vlay.addWidget(tab_widget, stretch=1)

        outer_splitter.addWidget(right_container)

        # 外层三大块初始宽度比例：工具栏忽略，中间:右侧 = 5:4
        outer_splitter.setStretchFactor(0, 5)
        outer_splitter.setStretchFactor(1, 4)


    def init_dock(self) -> None:
        """"""
        
        tick_widget, tick_dock = self.create_dock(
            TickMonitor, _("行情"), QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        order_widget, order_dock = self.create_dock(
            OrderMonitor, _("委托"), QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        active_widget, active_dock = self.create_dock(
            ActiveOrderMonitor, _("活动"), QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        trade_widget, trade_dock = self.create_dock(
            TradeMonitor, _("成交"), QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        log_widget, log_dock = self.create_dock(
            LogMonitor, _("日志"), QtCore.Qt.DockWidgetArea.BottomDockWidgetArea
        )
        account_widget, account_dock = self.create_dock(
            AccountMonitor, _("资金"), QtCore.Qt.DockWidgetArea.BottomDockWidgetArea
        )
        position_widget, position_dock = self.create_dock(
            PositionMonitor, _("持仓"), QtCore.Qt.DockWidgetArea.BottomDockWidgetArea
        )

        # self.tabifyDockWidget(active_dock, order_dock)

        self.save_window_setting("default")

    def init_menu(self) -> None:
        """"""
        bar: QtWidgets.QMenuBar = self.menuBar()
        bar.setNativeMenuBar(False)     # for mac and linux

        # System menu
        sys_menu: QtWidgets.QMenu = bar.addMenu(_("系统"))

        gateway_names: list = self.main_engine.get_all_gateway_names()
        for name in gateway_names:
            func: Callable = partial(self.connect_gateway, name)
            self.add_action(
                sys_menu,
                _("连接{}").format(name),
                get_icon_path(__file__, "connect.ico"),
                func
            )

        sys_menu.addSeparator()

        self.add_action(
            sys_menu,
            _("退出"),
            get_icon_path(__file__, "exit.ico"),
            self.close
        )

        # App menu
        app_menu: QtWidgets.QMenu = bar.addMenu(_("功能"))

        all_apps: list[BaseApp] = self.main_engine.get_all_apps()
        for app in all_apps:
            ui_module: ModuleType = import_module(app.app_module + ".ui")
            widget_class: type[QtWidgets.QWidget] = getattr(ui_module, app.widget_name)

            func = partial(self.open_widget, widget_class, app.app_name)

            self.add_action(app_menu, app.display_name, app.icon_name, func, True)

        # Global setting editor
        setting_action: QtGui.QAction = QtGui.QAction(_("配置"), self)
        setting_action.triggered.connect(self.edit_global_setting)
        bar.addAction(setting_action)

        # Wechat notification
        wechat_action: QtGui.QAction = QtGui.QAction(_("微信"), self)
        wechat_action.triggered.connect(self.open_wechat_dialog)
        bar.addAction(wechat_action)

        # Help menu
        help_menu: QtWidgets.QMenu = bar.addMenu(_("帮助"))

        self.add_action(
            help_menu,
            _("查询合约"),
            get_icon_path(__file__, "contract.ico"),
            partial(self.open_widget, ContractManager, "contract"),
            True
        )

        self.add_action(
            help_menu,
            _("还原窗口"),
            get_icon_path(__file__, "restore.ico"),
            self.restore_window_setting
        )

        self.add_action(
            help_menu,
            _("测试邮件"),
            get_icon_path(__file__, "email.ico"),
            self.send_test_email
        )

        self.add_action(
            help_menu,
            _("社区论坛"),
            get_icon_path(__file__, "forum.ico"),
            self.open_forum,
            True
        )

        self.add_action(
            help_menu,
            _("关于"),
            get_icon_path(__file__, "about.ico"),
            partial(self.open_widget, AboutDialog, "about"),
        )

    def init_toolbar(self) -> None:
        """"""
        self.toolbar: QtWidgets.QToolBar = QtWidgets.QToolBar(self)
        self.toolbar.setObjectName(_("工具栏"))
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        # Set button size
        w: int = 40
        size = QtCore.QSize(w, w)
        self.toolbar.setIconSize(size)

        # Set button spacing
        layout: QtWidgets.QLayout | None = self.toolbar.layout()
        if layout:
            layout.setSpacing(10)

        # self.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self.toolbar)

    def add_action(
        self,
        menu: QtWidgets.QMenu,
        action_name: str,
        icon_name: str,
        func: Callable,
        toolbar: bool = False
    ) -> None:
        """"""
        icon: QtGui.QIcon = QtGui.QIcon(icon_name)

        action: QtGui.QAction = QtGui.QAction(action_name, self)
        action.triggered.connect(func)
        action.setIcon(icon)

        menu.addAction(action)

        if toolbar:
            self.toolbar.addAction(action)

    def create_dock(
        self,
        widget_class: type[WidgetType],
        name: str,
        area: QtCore.Qt.DockWidgetArea
    ) -> tuple[WidgetType, QtWidgets.QDockWidget]:
        """
        Initialize a dock widget.
        """
        widget: WidgetType = widget_class(self.main_engine, self.event_engine)      # type: ignore
        if isinstance(widget, BaseMonitor):
            self.monitors[name] = widget

        dock: QtWidgets.QDockWidget = QtWidgets.QDockWidget(name)
        dock.setWidget(widget)
        dock.setObjectName(name)
        dock.setFeatures(dock.DockWidgetFeature.DockWidgetFloatable | dock.DockWidgetFeature.DockWidgetMovable)
        # self.addDockWidget(area, dock)
        self._docks.append(dock)
        return widget, dock

    def connect_gateway(self, gateway_name: str) -> None:
        """
        Open connect dialog for gateway connection.
        """
        dialog: ConnectDialog = ConnectDialog(self.main_engine, gateway_name)
        dialog.exec()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Call main engine close function before exit.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            _("退出"),
            _("确认退出？"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            for widget in self.widgets.values():
                widget.close()

            for monitor in self.monitors.values():
                monitor.save_setting()

            self.save_window_setting("custom")

            self.main_engine.close()

            event.accept()
        else:
            event.ignore()

    def open_widget(self, widget_class: type[QtWidgets.QWidget], name: str) -> None:
        """
        Open contract manager.
        """
        widget: QtWidgets.QWidget | None = self.widgets.get(name, None)
        if not widget:
            widget = widget_class(self.main_engine, self.event_engine)      # type: ignore
            self.widgets[name] = widget

        if isinstance(widget, QtWidgets.QDialog):
            widget.exec()
        else:
            widget.show()

    def save_window_setting(self, name: str) -> None:
        """
        Save current window size and state by trader path and setting name.
        """
        settings: QtCore.QSettings = QtCore.QSettings(self.window_title, name)
        settings.setValue("state", self.saveState())
        settings.setValue("geometry", self.saveGeometry())

    def load_window_setting(self, name: str) -> None:
        """
        Load previous window size and state by trader path and setting name.
        """
        settings: QtCore.QSettings = QtCore.QSettings(self.window_title, name)
        state = settings.value("state")
        geometry = settings.value("geometry")

        if isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
            self.restoreGeometry(geometry)

    def restore_window_setting(self) -> None:
        """
        Restore window to default setting.
        """
        self.load_window_setting("default")
        self.showMaximized()

    def send_test_email(self) -> None:
        """
        Sending a test email.
        """
        email_engine: EmailEngine = cast(EmailEngine, self.main_engine.get_engine("email"))
        email_engine.send_email("VeighNa Trader", "testing")

    def open_forum(self) -> None:
        """
        """
        webbrowser.open("https://www.vnpy.com/forum/")

    def edit_global_setting(self) -> None:
        """
        """
        dialog: GlobalDialog = GlobalDialog()
        dialog.exec()

    def open_wechat_dialog(self) -> None:
        """
        Open WeChat notification dialog.
        """
        dialog: WechatDialog = WechatDialog(self.main_engine, self.event_engine)
        dialog.exec()
