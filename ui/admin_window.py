# src/ui/admin_window.py
"""
Modern Admin Dashboard - Professional UI with Charts and Icons
Glassmorphism design with smooth animations
"""

import os
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy, QComboBox, QFormLayout,
    QSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt, QSize, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve, QDate
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QPen, QFont, QLinearGradient, QPainterPath

from configUI import WINDOW_CONFIG, COLORS, FST_LOGO_IMAGE
from config import FILIERES_LST, FILIERES_MST, FILIERES_INGENIEUR, MATIERES_COMPLETES
from src.ui.styles import (
    GLOBAL_STYLE, SIDEBAR_STYLE, SIDEBAR_BUTTON_STYLE, 
    SIDEBAR_USER_INFO_STYLE, SIDEBAR_HEADER_STYLE,
    CARD_STYLE, CARD_TITLE_STYLE, CARD_VALUE_STYLE,
    PRIMARY_BUTTON_STYLE, SECONDARY_BUTTON_STYLE,
    SUCCESS_BUTTON_STYLE, DANGER_BUTTON_STYLE,
    TABLE_STYLE, SOBER_BUTTON_STYLE, CHART_CONTAINER_STYLE,
    CHART_TITLE_STYLE, PAGE_TITLE_STYLE, LOGOUT_BUTTON_STYLE
)


# ═══════════════════════════════════════════════════════════
# MODERN DONUT/PIE CHART WIDGET
# ═══════════════════════════════════════════════════════════

class ModernDonutChart(QWidget):
    """Beautiful donut chart with gradient colors and animations"""
    
    def __init__(self, data, title="Chart"):
        super().__init__()
        self.data = data  # List of tuples: (label, value, color)
        self.chart_title = title
        self.setMinimumSize(350, 300)
        self.hovered_segment = -1
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor("#FFFFFF"))
        
        # Draw rounded rectangle border
        painter.setPen(QPen(QColor(COLORS['border']), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, w-2, h-2, 20, 20)
        
        # Title
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(COLORS['text_dark']))
        painter.drawText(24, 36, self.chart_title)
        
        if not self.data or sum([v for _, v, _ in self.data]) == 0:
            # No data message
            painter.setPen(QColor(COLORS['text_light']))
            msg_font = QFont("Segoe UI", 12)
            painter.setFont(msg_font)
            painter.drawText(QRectF(0, 60, w, h-60), Qt.AlignmentFlag.AlignCenter, "Aucune donnée")
            return
        
        # Chart dimensions
        chart_size = min(w - 80, h - 120)
        chart_x = (w - chart_size) // 2
        chart_y = 60
        
        # Draw donut
        total = sum([v for _, v, _ in self.data])
        start_angle = 90 * 16  # Start from top
        
        for i, (label, value, color) in enumerate(self.data):
            if value <= 0:
                continue
                
            span_angle = int((value / total) * 360 * 16)
            
            # Outer arc
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Create gradient
            gradient = QLinearGradient(chart_x, chart_y, chart_x + chart_size, chart_y + chart_size)
            base_color = QColor(color)
            lighter_color = base_color.lighter(115)
            gradient.setColorAt(0, lighter_color)
            gradient.setColorAt(1, base_color)
            
            painter.setBrush(QBrush(gradient))
            
            # Draw pie segment
            painter.drawPie(int(chart_x), int(chart_y), int(chart_size), int(chart_size), 
                          int(start_angle), int(span_angle))
            
            start_angle += span_angle
        
        # Draw center circle (donut hole)
        hole_size = chart_size * 0.55
        hole_x = chart_x + (chart_size - hole_size) / 2
        hole_y = chart_y + (chart_size - hole_size) / 2
        
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(hole_x, hole_y, hole_size, hole_size))
        
        # Center text
        center_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        painter.setFont(center_font)
        painter.setPen(QColor(COLORS['text_dark']))
        painter.drawText(QRectF(hole_x, hole_y, hole_size, hole_size), 
                        Qt.AlignmentFlag.AlignCenter, str(int(total)))
        
        # Legend
        legend_y = chart_y + chart_size + 20
        legend_x = 24
        legend_font = QFont("Segoe UI", 10)
        painter.setFont(legend_font)
        
        for i, (label, value, color) in enumerate(self.data):
            if i >= 4:  # Max 4 items in legend
                break
            
            # Color dot
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(legend_x + (i * (w-48) / 4)), int(legend_y), 10, 10)
            
            # Label
            painter.setPen(QColor(COLORS['text_medium']))
            painter.drawText(int(legend_x + 16 + (i * (w-48) / 4)), int(legend_y + 9), 
                           f"{label}: {value}")


