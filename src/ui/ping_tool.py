"""
Ping Tool Widget
Advanced ping utilities with continuous monitoring and statistics
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QGroupBox, QLineEdit, QPushButton, QTextEdit,
                            QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
                            QComboBox, QProgressBar, QTabWidget, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
import ping3
import time
import socket
from datetime import datetime
import statistics
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.style as mplstyle
from collections import deque

from ..utils.theme import get_accent_color, get_success_color, get_warning_color, get_error_color


class PingWorker(QThread):
    """Worker thread for ping operations"""
    ping_result = pyqtSignal(dict)
    ping_completed = pyqtSignal(dict)
    
    def __init__(self, host, count=4, interval=1, timeout=3, packet_size=32):
        super().__init__()
        self.host = host
        self.count = count
        self.interval = interval
        self.timeout = timeout
        self.packet_size = packet_size
        self.running = False
        
    def run(self):
        """Run ping test"""
        self.running = True
        results = []
        packets_sent = 0
        packets_received = 0
        
        for i in range(self.count):
            if not self.running:
                break
                
            packets_sent += 1
            start_time = time.time()
            
            try:
                # Perform ping
                response_time = ping3.ping(self.host, timeout=self.timeout, size=self.packet_size)
                
                if response_time is not None:
                    response_time_ms = response_time * 1000
                    packets_received += 1
                    results.append(response_time_ms)
                    
                    ping_data = {
                        'sequence': i + 1,
                        'time': response_time_ms,
                        'success': True,
                        'timestamp': datetime.now()
                    }
                else:
                    ping_data = {
                        'sequence': i + 1,
                        'time': None,
                        'success': False,
                        'error': 'Request timeout',
                        'timestamp': datetime.now()
                    }
                
                self.ping_result.emit(ping_data)
                
            except Exception as e:
                ping_data = {
                    'sequence': i + 1,
                    'time': None,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now()
                }
                self.ping_result.emit(ping_data)
            
            # Wait for interval (except for last ping)
            if i < self.count - 1 and self.running:
                time.sleep(self.interval)
        
        # Calculate statistics
        packet_loss = ((packets_sent - packets_received) / packets_sent) * 100 if packets_sent > 0 else 100
        
        stats = {
            'packets_sent': packets_sent,
            'packets_received': packets_received,
            'packet_loss': packet_loss,
            'min_time': min(results) if results else None,
            'max_time': max(results) if results else None,
            'avg_time': statistics.mean(results) if results else None,
            'median_time': statistics.median(results) if results else None,
            'std_dev': statistics.stdev(results) if len(results) > 1 else None
        }
        
        self.ping_completed.emit(stats)
        
    def stop(self):
        """Stop ping test"""
        self.running = False


class ContinuousPingWorker(QThread):
    """Worker thread for continuous ping monitoring"""
    ping_result = pyqtSignal(dict)
    
    def __init__(self, host, interval=1, timeout=3):
        super().__init__()
        self.host = host
        self.interval = interval
        self.timeout = timeout
        self.running = False
        
    def run(self):
        """Run continuous ping"""
        self.running = True
        sequence = 0
        
        while self.running:
            sequence += 1
            
            try:
                response_time = ping3.ping(self.host, timeout=self.timeout)
                
                if response_time is not None:
                    response_time_ms = response_time * 1000
                    ping_data = {
                        'sequence': sequence,
                        'time': response_time_ms,
                        'success': True,
                        'timestamp': datetime.now()
                    }
                else:
                    ping_data = {
                        'sequence': sequence,
                        'time': None,
                        'success': False,
                        'error': 'Request timeout',
                        'timestamp': datetime.now()
                    }
                
                self.ping_result.emit(ping_data)
                
            except Exception as e:
                ping_data = {
                    'sequence': sequence,
                    'time': None,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now()
                }
                self.ping_result.emit(ping_data)
            
            time.sleep(self.interval)
            
    def stop(self):
        """Stop continuous ping"""
        self.running = False
        self.wait()


class PingChart(FigureCanvas):
    """Real-time ping chart"""
    
    def __init__(self, parent=None):
        mplstyle.use('dark_background')
        
        self.figure = Figure(figsize=(12, 4), facecolor='#353535')
        super().__init__(self.figure)
        self.setParent(parent)
        
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor('#2b2b2b')
        self.axes.set_title('Ping Response Times', color='white', fontsize=12)
        self.axes.set_xlabel('Sequence Number', color='white')
        self.axes.set_ylabel('Response Time (ms)', color='white')
        
        # Configure axes colors
        self.axes.tick_params(colors='white')
        for spine in self.axes.spines.values():
            spine.set_color('white')
        
        self.figure.tight_layout()
        
        # Data storage
        self.max_points = 100
        self.sequences = deque(maxlen=self.max_points)
        self.response_times = deque(maxlen=self.max_points)
        self.timeouts = deque(maxlen=self.max_points)
        
    def add_ping_result(self, sequence, response_time, success):
        """Add ping result to chart"""
        self.sequences.append(sequence)
        
        if success and response_time is not None:
            self.response_times.append(response_time)
            self.timeouts.append(None)
        else:
            self.response_times.append(None)
            self.timeouts.append(sequence)
        
        self.update_chart()
        
    def update_chart(self):
        """Update the chart"""
        if len(self.sequences) < 2:
            return
            
        self.axes.clear()
        self.axes.set_facecolor('#2b2b2b')
        self.axes.set_title('Ping Response Times', color='white', fontsize=12)
        self.axes.set_xlabel('Sequence Number', color='white')
        self.axes.set_ylabel('Response Time (ms)', color='white')
        
        # Plot successful pings
        successful_sequences = []
        successful_times = []
        
        for seq, time in zip(self.sequences, self.response_times):
            if time is not None:
                successful_sequences.append(seq)
                successful_times.append(time)
        
        if successful_sequences:
            self.axes.plot(successful_sequences, successful_times, 
                          color='#4ecdc4', linewidth=2, marker='o', markersize=4, 
                          label='Response Time')
        
        # Mark timeouts
        timeout_sequences = [seq for seq, timeout in zip(self.sequences, self.timeouts) if timeout is not None]
        if timeout_sequences:
            # Use a high value for visualization
            max_time = max(successful_times) if successful_times else 100
            timeout_y = [max_time * 1.1] * len(timeout_sequences)
            self.axes.scatter(timeout_sequences, timeout_y, 
                            color='#ff6b6b', marker='x', s=50, 
                            label='Timeout')
        
        self.axes.legend()
        self.axes.grid(True, alpha=0.3)
        self.axes.tick_params(colors='white')
        
        for spine in self.axes.spines.values():
            spine.set_color('white')
        
        # Set x-axis limits
        if self.sequences:
            self.axes.set_xlim(min(self.sequences), max(self.sequences))
        
        self.draw()


class PingToolWidget(QWidget):
    """Ping tool widget with advanced ping functionality"""
    
    def __init__(self):
        super().__init__()
        self.ping_history = []
        self.continuous_stats = {
            'total_pings': 0,
            'successful_pings': 0,
            'failed_pings': 0,
            'min_time': None,
            'max_time': None,
            'avg_time': None
        }
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Standard Ping tab
        standard_tab = self.create_standard_ping_tab()
        tab_widget.addTab(standard_tab, "Standard Ping")
        
        # Continuous Ping tab
        continuous_tab = self.create_continuous_ping_tab()
        tab_widget.addTab(continuous_tab, "Continuous Ping")
        
        # Multi-Host Ping tab
        multi_host_tab = self.create_multi_host_tab()
        tab_widget.addTab(multi_host_tab, "Multi-Host Ping")
        
    def create_standard_ping_tab(self):
        """Create standard ping tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Ping configuration
        config_group = QGroupBox("Ping Configuration")
        config_layout = QGridLayout(config_group)
        
        # Host input
        config_layout.addWidget(QLabel("Host:"), 0, 0)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Enter hostname or IP address")
        self.host_input.returnPressed.connect(self.start_standard_ping)
        config_layout.addWidget(self.host_input, 0, 1, 1, 2)
        
        # Count
        config_layout.addWidget(QLabel("Count:"), 1, 0)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 1000)
        self.count_spin.setValue(4)
        config_layout.addWidget(self.count_spin, 1, 1)
        
        # Interval
        config_layout.addWidget(QLabel("Interval (s):"), 1, 2)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(1)
        config_layout.addWidget(self.interval_spin, 1, 3)
        
        # Timeout
        config_layout.addWidget(QLabel("Timeout (s):"), 2, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 30)
        self.timeout_spin.setValue(3)
        config_layout.addWidget(self.timeout_spin, 2, 1)
        
        # Packet size
        config_layout.addWidget(QLabel("Packet Size:"), 2, 2)
        self.packet_size_spin = QSpinBox()
        self.packet_size_spin.setRange(8, 65507)
        self.packet_size_spin.setValue(32)
        config_layout.addWidget(self.packet_size_spin, 2, 3)
        
        # Start button
        self.start_ping_btn = QPushButton("Start Ping")
        self.start_ping_btn.clicked.connect(self.start_standard_ping)
        config_layout.addWidget(self.start_ping_btn, 3, 0, 1, 2)
        
        # Stop button
        self.stop_ping_btn = QPushButton("Stop Ping")
        self.stop_ping_btn.clicked.connect(self.stop_standard_ping)
        self.stop_ping_btn.setEnabled(False)
        config_layout.addWidget(self.stop_ping_btn, 3, 2, 1, 2)
        
        layout.addWidget(config_group)
        
        # Progress
        self.ping_progress = QProgressBar()
        self.ping_progress.setVisible(False)
        layout.addWidget(self.ping_progress)
        
        # Results section
        results_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(results_splitter)
        
        # Results table
        results_group = QGroupBox("Ping Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        results_splitter.addWidget(results_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.stats_labels = {}
        stats_fields = [
            ("Packets Sent", "sent"),
            ("Packets Received", "received"),
            ("Packet Loss", "loss"),
            ("Min Time (ms)", "min"),
            ("Max Time (ms)", "max"),
            ("Avg Time (ms)", "avg"),
            ("Median Time (ms)", "median"),
            ("Std Deviation", "std")
        ]
        
        for i, (label, key) in enumerate(stats_fields):
            row = i // 2
            col = (i % 2) * 2
            
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            stats_layout.addWidget(label_widget, row, col)
            
            value_widget = QLabel("N/A")
            value_widget.setStyleSheet(f"color: {get_accent_color()};")
            self.stats_labels[key] = value_widget
            stats_layout.addWidget(value_widget, row, col + 1)
        
        results_splitter.addWidget(stats_group)
        results_splitter.setSizes([400, 200])
        
        return widget
        
    def create_continuous_ping_tab(self):
        """Create continuous ping tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls_group = QGroupBox("Continuous Ping Controls")
        controls_layout = QGridLayout(controls_group)
        
        # Host input
        controls_layout.addWidget(QLabel("Host:"), 0, 0)
        self.continuous_host_input = QLineEdit()
        self.continuous_host_input.setPlaceholderText("Enter hostname or IP address")
        controls_layout.addWidget(self.continuous_host_input, 0, 1, 1, 2)
        
        # Interval
        controls_layout.addWidget(QLabel("Interval (s):"), 1, 0)
        self.continuous_interval_spin = QSpinBox()
        self.continuous_interval_spin.setRange(1, 60)
        self.continuous_interval_spin.setValue(1)
        controls_layout.addWidget(self.continuous_interval_spin, 1, 1)
        
        # Timeout
        controls_layout.addWidget(QLabel("Timeout (s):"), 1, 2)
        self.continuous_timeout_spin = QSpinBox()
        self.continuous_timeout_spin.setRange(1, 30)
        self.continuous_timeout_spin.setValue(3)
        controls_layout.addWidget(self.continuous_timeout_spin, 1, 3)
        
        # Control buttons
        self.start_continuous_btn = QPushButton("Start Continuous Ping")
        self.start_continuous_btn.clicked.connect(self.start_continuous_ping)
        controls_layout.addWidget(self.start_continuous_btn, 2, 0, 1, 2)
        
        self.stop_continuous_btn = QPushButton("Stop Continuous Ping")
        self.stop_continuous_btn.clicked.connect(self.stop_continuous_ping)
        self.stop_continuous_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_continuous_btn, 2, 2, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Real-time chart
        chart_group = QGroupBox("Real-time Ping Chart")
        chart_layout = QVBoxLayout(chart_group)
        
        self.ping_chart = PingChart()
        chart_layout.addWidget(self.ping_chart)
        
        layout.addWidget(chart_group)
        
        # Live statistics
        live_stats_group = QGroupBox("Live Statistics")
        live_stats_layout = QGridLayout(live_stats_group)
        
        self.live_stats_labels = {}
        live_stats_fields = [
            ("Total Pings", "total"),
            ("Successful", "successful"),
            ("Failed", "failed"),
            ("Success Rate", "success_rate"),
            ("Current Min (ms)", "current_min"),
            ("Current Max (ms)", "current_max"),
            ("Current Avg (ms)", "current_avg"),
            ("Last Response (ms)", "last_response")
        ]
        
        for i, (label, key) in enumerate(live_stats_fields):
            row = i // 4
            col = (i % 4) * 2
            
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            live_stats_layout.addWidget(label_widget, row, col)
            
            value_widget = QLabel("N/A")
            value_widget.setStyleSheet(f"color: {get_accent_color()};")
            self.live_stats_labels[key] = value_widget
            live_stats_layout.addWidget(value_widget, row, col + 1)
        
        layout.addWidget(live_stats_group)
        
        return widget
        
    def create_multi_host_tab(self):
        """Create multi-host ping tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Host list
        hosts_group = QGroupBox("Host List")
        hosts_layout = QVBoxLayout(hosts_group)
        
        # Host input
        host_input_layout = QHBoxLayout()
        
        self.multi_host_input = QLineEdit()
        self.multi_host_input.setPlaceholderText("Enter hostname or IP address")
        host_input_layout.addWidget(self.multi_host_input)
        
        add_host_btn = QPushButton("Add Host")
        add_host_btn.clicked.connect(self.add_ping_host)
        host_input_layout.addWidget(add_host_btn)
        
        hosts_layout.addLayout(host_input_layout)
        
        # Hosts table
        self.hosts_table = QTableWidget()
        self.setup_hosts_table()
        hosts_layout.addWidget(self.hosts_table)
        
        # Multi-ping controls
        multi_controls = QHBoxLayout()
        
        self.ping_all_btn = QPushButton("Ping All Hosts")
        self.ping_all_btn.clicked.connect(self.ping_all_hosts)
        multi_controls.addWidget(self.ping_all_btn)
        
        clear_hosts_btn = QPushButton("Clear All Hosts")
        clear_hosts_btn.clicked.connect(self.clear_all_hosts)
        multi_controls.addWidget(clear_hosts_btn)
        
        multi_controls.addStretch()
        hosts_layout.addLayout(multi_controls)
        
        layout.addWidget(hosts_group)
        
        return widget
        
    def setup_results_table(self):
        """Setup ping results table"""
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Sequence", "Time (ms)", "Status", "Timestamp"
        ])
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        
    def setup_hosts_table(self):
        """Setup multi-host table"""
        self.hosts_table.setColumnCount(5)
        self.hosts_table.setHorizontalHeaderLabels([
            "Host", "Status", "Response Time (ms)", "Last Ping", "Actions"
        ])
        self.hosts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.hosts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hosts_table.setAlternatingRowColors(True)
        
    def start_standard_ping(self):
        """Start standard ping test"""
        host = self.host_input.text().strip()
        if not host:
            return
            
        # Clear previous results
        self.results_table.setRowCount(0)
        self.ping_history.clear()
        
        # Setup progress bar
        count = self.count_spin.value()
        self.ping_progress.setVisible(True)
        self.ping_progress.setRange(0, count)
        self.ping_progress.setValue(0)
        
        # Disable start button
        self.start_ping_btn.setEnabled(False)
        self.stop_ping_btn.setEnabled(True)
        
        # Start ping worker
        self.ping_worker = PingWorker(
            host=host,
            count=count,
            interval=self.interval_spin.value(),
            timeout=self.timeout_spin.value(),
            packet_size=self.packet_size_spin.value()
        )
        self.ping_worker.ping_result.connect(self.on_ping_result)
        self.ping_worker.ping_completed.connect(self.on_ping_completed)
        self.ping_worker.start()
        
    def stop_standard_ping(self):
        """Stop standard ping test"""
        if hasattr(self, 'ping_worker'):
            self.ping_worker.stop()
        self.start_ping_btn.setEnabled(True)
        self.stop_ping_btn.setEnabled(False)
        self.ping_progress.setVisible(False)
        
    def on_ping_result(self, result):
        """Handle individual ping result"""
        self.ping_history.append(result)
        
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(str(result['sequence'])))
        
        if result['success']:
            time_item = QTableWidgetItem(f"{result['time']:.2f}")
            time_item.setBackground(Qt.GlobalColor.darkGreen)
            status_item = QTableWidgetItem("Success")
            status_item.setBackground(Qt.GlobalColor.darkGreen)
        else:
            time_item = QTableWidgetItem("Timeout")
            time_item.setBackground(Qt.GlobalColor.darkRed)
            status_item = QTableWidgetItem(result.get('error', 'Failed'))
            status_item.setBackground(Qt.GlobalColor.darkRed)
        
        self.results_table.setItem(row, 1, time_item)
        self.results_table.setItem(row, 2, status_item)
        self.results_table.setItem(row, 3, QTableWidgetItem(result['timestamp'].strftime("%H:%M:%S")))
        
        # Update progress
        self.ping_progress.setValue(result['sequence'])
        
        # Scroll to bottom
        self.results_table.scrollToBottom()
        
    def on_ping_completed(self, stats):
        """Handle ping completion"""
        self.start_ping_btn.setEnabled(True)
        self.stop_ping_btn.setEnabled(False)
        self.ping_progress.setVisible(False)
        
        # Update statistics labels
        self.stats_labels['sent'].setText(str(stats['packets_sent']))
        self.stats_labels['received'].setText(str(stats['packets_received']))
        self.stats_labels['loss'].setText(f"{stats['packet_loss']:.1f}%")
        
        if stats['min_time'] is not None:
            self.stats_labels['min'].setText(f"{stats['min_time']:.2f}")
            self.stats_labels['max'].setText(f"{stats['max_time']:.2f}")
            self.stats_labels['avg'].setText(f"{stats['avg_time']:.2f}")
            self.stats_labels['median'].setText(f"{stats['median_time']:.2f}")
            
            if stats['std_dev'] is not None:
                self.stats_labels['std'].setText(f"{stats['std_dev']:.2f}")
            else:
                self.stats_labels['std'].setText("N/A")
        else:
            for key in ['min', 'max', 'avg', 'median', 'std']:
                self.stats_labels[key].setText("N/A")
                
    def start_continuous_ping(self):
        """Start continuous ping"""
        host = self.continuous_host_input.text().strip()
        if not host:
            return
            
        # Reset statistics
        self.continuous_stats = {
            'total_pings': 0,
            'successful_pings': 0,
            'failed_pings': 0,
            'response_times': [],
            'min_time': None,
            'max_time': None,
            'avg_time': None
        }
        
        # Update UI
        self.start_continuous_btn.setEnabled(False)
        self.stop_continuous_btn.setEnabled(True)
        
        # Start continuous worker
        self.continuous_worker = ContinuousPingWorker(
            host=host,
            interval=self.continuous_interval_spin.value(),
            timeout=self.continuous_timeout_spin.value()
        )
        self.continuous_worker.ping_result.connect(self.on_continuous_ping_result)
        self.continuous_worker.start()
        
    def stop_continuous_ping(self):
        """Stop continuous ping"""
        if hasattr(self, 'continuous_worker'):
            self.continuous_worker.stop()
        self.start_continuous_btn.setEnabled(True)
        self.stop_continuous_btn.setEnabled(False)
        
    def on_continuous_ping_result(self, result):
        """Handle continuous ping result"""
        self.continuous_stats['total_pings'] += 1
        
        if result['success']:
            self.continuous_stats['successful_pings'] += 1
            response_time = result['time']
            self.continuous_stats['response_times'].append(response_time)
            
            # Update min/max/avg
            if self.continuous_stats['min_time'] is None or response_time < self.continuous_stats['min_time']:
                self.continuous_stats['min_time'] = response_time
            if self.continuous_stats['max_time'] is None or response_time > self.continuous_stats['max_time']:
                self.continuous_stats['max_time'] = response_time
            self.continuous_stats['avg_time'] = statistics.mean(self.continuous_stats['response_times'])
            
            # Update chart
            self.ping_chart.add_ping_result(result['sequence'], response_time, True)
            
            # Update last response
            self.live_stats_labels['last_response'].setText(f"{response_time:.2f}")
            self.live_stats_labels['last_response'].setStyleSheet(f"color: {get_success_color()};")
        else:
            self.continuous_stats['failed_pings'] += 1
            
            # Update chart
            self.ping_chart.add_ping_result(result['sequence'], None, False)
            
            # Update last response
            self.live_stats_labels['last_response'].setText("Timeout")
            self.live_stats_labels['last_response'].setStyleSheet(f"color: {get_error_color()};")
        
        # Update live statistics
        self.update_live_stats()
        
    def update_live_stats(self):
        """Update live statistics display"""
        stats = self.continuous_stats
        
        self.live_stats_labels['total'].setText(str(stats['total_pings']))
        self.live_stats_labels['successful'].setText(str(stats['successful_pings']))
        self.live_stats_labels['failed'].setText(str(stats['failed_pings']))
        
        if stats['total_pings'] > 0:
            success_rate = (stats['successful_pings'] / stats['total_pings']) * 100
            self.live_stats_labels['success_rate'].setText(f"{success_rate:.1f}%")
        
        if stats['min_time'] is not None:
            self.live_stats_labels['current_min'].setText(f"{stats['min_time']:.2f}")
            self.live_stats_labels['current_max'].setText(f"{stats['max_time']:.2f}")
            self.live_stats_labels['current_avg'].setText(f"{stats['avg_time']:.2f}")
            
    def add_ping_host(self):
        """Add host to multi-ping list"""
        host = self.multi_host_input.text().strip()
        if not host:
            return
            
        # Check if host already exists
        for row in range(self.hosts_table.rowCount()):
            if self.hosts_table.item(row, 0).text() == host:
                return  # Host already exists
        
        # Add to table
        row = self.hosts_table.rowCount()
        self.hosts_table.insertRow(row)
        
        self.hosts_table.setItem(row, 0, QTableWidgetItem(host))
        self.hosts_table.setItem(row, 1, QTableWidgetItem("Not tested"))
        self.hosts_table.setItem(row, 2, QTableWidgetItem("N/A"))
        self.hosts_table.setItem(row, 3, QTableWidgetItem("N/A"))
        
        # Add remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_ping_host(row))
        self.hosts_table.setCellWidget(row, 4, remove_btn)
        
        self.multi_host_input.clear()
        
    def remove_ping_host(self, row):
        """Remove host from multi-ping list"""
        self.hosts_table.removeRow(row)
        
    def clear_all_hosts(self):
        """Clear all hosts from multi-ping list"""
        self.hosts_table.setRowCount(0)
        
    def ping_all_hosts(self):
        """Ping all hosts in the list"""
        if self.hosts_table.rowCount() == 0:
            return
            
        self.ping_all_btn.setEnabled(False)
        
        # Ping each host
        for row in range(self.hosts_table.rowCount()):
            host = self.hosts_table.item(row, 0).text()
            
            try:
                response_time = ping3.ping(host, timeout=3)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if response_time is not None:
                    response_time_ms = response_time * 1000
                    
                    status_item = QTableWidgetItem("Online")
                    status_item.setBackground(Qt.GlobalColor.darkGreen)
                    self.hosts_table.setItem(row, 1, status_item)
                    
                    time_item = QTableWidgetItem(f"{response_time_ms:.2f}")
                    self.hosts_table.setItem(row, 2, time_item)
                else:
                    status_item = QTableWidgetItem("Offline")
                    status_item.setBackground(Qt.GlobalColor.darkRed)
                    self.hosts_table.setItem(row, 1, status_item)
                    
                    self.hosts_table.setItem(row, 2, QTableWidgetItem("Timeout"))
                
                self.hosts_table.setItem(row, 3, QTableWidgetItem(timestamp))
                
            except Exception as e:
                status_item = QTableWidgetItem("Error")
                status_item.setBackground(Qt.GlobalColor.darkRed)
                self.hosts_table.setItem(row, 1, status_item)
                
                self.hosts_table.setItem(row, 2, QTableWidgetItem(str(e)))
                self.hosts_table.setItem(row, 3, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        
        self.ping_all_btn.setEnabled(True)
        
    def refresh(self):
        """Refresh ping tool data"""
        # Nothing specific to refresh for ping tool
        pass
