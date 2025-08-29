"""
Speed Test Widget
Network speed testing with multiple servers and detailed analytics
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QGroupBox, QPushButton, QProgressBar,
                            QComboBox, QTableWidget, QTableWidgetItem, QTextEdit,
                            QSpinBox, QCheckBox, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette
import speedtest
import time
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.style as mplstyle

from ..utils.theme import get_accent_color, get_success_color, get_warning_color, get_error_color


class SpeedTestWorker(QThread):
    """Worker thread for speed testing"""
    progress_updated = pyqtSignal(str, int)
    test_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, test_type='full', server_id=None):
        super().__init__()
        self.test_type = test_type
        self.server_id = server_id
        
    def run(self):
        """Run speed test"""
        try:
            self.progress_updated.emit("Initializing speed test...", 0)
            st = speedtest.Speedtest()
            
            self.progress_updated.emit("Getting server list...", 10)
            st.get_servers()
            
            if self.server_id:
                st.servers = [st.servers[self.server_id]]
            
            self.progress_updated.emit("Selecting best server...", 20)
            st.get_best_server()
            
            server_info = {
                'name': st.best['name'],
                'country': st.best['country'],
                'sponsor': st.best['sponsor'],
                'distance': st.best['d'],
                'latency': st.best['latency']
            }
            
            results = {'server': server_info}
            
            if self.test_type in ['full', 'download']:
                self.progress_updated.emit("Testing download speed...", 30)
                download_speed = st.download()
                results['download'] = download_speed / 1_000_000  # Convert to Mbps
                self.progress_updated.emit("Download test completed", 60)
            
            if self.test_type in ['full', 'upload']:
                self.progress_updated.emit("Testing upload speed...", 70)
                upload_speed = st.upload()
                results['upload'] = upload_speed / 1_000_000  # Convert to Mbps
                self.progress_updated.emit("Upload test completed", 90)
            
            self.progress_updated.emit("Finalizing results...", 95)
            
            # Ping test
            results['ping'] = st.results.ping
            results['timestamp'] = datetime.now()
            
            self.progress_updated.emit("Speed test completed!", 100)
            self.test_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class LatencyTestWorker(QThread):
    """Worker thread for latency testing"""
    latency_result = pyqtSignal(dict)
    
    def __init__(self, hosts):
        super().__init__()
        self.hosts = hosts
        
    def run(self):
        """Run latency test"""
        results = {}
        
        for host in self.hosts:
            try:
                import ping3
                # Test multiple pings
                ping_times = []
                for _ in range(5):
                    ping_time = ping3.ping(host, timeout=3)
                    if ping_time is not None:
                        ping_times.append(ping_time * 1000)  # Convert to ms
                    time.sleep(0.2)
                
                if ping_times:
                    results[host] = {
                        'min': min(ping_times),
                        'max': max(ping_times),
                        'avg': sum(ping_times) / len(ping_times),
                        'loss': (5 - len(ping_times)) / 5 * 100
                    }
                else:
                    results[host] = {
                        'min': None,
                        'max': None,
                        'avg': None,
                        'loss': 100
                    }
                    
            except Exception as e:
                results[host] = {
                    'error': str(e),
                    'min': None,
                    'max': None,
                    'avg': None,
                    'loss': 100
                }
        
        self.latency_result.emit(results)


class SpeedChart(FigureCanvas):
    """Chart for speed test history"""
    
    def __init__(self, parent=None):
        mplstyle.use('dark_background')
        
        self.figure = Figure(figsize=(10, 4), facecolor='#353535')
        super().__init__(self.figure)
        self.setParent(parent)
        
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor('#2b2b2b')
        self.axes.set_title('Speed Test History', color='white', fontsize=12)
        self.axes.set_xlabel('Test Number', color='white')
        self.axes.set_ylabel('Speed (Mbps)', color='white')
        
        # Configure axes colors
        self.axes.tick_params(colors='white')
        for spine in self.axes.spines.values():
            spine.set_color('white')
        
        self.figure.tight_layout()
        
        # Data storage
        self.test_numbers = []
        self.download_speeds = []
        self.upload_speeds = []
        
    def add_test_result(self, download, upload):
        """Add new test result to chart"""
        test_num = len(self.test_numbers) + 1
        self.test_numbers.append(test_num)
        self.download_speeds.append(download)
        self.upload_speeds.append(upload)
        
        # Keep only last 20 tests
        if len(self.test_numbers) > 20:
            self.test_numbers = self.test_numbers[-20:]
            self.download_speeds = self.download_speeds[-20:]
            self.upload_speeds = self.upload_speeds[-20:]
        
        self.update_chart()
        
    def update_chart(self):
        """Update the chart"""
        self.axes.clear()
        self.axes.set_facecolor('#2b2b2b')
        self.axes.set_title('Speed Test History', color='white', fontsize=12)
        self.axes.set_xlabel('Test Number', color='white')
        self.axes.set_ylabel('Speed (Mbps)', color='white')
        
        if self.download_speeds:
            self.axes.plot(self.test_numbers, self.download_speeds, 
                          label='Download', color='#4ecdc4', linewidth=2, marker='o')
        if self.upload_speeds:
            self.axes.plot(self.test_numbers, self.upload_speeds, 
                          label='Upload', color='#ff6b6b', linewidth=2, marker='s')
        
        self.axes.legend()
        self.axes.grid(True, alpha=0.3)
        self.axes.tick_params(colors='white')
        
        for spine in self.axes.spines.values():
            spine.set_color('white')
        
        self.draw()


class SpeedTestWidget(QWidget):
    """Speed test widget with comprehensive network speed analysis"""
    
    def __init__(self):
        super().__init__()
        self.test_history = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Speed Test tab
        speed_tab = self.create_speed_test_tab()
        tab_widget.addTab(speed_tab, "Speed Test")
        
        # Latency Test tab
        latency_tab = self.create_latency_test_tab()
        tab_widget.addTab(latency_tab, "Latency Test")
        
        # History tab
        history_tab = self.create_history_tab()
        tab_widget.addTab(history_tab, "Test History")
        
    def create_speed_test_tab(self):
        """Create speed test tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Test controls
        controls_group = QGroupBox("Speed Test Controls")
        controls_layout = QGridLayout(controls_group)
        
        # Test type selection
        controls_layout.addWidget(QLabel("Test Type:"), 0, 0)
        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems(["Full Test (Download + Upload)", "Download Only", "Upload Only"])
        controls_layout.addWidget(self.test_type_combo, 0, 1)
        
        # Server selection
        controls_layout.addWidget(QLabel("Server:"), 1, 0)
        self.server_combo = QComboBox()
        self.server_combo.addItem("Auto (Best Server)")
        controls_layout.addWidget(self.server_combo, 1, 1)
        
        # Refresh servers button
        refresh_servers_btn = QPushButton("Refresh Servers")
        refresh_servers_btn.clicked.connect(self.refresh_servers)
        controls_layout.addWidget(refresh_servers_btn, 1, 2)
        
        # Start test button
        self.start_test_btn = QPushButton("Start Speed Test")
        self.start_test_btn.clicked.connect(self.start_speed_test)
        controls_layout.addWidget(self.start_test_btn, 2, 0, 1, 3)
        
        layout.addWidget(controls_group)
        
        # Progress section
        progress_group = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_label = QLabel("Ready to start test")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox("Test Results")
        results_layout = QGridLayout(results_group)
        
        # Current test results
        self.result_labels = {}
        result_fields = [
            ("Server", "server"),
            ("Download Speed", "download"),
            ("Upload Speed", "upload"),
            ("Ping", "ping"),
            ("Test Date", "timestamp")
        ]
        
        for i, (label, key) in enumerate(result_fields):
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            results_layout.addWidget(label_widget, i, 0)
            
            value_widget = QLabel("N/A")
            value_widget.setStyleSheet(f"color: {get_accent_color()};")
            self.result_labels[key] = value_widget
            results_layout.addWidget(value_widget, i, 1)
        
        layout.addWidget(results_group)
        
        # Chart section
        chart_group = QGroupBox("Speed History Chart")
        chart_layout = QVBoxLayout(chart_group)
        
        self.speed_chart = SpeedChart()
        chart_layout.addWidget(self.speed_chart)
        
        layout.addWidget(chart_group)
        
        return widget
        
    def create_latency_test_tab(self):
        """Create latency test tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Latency test controls
        controls_group = QGroupBox("Latency Test Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Host input
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Test Hosts:"))
        
        self.host_input = QTextEdit()
        self.host_input.setMaximumHeight(80)
        self.host_input.setPlainText("8.8.8.8\n1.1.1.1\ngoogle.com\nfacebook.com")
        host_layout.addWidget(self.host_input)
        
        controls_layout.addLayout(host_layout)
        
        # Start latency test
        self.latency_test_btn = QPushButton("Start Latency Test")
        self.latency_test_btn.clicked.connect(self.start_latency_test)
        controls_layout.addWidget(self.latency_test_btn)
        
        layout.addWidget(controls_group)
        
        # Latency results
        latency_results_group = QGroupBox("Latency Test Results")
        latency_results_layout = QVBoxLayout(latency_results_group)
        
        self.latency_table = QTableWidget()
        self.setup_latency_table()
        latency_results_layout.addWidget(self.latency_table)
        
        layout.addWidget(latency_results_group)
        
        return widget
        
    def create_history_tab(self):
        """Create test history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # History controls
        controls_layout = QHBoxLayout()
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self.clear_history)
        controls_layout.addWidget(clear_history_btn)
        
        export_history_btn = QPushButton("Export History")
        export_history_btn.clicked.connect(self.export_history)
        controls_layout.addWidget(export_history_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # History table
        history_group = QGroupBox("Speed Test History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.setup_history_table()
        history_layout.addWidget(self.history_table)
        
        layout.addWidget(history_group)
        
        return widget
        
    def setup_latency_table(self):
        """Setup latency results table"""
        self.latency_table.setColumnCount(5)
        self.latency_table.setHorizontalHeaderLabels([
            "Host", "Min (ms)", "Max (ms)", "Avg (ms)", "Loss (%)"
        ])
        self.latency_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.latency_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.latency_table.setAlternatingRowColors(True)
        
    def setup_history_table(self):
        """Setup history table"""
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date/Time", "Server", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)", "Location"
        ])
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        
    def refresh_servers(self):
        """Refresh server list"""
        try:
            self.progress_label.setText("Loading server list...")
            st = speedtest.Speedtest()
            st.get_servers()
            
            self.server_combo.clear()
            self.server_combo.addItem("Auto (Best Server)")
            
            # Add top servers
            for server_id, server_info in list(st.servers.items())[:10]:
                server_name = f"{server_info[0]['name']} - {server_info[0]['sponsor']} ({server_info[0]['country']})"
                self.server_combo.addItem(server_name, server_id)
                
            self.progress_label.setText("Server list updated")
            
        except Exception as e:
            self.progress_label.setText(f"Error loading servers: {str(e)}")
            
    def start_speed_test(self):
        """Start speed test"""
        # Determine test type
        test_type_map = {
            0: 'full',
            1: 'download', 
            2: 'upload'
        }
        test_type = test_type_map[self.test_type_combo.currentIndex()]
        
        # Get server ID
        server_id = None
        if self.server_combo.currentIndex() > 0:
            server_id = self.server_combo.currentData()
            
        # Setup UI for testing
        self.start_test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker thread
        self.speed_worker = SpeedTestWorker(test_type, server_id)
        self.speed_worker.progress_updated.connect(self.on_progress_updated)
        self.speed_worker.test_completed.connect(self.on_test_completed)
        self.speed_worker.error_occurred.connect(self.on_test_error)
        self.speed_worker.start()
        
    def on_progress_updated(self, message, progress):
        """Handle progress update"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
        
    def on_test_completed(self, results):
        """Handle test completion"""
        self.progress_bar.setVisible(False)
        self.start_test_btn.setEnabled(True)
        self.progress_label.setText("Test completed successfully!")
        
        # Update result labels
        server_info = results['server']
        server_text = f"{server_info['name']} ({server_info['country']}) - {server_info['distance']:.1f} km"
        self.result_labels['server'].setText(server_text)
        
        if 'download' in results:
            self.result_labels['download'].setText(f"{results['download']:.2f} Mbps")
        else:
            self.result_labels['download'].setText("N/A")
            
        if 'upload' in results:
            self.result_labels['upload'].setText(f"{results['upload']:.2f} Mbps")
        else:
            self.result_labels['upload'].setText("N/A")
            
        self.result_labels['ping'].setText(f"{results['ping']:.2f} ms")
        self.result_labels['timestamp'].setText(results['timestamp'].strftime("%Y-%m-%d %H:%M:%S"))
        
        # Add to history
        self.test_history.append(results)
        self.update_history_table()
        
        # Update chart
        download = results.get('download', 0)
        upload = results.get('upload', 0)
        self.speed_chart.add_test_result(download, upload)
        
    def on_test_error(self, error):
        """Handle test error"""
        self.progress_bar.setVisible(False)
        self.start_test_btn.setEnabled(True)
        self.progress_label.setText(f"Test failed: {error}")
        
    def start_latency_test(self):
        """Start latency test"""
        hosts = [host.strip() for host in self.host_input.toPlainText().split('\n') if host.strip()]
        if not hosts:
            return
            
        self.latency_test_btn.setEnabled(False)
        
        # Start latency worker
        self.latency_worker = LatencyTestWorker(hosts)
        self.latency_worker.latency_result.connect(self.on_latency_completed)
        self.latency_worker.start()
        
    def on_latency_completed(self, results):
        """Handle latency test completion"""
        self.latency_test_btn.setEnabled(True)
        
        # Update latency table
        self.latency_table.setRowCount(len(results))
        
        for row, (host, result) in enumerate(results.items()):
            self.latency_table.setItem(row, 0, QTableWidgetItem(host))
            
            if 'error' not in result and result['avg'] is not None:
                min_item = QTableWidgetItem(f"{result['min']:.2f}")
                max_item = QTableWidgetItem(f"{result['max']:.2f}")
                avg_item = QTableWidgetItem(f"{result['avg']:.2f}")
                loss_item = QTableWidgetItem(f"{result['loss']:.1f}")
                
                # Color code based on performance
                if result['avg'] < 50:
                    avg_item.setBackground(Qt.GlobalColor.darkGreen)
                elif result['avg'] > 150:
                    avg_item.setBackground(Qt.GlobalColor.darkRed)
                    
                if result['loss'] > 5:
                    loss_item.setBackground(Qt.GlobalColor.darkRed)
                    
                self.latency_table.setItem(row, 1, min_item)
                self.latency_table.setItem(row, 2, max_item)
                self.latency_table.setItem(row, 3, avg_item)
                self.latency_table.setItem(row, 4, loss_item)
            else:
                error_text = result.get('error', 'Timeout')
                for col in range(1, 5):
                    error_item = QTableWidgetItem(error_text)
                    error_item.setBackground(Qt.GlobalColor.darkRed)
                    self.latency_table.setItem(row, col, error_item)
                    
        self.latency_table.resizeColumnsToContents()
        
    def update_history_table(self):
        """Update history table"""
        self.history_table.setRowCount(len(self.test_history))
        
        for row, result in enumerate(reversed(self.test_history)):
            timestamp = result['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            self.history_table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            server_info = result['server']
            server_text = f"{server_info['name']} - {server_info['sponsor']}"
            self.history_table.setItem(row, 1, QTableWidgetItem(server_text))
            
            download = result.get('download', 0)
            self.history_table.setItem(row, 2, QTableWidgetItem(f"{download:.2f}"))
            
            upload = result.get('upload', 0)
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{upload:.2f}"))
            
            ping = result.get('ping', 0)
            self.history_table.setItem(row, 4, QTableWidgetItem(f"{ping:.2f}"))
            
            location = f"{server_info['country']}"
            self.history_table.setItem(row, 5, QTableWidgetItem(location))
            
        self.history_table.resizeColumnsToContents()
        
    def clear_history(self):
        """Clear test history"""
        self.test_history.clear()
        self.history_table.setRowCount(0)
        # Reset chart
        self.speed_chart.test_numbers.clear()
        self.speed_chart.download_speeds.clear()
        self.speed_chart.upload_speeds.clear()
        self.speed_chart.update_chart()
        
    def export_history(self):
        """Export test history"""
        if not self.test_history:
            return
            
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Export History", "speed_test_history.csv", "CSV Files (*.csv)")
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'Server', 'Download (Mbps)', 'Upload (Mbps)', 'Ping (ms)', 'Location'])
                    
                    for result in self.test_history:
                        server_info = result['server']
                        writer.writerow([
                            result['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                            f"{server_info['name']} - {server_info['sponsor']}",
                            result.get('download', 0),
                            result.get('upload', 0),
                            result.get('ping', 0),
                            server_info['country']
                        ])
                        
                self.progress_label.setText(f"History exported to {filename}")
            except Exception as e:
                self.progress_label.setText(f"Export failed: {str(e)}")
        
    def refresh(self):
        """Refresh speed test data"""
        self.refresh_servers()
