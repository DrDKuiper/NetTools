"""
Main window for NetTools application
Provides the primary user interface with tabs for different network analysis tools
"""

from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
                            QMenuBar, QStatusBar, QSplitter, QHBoxLayout,
                            QLabel, QPushButton, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction
import sys
import os

from .dashboard import NetworkDashboard
from .interface_monitor import InterfaceMonitorWidget
from .dns_analyzer import DNSAnalyzerWidget
from .subnet_validator import SubnetValidatorWidget
from .speed_test import SpeedTestWidget
from .ping_tool import PingToolWidget
from ..utils.theme import get_accent_color, get_success_color


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_status_bar()
        self.setup_menu_bar()
        self.setup_timer()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("NetTools - Professional Network Analysis")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Set window icon
        self.set_window_icon()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create header
        header = self.create_header()
        layout.addWidget(header)
        
        # Create main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        content_splitter.addWidget(self.tab_widget)
        
        # Add tabs
        self.setup_tabs()
        
        # Set splitter proportions
        content_splitter.setSizes([1200, 200])
        
    def create_header(self):
        """Create the application header"""
        header_widget = QWidget()
        header_widget.setFixedHeight(60)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: #2b2b2b;
                border-bottom: 2px solid {get_accent_color()};
            }}
        """)
        
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo and title
        title_label = QLabel("NetTools")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {get_accent_color()}; border: none;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Professional Network Analysis Tool")
        subtitle_label.setStyleSheet("color: #cccccc; border: none; font-size: 12px;")
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"color: {get_success_color()}; font-size: 16px; border: none;")
        self.status_indicator.setToolTip("Application Status: Running")
        layout.addWidget(self.status_indicator)
        
        status_text = QLabel("Ready")
        status_text.setStyleSheet("color: #cccccc; border: none; margin-left: 5px;")
        layout.addWidget(status_text)
        
        return header_widget
        
    def setup_tabs(self):
        """Setup all application tabs"""
        # Dashboard tab
        self.dashboard = NetworkDashboard()
        self.tab_widget.addTab(self.dashboard, "🏠 Dashboard")
        
        # Interface Monitor tab
        self.interface_monitor = InterfaceMonitorWidget()
        self.tab_widget.addTab(self.interface_monitor, "📊 Interface Monitor")
        
        # DNS Analyzer tab
        self.dns_analyzer = DNSAnalyzerWidget()
        self.tab_widget.addTab(self.dns_analyzer, "🌐 DNS Analyzer")
        
        # Subnet Validator tab
        self.subnet_validator = SubnetValidatorWidget()
        self.tab_widget.addTab(self.subnet_validator, "🔍 Subnet Validator")
        
        # Speed Test tab
        self.speed_test = SpeedTestWidget()
        self.tab_widget.addTab(self.speed_test, "⚡ Speed Test")
        
        # Ping Tool tab
        self.ping_tool = PingToolWidget()
        self.tab_widget.addTab(self.ping_tool, "📡 Ping Tool")
        
    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export Report", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_report)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        refresh_action = QAction("Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        tools_menu.addAction(refresh_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets to status bar
        self.network_status = QLabel("Network: Connected")
        self.network_status.setStyleSheet(f"color: {get_success_color()};")
        self.status_bar.addPermanentWidget(self.network_status)
        
        self.status_bar.showMessage("Ready")
        
    def setup_timer(self):
        """Setup update timer for real-time data"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
        
    def set_window_icon(self):
        """Set the window icon"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", "nettools.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass  # Icon not found, continue without it
            
    def update_status(self):
        """Update status information"""
        # This would update network status, connection info, etc.
        pass
        
    def refresh_all(self):
        """Refresh all tabs"""
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'refresh'):
            current_tab.refresh()
            
    def export_report(self):
        """Export network analysis report"""
        # TODO: Implement report export functionality
        self.status_bar.showMessage("Export functionality coming soon...", 3000)
        
    def show_settings(self):
        """Show settings dialog"""
        # TODO: Implement settings dialog
        self.status_bar.showMessage("Settings dialog coming soon...", 3000)
        
    def show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = """
        <h2>NetTools v1.0.0</h2>
        <p>Professional Network Analysis Tool</p>
        <p>Features:</p>
        <ul>
        <li>Real-time network interface monitoring</li>
        <li>DNS route analysis</li>
        <li>Subnet validation</li>
        <li>Network speed testing</li>
        <li>Ping utilities</li>
        <li>Professional reporting</li>
        </ul>
        <p><b>Created with Python and PyQt6</b></p>
        """
        
        QMessageBox.about(self, "About NetTools", about_text)
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up any running processes
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
            
        event.accept()