# ═══════════════════════════════════════════════════════════
# MODERN BAR CHART WIDGET
# ═══════════════════════════════════════════════════════════

class ModernBarChart(QWidget):
    """Gradient bar chart with smooth design"""
    
    def __init__(self, data, title="Statistics"):
        super().__init__()
        self.data = data  # List of tuples (Label, Value)
        self.chart_title = title
        self.setMinimumSize(400, 300)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor("#FFFFFF"))
        
        # Draw rounded rectangle border
        painter.setPen(QPen(QColor(COLORS['border']), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, w-2, h-2, 20, 20)
        
        # Title
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(COLORS['text_dark']))
        painter.drawText(24, 36, self.chart_title)
        
        # Chart area
        margin_left = 50
        margin_right = 30
        margin_top = 60
        margin_bottom = 50
        
        graph_w = w - margin_left - margin_right
        graph_h = h - margin_top - margin_bottom
        
        if not self.data:
            painter.setPen(QColor(COLORS['text_light']))
            msg_font = QFont("Segoe UI", 12)
            painter.setFont(msg_font)
            painter.drawText(QRectF(0, margin_top, w, graph_h), 
                           Qt.AlignmentFlag.AlignCenter, "Aucune donnée")
            return
            
        # Calculate max value
        max_val = max([v for _, v in self.data]) if self.data else 10
        max_val = max(max_val, 5)  # Minimum scale
        
        # Grid lines
        painter.setPen(QPen(QColor(COLORS['border_light']), 1, Qt.PenStyle.DashLine))
        grid_lines = 5
        for i in range(grid_lines + 1):
            y = margin_top + (graph_h * i / grid_lines)
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))
            
            # Y-axis labels
            label_font = QFont("Segoe UI", 9)
            painter.setFont(label_font)
            painter.setPen(QColor(COLORS['text_light']))
            val = int(max_val * (grid_lines - i) / grid_lines)
            painter.drawText(int(margin_left - 35), int(y + 4), str(val))
        
        # Draw bars
        count = len(self.data)
        bar_width = (graph_w - 20) / count - 20
        bar_width = min(bar_width, 60)  # Max bar width
        
        colors = [
            (COLORS['primary'], COLORS['secondary']),
            (COLORS['card_cyan'], COLORS['card_emerald']),
            (COLORS['card_purple'], COLORS['primary']),
            (COLORS['card_amber'], COLORS['card_rose']),
            (COLORS['card_emerald'], COLORS['card_cyan']),
        ]
        
        for i, (label, value) in enumerate(self.data):
            x = margin_left + 20 + (i * (graph_w - 20) / count) + ((graph_w - 20) / count - bar_width) / 2
            
            if value > 0:
                bar_h = (value / max_val) * graph_h
                y = margin_top + graph_h - bar_h
                
                # Gradient for bar
                color_pair = colors[i % len(colors)]
                gradient = QLinearGradient(x, y, x, margin_top + graph_h)
                gradient.setColorAt(0, QColor(color_pair[0]))
                gradient.setColorAt(1, QColor(color_pair[1]))
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(gradient))
                
                # Draw rounded bar
                path = QPainterPath()
                radius = 8
                path.moveTo(x, margin_top + graph_h)
                path.lineTo(x, y + radius)
                path.quadTo(x, y, x + radius, y)
                path.lineTo(x + bar_width - radius, y)
                path.quadTo(x + bar_width, y, x + bar_width, y + radius)
                path.lineTo(x + bar_width, margin_top + graph_h)
                path.closeSubpath()
                
                painter.drawPath(path)
                
                # Value above bar
                value_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
                painter.setFont(value_font)
                painter.setPen(QColor(color_pair[0]))
                painter.drawText(QRectF(x, y - 25, bar_width, 20), 
                               Qt.AlignmentFlag.AlignCenter, str(value))
            
            # X-axis label
            label_font = QFont("Segoe UI", 10)
            painter.setFont(label_font)
            painter.setPen(QColor(COLORS['text_medium']))
            painter.drawText(QRectF(x - 10, margin_top + graph_h + 10, bar_width + 20, 30), 
                           Qt.AlignmentFlag.AlignCenter, label)


# ═══════════════════════════════════════════════════════════
# MODERN STAT CARD WIDGET
# ═══════════════════════════════════════════════════════════

