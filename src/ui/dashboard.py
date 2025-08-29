"""
Network Dashboard - Main overview widget
Provides a comprehensive overview of network status and statistics
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QGroupBox, QProgressBar, QPushButton,
                            QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette
import psutil
import platform
from datetime import datetime

from ..utils.theme import get_accent_color, get_success_color, get_warning_color, get_error_color


class NetworkDashboard(QWidget):
    """Network dashboard providing system overview"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timer()
        self.update_data()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)
        
        # Main content widget
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)
        
        # Welcome section
        welcome_section = self.create_welcome_section()
        content_layout.addWidget(welcome_section)
        
        # Stats grid
        stats_grid = self.create_stats_grid()
        content_layout.addWidget(stats_grid)
        
        # Network interfaces section
        interfaces_section = self.create_interfaces_section()
        content_layout.addWidget(interfaces_section)
        
        # System info section
        system_section = self.create_system_section()
        content_layout.addWidget(system_section)
        
        content_layout.addStretch()
        
    def create_welcome_section(self):
        """Create welcome section"""
        group = QGroupBox("Welcome to NetTools")
        layout = QVBoxLayout(group)
        
        welcome_label = QLabel("Professional Network Analysis Tool")
        welcome_font = QFont()
        welcome_font.setPointSize(14)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet(f"color: {get_accent_color()}; padding: 10px;")
        layout.addWidget(welcome_label)
        
        desc_label = QLabel("Monitor your network interfaces, analyze DNS routes, validate subnets, and more.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; padding: 5px 10px;")
        layout.addWidget(desc_label)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        quick_scan_btn = QPushButton("Quick Network Scan")
        quick_scan_btn.clicked.connect(self.quick_scan)
        actions_layout.addWidget(quick_scan_btn)
        
        refresh_btn = QPushButton("Refresh Dashboard")
        refresh_btn.clicked.connect(self.update_data)
        actions_layout.addWidget(refresh_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return group
        
    def create_stats_grid(self):
        """Create statistics grid"""
        group = QGroupBox("Network Statistics")
        grid_layout = QGridLayout(group)
        
        # Network status
        self.network_status_card = self.create_stat_card("Network Status", "Checking...", get_success_color())
        grid_layout.addWidget(self.network_status_card, 0, 0)
        
        # Active connections
        self.connections_card = self.create_stat_card("Active Connections", "0", get_accent_color())
        grid_layout.addWidget(self.connections_card, 0, 1)
        
        # Data sent
        self.data_sent_card = self.create_stat_card("Data Sent", "0 MB", get_warning_color())
        grid_layout.addWidget(self.data_sent_card, 0, 2)
        
        # Data received
        self.data_received_card = self.create_stat_card("Data Received", "0 MB", get_warning_color())
        grid_layout.addWidget(self.data_received_card, 0, 3)
        
        return group
        
    def create_stat_card(self, title, value, color):
        """Create a statistics card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #5a5a5a;
                border-radius: 5px;
                background-color: #2b2b2b;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Store value label for updates
        card.value_label = value_label
        
        return card
        
    def create_interfaces_section(self):
        """Create network interfaces section"""
        group = QGroupBox("Network Interfaces")
        layout = QVBoxLayout(group)
        
        self.interfaces_layout = QVBoxLayout()
        layout.addLayout(self.interfaces_layout)
        
        return group
        
    def create_system_section(self):
        """Create system information section"""
        group = QGroupBox("System Information")
        layout = QGridLayout(group)
        
        # System info labels
        info_data = [
            ("Operating System", platform.system() + " " + platform.release()),
            ("Machine", platform.machine()),
            ("Processor", platform.processor()[:50] + "..." if len(platform.processor()) > 50 else platform.processor()),
            ("Python Version", platform.python_version()),
            ("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]
        
        for i, (label, value) in enumerate(info_data):
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("color: #cccccc; font-weight: bold;")
            layout.addWidget(label_widget, i, 0)
            
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {get_accent_color()};")
            layout.addWidget(value_widget, i, 1)
            
        return group
        
    def update_interfaces(self):
        """Update network interfaces information"""
        # Clear existing interface widgets
        for i in reversed(range(self.interfaces_layout.count())):
            child = self.interfaces_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Get network interfaces
        try:
            interfaces = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            
            for interface_name, stats in interfaces.items():
                if interface_name.startswith('lo'):  # Skip loopback
                    continue
                    
                interface_widget = self.create_interface_widget(interface_name, stats, addrs.get(interface_name, []))
                self.interfaces_layout.addWidget(interface_widget)
                
        except Exception as e:
            error_label = QLabel(f"Error loading interfaces: {str(e)}")
            error_label.setStyleSheet(f"color: {get_error_color()};")
            self.interfaces_layout.addWidget(error_label)
            
    def create_interface_widget(self, name, stats, addresses):
        """Create widget for a network interface"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                background-color: #191919;
                margin: 2px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        
        # Interface name and status
        info_layout = QVBoxLayout()
        
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {get_accent_color()}; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        status_color = get_success_color() if stats.isup else get_error_color()
        status_text = "Up" if stats.isup else "Down"
        status_label = QLabel(f"Status: {status_text}")
        status_label.setStyleSheet(f"color: {status_color};")
        info_layout.addWidget(status_label)
        
        # Add IP addresses
        for addr in addresses:
            if addr.family.name in ['AF_INET', 'AF_INET6']:
                ip_label = QLabel(f"IP: {addr.address}")
                ip_label.setStyleSheet("color: #cccccc; font-size: 11px;")
                info_layout.addWidget(ip_label)
                break
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Speed info
        if hasattr(stats, 'speed') and stats.speed > 0:
            speed_label = QLabel(f"{stats.speed} Mbps")
            speed_label.setStyleSheet(f"color: {get_warning_color()}; font-weight: bold;")
            layout.addWidget(speed_label)
        
        return widget
        
    def update_data(self):
        """Update all dashboard data"""
        try:
            # Update network statistics
            net_io = psutil.net_io_counters()
            connections = len(psutil.net_connections())
            
            # Update stat cards
            self.network_status_card.value_label.setText("Connected")
            self.network_status_card.value_label.setStyleSheet(f"color: {get_success_color()}; font-size: 18px; font-weight: bold;")
            
            self.connections_card.value_label.setText(str(connections))
            
            # Convert bytes to MB
            sent_mb = net_io.bytes_sent / (1024 * 1024)
            received_mb = net_io.bytes_recv / (1024 * 1024)
            
            self.data_sent_card.value_label.setText(f"{sent_mb:.1f} MB")
            self.data_received_card.value_label.setText(f"{received_mb:.1f} MB")
            
            # Update interfaces
            self.update_interfaces()
            
        except Exception as e:
            self.network_status_card.value_label.setText("Error")
            self.network_status_card.value_label.setStyleSheet(f"color: {get_error_color()}; font-size: 18px; font-weight: bold;")
            
    def setup_timer(self):
        """Setup update timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(10000)  # Update every 10 seconds
        
    def quick_scan(self):
        """Perform a quick network scan"""
        # TODO: Implement quick network scan
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Quick Scan", "Quick network scan functionality will be implemented soon!")
        
    def refresh(self):
        """Refresh dashboard data"""
        self.update_data()
