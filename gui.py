import sys
import os

from installer import Installer, is_termux


def run_cli_mode():
    installer = Installer()
    all_pkgs = installer.get_all_packages()
    termux_pkgs = [p for p in all_pkgs if "termux" in p.get("install", {})]

    print(f"\nAnything Setup Tool - Termux Mode")
    print(f"Detected {len(termux_pkgs)} packages available for Termux\n")

    categories = [c for c in installer.get_categories() if c.get("packages")]
    for cat in categories:
        pkgs = [p for p in cat["packages"] if "termux" in p.get("install", {})]
        if pkgs:
            print(f"[{cat['id']}] {cat['name']} ({len(pkgs)} packages)")
            for p in pkgs:
                installed = installer.is_installed(p["id"])
                status = "OK" if installed else "  "
                print(f"  {status} {p['id']:20s} - {p.get('description', '')[:50]}")
            print()

    selected = input("Enter package IDs (comma-separated), 'all' for all, or 'q' to quit: ").strip()
    if selected.lower() in ("q", "quit", ""):
        return

    if selected.lower() == "all":
        pkg_ids = [p["id"] for p in termux_pkgs]
    else:
        pkg_ids = [s.strip() for s in selected.split(",") if s.strip()]

    if not pkg_ids:
        print("No packages selected.")
        return

    print(f"\nInstalling {len(pkg_ids)} package(s)...")
    installer.install(pkg_ids, callback=lambda pct, msg: print(f"  {msg}"))
    print("\nDone!")


