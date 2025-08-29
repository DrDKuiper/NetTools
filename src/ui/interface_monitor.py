"""
Interface Monitor Widget
Real-time monitoring of network interfaces with graphs and statistics
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
                            QPushButton, QComboBox, QSpinBox, QCheckBox,
                            QProgressBar, QSplitter)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont
import psutil
import time
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.style as mplstyle

from ..utils.theme import get_accent_color, get_success_color, get_warning_color, get_error_color


class NetworkMonitorWorker(QThread):
    """Worker thread for network monitoring"""
    data_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.interval = 1.0  # seconds
        
    def run(self):
        """Run the monitoring loop"""
        self.running = True
        last_net_io = psutil.net_io_counters(pernic=True)
        last_time = time.time()
        
        while self.running:
            time.sleep(self.interval)
            
            current_time = time.time()
            current_net_io = psutil.net_io_counters(pernic=True)
            time_diff = current_time - last_time
            
            interface_data = {}
            
            for interface, current_stats in current_net_io.items():
                if interface in last_net_io:
                    last_stats = last_net_io[interface]
                    
                    # Calculate speeds (bytes per second)
                    upload_speed = (current_stats.bytes_sent - last_stats.bytes_sent) / time_diff
                    download_speed = (current_stats.bytes_recv - last_stats.bytes_recv) / time_diff
                    
                    interface_data[interface] = {
                        'upload_speed': upload_speed,
                        'download_speed': download_speed,
                        'total_sent': current_stats.bytes_sent,
                        'total_recv': current_stats.bytes_recv,
                        'packets_sent': current_stats.packets_sent,
                        'packets_recv': current_stats.packets_recv,
                        'errors_in': current_stats.errin,
                        'errors_out': current_stats.errout,
                        'drops_in': current_stats.dropin,
                        'drops_out': current_stats.dropout
                    }
            
            self.data_updated.emit(interface_data)
            
            last_net_io = current_net_io
            last_time = current_time
            
    def stop(self):
        """Stop the monitoring"""
        self.running = False
        self.wait()


class NetworkGraph(FigureCanvas):
    """Real-time network usage graph"""
    
    def __init__(self, parent=None, title="Network Usage"):
        # Setup matplotlib for dark theme
        mplstyle.use('dark_background')
        
        self.figure = Figure(figsize=(12, 4), facecolor='#353535')
        super().__init__(self.figure)
        self.setParent(parent)
        
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor('#2b2b2b')
        self.axes.set_title(title, color='white', fontsize=12)
        self.axes.set_xlabel('Time', color='white')
        self.axes.set_ylabel('Speed (MB/s)', color='white')
        
        # Configure axes colors
        self.axes.tick_params(colors='white')
        self.axes.spines['bottom'].set_color('white')
        self.axes.spines['top'].set_color('white')
        self.axes.spines['right'].set_color('white')
        self.axes.spines['left'].set_color('white')
        
        # Data storage
        self.max_points = 60  # Show last 60 data points
        self.time_data = deque(maxlen=self.max_points)
        self.upload_data = deque(maxlen=self.max_points)
        self.download_data = deque(maxlen=self.max_points)
        
        # Lines
        self.upload_line, = self.axes.plot([], [], label='Upload', color='#ff6b6b', linewidth=2)
        self.download_line, = self.axes.plot([], [], label='Download', color='#4ecdc4', linewidth=2)
        
        self.axes.legend(loc='upper right')
        self.axes.grid(True, alpha=0.3)
        
        # Tight layout
        self.figure.tight_layout()
        
    def update_data(self, upload_speed, download_speed):
        """Update graph data"""
        current_time = time.time()
        
        # Convert bytes to MB
        upload_mb = upload_speed / (1024 * 1024)
        download_mb = download_speed / (1024 * 1024)
        
        self.time_data.append(current_time)
        self.upload_data.append(upload_mb)
        self.download_data.append(download_mb)
        
        if len(self.time_data) > 1:
            # Convert time to relative seconds
            time_relative = [(t - self.time_data[0]) for t in self.time_data]
            
            self.upload_line.set_data(time_relative, self.upload_data)
            self.download_line.set_data(time_relative, self.download_data)
            
            # Update axes limits
            self.axes.set_xlim(0, max(time_relative))
            
            max_speed = max(max(self.upload_data, default=0), max(self.download_data, default=0))
            self.axes.set_ylim(0, max(max_speed * 1.1, 1))  # At least 1 MB/s scale
            
            self.draw()


class InterfaceMonitorWidget(QWidget):
    """Interface monitoring widget with real-time graphs and statistics"""
    
    def __init__(self):
        super().__init__()
        self.interface_data = {}
        self.init_ui()
        self.setup_monitoring()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Graph section
        graph_group = QGroupBox("Real-time Network Usage")
        graph_layout = QVBoxLayout(graph_group)
        
        self.network_graph = NetworkGraph(title="Network Interface Usage")
        graph_layout.addWidget(self.network_graph)
        
        splitter.addWidget(graph_group)
        
        # Statistics table
        stats_group = QGroupBox("Interface Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_table = QTableWidget()
        self.setup_stats_table()
        stats_layout.addWidget(self.stats_table)
        
        splitter.addWidget(stats_group)
        
        # Set splitter proportions
        splitter.setSizes([400, 300])
        
    def create_control_panel(self):
        """Create control panel"""
        group = QGroupBox("Monitor Settings")
        layout = QHBoxLayout(group)
        
        # Interface selection
        layout.addWidget(QLabel("Interface:"))
        self.interface_combo = QComboBox()
        self.interface_combo.currentTextChanged.connect(self.on_interface_changed)
        layout.addWidget(self.interface_combo)
        
        layout.addStretch()
        
        # Update interval
        layout.addWidget(QLabel("Update Interval:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(1)
        self.interval_spin.setSuffix(" sec")
        self.interval_spin.valueChanged.connect(self.on_interval_changed)
        layout.addWidget(self.interval_spin)
        
        layout.addStretch()
        
        # Auto-refresh checkbox
        self.auto_refresh_check = QCheckBox("Auto Refresh")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.toggled.connect(self.on_auto_refresh_toggled)
        layout.addWidget(self.auto_refresh_check)
        
        # Control buttons
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        return group
        
    def setup_stats_table(self):
        """Setup statistics table"""
        self.stats_table.setColumnCount(7)
        self.stats_table.setHorizontalHeaderLabels([
            "Interface", "Status", "Upload Speed", "Download Speed", 
            "Total Sent", "Total Received", "Errors"
        ])
        
        # Make table read-only and set selection behavior
        self.stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stats_table.setAlternatingRowColors(True)
        
        # Resize columns to content
        self.stats_table.resizeColumnsToContents()
        
    def populate_interfaces(self):
        """Populate interface combo box"""
        self.interface_combo.clear()
        self.interface_combo.addItem("All Interfaces")
        
        try:
            interfaces = psutil.net_if_stats()
            for interface_name in interfaces.keys():
                if not interface_name.startswith('lo'):  # Skip loopback
                    self.interface_combo.addItem(interface_name)
        except Exception as e:
            print(f"Error loading interfaces: {e}")
            
    def setup_monitoring(self):
        """Setup monitoring worker"""
        self.monitor_worker = NetworkMonitorWorker()
        self.monitor_worker.data_updated.connect(self.update_data)
        
        # Populate interfaces
        self.populate_interfaces()
        
    def start_monitoring(self):
        """Start network monitoring"""
        if not self.monitor_worker.isRunning():
            self.monitor_worker.interval = self.interval_spin.value()
            self.monitor_worker.start()
            
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
    def stop_monitoring(self):
        """Stop network monitoring"""
        if self.monitor_worker.isRunning():
            self.monitor_worker.stop()
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def update_data(self, data):
        """Update UI with new data"""
        self.interface_data = data
        
        # Update graph for selected interface
        selected_interface = self.interface_combo.currentText()
        
        if selected_interface == "All Interfaces":
            # Sum all interfaces
            total_upload = sum(iface_data['upload_speed'] for iface_data in data.values())
            total_download = sum(iface_data['download_speed'] for iface_data in data.values())
            self.network_graph.update_data(total_upload, total_download)
        elif selected_interface in data:
            iface_data = data[selected_interface]
            self.network_graph.update_data(iface_data['upload_speed'], iface_data['download_speed'])
            
        # Update statistics table
        self.update_stats_table()
        
    def update_stats_table(self):
        """Update statistics table"""
        self.stats_table.setRowCount(len(self.interface_data))
        
        for row, (interface, data) in enumerate(self.interface_data.items()):
            # Interface name
            self.stats_table.setItem(row, 0, QTableWidgetItem(interface))
            
            # Status
            try:
                status = "Up" if psutil.net_if_stats()[interface].isup else "Down"
                status_item = QTableWidgetItem(status)
                if status == "Up":
                    status_item.setBackground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setBackground(Qt.GlobalColor.darkRed)
                self.stats_table.setItem(row, 1, status_item)
            except:
                self.stats_table.setItem(row, 1, QTableWidgetItem("Unknown"))
            
            # Upload speed
            upload_mbps = data['upload_speed'] / (1024 * 1024)
            self.stats_table.setItem(row, 2, QTableWidgetItem(f"{upload_mbps:.2f} MB/s"))
            
            # Download speed
            download_mbps = data['download_speed'] / (1024 * 1024)
            self.stats_table.setItem(row, 3, QTableWidgetItem(f"{download_mbps:.2f} MB/s"))
            
            # Total sent
            total_sent_mb = data['total_sent'] / (1024 * 1024)
            self.stats_table.setItem(row, 4, QTableWidgetItem(f"{total_sent_mb:.1f} MB"))
            
            # Total received
            total_recv_mb = data['total_recv'] / (1024 * 1024)
            self.stats_table.setItem(row, 5, QTableWidgetItem(f"{total_recv_mb:.1f} MB"))
            
            # Errors
            total_errors = data['errors_in'] + data['errors_out']
            error_item = QTableWidgetItem(str(total_errors))
            if total_errors > 0:
                error_item.setBackground(Qt.GlobalColor.darkYellow)
            self.stats_table.setItem(row, 6, error_item)
            
    def on_interface_changed(self, interface):
        """Handle interface selection change"""
        # Update graph title
        if interface == "All Interfaces":
            self.network_graph.axes.set_title("All Interfaces Usage", color='white')
        else:
            self.network_graph.axes.set_title(f"{interface} Usage", color='white')
        self.network_graph.draw()
        
    def on_interval_changed(self, interval):
        """Handle update interval change"""
        if hasattr(self, 'monitor_worker'):
            self.monitor_worker.interval = interval
            
    def on_auto_refresh_toggled(self, checked):
        """Handle auto refresh toggle"""
        if checked and not self.monitor_worker.isRunning():
            self.start_monitoring()
        elif not checked and self.monitor_worker.isRunning():
            self.stop_monitoring()
            
    def refresh(self):
        """Refresh interface data"""
        self.populate_interfaces()
        if self.auto_refresh_check.isChecked():
            self.start_monitoring()
            
    def closeEvent(self, event):
        """Handle widget close"""
        if hasattr(self, 'monitor_worker'):
            self.monitor_worker.stop()
        event.accept()
