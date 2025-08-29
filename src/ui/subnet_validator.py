"""
Subnet Validator Widget
Validate subnets, calculate network information, and detect conflicts
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QGroupBox, QLineEdit, QPushButton, QTextEdit,
                            QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
                            QTabWidget, QSplitter, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
import ipaddress
import psutil
import socket
from datetime import datetime

from ..utils.theme import get_accent_color, get_success_color, get_warning_color, get_error_color


class SubnetValidatorWidget(QWidget):
    """Subnet validator widget for network analysis and validation"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_current_networks()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Subnet Calculator tab
        calculator_tab = self.create_calculator_tab()
        tab_widget.addTab(calculator_tab, "Subnet Calculator")
        
        # Network Scanner tab
        scanner_tab = self.create_scanner_tab()
        tab_widget.addTab(scanner_tab, "Network Scanner")
        
        # Conflict Detection tab
        conflict_tab = self.create_conflict_tab()
        tab_widget.addTab(conflict_tab, "Conflict Detection")
        
    def create_calculator_tab(self):
        """Create subnet calculator tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Input section
        input_group = QGroupBox("Subnet Input")
        input_layout = QGridLayout(input_group)
        
        # Network input
        input_layout.addWidget(QLabel("Network Address:"), 0, 0)
        self.network_input = QLineEdit()
        self.network_input.setPlaceholderText("e.g., 192.168.1.0/24 or 192.168.1.0 255.255.255.0")
        self.network_input.textChanged.connect(self.calculate_subnet)
        input_layout.addWidget(self.network_input, 0, 1)
        
        # CIDR/Netmask selection
        input_layout.addWidget(QLabel("Input Type:"), 1, 0)
        input_type_layout = QHBoxLayout()
        
        self.cidr_radio = QCheckBox("CIDR Notation")
        self.cidr_radio.setChecked(True)
        self.cidr_radio.toggled.connect(self.on_input_type_changed)
        input_type_layout.addWidget(self.cidr_radio)
        
        self.netmask_radio = QCheckBox("Netmask")
        self.netmask_radio.toggled.connect(self.on_input_type_changed)
        input_type_layout.addWidget(self.netmask_radio)
        
        input_type_layout.addStretch()
        input_layout.addLayout(input_type_layout, 1, 1)
        
        # Calculate button
        self.calculate_button = QPushButton("Calculate Subnet")
        self.calculate_button.clicked.connect(self.calculate_subnet)
        input_layout.addWidget(self.calculate_button, 2, 0, 1, 2)
        
        layout.addWidget(input_group)
        
        # Results section
        results_group = QGroupBox("Subnet Information")
        results_layout = QGridLayout(results_group)
        
        # Create result labels
        self.result_labels = {}
        result_fields = [
            ("Network Address", "network_address"),
            ("Netmask", "netmask"),
            ("Wildcard Mask", "wildcard"),
            ("Broadcast Address", "broadcast"),
            ("First Host", "first_host"),
            ("Last Host", "last_host"),
            ("Total Hosts", "total_hosts"),
            ("Usable Hosts", "usable_hosts"),
            ("Network Class", "network_class"),
            ("Is Private", "is_private"),
            ("Is Multicast", "is_multicast"),
            ("Is Reserved", "is_reserved")
        ]
        
        for i, (label, key) in enumerate(result_fields):
            row = i // 2
            col = (i % 2) * 2
            
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            results_layout.addWidget(label_widget, row, col)
            
            value_widget = QLabel("N/A")
            value_widget.setStyleSheet(f"color: {get_accent_color()};")
            value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.result_labels[key] = value_widget
            results_layout.addWidget(value_widget, row, col + 1)
        
        layout.addWidget(results_group)
        
        # Subnetting section
        subnetting_group = QGroupBox("Subnet Division")
        subnetting_layout = QVBoxLayout(subnetting_group)
        
        subnet_controls = QHBoxLayout()
        subnet_controls.addWidget(QLabel("Divide into:"))
        
        self.subnet_count_spin = QSpinBox()
        self.subnet_count_spin.setRange(2, 1024)
        self.subnet_count_spin.setValue(4)
        subnet_controls.addWidget(self.subnet_count_spin)
        
        subnet_controls.addWidget(QLabel("subnets"))
        
        divide_button = QPushButton("Divide Network")
        divide_button.clicked.connect(self.divide_network)
        subnet_controls.addWidget(divide_button)
        
        subnet_controls.addStretch()
        subnetting_layout.addLayout(subnet_controls)
        
        # Subnets table
        self.subnets_table = QTableWidget()
        self.setup_subnets_table()
        subnetting_layout.addWidget(self.subnets_table)
        
        layout.addWidget(subnetting_group)
        
        return widget
        
    def create_scanner_tab(self):
        """Create network scanner tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current networks section
        current_group = QGroupBox("Current Network Interfaces")
        current_layout = QVBoxLayout(current_group)
        
        refresh_button = QPushButton("Refresh Network Interfaces")
        refresh_button.clicked.connect(self.load_current_networks)
        current_layout.addWidget(refresh_button)
        
        self.networks_table = QTableWidget()
        self.setup_networks_table()
        current_layout.addWidget(self.networks_table)
        
        layout.addWidget(current_group)
        
        # Network analysis
        analysis_group = QGroupBox("Network Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setMaximumHeight(200)
        self.analysis_text.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_text)
        
        analyze_button = QPushButton("Analyze Networks")
        analyze_button.clicked.connect(self.analyze_networks)
        analysis_layout.addWidget(analyze_button)
        
        layout.addWidget(analysis_group)
        
        return widget
        
    def create_conflict_tab(self):
        """Create conflict detection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Network list for conflict checking
        networks_group = QGroupBox("Networks to Check")
        networks_layout = QVBoxLayout(networks_group)
        
        networks_input_layout = QHBoxLayout()
        
        self.conflict_network_input = QLineEdit()
        self.conflict_network_input.setPlaceholderText("Enter network (e.g., 192.168.1.0/24)")
        networks_input_layout.addWidget(self.conflict_network_input)
        
        add_network_button = QPushButton("Add Network")
        add_network_button.clicked.connect(self.add_conflict_network)
        networks_input_layout.addWidget(add_network_button)
        
        networks_layout.addLayout(networks_input_layout)
        
        self.conflict_networks_table = QTableWidget()
        self.setup_conflict_networks_table()
        networks_layout.addWidget(self.conflict_networks_table)
        
        conflict_controls = QHBoxLayout()
        
        check_conflicts_button = QPushButton("Check for Conflicts")
        check_conflicts_button.clicked.connect(self.check_conflicts)
        conflict_controls.addWidget(check_conflicts_button)
        
        clear_networks_button = QPushButton("Clear All")
        clear_networks_button.clicked.connect(self.clear_conflict_networks)
        conflict_controls.addWidget(clear_networks_button)
        
        conflict_controls.addStretch()
        networks_layout.addLayout(conflict_controls)
        
        layout.addWidget(networks_group)
        
        # Conflict results
        results_group = QGroupBox("Conflict Detection Results")
        results_layout = QVBoxLayout(results_group)
        
        self.conflict_results = QTextEdit()
        self.conflict_results.setReadOnly(True)
        results_layout.addWidget(self.conflict_results)
        
        layout.addWidget(results_group)
        
        return widget
        
    def setup_subnets_table(self):
        """Setup subnets table"""
        self.subnets_table.setColumnCount(6)
        self.subnets_table.setHorizontalHeaderLabels([
            "Subnet #", "Network", "Netmask", "Broadcast", "First Host", "Last Host"
        ])
        self.subnets_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.subnets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.subnets_table.setAlternatingRowColors(True)
        
    def setup_networks_table(self):
        """Setup current networks table"""
        self.networks_table.setColumnCount(5)
        self.networks_table.setHorizontalHeaderLabels([
            "Interface", "IP Address", "Netmask", "Network", "Status"
        ])
        self.networks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.networks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.networks_table.setAlternatingRowColors(True)
        
    def setup_conflict_networks_table(self):
        """Setup conflict networks table"""
        self.conflict_networks_table.setColumnCount(4)
        self.conflict_networks_table.setHorizontalHeaderLabels([
            "Network", "Netmask", "Hosts", "Actions"
        ])
        self.conflict_networks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.conflict_networks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.conflict_networks_table.setAlternatingRowColors(True)
        
    def calculate_subnet(self):
        """Calculate subnet information"""
        network_text = self.network_input.text().strip()
        if not network_text:
            return
            
        try:
            # Parse network input
            if self.cidr_radio.isChecked():
                # CIDR notation
                if '/' not in network_text:
                    network_text += '/24'  # Default to /24
                network = ipaddress.IPv4Network(network_text, strict=False)
            else:
                # Netmask notation
                parts = network_text.split()
                if len(parts) == 2:
                    ip, netmask = parts
                    # Convert netmask to CIDR
                    netmask_obj = ipaddress.IPv4Address(netmask)
                    prefix_len = sum(bin(int(x)).count('1') for x in str(netmask_obj).split('.'))
                    network = ipaddress.IPv4Network(f"{ip}/{prefix_len}", strict=False)
                else:
                    raise ValueError("Invalid netmask format")
            
            # Update result labels
            self.result_labels['network_address'].setText(str(network.network_address))
            self.result_labels['netmask'].setText(str(network.netmask))
            self.result_labels['wildcard'].setText(str(network.hostmask))
            self.result_labels['broadcast'].setText(str(network.broadcast_address))
            
            hosts = list(network.hosts())
            if hosts:
                self.result_labels['first_host'].setText(str(hosts[0]))
                self.result_labels['last_host'].setText(str(hosts[-1]))
            else:
                self.result_labels['first_host'].setText("N/A")
                self.result_labels['last_host'].setText("N/A")
            
            self.result_labels['total_hosts'].setText(str(network.num_addresses))
            self.result_labels['usable_hosts'].setText(str(network.num_addresses - 2))
            
            # Determine network class
            first_octet = int(str(network.network_address).split('.')[0])
            if 1 <= first_octet <= 126:
                network_class = "A"
            elif 128 <= first_octet <= 191:
                network_class = "B"
            elif 192 <= first_octet <= 223:
                network_class = "C"
            else:
                network_class = "Other"
            self.result_labels['network_class'].setText(network_class)
            
            # Check network properties
            self.result_labels['is_private'].setText("Yes" if network.is_private else "No")
            self.result_labels['is_multicast'].setText("Yes" if network.is_multicast else "No")
            self.result_labels['is_reserved'].setText("Yes" if network.is_reserved else "No")
            
            # Store current network for subnetting
            self.current_network = network
            
        except Exception as e:
            # Clear results on error
            for label in self.result_labels.values():
                label.setText("Invalid Input")
                label.setStyleSheet(f"color: {get_error_color()};")
            return
            
        # Reset label colors to normal
        for label in self.result_labels.values():
            label.setStyleSheet(f"color: {get_accent_color()};")
            
    def divide_network(self):
        """Divide network into subnets"""
        if not hasattr(self, 'current_network'):
            return
            
        try:
            subnet_count = self.subnet_count_spin.value()
            
            # Calculate required prefix length
            import math
            required_bits = math.ceil(math.log2(subnet_count))
            new_prefix = self.current_network.prefixlen + required_bits
            
            if new_prefix > 30:  # Too small subnets
                self.subnets_table.setRowCount(1)
                self.subnets_table.setItem(0, 0, QTableWidgetItem("Error"))
                self.subnets_table.setItem(0, 1, QTableWidgetItem("Too many subnets requested"))
                return
            
            # Generate subnets
            subnets = list(self.current_network.subnets(new_prefix=new_prefix))
            
            # Populate table
            self.subnets_table.setRowCount(len(subnets))
            
            for i, subnet in enumerate(subnets):
                self.subnets_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.subnets_table.setItem(i, 1, QTableWidgetItem(str(subnet)))
                self.subnets_table.setItem(i, 2, QTableWidgetItem(str(subnet.netmask)))
                self.subnets_table.setItem(i, 3, QTableWidgetItem(str(subnet.broadcast_address)))
                
                hosts = list(subnet.hosts())
                if hosts:
                    self.subnets_table.setItem(i, 4, QTableWidgetItem(str(hosts[0])))
                    self.subnets_table.setItem(i, 5, QTableWidgetItem(str(hosts[-1])))
                else:
                    self.subnets_table.setItem(i, 4, QTableWidgetItem("N/A"))
                    self.subnets_table.setItem(i, 5, QTableWidgetItem("N/A"))
            
            self.subnets_table.resizeColumnsToContents()
            
        except Exception as e:
            self.subnets_table.setRowCount(1)
            self.subnets_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.subnets_table.setItem(0, 1, QTableWidgetItem(str(e)))
            
    def load_current_networks(self):
        """Load current network interfaces"""
        try:
            interfaces_stats = psutil.net_if_stats()
            interfaces_addrs = psutil.net_if_addrs()
            self.networks_table.setRowCount(0)
            
            row = 0
            for interface, stats in interfaces_stats.items():
                if interface.startswith('lo'):  # Skip loopback
                    continue
                    
                if interface in interfaces_addrs:
                    for addr in interfaces_addrs[interface]:
                        if addr.family == socket.AF_INET:  # IPv4 only
                            ip = addr.address
                            netmask = addr.netmask
                            
                            if ip and netmask:
                                self.networks_table.insertRow(row)
                                
                                # Interface
                                self.networks_table.setItem(row, 0, QTableWidgetItem(interface))
                                
                                # IP Address
                                self.networks_table.setItem(row, 1, QTableWidgetItem(ip))
                                
                                # Netmask
                                self.networks_table.setItem(row, 2, QTableWidgetItem(netmask))
                                
                                # Calculate network
                                try:
                                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                                    self.networks_table.setItem(row, 3, QTableWidgetItem(str(network)))
                                except:
                                    self.networks_table.setItem(row, 3, QTableWidgetItem("Invalid"))
                                
                                # Status
                                status = "Up" if stats.isup else "Down"
                                status_item = QTableWidgetItem(status)
                                if status == "Up":
                                    status_item.setBackground(Qt.GlobalColor.darkGreen)
                                else:
                                    status_item.setBackground(Qt.GlobalColor.darkRed)
                                self.networks_table.setItem(row, 4, status_item)
                                
                                row += 1
            
            self.networks_table.resizeColumnsToContents()
            
        except Exception as e:
            self.networks_table.setRowCount(1)
            self.networks_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.networks_table.setItem(0, 1, QTableWidgetItem(str(e)))
            
    def analyze_networks(self):
        """Analyze current networks"""
        analysis_text = f"Network Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        analysis_text += "=" * 60 + "\n\n"
        
        try:
            interfaces_stats = psutil.net_if_stats()
            interfaces_addrs = psutil.net_if_addrs()
            networks = []
            
            for interface, stats in interfaces_stats.items():
                if interface.startswith('lo'):
                    continue
                    
                if interface in interfaces_addrs:
                    for addr in interfaces_addrs[interface]:
                        if addr.family == socket.AF_INET:  # IPv4 only
                            ip = addr.address
                            netmask = addr.netmask
                            
                            if ip and netmask:
                                try:
                                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                                    networks.append((interface, network, ip))
                                except:
                                    pass
            
            analysis_text += f"Found {len(networks)} active network interfaces:\n\n"
            
            for interface, network, ip in networks:
                analysis_text += f"Interface: {interface}\n"
                analysis_text += f"  IP Address: {ip}\n"
                analysis_text += f"  Network: {network}\n"
                analysis_text += f"  Private: {'Yes' if network.is_private else 'No'}\n"
                analysis_text += f"  Usable Hosts: {network.num_addresses - 2}\n\n"
            
            # Check for potential issues
            analysis_text += "Potential Issues:\n"
            analysis_text += "-" * 20 + "\n"
            
            # Check for overlapping networks
            for i, (if1, net1, ip1) in enumerate(networks):
                for j, (if2, net2, ip2) in enumerate(networks[i+1:], i+1):
                    if net1.overlaps(net2):
                        analysis_text += f"⚠️  Overlapping networks detected:\n"
                        analysis_text += f"    {if1}: {net1} and {if2}: {net2}\n\n"
            
            # Check for non-private networks
            for interface, network, ip in networks:
                if not network.is_private and not network.is_loopback:
                    analysis_text += f"⚠️  Public IP detected on {interface}: {network}\n\n"
            
            self.analysis_text.setPlainText(analysis_text)
            
        except Exception as e:
            self.analysis_text.setPlainText(f"Error during analysis: {str(e)}")
            
    def add_conflict_network(self):
        """Add network to conflict checking list"""
        network_text = self.conflict_network_input.text().strip()
        if not network_text:
            return
            
        try:
            if '/' not in network_text:
                network_text += '/24'
            network = ipaddress.IPv4Network(network_text, strict=False)
            
            # Add to table
            row = self.conflict_networks_table.rowCount()
            self.conflict_networks_table.insertRow(row)
            
            self.conflict_networks_table.setItem(row, 0, QTableWidgetItem(str(network)))
            self.conflict_networks_table.setItem(row, 1, QTableWidgetItem(str(network.netmask)))
            self.conflict_networks_table.setItem(row, 2, QTableWidgetItem(str(network.num_addresses - 2)))
            
            # Remove button
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda: self.remove_conflict_network(row))
            self.conflict_networks_table.setCellWidget(row, 3, remove_button)
            
            self.conflict_network_input.clear()
            self.conflict_networks_table.resizeColumnsToContents()
            
        except Exception as e:
            # Show error in results
            self.conflict_results.setPlainText(f"Error adding network: {str(e)}")
            
    def remove_conflict_network(self, row):
        """Remove network from conflict checking list"""
        self.conflict_networks_table.removeRow(row)
        
    def clear_conflict_networks(self):
        """Clear all networks from conflict checking"""
        self.conflict_networks_table.setRowCount(0)
        self.conflict_results.clear()
        
    def check_conflicts(self):
        """Check for network conflicts"""
        networks = []
        
        # Get networks from table
        for row in range(self.conflict_networks_table.rowCount()):
            network_item = self.conflict_networks_table.item(row, 0)
            if network_item:
                try:
                    network = ipaddress.IPv4Network(network_item.text(), strict=False)
                    networks.append(network)
                except:
                    pass
        
        if len(networks) < 2:
            self.conflict_results.setPlainText("Please add at least 2 networks to check for conflicts.")
            return
            
        # Check for conflicts
        conflicts_text = f"Conflict Detection Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        conflicts_text += "=" * 60 + "\n\n"
        
        conflicts_found = 0
        
        for i, net1 in enumerate(networks):
            for j, net2 in enumerate(networks[i+1:], i+1):
                if net1.overlaps(net2):
                    conflicts_found += 1
                    conflicts_text += f"CONFLICT #{conflicts_found}:\n"
                    conflicts_text += f"  Network 1: {net1}\n"
                    conflicts_text += f"  Network 2: {net2}\n"
                    
                    # Find overlap
                    try:
                        if net1.subnet_of(net2):
                            conflicts_text += f"  Type: {net1} is a subnet of {net2}\n"
                        elif net2.subnet_of(net1):
                            conflicts_text += f"  Type: {net2} is a subnet of {net1}\n"
                        else:
                            conflicts_text += f"  Type: Networks overlap\n"
                    except:
                        conflicts_text += f"  Type: Networks overlap\n"
                    
                    conflicts_text += "\n"
        
        if conflicts_found == 0:
            conflicts_text += "✅ No conflicts detected! All networks are properly separated.\n"
        else:
            conflicts_text += f"⚠️  Total conflicts found: {conflicts_found}\n"
            conflicts_text += "\nRecommendations:\n"
            conflicts_text += "- Review network design to eliminate overlaps\n"
            conflicts_text += "- Use proper subnetting to separate networks\n"
            conflicts_text += "- Ensure routing is configured correctly\n"
        
        self.conflict_results.setPlainText(conflicts_text)
        
    def on_input_type_changed(self):
        """Handle input type change"""
        if self.sender() == self.cidr_radio:
            if self.cidr_radio.isChecked():
                self.netmask_radio.setChecked(False)
                self.network_input.setPlaceholderText("e.g., 192.168.1.0/24")
        else:
            if self.netmask_radio.isChecked():
                self.cidr_radio.setChecked(False)
                self.network_input.setPlaceholderText("e.g., 192.168.1.0 255.255.255.0")
                
    def refresh(self):
        """Refresh subnet validator data"""
        self.load_current_networks()
        self.analyze_networks()
