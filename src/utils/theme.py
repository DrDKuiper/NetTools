"""
Theme management for NetTools application
Provides dark mode and styling functionality
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
import darkdetect


def apply_dark_theme(app: QApplication):
    """Apply dark theme to the application"""
    
    # Create dark palette
    dark_palette = QPalette()
    
    # Window colors
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    
    # Base colors (input fields)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    
    # Text colors
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    
    # Button colors
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    
    # Highlight colors
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    
    # Apply palette
    app.setPalette(dark_palette)
    
    # Additional styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #353535;
            color: #ffffff;
        }
        
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-bottom: 1px solid #5a5a5a;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 5px 10px;
        }
        
        QMenuBar::item:selected {
            background-color: #404040;
            border-radius: 3px;
        }
        
        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #5a5a5a;
        }
        
        QMenu::item:selected {
            background-color: #404040;
        }
        
        QStatusBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-top: 1px solid #5a5a5a;
        }
        
        QTabWidget::pane {
            border: 1px solid #5a5a5a;
            background-color: #353535;
        }
        
        QTabBar::tab {
            background-color: #2b2b2b;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #353535;
            border-bottom: 2px solid #2a82da;
        }
        
        QTabBar::tab:hover {
            background-color: #404040;
        }
        
        QPushButton {
            background-color: #2a82da;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #3a92ea;
        }
        
        QPushButton:pressed {
            background-color: #1a72ca;
        }
        
        QPushButton:disabled {
            background-color: #555555;
            color: #888888;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QComboBox {
            background-color: #191919;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            padding: 5px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
            border: 2px solid #2a82da;
        }
        
        QGroupBox {
            color: #ffffff;
            border: 1px solid #5a5a5a;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QProgressBar {
            border: 1px solid #5a5a5a;
            border-radius: 3px;
            text-align: center;
            background-color: #191919;
        }
        
        QProgressBar::chunk {
            background-color: #2a82da;
            border-radius: 2px;
        }
        
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #5a5a5a;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #707070;
        }
        
        QTableWidget {
            background-color: #191919;
            alternate-background-color: #2b2b2b;
            gridline-color: #5a5a5a;
            selection-background-color: #2a82da;
        }
        
        QHeaderView::section {
            background-color: #2b2b2b;
            color: #ffffff;
            padding: 5px;
            border: 1px solid #5a5a5a;
            font-weight: bold;
        }
        
        QSplitter::handle {
            background-color: #5a5a5a;
        }
        
        QSplitter::handle:hover {
            background-color: #707070;
        }
    """)


def get_accent_color():
    """Get the application accent color"""
    return "#2a82da"


def get_success_color():
    """Get success color"""
    return "#28a745"


def get_warning_color():
    """Get warning color"""
    return "#ffc107"


def get_error_color():
    """Get error color"""
    return "#dc3545"


def get_info_color():
    """Get info color"""
    return "#17a2b8"