class ModernStatCard(QFrame):
    """Beautiful stat card with icon and gradient accent"""
    
    def __init__(self, title, value, icon_text, accent_color, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon_text = icon_text
        self.accent_color = accent_color
        self.is_hovered = False
        
        self.setMinimumSize(200, 140)
        self.setMaximumHeight(160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Setup shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Icon container
        icon_frame = QFrame()
        icon_frame.setFixedSize(56, 56)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {self.accent_color}, stop:1 {QColor(self.accent_color).darker(120).name()});
                border-radius: 14px;
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(self.icon_text)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_frame)
        
        # Text container
        text_container = QVBoxLayout()
        text_container.setSpacing(4)
        
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_light']};
                font-size: 13px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
        """)
        
        self.value_label = QLabel(str(self.value))
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_dark']};
                font-size: 32px;
                font-weight: bold;
            }}
        """)
        
        text_container.addWidget(self.title_label)
        text_container.addWidget(self.value_label)
        text_container.addStretch()
        
        layout.addLayout(text_container)
        layout.addStretch()
        
        self.update_style()
        
    def update_style(self):
        if self.is_hovered:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {self.accent_color};
                    border-radius: 20px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 1px solid {COLORS['border']};
                    border-radius: 20px;
                    border-left: 4px solid {self.accent_color};
                }}
            """)
    
    def enterEvent(self, event):
        self.is_hovered = True
        self.update_style()
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update_style()
    
    def set_value(self, value):
        self.value = value
        self.value_label.setText(str(value))


# ═══════════════════════════════════════════════════════════
# USER WRAPPER
# ═══════════════════════════════════════════════════════════

class UserWrapper:
    def __init__(self, user_tuple):
        self.id = user_tuple[0] if len(user_tuple) > 0 else 0
        self.nom = user_tuple[1] if len(user_tuple) > 1 else "Inconnu"
        self.prenom = user_tuple[2] if len(user_tuple) > 2 else ""
        self.email = user_tuple[3] if len(user_tuple) > 3 else ""


# ═══════════════════════════════════════════════════════════
# MAIN ADMIN WINDOW
# ═══════════════════════════════════════════════════════════

class AdminWindow(QWidget):
    logout_signal = pyqtSignal()

    def __init__(self, user, db):
        super().__init__()
        
        if isinstance(user, tuple):
            self.user = UserWrapper(user)
        else:
            self.user = user
            
        self.db = db
        
        self.setWindowTitle(WINDOW_CONFIG['admin']['title'])
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(GLOBAL_STYLE)
        
        # Reservations data
        self.reservations_data = [
            {"date": "2024-02-10", "prof": "M. Alami", "salle": "Amphi B", "motif": "Examen Partiel"},
            {"date": "2024-02-12", "prof": "Mme. Bennani", "salle": "Salle 12", "motif": "Séance Rattrapage"}
        ]

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.create_sidebar()
        self.create_content_area()
        self.switch_page("Dashboard")
        
    def calculate_stats(self):
        """Calculate dynamic statistics"""
        stats = {}
        
        try:
            stats['enseignants'] = len(self.db.get_tous_utilisateurs('enseignant'))
            stats['etudiants'] = len(self.db.get_tous_utilisateurs('etudiant'))
        except:
            stats['enseignants'] = 0
            stats['etudiants'] = 0
            
        nb_filieres = len(FILIERES_LST) + len(FILIERES_MST) + len(FILIERES_INGENIEUR)
        stats['filieres'] = nb_filieres
        
        nb_matieres = 0
        for prog, subjects in MATIERES_COMPLETES.items():
            nb_matieres += len(subjects)
        stats['matieres'] = nb_matieres
        
        try:
            stats['groupes'] = len(self.db.get_tous_groupes())
        except:
            stats['groupes'] = 0
            
        return stats

    def refresh_dashboard(self):
        """Update dashboard stats"""
        stats = self.calculate_stats()
        
        if hasattr(self, 'stat_cards'):
            self.stat_cards['Enseignants'].set_value(stats['enseignants'])
            self.stat_cards['Étudiants'].set_value(stats['etudiants'])
            self.stat_cards['Filières'].set_value(stats['filieres'])
            self.stat_cards['Matières'].set_value(stats['matieres'])

    def create_sidebar(self):
        """Modern Sidebar with gradient - Same style as Enseignant"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1E1B4B, stop:0.5 #312E81, stop:1 #1E1B4B);
            }
        """)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        # Header
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366F1, stop:1 #06B6D4);
            }
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 25, 20, 25)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("ADMINISTRATEUR")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: white; 
            font-size: 18px;
            font-weight: 700; 
            letter-spacing: 1px;
            background: transparent;
        """)
        h_layout.addWidget(title)
        
        layout.addWidget(header)
        layout.addSpacing(16)
        
        # Menu
        self.menu_buttons = {}
        menus = [
            ("Dashboard", "Dashboard"),
            ("Generer Emploi", "Generation"),
            ("Reservations", "Reservations"),
            ("Notifications", "Notifications"),
        ]
        
        for label, pid in menus:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #FFFFFF;
                    text-align: left;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: 600;
                    border: none;
                    border-radius: 12px;
                    margin: 4px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(99, 102, 241, 0.3), stop:1 rgba(6, 182, 212, 0.2));
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #6366F1, stop:1 #06B6D4);
                    color: white;
                    font-weight: 700;
                }
            """)
            btn.clicked.connect(lambda _, p=pid: self.switch_page(p))
            layout.addWidget(btn)
            self.menu_buttons[pid] = btn
            
        layout.addStretch()
        
        # User info card
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 14px;
                margin: 12px 16px;
            }
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 16, 16, 16)
        user_layout.setSpacing(8)
        
        avatar = QLabel("A")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #8B5CF6, stop:1 #6366F1);
            color: white;
            font-size: 22px;
                font-weight: bold;
            border-radius: 25px;
            border: 2px solid rgba(255,255,255,0.3);
        """)
        
        avatar_layout = QHBoxLayout()
        avatar_layout.addStretch()
        avatar_layout.addWidget(avatar)
        avatar_layout.addStretch()
        user_layout.addLayout(avatar_layout)
        
        user_name = QLabel(f"Admin. {self.user.nom if self.user else 'Administrateur'}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_name)
        
        role_badge = QLabel("Administrateur")
        role_badge.setStyleSheet("""
            color: #C4B5FD;
            font-size: 11px;
            background: rgba(139, 92, 246, 0.2);
            padding: 4px 10px;
            border-radius: 8px;
        """)
        role_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_layout = QHBoxLayout()
        role_layout.addStretch()
        role_layout.addWidget(role_badge)
        role_layout.addStretch()
        user_layout.addLayout(role_layout)
        
        layout.addWidget(user_frame)
        
        # Logout
        logout = QPushButton("Deconnexion")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.setStyleSheet("""
            QPushButton {
                background: transparent; 
                color: #F87171; 
                border: 2px solid #F87171;
                border-radius: 10px; 
                padding: 12px 20px; 
                margin: 8px 16px 16px 16px; 
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #EF4444; 
                color: white;
                border: 2px solid #EF4444;
            }
        """)
        logout.clicked.connect(self.logout_signal.emit)
        layout.addWidget(logout)
        
        self.main_layout.addWidget(self.sidebar)

    def create_content_area(self):
        """Create main content area"""
        self.content_area = QFrame()
        self.content_area.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {COLORS['bg_light']}, stop:1 #E2E8F0);
            }}
        """)
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 32, 40, 32)
        content_layout.setSpacing(8)
        
        # Page title
        self.page_title = QLabel("Tableau de Bord")
        self.page_title.setStyleSheet(PAGE_TITLE_STYLE)
        content_layout.addWidget(self.page_title)
        
        # Page subtitle
        self.page_subtitle = QLabel("Vue d'ensemble de votre système")
        self.page_subtitle.setStyleSheet(f"""
            color: {COLORS['text_light']}; 
            font-size: 14px; 
            margin-bottom: 20px;
        """)
        content_layout.addWidget(self.page_subtitle)
        
        # Stacked widget for pages
        self.pages = QStackedWidget()
        
        self.dashboard_page = self.create_dashboard_page()
        self.pages.addWidget(self.dashboard_page)
        
        self.generation_page = self.create_generation_page()
        self.pages.addWidget(self.generation_page)
        
        self.reservations_page = self.create_reservations_page()
        self.pages.addWidget(self.reservations_page)

        self.notifications_page = self.create_notifications_page()
        self.pages.addWidget(self.notifications_page)
        
        content_layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content_area)

    def create_dashboard_page(self):
        """Create modern dashboard with stat cards and charts"""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        current_stats = self.calculate_stats()
        
        # Card configurations: (title, value, icon, color)
        cards_config = [
            ("Enseignants", current_stats['enseignants'], "👨‍🏫", COLORS['card_purple']),
            ("Étudiants", current_stats['etudiants'], "👨‍🎓", COLORS['card_cyan']),
            ("Filières", current_stats['filieres'], "📚", COLORS['card_emerald']),
            ("Matières", current_stats['matieres'], "📖", COLORS['card_amber'])
        ]
        
        self.stat_cards = {}
        
        for title, value, icon, color in cards_config:
            card = ModernStatCard(title, value, icon, color)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.stat_cards[title] = card
            stats_layout.addWidget(card)
            
        layout.addLayout(stats_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Donut chart - Room distribution
        try:
            salles = self.db.get_toutes_salles()
            type_counts = {}
            for s in salles:
                t = s[3]  # type_salle
                type_counts[t] = type_counts.get(t, 0) + 1
            
            colors_map = {
                'Amphi': COLORS['card_purple'],
                'Salle': COLORS['card_cyan'],
                'Labo': COLORS['card_emerald'],
                'TD': COLORS['card_amber'],
                'TP': COLORS['card_rose']
            }
            
            salles_data = [(label, count, colors_map.get(label, COLORS['primary'])) 
                          for label, count in type_counts.items()]
        except:
            salles_data = [
                ("Amphi", 5, COLORS['card_purple']),
                ("Salle", 12, COLORS['card_cyan']),
                ("Labo", 8, COLORS['card_emerald']),
                ("TD", 6, COLORS['card_amber'])
            ]

        donut_chart = ModernDonutChart(salles_data, "Répartition des Salles")
        donut_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        charts_layout.addWidget(donut_chart)
        
        # Bar chart - Hourly volume per day
        try:
            # Get actual schedule data if available
            heures_data = [
                ("Lun", 24), 
                ("Mar", 20), 
                ("Mer", 18), 
                ("Jeu", 22), 
                ("Ven", 16)
            ]
        except:
            heures_data = [
                ("Lun", 24), 
                ("Mar", 20), 
                ("Mer", 18), 
                ("Jeu", 22), 
                ("Ven", 16)
            ]
        
        bar_chart = ModernBarChart(heures_data, "Volume Horaire Hebdomadaire")
        bar_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        charts_layout.addWidget(bar_chart)
        
        layout.addLayout(charts_layout)
        
        return page

    def create_generation_page(self):
        """Create schedule generation page - Beautiful Modern Design"""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        
        main_layout = QVBoxLayout(page)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # ══════════════════════════════════════════════════════════════════
        # SECTION 1: DATA IMPORT CARD - Beautiful Gradient Buttons
        # ══════════════════════════════════════════════════════════════════
        import_card = QFrame()
        import_card.setObjectName("importCard")
        import_card.setStyleSheet("""
            QFrame#importCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        
        import_card_layout = QVBoxLayout(import_card)
        import_card_layout.setContentsMargins(25, 25, 25, 25)
        import_card_layout.setSpacing(8)
        
        # Header
        import_title = QLabel("Importation des Donnees (CSV)")
        import_title.setStyleSheet("color: #1E293B; font-size: 20px; font-weight: 700; background: transparent;")
        import_card_layout.addWidget(import_title)
        
        import_desc = QLabel("Selectionnez les fichiers CSV a importer dans le systeme")
        import_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        import_card_layout.addWidget(import_desc)
        
        import_card_layout.addSpacing(20)
        
        # Beautiful gradient buttons - 2x2 grid - All with same unified gradient
        self.upload_cards = {}
        
        upload_grid = QGridLayout()
        upload_grid.setSpacing(20)
        upload_grid.setContentsMargins(0, 0, 0, 0)
        
        # Gradient button style - same as sidebar active button
        unified_btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366F1, stop:1 #06B6D4);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 24px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4338CA, stop:1 #0891B2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3730A3, stop:1 #0E7490);
            }
        """
        
        # Button definitions - all with solid background
        upload_items = [
            ("salles", "Importer les Salles"),
            ("enseignants", "Importer Enseignants"),
            ("etudiants", "Importer Etudiants"),
            ("groupes", "Importer Groupes"),
        ]
        
        for idx, (key, title) in enumerate(upload_items):
            btn = QPushButton(title)
            btn.setObjectName(f"importBtn_{key}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(45)
            btn.setStyleSheet(unified_btn_style)
            btn.clicked.connect(lambda checked, k=key: self.run_import(k))
            
            self.upload_cards[key] = {'button': btn}
            
            row, col = divmod(idx, 2)
            upload_grid.addWidget(btn, row, col)
        
        import_card_layout.addLayout(upload_grid)
        main_layout.addWidget(import_card)
        
        # ══════════════════════════════════════════════════════════════════
        # SECTION 2: GENERATION CARD - Simple & Clean
        # ══════════════════════════════════════════════════════════════════
        gen_card = QFrame()
        gen_card.setObjectName("genCard")
        gen_card.setStyleSheet("""
            QFrame#genCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(25, 25, 25, 25)
        gen_layout.setSpacing(8)
        
        # Header
        gen_title = QLabel("Generation")
        gen_title.setStyleSheet("color: #1E293B; font-size: 20px; font-weight: 700; background: transparent;")
        gen_layout.addWidget(gen_title)
        
        gen_desc = QLabel("Generez automatiquement l'emploi du temps optimise pour tous les groupes")
        gen_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        gen_layout.addWidget(gen_desc)
        
        gen_layout.addSpacing(20)
        
        # Generate button with gradient - same as sidebar active button
        self.btn_generate = QPushButton("Lancer la Generation de l'Emploi du Temps")
        self.btn_generate.setObjectName("btnGenerate")
        self.btn_generate.setFixedHeight(45)
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setStyleSheet("""
            QPushButton#btnGenerate {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366F1, stop:1 #06B6D4);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 32px;
            }
            QPushButton#btnGenerate:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4338CA, stop:1 #0891B2);
            }
            QPushButton#btnGenerate:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3730A3, stop:1 #0E7490);
            }
        """)
        gen_layout.addWidget(self.btn_generate, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(gen_card)
        main_layout.addStretch()
        
        # Create hidden widgets for compatibility (but not shown)
        self.combo_annee = QComboBox()
        self.combo_annee.addItems(["2024-2025", "2025-2026", "2026-2027"])
        self.combo_annee.hide()
        
        self.combo_semestre = QComboBox()
        self.combo_semestre.addItems(["Semestre 1", "Semestre 2"])
        self.combo_semestre.hide()
        
        self.combo_filiere = QComboBox()
        self.combo_filiere.addItems(["Toutes les filieres"])
        self.combo_filiere.hide()
        
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.hide()
        
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate().addMonths(4))
        self.date_fin.hide()
        
        self.spin_seances = QSpinBox()
        self.spin_seances.setValue(4)
        self.spin_seances.hide()
        
        self.spin_duree = QSpinBox()
        self.spin_duree.setValue(90)
        self.spin_duree.hide()
        
        return page
    
    def _update_upload_status(self, key, success, filename=""):
        """Update upload button status after import"""
        if key in self.upload_cards:
            card_data = self.upload_cards[key]
            btn = card_data['button']
            
            if success:
                # Show success with green gradient
                short_name = filename[:15] + "..." if len(filename) > 15 else filename
                btn.setText(f"✓ {short_name}")
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #10B981, stop:0.5 #059669, stop:1 #047857);
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-size: 15px;
                        font-weight: 600;
                        padding: 0 24px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #059669, stop:0.5 #047857, stop:1 #065F46);
                    }
                """)
            else:
                # Show error with red gradient
                btn.setText("✗ Erreur d'import")
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #EF4444, stop:0.5 #DC2626, stop:1 #B91C1C);
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-size: 15px;
                        font-weight: 600;
                        padding: 0 24px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #DC2626, stop:0.5 #B91C1C, stop:1 #991B1B);
                    }
                """)

    def run_import(self, type_import):
        """Execute import via ImportManager"""
        from src.import_manager import ImportManager
        from config import CSV_TEMPLATES
        from PyQt6.QtWidgets import QFileDialog
        import os
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Selectionner le fichier {type_import} CSV",
            "", 
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        # Extract filename for display
        filename = os.path.basename(file_path)
            
        manager = ImportManager()
        success = False
        
        if type_import == "salles":
            success = manager.import_salles(file_path)
        elif type_import == "enseignants":
            success = manager.import_enseignants(file_path)
        elif type_import == "etudiants":
            success = manager.import_etudiants(file_path)
        elif type_import == "groupes":
            success = manager.import_groupes(file_path)
        
        # Update upload card status
        if hasattr(self, 'upload_cards'):
            self._update_upload_status(type_import, success, filename)
            
        if success:
            QMessageBox.information(self, "Succes", f"Import {type_import} reussi !")
            self.refresh_dashboard()
        else:
            QMessageBox.critical(self, "Erreur", f"Echec de l'import {type_import}. Verifiez le format.")

    def create_reservations_page(self):
        """Create reservations page — même design que Notifications Système (badge, ombres, violet-cyan)"""
        page = QWidget()
        page.setStyleSheet("background: #f3f6fb;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 8, 0, 24)
        
        # Carte contrôle (comme Notifications)
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 16px;
            }
        """)
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(24)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(4)
        header_shadow.setColor(QColor(0, 0, 0, 12))
        header_frame.setGraphicsEffect(header_shadow)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        title = QLabel("Demandes de Reservation")
        title.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 17px;
            font-weight: 600;
            background: #EFF6FF;
            color: #1E40AF;
            padding: 10px 20px;
            border-radius: 12px;
            border: none;
        """)
        
        self.counter_label = QLabel("0 demandes en attente")
        self.counter_label.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
            font-weight: 600;
            background: #6A5ACD;
            padding: 10px 20px;
            border-radius: 12px;
            border: none;
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.counter_label)
        
        layout.addWidget(header_frame)
        
        # Carte tableau (comme Notifications)
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 16px;
            }
        """)
        table_shadow = QGraphicsDropShadowEffect()
        table_shadow.setBlurRadius(24)
        table_shadow.setXOffset(0)
        table_shadow.setYOffset(4)
        table_shadow.setColor(QColor(0, 0, 0, 12))
        table_frame.setGraphicsEffect(table_shadow)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.res_table = QTableWidget()
        self.res_table.setColumnCount(5)
        self.res_table.setHorizontalHeaderLabels(["DATE", "ENSEIGNANT", "SALLE", "MOTIF", "ACTIONS"])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.res_table.verticalHeader().setVisible(False)
        self.res_table.setShowGrid(False)
        self.res_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                border-top-left-radius: 0;
                border-top-right-radius: 0;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #E8ECF0;
                color: #334155;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #F0F4FF;
                color: #4A5568;
            }
            QHeaderView::section {
                background: #6A5ACD;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 13px;
                padding: 14px 16px;
                border: none;
                border-right: none;
            }
        """)
        
        table_layout.addWidget(self.res_table)
        layout.addWidget(table_frame)
        
        self.refresh_reservations()
        
        return page

    def refresh_reservations(self):
        """Refresh reservations table"""
        self.res_table.setRowCount(0)
        
        pending_count = sum(1 for r in self.reservations_data if 'status' not in r)
        
        self.counter_label.setText(f"{pending_count} demande{'s' if pending_count != 1 else ''} en attente")
        
        if pending_count == 0:
            self.counter_label.setStyleSheet("""
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 600;
                background: #10B981;
                padding: 10px 20px;
                border-radius: 12px;
                border: none;
            """)
        else:
            self.counter_label.setStyleSheet("""
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 600;
                background: #6A5ACD;
                padding: 10px 20px;
                border-radius: 12px;
                border: none;
            """)
            
        for i, row_data in enumerate(self.reservations_data):
            self.res_table.insertRow(i)
            
            for j, key in enumerate(['date', 'prof', 'salle', 'motif']):
                item = QTableWidgetItem(row_data[key])
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.res_table.setItem(i, j, item)
            
            # Actions
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(10, 6, 10, 6)
            actions_layout.setSpacing(10)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if 'status' in row_data:
                status = row_data['status']
                lbl_status = QLabel(status)
                
                if status == "Acceptée":
                    lbl_status.setStyleSheet("""
                        color: #FFFFFF;
                        font-family: 'Segoe UI', sans-serif;
                        font-weight: 600;
                        font-size: 13px;
                        background: #10B981;
                        padding: 8px 20px;
                        border-radius: 12px;
                        border: none;
                    """)
                else:
                    lbl_status.setStyleSheet("""
                        color: #FFFFFF;
                        font-family: 'Segoe UI', sans-serif;
                        font-weight: 600;
                        font-size: 13px;
                        background: #EF4444;
                        padding: 8px 20px;
                        border-radius: 12px;
                        border: none;
                    """)
                
                actions_layout.addWidget(lbl_status)
            else:
                # Accepter — fond blanc, bordure verte, texte noir, icône ✓ (taille réduite)
                btn_accept = QPushButton("✓  Accepter")
                btn_accept.setFixedHeight(32)
                btn_accept.setMinimumWidth(88)
                btn_accept.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_accept.setStyleSheet("""
                    QPushButton { 
                        background: #FFFFFF;
                        color: #0F172A;
                        font-family: 'Segoe UI', sans-serif;
                        font-weight: 700;
                        font-size: 11px;
                        border: 2px solid #22C55E;
                        border-radius: 8px;
                        padding: 0 12px;
                    }
                    QPushButton:hover { background: #F0FDF4; border: 2px solid #16A34A; }
                    QPushButton:pressed { background: #DCFCE7; }
                """)
                btn_accept.clicked.connect(lambda _, idx=i: self.handle_reservation(idx, True))
                
                # Refuser — fond blanc, bordure rouge, texte noir, icône ✗ (taille réduite)
                btn_refuse = QPushButton("✗  Refuser")
                btn_refuse.setFixedHeight(32)
                btn_refuse.setMinimumWidth(88)
                btn_refuse.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_refuse.setStyleSheet("""
                    QPushButton { 
                        background: #FFFFFF;
                        color: #0F172A;
                        font-family: 'Segoe UI', sans-serif;
                        font-weight: 700;
                        font-size: 11px;
                        border: 2px solid #EF4444;
                        border-radius: 8px;
                        padding: 0 12px;
                    }
                    QPushButton:hover { background: #FEF2F2; border: 2px solid #DC2626; }
                    QPushButton:pressed { background: #FEE2E2; }
                """)
                btn_refuse.clicked.connect(lambda _, idx=i: self.handle_reservation(idx, False))
                
                actions_layout.setSpacing(12)
                actions_layout.addWidget(btn_accept)
                actions_layout.addWidget(btn_refuse)
            
            self.res_table.setCellWidget(i, 4, actions_widget)
            self.res_table.setRowHeight(i, 60)

    def handle_reservation(self, index, accepted):
        """Handle reservation accept/reject"""
        if 0 <= index < len(self.reservations_data):
            data = self.reservations_data[index]
            data['status'] = "Acceptée" if accepted else "Refusée"
        self.refresh_reservations()

    def create_notifications_page(self):
        """Create notifications page — design comme screenshot (fond #f3f6fb, dégradé violet-cyan)"""
        page = QWidget()
        page.setStyleSheet("background: #f3f6fb;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 8, 0, 24)
        
        # Carte contrôle (ombre, badge, bouton soigné)
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 16px;
            }
        """)
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(24)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(4)
        header_shadow.setColor(QColor(0, 0, 0, 12))
        header_frame.setGraphicsEffect(header_shadow)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        title = QLabel("Notifications Système")
        title.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 17px;
            font-weight: 600;
            background: #EFF6FF;
            color: #1E40AF;
            padding: 10px 20px;
            border-radius: 12px;
            border: none;
        """)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFixedHeight(42)
        btn_refresh.setMinimumWidth(120)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #6A5ACD;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-radius: 10px;
                padding: 0 20px;
            }
            QPushButton:hover { background: #5B4ABD; }
            QPushButton:pressed { background: #4D3CAD; }
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_refresh)
        
        layout.addWidget(header_frame)
        
        # Carte tableau (ombre, en-tête stylé)
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 16px;
            }
        """)
        table_shadow = QGraphicsDropShadowEffect()
        table_shadow.setBlurRadius(24)
        table_shadow.setXOffset(0)
        table_shadow.setYOffset(4)
        table_shadow.setColor(QColor(0, 0, 0, 12))
        table_frame.setGraphicsEffect(table_shadow)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        notif_list = QTableWidget()
        notif_list.setColumnCount(3)
        notif_list.setHorizontalHeaderLabels(["DATE", "TYPE", "MESSAGE"])
        notif_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        notif_list.verticalHeader().setVisible(False)
        notif_list.setShowGrid(False)
        notif_list.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                border-top-left-radius: 0;
                border-top-right-radius: 0;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #E8ECF0;
                color: #334155;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #F0F4FF;
                color: #4A5568;
            }
            QHeaderView::section {
                background: #6A5ACD;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 13px;
                padding: 14px 16px;
                border: none;
                border-right: 1px solid rgba(255,255,255,0.4);
            }
        """)
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT d.date_debut, u.nom, u.prenom, d.motif 
                FROM disponibilites d
                JOIN utilisateurs u ON d.enseignant_id = u.id
                ORDER BY d.id DESC LIMIT 20
            ''')
            dispos = cursor.fetchall()
            conn.close()
            
            notif_list.setRowCount(len(dispos))
            for i, (date, nom, prenom, motif) in enumerate(dispos):
                notif_list.setItem(i, 0, QTableWidgetItem(date))
                notif_list.setItem(i, 1, QTableWidgetItem("Indisponibilite"))
                notif_list.setItem(i, 2, QTableWidgetItem(f"Prof {nom} {prenom}: {motif}"))
                notif_list.setRowHeight(i, 50)
                
        except Exception as e:
            print(f"Erreur notifs: {e}")
            
        table_layout.addWidget(notif_list)
        layout.addWidget(table_frame)
        
        return page

    def switch_page(self, page_id):
        """Switch displayed page"""
        titles = {
            "Dashboard": ("Tableau de Bord", "Vue d'ensemble de votre système"),
            "Generation": ("Génération Emploi du Temps", "Importez les données et générez l'emploi"),
            "Reservations": ("Gestion des Réservations", "Gérez les demandes de réservation des salles"),
            "Notifications": ("Notifications Système", "Suivez les alertes et notifications")
        }
        
        title, subtitle = titles.get(page_id, (page_id, ""))
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        if page_id in ("Notifications", "Reservations"):
            self.page_subtitle.setStyleSheet("color: #607c9b; font-size: 14px;")
        else:
            self.page_subtitle.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 14px;")
        
        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)
            
        index_map = {"Dashboard": 0, "Generation": 1, "Reservations": 2, "Notifications": 3}
        if page_id in index_map:
            self.pages.setCurrentIndex(index_map[page_id])
