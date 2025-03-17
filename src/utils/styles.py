"""
Styles CSS et constantes d'interface utilisateur pour l'application
"""

# Couleurs principales
PRIMARY_COLOR = "#4CAF50"
PRIMARY_DARK = "#388E3C"
ACCENT_COLOR = "#FF5722"
DANGER_COLOR = "#e74c3c"
WARNING_COLOR = "#f39c12"
INFO_COLOR = "#3498db"

# Styles pour les boutons principaux
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_DARK};
    }}
    QPushButton:disabled {{
        background-color: #CCCCCC;
        color: #888888;
    }}
"""

DANGER_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {DANGER_COLOR};
        color: white;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: #c0392b;
    }}
    QPushButton:disabled {{
        background-color: #CCCCCC;
        color: #888888;
    }}
"""

# Styles pour les tableaux
TABLE_STYLE = """
    QTableWidget {
        gridline-color: #DDDDDD;
        selection-background-color: #E3F2FD;
        selection-color: black;
    }
    QTableWidget::item {
        padding: 4px;
    }
    QHeaderView::section {
        background-color: #F5F5F5;
        padding: 6px;
        border: 1px solid #DDDDDD;
        font-weight: bold;
    }
"""

# Styles pour les tooltips
TOOLTIP_STYLE = """
    QToolTip {
        background-color: #FCF8E3;
        color: #8A6D3B;
        border: 1px solid #FAEBCC;
        padding: 8px;
        opacity: 230;
    }
"""