def run_gui_mode():
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
        QProgressBar, QTextEdit, QGroupBox, QLineEdit, QComboBox,
        QMessageBox, QCheckBox, QScrollArea, QFrame,
        QInputDialog, QSplitter, QStackedWidget, QSizePolicy,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
    from PyQt6.QtGui import QFont, QColor, QTextCursor, QCloseEvent, QIcon, QPixmap

    C = {
        "bg":           "#0f172a",
        "bg_card":      "#1e293b",
        "bg_card_alt":  "#334155",
        "bg_input":     "#1e293b",
        "bg_sidebar":   "#0f172a",
        "border":       "#334155",
        "border_light": "#475569",
        "text":         "#f1f5f9",
        "text_dim":     "#94a3b8",
        "text_muted":   "#64748b",
        "accent":       "#38bdf8",
        "accent_hover": "#7dd3fc",
        "green":        "#4ade80",
        "green_bg":     "#166534",
        "red":          "#f87171",
        "red_bg":       "#991b1b",
        "orange":       "#fb923c",
        "orange_bg":    "#9a3412",
        "purple":       "#c084fc",
        "purple_bg":    "#6b21a8",
        "yellow":       "#facc15",
        "sidebar_w":    220,
    }

    STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {C['bg']};
        color: {C['text']};
    }}
    QLabel {{
        color: {C['text']};
        background: transparent;
    }}
    QLineEdit {{
        background-color: {C['bg_input']};
        color: {C['text']};
        border: 1px solid {C['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        selection-background-color: {C['accent']};
    }}
    QLineEdit:focus {{ border: 1px solid {C['accent']}; }}
    QLineEdit::placeholder {{ color: {C['text_muted']}; }}
    QPushButton {{
        background-color: {C['bg_card']};
        color: {C['text']};
        border: 1px solid {C['border']};
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 13px;
    }}
    QPushButton:hover {{ background-color: {C['bg_card_alt']}; border-color: {C['border_light']}; }}
    QPushButton:pressed {{ background-color: {C['border']}; }}
    QComboBox {{
        background-color: {C['bg_input']};
        color: {C['text']};
        border: 1px solid {C['border']};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
    }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {C['text_dim']};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {C['bg_card']};
        color: {C['text']};
        border: 1px solid {C['border']};
        selection-background-color: {C['accent']};
        selection-color: {C['bg']};
        outline: none;
    }}
    QProgressBar {{
        background-color: {C['bg_card']};
        border: 1px solid {C['border']};
        border-radius: 6px;
        text-align: center;
        color: {C['text']};
        font-size: 12px;
        height: 22px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {C['accent']}, stop:1 {C['purple']});
        border-radius: 5px;
    }}
    QTextEdit {{
        background-color: #0c0c14;
        color: #c8d6e5;
        border: 1px solid {C['border']};
        border-radius: 8px;
        padding: 8px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 12px;
        selection-background-color: #264f78;
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: {C['bg']}; width: 6px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {C['border']}; border-radius: 3px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {C['border_light']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: {C['bg']}; height: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {C['border']}; border-radius: 3px; min-width: 30px;
    }}
    QCheckBox {{ spacing: 6px; color: {C['text']}; background: transparent; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border: 2px solid {C['border_light']};
        border-radius: 4px;
        background: {C['bg_input']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {C['accent']};
        border-color: {C['accent']};
    }}
    QCheckBox::indicator:hover {{ border-color: {C['accent']}; }}
    QTreeWidget {{
        background-color: {C['bg_card']};
        color: {C['text']};
        border: 1px solid {C['border']};
        border-radius: 8px;
        outline: none;
        font-size: 13px;
    }}
    QTreeWidget::item {{
        padding: 6px 4px;
        border-bottom: 1px solid {C['border']};
    }}
    QTreeWidget::item:selected {{
        background-color: {C['accent']};
        color: {C['bg']};
    }}
    QTreeWidget::item:hover {{ background-color: {C['bg_card_alt']}; }}
    QHeaderView::section {{
        background-color: {C['bg_card_alt']};
        color: {C['text']};
        border: none;
        border-bottom: 2px solid {C['border']};
        padding: 8px 6px;
        font-weight: bold;
        font-size: 12px;
    }}
    QSplitter::handle {{ background-color: {C['border']}; width: 1px; }}
    """

    class InstallThread(QThread):
        progress = pyqtSignal(int, str)
        finished_signal = pyqtSignal(bool)

        def __init__(self, installer, pkg_ids):
            super().__init__()
            self.installer = installer
            self.pkg_ids = pkg_ids
            self._stop = False

        def run(self):
            ok = self.installer.install(self.pkg_ids, callback=self._on_progress)
            self.finished_signal.emit(ok)

        def _on_progress(self, percent, message):
            if not self._stop:
                self.progress.emit(percent, message)

        def stop(self):
            self._stop = True

    class SideButton(QWidget):
        clicked = pyqtSignal()

        def __init__(self, icon_char, label, parent=None):
            super().__init__(parent)
            self._icon_char = icon_char
            self._label = label
            self._active = False
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setFixedHeight(44)
            self.setToolTip(label)

            layout = QHBoxLayout(self)
            layout.setContentsMargins(14, 0, 14, 0)
            layout.setSpacing(10)

            self._icon_lbl = QLabel(icon_char)
            self._icon_lbl.setFixedWidth(24)
            self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self._icon_lbl)

            self._text_lbl = QLabel(label)
            self._text_lbl.setFont(QFont("Sans Serif", 11))
            layout.addWidget(self._text_lbl, 1)

            self._apply_style()

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.clicked.emit()

        def _apply_style(self):
            if self._active:
                bg = C['bg_card']
                color = C['accent']
                border = f"border-left: 3px solid {C['accent']};"
            else:
                bg = "transparent"
                color = C['text_dim']
                border = "border-left: 3px solid transparent;"
            self.setStyleSheet(f"""
                SideButton {{
                    background-color: {bg};
                    border-radius: 0px;
                    {border}
                }}
                SideButton:hover {{
                    background-color: {C['bg_card'] if not self._active else C['bg_card_alt']};
                }}
            """)
            self._icon_lbl.setStyleSheet(f"color: {color}; font-size: 16px; background: transparent; border: none;")
            self._text_lbl.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; border: none;")

        def set_active(self, active):
            self._active = active
            self._apply_style()

        def sizeHint(self):
            return QSize(200, 44)

    class PackageCard(QFrame):
        def __init__(self, pkg, installed, parent=None):
            super().__init__(parent)
            self.pkg = pkg
            self.pkg_id = pkg["id"]
            self.setFixedHeight(58)
            self.setCursor(Qt.CursorShape.PointingHandCursor)

            self.setStyleSheet(f"""
                PackageCard {{
                    background-color: {C['bg_card']};
                    border: 1px solid {C['border']};
                    border-radius: 8px;
                }}
                PackageCard:hover {{
                    border-color: {C['accent']};
                    background-color: {C['bg_card_alt']};
                }}
            """)

            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 6, 10, 6)
            layout.setSpacing(8)

            self.checkbox = QCheckBox()
            self.checkbox.setChecked(False)
            self.checkbox.setFixedSize(18, 18)
            layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignVCenter)

            info_col = QVBoxLayout()
            info_col.setSpacing(1)
            info_col.setContentsMargins(0, 0, 0, 0)

            name_row = QHBoxLayout()
            name_row.setSpacing(6)

            name_lbl = QLabel(f"<b>{pkg['name']}</b>")
            name_lbl.setStyleSheet(f"font-size: 13px; color: {C['text']};")
            name_row.addWidget(name_lbl)

            id_lbl = QLabel(pkg["id"])
            id_lbl.setStyleSheet(f"font-size: 10px; color: {C['text_muted']}; font-family: monospace;")
            name_row.addWidget(id_lbl)
            name_row.addStretch()

            if installed:
                st = QLabel("\u2713")
                st.setStyleSheet(f"color: {C['green']}; font-size: 12px; font-weight: bold;")
                name_row.addWidget(st, 0, Qt.AlignmentFlag.AlignVCenter)

            info_col.addLayout(name_row)

            desc = pkg.get("description", "")
            if desc:
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet(f"font-size: 11px; color: {C['text_muted']};")
                info_col.addWidget(desc_lbl)

            layout.addLayout(info_col, 1)

        def isChecked(self):
            return self.checkbox.isChecked()

        def setChecked(self, val):
            self.checkbox.setChecked(val)

    class ManagePackageDialog(QWidget):
        saved = pyqtSignal()

        def __init__(self, installer, parent=None, edit_pkg=None):
            super().__init__(parent)
            self.installer = installer
            self.edit_pkg = edit_pkg
            self.setWindowTitle("Edit Package" if edit_pkg else "Add Package")
            self.setMinimumSize(640, 540)
            self.setStyleSheet(f"""
                QWidget {{ background-color: {C['bg']}; color: {C['text']}; }}
                QGroupBox {{
                    font-weight: bold;
                    border: 1px solid {C['border']};
                    border-radius: 8px;
                    margin-top: 12px;
                    padding: 14px 10px 10px 10px;
                    color: {C['accent']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                }}
            """)
            self._build_ui()
            if edit_pkg:
                self._fill_data()

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(20, 20, 20, 20)
            root.setSpacing(14)

            title = QLabel("Edit Package" if self.edit_pkg else "Add New Package")
            title.setFont(QFont("Sans Serif", 16, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {C['accent']};")
            root.addWidget(title)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            container = QWidget()
            form = QVBoxLayout(container)
            form.setSpacing(12)

            for label_text, attr, placeholder in [
                ("Category:", "combo_cat", None),
                ("ID:", "input_id", "e.g. rust, docker..."),
                ("Name:", "input_name", "Display name"),
                ("Description:", "input_desc", "Short description"),
            ]:
                row = QHBoxLayout()
                row.setSpacing(12)
                lbl = QLabel(label_text)
                lbl.setFixedWidth(70)
                lbl.setStyleSheet(f"color: {C['text_dim']};")
                row.addWidget(lbl, 0, Qt.AlignmentFlag.AlignVCenter)
                if attr == "combo_cat":
                    w = QComboBox()
                    w.setMinimumHeight(36)
                    for cat in self.installer.get_categories():
                        w.addItem(cat["name"], cat["id"])
                    setattr(self, attr, w)
                else:
                    w = QLineEdit()
                    w.setPlaceholderText(placeholder)
                    w.setMinimumHeight(36)
                    setattr(self, attr, w)
                row.addWidget(w, 1)
                form.addLayout(row)

            for grp_name, attr_name in [("Install command (per platform)", "inputs_install"), ("Check command (per platform)", "inputs_check")]:
                grp = QGroupBox(grp_name)
                gl = QVBoxLayout(grp)
                gl.setSpacing(8)
                inputs = {}
                for plat in ["linux", "darwin", "win32"]:
                    row = QHBoxLayout()
                    row.setSpacing(8)
                    lbl = QLabel(f"{plat}:")
                    lbl.setFixedWidth(60)
                    lbl.setStyleSheet(f"color: {C['text_dim']}; font-family: monospace;")
                    row.addWidget(lbl)
                    le = QLineEdit()
                    le.setPlaceholderText(f"Command for {plat}")
                    le.setMinimumHeight(32)
                    row.addWidget(le, 1)
                    inputs[plat] = le
                    gl.addLayout(row)
                setattr(self, attr_name, inputs)
                form.addWidget(grp)

            scroll.setWidget(container)
            root.addWidget(scroll, 1)

            btn_row = QHBoxLayout()
            btn_row.addStretch()

            btn_cancel = QPushButton("Cancel")
            btn_cancel.setFixedHeight(40)
            btn_cancel.setMinimumWidth(100)
            btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_cancel.setStyleSheet(f"QPushButton {{ background-color: {C['bg_card']}; color: {C['text_dim']}; border: 1px solid {C['border']}; border-radius: 8px; padding: 0 20px; }} QPushButton:hover {{ background-color: {C['bg_card_alt']}; color: {C['text']}; }}")
            btn_cancel.clicked.connect(self.close)
            btn_row.addWidget(btn_cancel)

            btn_save = QPushButton("\u2713 Save")
            btn_save.setFixedHeight(40)
            btn_save.setMinimumWidth(120)
            btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_save.setStyleSheet(f"QPushButton {{ background-color: {C['accent']}; color: {C['bg']}; border: none; border-radius: 8px; padding: 0 20px; font-weight: bold; }} QPushButton:hover {{ background-color: {C['accent_hover']}; }}")
            btn_save.clicked.connect(self._save)
            btn_row.addWidget(btn_save)
            root.addLayout(btn_row)

        def _fill_data(self):
            pkg = self.edit_pkg
            self.input_id.setText(pkg.get("id", ""))
            self.input_id.setReadOnly(True)
            self.input_id.setStyleSheet(f"background-color: {C['bg_card_alt']}; color: {C['text_muted']}; border: 1px solid {C['border']}; border-radius: 8px; padding: 8px 12px;")
            self.input_name.setText(pkg.get("name", ""))
            self.input_desc.setText(pkg.get("description", ""))
            idx = self.combo_cat.findData(pkg.get("category_id", ""))
            if idx >= 0:
                self.combo_cat.setCurrentIndex(idx)
            for plat, le in self.inputs_install.items():
                le.setText(pkg.get("install", {}).get(plat, ""))
            for plat, le in self.inputs_check.items():
                le.setText(pkg.get("check", {}).get(plat, ""))

        def _save(self):
            cat_id = self.combo_cat.currentData()
            pkg_id = self.input_id.text().strip()
            name = self.input_name.text().strip()
            desc = self.input_desc.text().strip()
            if not pkg_id or not name:
                QMessageBox.warning(self, "Error", "ID and Name cannot be empty!")
                return
            install = {p: v.strip() for p, le in self.inputs_install.items() if (v := le.text().strip())}
            check = {p: v.strip() for p, le in self.inputs_check.items() if (v := le.text().strip())}
            if not install:
                QMessageBox.warning(self, "Error", "Need at least one install command!")
                return
            if self.edit_pkg:
                self.installer.update_package(pkg_id, name=name, description=desc, install_cmds=install, check_cmds=check)
            else:
                if not self.installer.add_package(cat_id, pkg_id, name, desc, install, check):
                    QMessageBox.warning(self, "Error", f"Package '{pkg_id}' already exists!")
                    return
            self.saved.emit()
            self.close()

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.installer = Installer()
            self.install_thread = None
            self.cards = {}
            self.current_page = 0
            self._build_ui()
            self._load_packages()
            self._set_active_page(0)

        def _build_ui(self):
            self.setWindowTitle("Anything Setup Tool")
            self.setMinimumSize(1100, 700)
            self.resize(1200, 760)

            central = QWidget()
            self.setCentralWidget(central)
            root = QHBoxLayout(central)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            # Sidebar
            sidebar = QWidget()
            sidebar.setFixedWidth(C["sidebar_w"])
            sidebar.setStyleSheet(f"QWidget {{ background-color: {C['bg_sidebar']}; border-right: 1px solid {C['border']}; }}")
            sb_layout = QVBoxLayout(sidebar)
            sb_layout.setContentsMargins(0, 0, 0, 0)
            sb_layout.setSpacing(0)

            # Logo
            logo_container = QWidget()
            logo_container.setFixedHeight(64)
            logo_container.setStyleSheet(f"background-color: {C['bg_sidebar']};")
            logo_layout = QHBoxLayout(logo_container)
            logo_layout.setContentsMargins(16, 0, 16, 0)
            logo_layout.setSpacing(10)

            logo_icon = QLabel("A")
            logo_icon.setFont(QFont("Sans Serif", 20, QFont.Weight.Bold))
            logo_icon.setFixedSize(32, 32)
            logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_icon.setStyleSheet(f"color: {C['bg']}; background-color: {C['accent']}; border-radius: 8px;")
            logo_layout.addWidget(logo_icon, 0, Qt.AlignmentFlag.AlignVCenter)

            logo_text = QLabel("Anything")
            logo_text.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
            logo_text.setStyleSheet(f"color: {C['text']}; background: transparent;")
            logo_layout.addWidget(logo_text, 0, Qt.AlignmentFlag.AlignVCenter)
            logo_layout.addStretch()

            sb_layout.addWidget(logo_container)

            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background-color: {C['border']};")
            sb_layout.addWidget(sep)
            sb_layout.addSpacing(8)

            nav_items = [
                ("\u2699\uFE0F", "Install"),
                ("\u270E\uFE0F", "Manage"),
                ("\U0001F4DC", "Log"),
            ]
            self.page_buttons = []
            for i, (icon, label) in enumerate(nav_items):
                btn = SideButton(icon, label)
                btn.clicked.connect(lambda idx=i: self._set_active_page(idx))
                sb_layout.addWidget(btn)
                self.page_buttons.append(btn)

            sb_layout.addSpacing(8)

            sep2 = QFrame()
            sep2.setFixedHeight(1)
            sep2.setStyleSheet(f"background-color: {C['border']};")
            sb_layout.addWidget(sep2)
            sb_layout.addStretch()

            stats_container = QWidget()
            stats_container.setStyleSheet(f"background-color: {C['bg_card']}; border-radius: 8px; margin: 8px;")
            stats_layout = QVBoxLayout(stats_container)
            stats_layout.setContentsMargins(12, 10, 12, 10)
            stats_layout.setSpacing(4)

            pkg_count = len(self.installer.get_all_packages())
            cat_count = len([c for c in self.installer.get_categories() if c.get("packages")])

            stats_title = QLabel(f"{pkg_count} packages")
            stats_title.setFont(QFont("Sans Serif", 11, QFont.Weight.Bold))
            stats_title.setStyleSheet(f"color: {C['text']}; background: transparent;")
            stats_layout.addWidget(stats_title)

            stats_sub = QLabel(f"{cat_count} categories  \u00B7  {self.installer.platform_key}")
            stats_sub.setStyleSheet(f"color: {C['text_muted']}; font-size: 10px; background: transparent;")
            stats_layout.addWidget(stats_sub)

            sb_layout.addWidget(stats_container)

            root.addWidget(sidebar)

            # Main content
            content = QWidget()
            content.setStyleSheet(f"background-color: {C['bg']};")
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(20, 16, 20, 12)
            content_layout.setSpacing(10)

            header_row = QHBoxLayout()
            header_row.setSpacing(12)
            self.page_title = QLabel("Install Packages")
            self.page_title.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
            self.page_title.setStyleSheet(f"color: {C['text']};")
            header_row.addWidget(self.page_title)
            header_row.addStretch()

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("\U0001F50D Search...")
            self.search_input.setFixedWidth(220)
            self.search_input.setFixedHeight(34)
            self.search_input.textChanged.connect(self._filter_packages)
            header_row.addWidget(self.search_input)

            self.platform_filter = QComboBox()
            self.platform_filter.setFixedHeight(34)
            self.platform_filter.setFixedWidth(110)
            self.platform_filter.addItem("All", "all")
            self.platform_filter.addItem("Linux", "linux")
            self.platform_filter.addItem("macOS", "darwin")
            self.platform_filter.addItem("Windows", "win32")
            self.platform_filter.currentIndexChanged.connect(self._filter_packages)
            header_row.addWidget(self.platform_filter)

            content_layout.addLayout(header_row)

            self.stack = QStackedWidget()
            self.stack.addWidget(self._build_install_page())
            self.stack.addWidget(self._build_manage_page())
            self.stack.addWidget(self._build_log_page())
            content_layout.addWidget(self.stack, 1)

            bb = QWidget()
            bb.setFixedHeight(52)
            bb.setStyleSheet(f"QWidget {{ background-color: {C['bg']}; border-top: 1px solid {C['border']}; }}")
            bb_layout = QHBoxLayout(bb)
            bb_layout.setContentsMargins(0, 0, 0, 0)
            bb_layout.setSpacing(8)

            self.btn_install = QPushButton("\u25B6  Install Selected")
            self.btn_install.setFixedHeight(38)
            self.btn_install.setMinimumWidth(170)
            self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_install.setFont(QFont("Sans Serif", 11, QFont.Weight.Bold))
            self.btn_install.setStyleSheet(f"QPushButton {{ background-color: {C['accent']}; color: {C['bg']}; border: none; border-radius: 8px; padding: 0 20px; }} QPushButton:hover {{ background-color: {C['accent_hover']}; }} QPushButton:disabled {{ background-color: {C['border']}; color: {C['text_muted']}; }}")
            self.btn_install.clicked.connect(self._start_install)
            bb_layout.addWidget(self.btn_install)

            for text, func in [("Select All", self._select_all), ("Deselect All", self._deselect_all)]:
                b = QPushButton(text)
                b.setFixedHeight(34)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setStyleSheet(f"QPushButton {{ background: transparent; color: {C['text_dim']}; border: 1px solid {C['border']}; border-radius: 6px; padding: 0 12px; }} QPushButton:hover {{ color: {C['text']}; border-color: {C['accent']}; }}")
                b.clicked.connect(func)
                bb_layout.addWidget(b)

            bb_layout.addStretch()

            self.progress_bar = QProgressBar()
            self.progress_bar.setFixedHeight(20)
            self.progress_bar.setFixedWidth(200)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            bb_layout.addWidget(self.progress_bar)

            self.status_label = QLabel("Ready")
            self.status_label.setStyleSheet(f"color: {C['text_muted']}; font-size: 12px;")
            bb_layout.addWidget(self.status_label)

            content_layout.addWidget(bb)
            root.addWidget(content, 1)

        def _build_install_page(self):
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            self.left_container = QWidget()
            self.left_layout = QVBoxLayout(self.left_container)
            self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.left_layout.setSpacing(12)
            self.left_layout.setContentsMargins(0, 0, 6, 0)

            self.right_container = QWidget()
            self.right_layout = QVBoxLayout(self.right_container)
            self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.right_layout.setSpacing(12)
            self.right_layout.setContentsMargins(6, 0, 0, 0)

            left_scroll = QScrollArea()
            left_scroll.setWidgetResizable(True)
            left_scroll.setFrameShape(QFrame.Shape.NoFrame)
            left_scroll.setWidget(self.left_container)

            right_scroll = QScrollArea()
            right_scroll.setWidgetResizable(True)
            right_scroll.setFrameShape(QFrame.Shape.NoFrame)
            right_scroll.setWidget(self.right_container)

            self._sync_scroll(left_scroll, right_scroll)

            splitter = QSplitter(Qt.Orientation.Horizontal)
            splitter.addWidget(left_scroll)
            splitter.addWidget(right_scroll)
            splitter.setSizes([50, 50])
            splitter.setHandleWidth(2)
            layout.addWidget(splitter)

            return widget

        def _sync_scroll(self, s1, s2):
            syncing = [False]
            def on_s1(val):
                if not syncing[0]:
                    syncing[0] = True
                    s2.verticalScrollBar().setValue(val)
                    syncing[0] = False
            def on_s2(val):
                if not syncing[0]:
                    syncing[0] = True
                    s1.verticalScrollBar().setValue(val)
                    syncing[0] = False
            s1.verticalScrollBar().valueChanged.connect(on_s1)
            s2.verticalScrollBar().valueChanged.connect(on_s2)

        def _build_manage_page(self):
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)

            buttons = [
                ("+ Add Package", C['accent'], self._add_package),
                ("+ Add Category", C['purple'], self._add_category),
                ("Edit", C['orange'], self._edit_package),
                ("Delete", C['red'], self._remove_package),
                ("\u21BB Reload", None, self._reload_manage),
            ]
            for text, color, func in buttons:
                b = QPushButton(text)
                b.setFixedHeight(36)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                if color:
                    b.setStyleSheet(f"QPushButton {{ background-color: {color}; color: {C['bg']}; border: none; border-radius: 6px; padding: 0 14px; font-weight: bold; }} QPushButton:hover {{ opacity: 0.8; }}")
                else:
                    b.setStyleSheet(f"QPushButton {{ background: transparent; color: {C['text_dim']}; border: 1px solid {C['border']}; border-radius: 6px; padding: 0 14px; }} QPushButton:hover {{ color: {C['text']}; border-color: {C['accent']}; }}")
                b.clicked.connect(func)
                btn_row.addWidget(b)

            btn_row.addStretch()
            layout.addLayout(btn_row)

            self.manage_tree = QTreeWidget()
            self.manage_tree.setHeaderLabels(["ID", "Name", "Description", "Category", "Status"])
            self.manage_tree.setColumnWidth(0, 120)
            self.manage_tree.setColumnWidth(1, 150)
            self.manage_tree.setColumnWidth(2, 280)
            self.manage_tree.setColumnWidth(3, 110)
            self.manage_tree.setColumnWidth(4, 80)
            self.manage_tree.setAlternatingRowColors(True)
            self.manage_tree.setRootIsDecorated(False)
            self.manage_tree.itemDoubleClicked.connect(self._edit_package)
            layout.addWidget(self.manage_tree, 1)
            self._reload_manage()
            return widget

        def _build_log_page(self):
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            layout.addWidget(self.log_text, 1)

            btn_clear = QPushButton("Clear Log")
            btn_clear.setFixedHeight(32)
            btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_clear.setStyleSheet(f"QPushButton {{ background: transparent; color: {C['text_dim']}; border: 1px solid {C['border']}; border-radius: 6px; padding: 0 14px; }} QPushButton:hover {{ color: {C['text']}; border-color: {C['accent']}; }}")
            btn_clear.clicked.connect(self.log_text.clear)
            row = QHBoxLayout()
            row.addStretch()
            row.addWidget(btn_clear)
            layout.addLayout(row)
            return widget

        def _set_active_page(self, idx):
            self.current_page = idx
            self.stack.setCurrentIndex(idx)
            titles = ["Install Packages", "Manage Packages", "Install Log"]
            self.page_title.setText(titles[idx])
            for i, btn in enumerate(self.page_buttons):
                btn.set_active(i == idx)
            self.search_input.setVisible(idx == 0)
            self.platform_filter.setVisible(idx == 0)

        def _load_packages(self):
            for lay in [self.left_layout, self.right_layout]:
                while lay.count():
                    item = lay.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                    elif item.layout():
                        while item.layout().count():
                            sub = item.layout().takeAt(0)
                            if sub.widget():
                                sub.widget().setParent(None)

            self.cards.clear()

            categories = [c for c in self.installer.get_categories() if c.get("packages")]
            mid = (len(categories) + 1) // 2

            for idx, cat in enumerate(categories):
                packages = cat.get("packages", [])
                cat_group = self._make_category_group(cat)
                target = self.left_layout if idx < mid else self.right_layout
                target.addWidget(cat_group)

            self._update_status()

        def _make_category_group(self, cat):
            packages = cat.get("packages", [])
            cat_group = QGroupBox(f"  {cat['name']}  ({len(packages)})")
            cat_group.setFont(QFont("Sans Serif", 12, QFont.Weight.Bold))
            cat_group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 1px solid {C['border']};
                    border-radius: 8px;
                    margin-top: 14px;
                    padding: 18px 8px 8px 8px;
                    color: {C['accent']};
                    background-color: transparent;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 6px;
                }}
            """)
            cat_layout = QVBoxLayout()
            cat_layout.setSpacing(4)
            for pkg in packages:
                installed = self.installer.is_installed(pkg["id"])
                card = PackageCard(pkg, installed)
                card.checkbox.setChecked(False)
                self.cards[pkg["id"]] = card
                cat_layout.addWidget(card)
            cat_group.setLayout(cat_layout)
            return cat_group

        def _filter_packages(self):
            query = self.search_input.text().strip().lower()
            plat_filter = self.platform_filter.currentData()

            for lay in [self.left_layout, self.right_layout]:
                for i in range(lay.count()):
                    item = lay.itemAt(i)
                    if not item:
                        continue
                    group = item.widget()
                    if not group or not isinstance(group, QGroupBox):
                        continue
                    vis = 0
                    cl = group.layout()
                    if not cl:
                        continue
                    for j in range(cl.count()):
                        ci = cl.itemAt(j)
                        if not ci:
                            continue
                        card = ci.widget()
                        if not card or not isinstance(card, PackageCard):
                            continue
                        pkg = card.pkg
                        mq = not query or query in pkg["name"].lower() or query in pkg["id"].lower() or query in pkg.get("description", "").lower()
                        mp = plat_filter == "all" or plat_filter in pkg.get("install", {})
                        show = mq and mp
                        card.setVisible(show)
                        if show:
                            vis += 1
                    base = group.title().split("(")[0].strip()
                    group.setTitle(f"  {base}  ({vis})")
                    group.setVisible(vis > 0)

        def _update_status(self):
            total = len(self.cards)
            sel = sum(1 for c in self.cards.values() if c.isChecked())
            self.status_label.setText(f"Selected: {sel}/{total}")

        def _select_all(self):
            for c in self.cards.values():
                if c.isVisible():
                    c.setChecked(True)
            self._update_status()

        def _deselect_all(self):
            for c in self.cards.values():
                if c.isVisible():
                    c.setChecked(False)
            self._update_status()

        def _start_install(self):
            selected = [pid for pid, card in self.cards.items() if card.isChecked()]
            if not selected:
                QMessageBox.information(self, "Notice", "Select at least one package!")
                return

            sudo_needed = self.installer.needs_sudo_for_packages(selected)
            if sudo_needed:
                has_nopasswd = self.installer.check_sudo()
                if not has_nopasswd:
                    msg = (
                        "Some packages require root privileges (sudo).\n\n"
                        "Packages needing sudo:\n"
                        + "\n".join(f"  - {name}" for name in sudo_needed[:10])
                        + (f"\n  ... and {len(sudo_needed)-10} more" if len(sudo_needed) > 10 else "")
                        + "\n\nEnter your sudo password to continue:"
                    )
                    password, ok = QInputDialog.getText(
                        self, "Sudo Password Required", msg,
                        QLineEdit.EchoMode.Password,
                    )
                    if not ok or not password:
                        QMessageBox.warning(self, "Cancelled", "Installation cancelled — sudo password is required.")
                        return
                    self.installer.set_sudo_password(password)
                else:
                    self._log("[INFO] Passwordless sudo detected, proceeding...")

            reply = QMessageBox.question(
                self, "Confirm",
                f"Install {len(selected)} package(s)?\n\n{', '.join(selected[:12])}{'...' if len(selected) > 12 else ''}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.btn_install.setEnabled(False)
            self.progress_bar.setValue(0)
            self._set_active_page(2)
            self.log_text.clear()
            self._log(f"[START] Installing {len(selected)} package(s)...")
            self.install_thread = InstallThread(self.installer, selected)
            self.install_thread.progress.connect(self._on_install_progress)
            self.install_thread.finished_signal.connect(self._on_install_done)
            self.install_thread.start()

        def _on_install_progress(self, percent, message):
            if percent >= 0:
                self.progress_bar.setValue(percent)
            self._log(message)

        def _on_install_done(self, success):
            self.btn_install.setEnabled(True)
            if success:
                self.progress_bar.setValue(100)
                self._log("\n[DONE] All packages installed successfully!")
                self.status_label.setText("All installed!")
            else:
                self._log("\n[DONE] Some packages failed, check log.")
                self.status_label.setText("Failed - check log!")
            self._load_packages()

        def _log(self, msg):
            self.log_text.append(msg)
            self.log_text.moveCursor(QTextCursor.MoveOperation.End)

        def _reload_manage(self):
            self.manage_tree.clear()
            for cat in self.installer.get_categories():
                ci = QTreeWidgetItem([cat["name"], "", "", "", ""])
                ci.setFont(0, QFont("Sans Serif", 11, QFont.Weight.Bold))
                ci.setBackground(0, QColor(C["bg_card_alt"]))
                ci.setForeground(0, QColor(C["accent"]))
                self.manage_tree.addTopLevelItem(ci)
                for pkg in cat.get("packages", []):
                    installed = self.installer.is_installed(pkg["id"])
                    ch = QTreeWidgetItem([
                        pkg.get("id", ""),
                        pkg.get("name", ""),
                        pkg.get("description", ""),
                        cat["name"],
                        "\u2713 Yes" if installed else "\u2717 No",
                    ])
                    ch.setForeground(4, QColor(C["green"] if installed else C["red"]))
                    ci.addChild(ch)
                ci.setExpanded(True)

        def _add_package(self):
            dlg = ManagePackageDialog(self.installer, self)
            dlg.saved.connect(self._on_manage_changed)
            dlg.show()

        def _add_category(self):
            name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
            if ok and name.strip():
                cat_id = name.strip().lower().replace(" ", "_")
                if not self.installer.add_category(cat_id, name.strip()):
                    QMessageBox.warning(self, "Error", "Category already exists!")
                else:
                    self._on_manage_changed()

        def _edit_package(self):
            item = self.manage_tree.currentItem()
            if item is None or item.parent() is None:
                QMessageBox.information(self, "Notice", "Select a package to edit!")
                return
            pkg = self.installer.get_package(item.text(0))
            if pkg:
                dlg = ManagePackageDialog(self.installer, self, edit_pkg=pkg)
                dlg.saved.connect(self._on_manage_changed)
                dlg.show()

        def _remove_package(self):
            item = self.manage_tree.currentItem()
            if item is None or item.parent() is None:
                QMessageBox.information(self, "Notice", "Select a package to delete!")
                return
            reply = QMessageBox.question(
                self, "Confirm",
                f"Delete '{item.text(1)}' ({item.text(0)})?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.installer.remove_package(item.text(0))
                self._on_manage_changed()

        def _on_manage_changed(self):
            self.installer = Installer()
            self._reload_manage()
            self._load_packages()

        def closeEvent(self, event):
            if self.install_thread and self.install_thread.isRunning():
                reply = QMessageBox.question(
                    self, "Confirm",
                    "Install still running. Quit anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
                self.install_thread.stop()
                self.install_thread.wait(3000)
            event.accept()

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    app.exec()


def main():
    if is_termux():
        run_cli_mode()
    else:
        run_gui_mode()


if __name__ == "__main__":
    main()
