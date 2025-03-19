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

# Styles pour les boutons
BUTTON_STYLES = {
    "primary": f"""
        QPushButton {{
            background-color: none;
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_DARK};
        }}
        QPushButton:pressed {{
            background-color: #3d8b40;
        }}
    """,
    "add": f"""
        QPushButton {{
            background-color: {PRIMARY_COLOR};
            color: white;
            font-weight: bold;
            border-radius: 6px;
            min-width: 30px;
            min-height: 26px;
            max-width: 30px;
            max-height: 26px;
            padding: 0px;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_DARK};
        }}
        QPushButton:pressed {{
            background-color: #3d8b40;
        }}
    """,
    "delete": """
        QPushButton {{
            background-color: none;
            color: white;
            font-weight: bold;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: #d32f2f;
        }}
        QPushButton:pressed {{
            background-color: #b71c1c;
        }}
    """,
    "edit": f"""
        QPushButton {{
            background: none;
            color: white;
            font-weight: bold;
            border-radius: 4px;
            min-width: 28px;
            min-height: 28px;
            max-width: 28px;
            max-height: 28px;
            padding: 0px;
            font-size: 15px;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_COLOR};
        }}
        QPushButton:pressed {{
            background-color: #e65100;
        }}
    """,
    "replace": f"""
        QPushButton {{
            background: none;
            color: white;
            font-weight: bold;
            border-radius: 4px;
            min-width: 28px;
            min-height: 28px;
            max-width: 28px;
            max-height: 28px;
            padding: 0px;
            font-size: 15px;
        }}
        QPushButton:hover {{
            background-color: {INFO_COLOR};
        }}
        QPushButton:pressed {{
            background-color: #e65100;
        }}
    """,
}

# Styles pour les tableaux
TABLE_STYLE = f"""
    QTableWidget {{
        gridline-color: #DDDDDD;
        selection-background-color: {INFO_COLOR}33;
        selection-color: black;
    }}
    QTableWidget::item {{
        padding: 4px;
    }}
    QHeaderView::section {{
        background-color: {PRIMARY_COLOR};
        color: white;
        padding: 6px;
        border: 1px solid {PRIMARY_DARK};
        font-weight: bold;
    }}
"""

# Styles pour les tooltips
TOOLTIP_STYLE = f"""
    QToolTip {{
        background-color: #FCF8E3;
        color: {WARNING_COLOR};
        border: 1px solid #FAEBCC;
        padding: 8px;
        opacity: 230;
    }}
"""
