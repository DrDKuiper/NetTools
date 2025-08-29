"""
DNS Analyzer Widget
Analyze DNS routes, compare different DNS servers, and test resolution times
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QGroupBox, QLineEdit, QPushButton, QTextEdit,
                            QComboBox, QTableWidget, QTableWidgetItem, QProgressBar,
                            QTabWidget, QSplitter, QCheckBox, QSpinBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
import dns.resolver
import dns.query
import dns.message
import time
import socket
from datetime import datetime
import requests

from ..utils.theme import get_accent_color, get_success_color, get_warning_color, get_error_color


class DNSLookupWorker(QThread):
    """Worker thread for DNS lookups"""
    lookup_completed = pyqtSignal(dict)
    
    def __init__(self, domain, dns_servers, record_types):
        super().__init__()
        self.domain = domain
        self.dns_servers = dns_servers
        self.record_types = record_types
        
    def run(self):
        """Perform DNS lookups"""
        results = {}
        
        for server in self.dns_servers:
            server_results = {}
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [server]
            resolver.timeout = 10
            resolver.lifetime = 10
            
            for record_type in self.record_types:
                try:
                    start_time = time.time()
                    answer = resolver.resolve(self.domain, record_type)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    records = []
                    for record in answer:
                        records.append(str(record))
                    
                    server_results[record_type] = {
                        'success': True,
                        'records': records,
                        'response_time': response_time,
                        'ttl': answer.ttl
                    }
                    
                except Exception as e:
                    server_results[record_type] = {
                        'success': False,
                        'error': str(e),
                        'response_time': None,
                        'ttl': None
                    }
            
            results[server] = server_results
            
        self.lookup_completed.emit(results)


class DNSSpeedTestWorker(QThread):
    """Worker thread for DNS speed testing"""
    speed_test_completed = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, dns_servers, test_domains):
        super().__init__()
        self.dns_servers = dns_servers
        self.test_domains = test_domains
        
    def run(self):
        """Run DNS speed test"""
        results = {}
        total_tests = len(self.dns_servers) * len(self.test_domains)
        completed_tests = 0
        
        for server in self.dns_servers:
            server_times = []
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [server]
            resolver.timeout = 5
            resolver.lifetime = 5
            
            for domain in self.test_domains:
                try:
                    start_time = time.time()
                    resolver.resolve(domain, 'A')
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    server_times.append(response_time)
                    
                except Exception:
                    # Skip failed lookups
                    pass
                
                completed_tests += 1
                progress = int((completed_tests / total_tests) * 100)
                self.progress_updated.emit(progress)
            
            if server_times:
                results[server] = {
                    'min_time': min(server_times),
                    'max_time': max(server_times),
                    'avg_time': sum(server_times) / len(server_times),
                    'success_rate': len(server_times) / len(self.test_domains) * 100
                }
            else:
                results[server] = {
                    'min_time': None,
                    'max_time': None,
                    'avg_time': None,
                    'success_rate': 0
                }
        
        self.speed_test_completed.emit(results)


class DNSAnalyzerWidget(QWidget):
    """DNS analyzer widget with lookup and speed testing capabilities"""
    
    def __init__(self):
        super().__init__()
        self.dns_servers = [
            "8.8.8.8",      # Google
            "8.8.4.4",      # Google
            "1.1.1.1",      # Cloudflare
            "1.0.0.1",      # Cloudflare
            "208.67.222.222", # OpenDNS
            "208.67.220.220", # OpenDNS
            "9.9.9.9",      # Quad9
            "149.112.112.112" # Quad9
        ]
        self.record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # DNS Lookup tab
        lookup_tab = self.create_lookup_tab()
        tab_widget.addTab(lookup_tab, "DNS Lookup")
        
        # Speed Test tab
        speed_tab = self.create_speed_test_tab()
        tab_widget.addTab(speed_tab, "Speed Test")
        
        # DNS Servers tab
        servers_tab = self.create_servers_tab()
        tab_widget.addTab(servers_tab, "DNS Servers")
        
    def create_lookup_tab(self):
        """Create DNS lookup tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Input section
        input_group = QGroupBox("DNS Lookup")
        input_layout = QGridLayout(input_group)
        
        input_layout.addWidget(QLabel("Domain:"), 0, 0)
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("Enter domain name (e.g., google.com)")
        self.domain_input.returnPressed.connect(self.perform_lookup)
        input_layout.addWidget(self.domain_input, 0, 1)
        
        input_layout.addWidget(QLabel("Record Types:"), 1, 0)
        record_layout = QHBoxLayout()
        self.record_checkboxes = {}
        for record_type in self.record_types:
            checkbox = QCheckBox(record_type)
            checkbox.setChecked(record_type in ["A", "AAAA", "MX"])
            self.record_checkboxes[record_type] = checkbox
            record_layout.addWidget(checkbox)
        input_layout.addLayout(record_layout, 1, 1)
        
        self.lookup_button = QPushButton("Perform Lookup")
        self.lookup_button.clicked.connect(self.perform_lookup)
        input_layout.addWidget(self.lookup_button, 2, 0, 1, 2)
        
        layout.addWidget(input_group)
        
        # Progress bar
        self.lookup_progress = QProgressBar()
        self.lookup_progress.setVisible(False)
        layout.addWidget(self.lookup_progress)
        
        # Results section
        results_group = QGroupBox("Lookup Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        return widget
        
    def create_speed_test_tab(self):
        """Create DNS speed test tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Test configuration
        config_group = QGroupBox("Speed Test Configuration")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Test Domains:"), 0, 0)
        self.test_domains_input = QTextEdit()
        self.test_domains_input.setMaximumHeight(100)
        self.test_domains_input.setPlainText("google.com\nfacebook.com\namazon.com\nmicrosoft.com\napple.com")
        config_layout.addWidget(self.test_domains_input, 0, 1)
        
        self.speed_test_button = QPushButton("Run Speed Test")
        self.speed_test_button.clicked.connect(self.run_speed_test)
        config_layout.addWidget(self.speed_test_button, 1, 0, 1, 2)
        
        layout.addWidget(config_group)
        
        # Progress bar
        self.speed_progress = QProgressBar()
        self.speed_progress.setVisible(False)
        layout.addWidget(self.speed_progress)
        
        # Speed test results
        speed_results_group = QGroupBox("Speed Test Results")
        speed_results_layout = QVBoxLayout(speed_results_group)
        
        self.speed_results_table = QTableWidget()
        self.setup_speed_results_table()
        speed_results_layout.addWidget(self.speed_results_table)
        
        layout.addWidget(speed_results_group)
        
        return widget
        
    def create_servers_tab(self):
        """Create DNS servers management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current DNS servers
        current_group = QGroupBox("Current System DNS")
        current_layout = QVBoxLayout(current_group)
        
        self.current_dns_label = QLabel("Loading...")
        current_layout.addWidget(self.current_dns_label)
        
        refresh_current_button = QPushButton("Refresh Current DNS")
        refresh_current_button.clicked.connect(self.refresh_current_dns)
        current_layout.addWidget(refresh_current_button)
        
        layout.addWidget(current_group)
        
        # Test servers list
        servers_group = QGroupBox("DNS Servers for Testing")
        servers_layout = QVBoxLayout(servers_group)
        
        self.servers_table = QTableWidget()
        self.setup_servers_table()
        servers_layout.addWidget(self.servers_table)
        
        # Add/Remove servers
        servers_controls = QHBoxLayout()
        
        self.new_server_input = QLineEdit()
        self.new_server_input.setPlaceholderText("Enter DNS server IP")
        servers_controls.addWidget(self.new_server_input)
        
        add_server_button = QPushButton("Add Server")
        add_server_button.clicked.connect(self.add_dns_server)
        servers_controls.addWidget(add_server_button)
        
        remove_server_button = QPushButton("Remove Selected")
        remove_server_button.clicked.connect(self.remove_dns_server)
        servers_controls.addWidget(remove_server_button)
        
        servers_layout.addLayout(servers_controls)
        layout.addWidget(servers_group)
        
        # Initialize data
        self.refresh_current_dns()
        self.populate_servers_table()
        
        return widget
        
    def setup_results_table(self):
        """Setup DNS lookup results table"""
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "DNS Server", "Record Type", "Response Time (ms)", "TTL", "Records"
        ])
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        
    def setup_speed_results_table(self):
        """Setup speed test results table"""
        self.speed_results_table.setColumnCount(5)
        self.speed_results_table.setHorizontalHeaderLabels([
            "DNS Server", "Min Time (ms)", "Max Time (ms)", "Avg Time (ms)", "Success Rate (%)"
        ])
        self.speed_results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.speed_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.speed_results_table.setAlternatingRowColors(True)
        
    def setup_servers_table(self):
        """Setup DNS servers table"""
        self.servers_table.setColumnCount(3)
        self.servers_table.setHorizontalHeaderLabels([
            "DNS Server", "Provider", "Status"
        ])
        self.servers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.servers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.servers_table.setAlternatingRowColors(True)
        
    def perform_lookup(self):
        """Perform DNS lookup"""
        domain = self.domain_input.text().strip()
        if not domain:
            return
            
        # Get selected record types
        selected_types = []
        for record_type, checkbox in self.record_checkboxes.items():
            if checkbox.isChecked():
                selected_types.append(record_type)
                
        if not selected_types:
            return
            
        # Show progress
        self.lookup_progress.setVisible(True)
        self.lookup_progress.setRange(0, 0)  # Indeterminate
        self.lookup_button.setEnabled(False)
        
        # Start lookup worker
        self.lookup_worker = DNSLookupWorker(domain, self.dns_servers, selected_types)
        self.lookup_worker.lookup_completed.connect(self.on_lookup_completed)
        self.lookup_worker.start()
        
    def on_lookup_completed(self, results):
        """Handle lookup completion"""
        self.lookup_progress.setVisible(False)
        self.lookup_button.setEnabled(True)
        
        # Clear previous results
        self.results_table.setRowCount(0)
        
        row = 0
        for server, server_results in results.items():
            for record_type, result in server_results.items():
                self.results_table.insertRow(row)
                
                # DNS Server
                self.results_table.setItem(row, 0, QTableWidgetItem(server))
                
                # Record Type
                self.results_table.setItem(row, 1, QTableWidgetItem(record_type))
                
                if result['success']:
                    # Response Time
                    response_time = f"{result['response_time']:.2f}" if result['response_time'] else "N/A"
                    time_item = QTableWidgetItem(response_time)
                    if result['response_time'] and result['response_time'] < 50:
                        time_item.setBackground(Qt.GlobalColor.darkGreen)
                    elif result['response_time'] and result['response_time'] > 200:
                        time_item.setBackground(Qt.GlobalColor.darkRed)
                    self.results_table.setItem(row, 2, time_item)
                    
                    # TTL
                    ttl = str(result['ttl']) if result['ttl'] else "N/A"
                    self.results_table.setItem(row, 3, QTableWidgetItem(ttl))
                    
                    # Records
                    records_text = "\n".join(result['records'][:3])  # Show first 3 records
                    if len(result['records']) > 3:
                        records_text += f"\n... and {len(result['records']) - 3} more"
                    self.results_table.setItem(row, 4, QTableWidgetItem(records_text))
                else:
                    # Error case
                    error_item = QTableWidgetItem("Error")
                    error_item.setBackground(Qt.GlobalColor.darkRed)
                    self.results_table.setItem(row, 2, error_item)
                    
                    self.results_table.setItem(row, 3, QTableWidgetItem("N/A"))
                    self.results_table.setItem(row, 4, QTableWidgetItem(result['error']))
                
                row += 1
                
        self.results_table.resizeColumnsToContents()
        
    def run_speed_test(self):
        """Run DNS speed test"""
        test_domains = [domain.strip() for domain in self.test_domains_input.toPlainText().split('\n') if domain.strip()]
        if not test_domains:
            return
            
        # Show progress
        self.speed_progress.setVisible(True)
        self.speed_progress.setRange(0, 100)
        self.speed_progress.setValue(0)
        self.speed_test_button.setEnabled(False)
        
        # Start speed test worker
        self.speed_worker = DNSSpeedTestWorker(self.dns_servers, test_domains)
        self.speed_worker.speed_test_completed.connect(self.on_speed_test_completed)
        self.speed_worker.progress_updated.connect(self.speed_progress.setValue)
        self.speed_worker.start()
        
    def on_speed_test_completed(self, results):
        """Handle speed test completion"""
        self.speed_progress.setVisible(False)
        self.speed_test_button.setEnabled(True)
        
        # Clear previous results
        self.speed_results_table.setRowCount(len(results))
        
        row = 0
        for server, result in results.items():
            self.speed_results_table.setItem(row, 0, QTableWidgetItem(server))
            
            if result['avg_time'] is not None:
                # Min Time
                min_time_item = QTableWidgetItem(f"{result['min_time']:.2f}")
                self.speed_results_table.setItem(row, 1, min_time_item)
                
                # Max Time
                max_time_item = QTableWidgetItem(f"{result['max_time']:.2f}")
                self.speed_results_table.setItem(row, 2, max_time_item)
                
                # Avg Time
                avg_time_item = QTableWidgetItem(f"{result['avg_time']:.2f}")
                if result['avg_time'] < 50:
                    avg_time_item.setBackground(Qt.GlobalColor.darkGreen)
                elif result['avg_time'] > 200:
                    avg_time_item.setBackground(Qt.GlobalColor.darkRed)
                self.speed_results_table.setItem(row, 3, avg_time_item)
                
                # Success Rate
                success_item = QTableWidgetItem(f"{result['success_rate']:.1f}")
                if result['success_rate'] >= 90:
                    success_item.setBackground(Qt.GlobalColor.darkGreen)
                elif result['success_rate'] < 70:
                    success_item.setBackground(Qt.GlobalColor.darkRed)
                self.speed_results_table.setItem(row, 4, success_item)
            else:
                # Failed server
                for col in range(1, 5):
                    failed_item = QTableWidgetItem("Failed")
                    failed_item.setBackground(Qt.GlobalColor.darkRed)
                    self.speed_results_table.setItem(row, col, failed_item)
            
            row += 1
            
        self.speed_results_table.resizeColumnsToContents()
        
    def refresh_current_dns(self):
        """Refresh current system DNS settings"""
        try:
            # Get system DNS servers
            import dns.resolver
            resolver = dns.resolver.Resolver()
            dns_servers = resolver.nameservers
            
            dns_text = "Current DNS Servers:\n" + "\n".join(dns_servers)
            self.current_dns_label.setText(dns_text)
        except Exception as e:
            self.current_dns_label.setText(f"Error getting DNS servers: {str(e)}")
            
    def populate_servers_table(self):
        """Populate DNS servers table"""
        server_info = {
            "8.8.8.8": "Google",
            "8.8.4.4": "Google",
            "1.1.1.1": "Cloudflare",
            "1.0.0.1": "Cloudflare",
            "208.67.222.222": "OpenDNS",
            "208.67.220.220": "OpenDNS",
            "9.9.9.9": "Quad9",
            "149.112.112.112": "Quad9"
        }
        
        self.servers_table.setRowCount(len(self.dns_servers))
        
        for row, server in enumerate(self.dns_servers):
            self.servers_table.setItem(row, 0, QTableWidgetItem(server))
            provider = server_info.get(server, "Unknown")
            self.servers_table.setItem(row, 1, QTableWidgetItem(provider))
            self.servers_table.setItem(row, 2, QTableWidgetItem("Active"))
            
        self.servers_table.resizeColumnsToContents()
        
    def add_dns_server(self):
        """Add a new DNS server"""
        server = self.new_server_input.text().strip()
        if server and server not in self.dns_servers:
            self.dns_servers.append(server)
            self.populate_servers_table()
            self.new_server_input.clear()
            
    def remove_dns_server(self):
        """Remove selected DNS server"""
        current_row = self.servers_table.currentRow()
        if current_row >= 0 and current_row < len(self.dns_servers):
            del self.dns_servers[current_row]
            self.populate_servers_table()
            
    def refresh(self):
        """Refresh DNS analyzer data"""
        self.refresh_current_dns()
        self.populate_servers_table()
