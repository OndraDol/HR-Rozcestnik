#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrayBookmarks – HR rozcestník v pop-upu z tray ikony
===================================================
• Kliknutím na ikonu „HR“ otevřete a skryjete kompaktní bílé okno se stínem.
• Výška okna se přizpůsobí počtu položek (do 12 bez scrollu).
• Přidávání (+) a mazání (×) odkazů, perzistence do bookmarks.json.
• Ikony: Excel (X zelená), SharePoint (S modrá), ostatní (L šedá).
• UTF-8 podpora české diakritiky.

Spuštění:
```bash
pip install --upgrade PySide6
python tray_bookmarks.py
```
"""
import sys, json, webbrowser
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialog, QDialogButtonBox, QToolButton, QFrame,
    QGraphicsDropShadowEffect, QLineEdit, QMessageBox,
    QSystemTrayIcon, QMenu
)

# ---------- Config ----------
APP_NAME = "TrayBookmarks"
ICON_SIZE = 18
POPUP_WIDTH = 260
ITEM_HEIGHT = 28
MAX_ITEMS = 12
BOOKMARK_FILE = Path(sys.argv[0]).with_name("bookmarks.json")
DEFAULT_BOOKMARKS = [
    {"name": "Vacancies", "url": "https://aaaautoeu.sharepoint.com/...", "type": "excel"},
    {"name": "Docházka",  "url": "https://aaaautoeu.sharepoint.com/...", "type": "excel"},
]

# ---------- Storage ----------
def load_bookmarks():
    if BOOKMARK_FILE.exists():
        try:
            return json.loads(BOOKMARK_FILE.read_text('utf-8'))
        except:
            pass
    save_bookmarks(DEFAULT_BOOKMARKS)
    return DEFAULT_BOOKMARKS.copy()

def save_bookmarks(data):
    BOOKMARK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')

# ---------- Helpers ----------
def detect_type(url: str) -> str:
    u = url.lower()
    if u.endswith(('.xls', '.xlsx')):
        return 'excel'
    if 'sharepoint' in u or 'intranet' in u:
        return 'sharepoint'
    return 'link'

# ---------- Icon Creation ----------
def _make_pix(color: QColor, letter: str) -> QPixmap:
    pix = QPixmap(ICON_SIZE, ICON_SIZE)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
    p.setBrush(color)
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, ICON_SIZE, ICON_SIZE, 3, 3)
    p.setPen(Qt.white)
    f = p.font(); f.setBold(True); f.setPixelSize(int(ICON_SIZE * 0.6)); p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignCenter, letter)
    p.end()
    return pix

def make_icon(kind: str) -> QIcon:
    if kind == 'excel':
        pix = _make_pix(QColor('#1d6f42'), 'X')
    elif kind == 'sharepoint':
        pix = _make_pix(QColor('#0078D4'), 'S')
    else:
        pix = _make_pix(QColor('#888888'), 'L')
    return QIcon(pix)

def make_tray_icon() -> QIcon:
    pix = QPixmap(ICON_SIZE, ICON_SIZE)
    pix.fill(Qt.white)
    p = QPainter(pix)
    p.setPen(QColor('#0078D4'))
    f = p.font(); f.setBold(True); f.setPixelSize(ICON_SIZE // 2); p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignCenter, 'HR')
    p.end()
    return QIcon(pix)

# ---------- Styles ----------
def apply_style(app: QApplication):
    app.setStyleSheet("""
        QWidget { font-family: 'Segoe UI'; font-size: 9pt; }
        QFrame#bg { background: white; border-radius: 6px; }
        QPushButton { border: none; text-align: left; padding: 2px 6px; border-radius: 3px; }
        QPushButton:hover { background: rgba(0,120,212,0.12); }
        QToolButton#x { min-width:16px; max-width:16px; font-weight:bold; color:#c33; background: transparent; border: none; }
        QToolButton#x[hover="false"] { color: transparent; }
        QToolButton { color: #0078D4; background: transparent; }
        QLineEdit { padding: 4px; border: 1px solid #bbb; border-radius: 3px; }
    """)

# ---------- Bookmark Item ----------
class BookmarkItem(QWidget):
    removed = Signal(str)

    def __init__(self, name: str, url: str, kind: str):
        super().__init__()
        self.url = url
        self.setFixedHeight(ITEM_HEIGHT)
        h = QHBoxLayout(self)
        h.setContentsMargins(6, 0, 6, 0)
        h.setSpacing(6)

        h.addWidget(QLabel(pixmap=make_icon(kind).pixmap(ICON_SIZE, ICON_SIZE)))

                # Open URL and hide popup
        btn = QPushButton(name)
        btn.clicked.connect(self._open_url)
        h.addWidget(btn, 1)

        # close button
        x = QToolButton(objectName='x')
        x.setText('×')
        x.setCursor(Qt.PointingHandCursor)
        x.setProperty('hover', False)
        x.clicked.connect(lambda: self.removed.emit(self.url))
        h.addWidget(x)
        self._x = x

    def _open_url(self):
        webbrowser.open(self.url)
        # hide parent popup
        parent = self.window()
        if isinstance(parent, QWidget):
            parent.hide()

    def enterEvent(self, event):
        self._x.setProperty('hover', True)
        self._refresh()

    def leaveEvent(self, event):
        self._x.setProperty('hover', False)
        self._refresh()

    def _refresh(self):
        self._x.style().unpolish(self._x)
        self._x.style().polish(self._x)

# ---------- Add Dialog ----------
class AddDialog(QDialog):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Přidat odkaz'); self.setFixedWidth(280)
        v = QVBoxLayout(self)
        self.name = QLineEdit(); self.name.setPlaceholderText('Název'); v.addWidget(self.name)
        self.url  = QLineEdit(); self.url.setPlaceholderText('URL');  v.addWidget(self.url)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); v.addWidget(bb)
    def get_data(self): return self.name.text().strip(), self.url.text().strip()
    def accept(self):
        if not all(self.get_data()): QMessageBox.warning(self, APP_NAME, 'Vyplň název i URL'); return
        super().accept()

# ---------- Popup ----------
class Popup(QWidget):
    def __init__(self, bookmarks: list[dict]):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.bookmarks = bookmarks
        bg = QFrame(self, objectName='bg')
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(12); shadow.setOffset(0,3); shadow.setColor(QColor(0,0,0,150)); bg.setGraphicsEffect(shadow)
        vb = QVBoxLayout(bg); vb.setContentsMargins(4,4,4,4); vb.setSpacing(2)
        top = QHBoxLayout(); top.addStretch(1)
        plus = QToolButton(text='+'); plus.setCursor(Qt.PointingHandCursor); plus.clicked.connect(self._add); top.addWidget(plus); vb.addLayout(top)
        self.list_layout = QVBoxLayout(); self.list_layout.setSpacing(1); vb.addLayout(self.list_layout)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.addWidget(bg)
        self._refresh()
    def _refresh(self):
        # clear
        while self.list_layout.count(): w=self.list_layout.takeAt(0).widget();
        for bm in self.bookmarks:
            it = BookmarkItem(bm['name'], bm['url'], bm['type']); it.removed.connect(self._remove); self.list_layout.addWidget(it)
        height = 30 + min(len(self.bookmarks), MAX_ITEMS) * ITEM_HEIGHT + 8
        self.setFixedSize(POPUP_WIDTH, height)
    def _add(self):
        dlg = AddDialog()
        if dlg.exec():
            name, url = dlg.get_data()
            self.bookmarks.append({'name': name, 'url': url, 'type': detect_type(url)})
            save_bookmarks(self.bookmarks)
            self._refresh()
    def _remove(self, url):
        self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
        save_bookmarks(self.bookmarks)
        self._refresh()

# ---------- Tray Application ----------
# ---------- Tray Application ----------
class TrayApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        apply_style(self)
        self.setQuitOnLastWindowClosed(False)
        self.bookmarks = load_bookmarks()
        # tray icon setup
        from PySide6.QtGui import QCursor
        self.tray = QSystemTrayIcon(make_tray_icon(), self)
        self.tray.setToolTip(APP_NAME)
        menu = QMenu()
        menu.addAction('Konec', self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.toggle_popup)
        self.tray.show()
        # initial popup
        self.popup = None

    def toggle_popup(self, reason):
        if reason != QSystemTrayIcon.Trigger:
            return
        # hide existing
        if self.popup and self.popup.isVisible():
            self.popup.hide()
            return
        # recreate popup for consistent style
        if self.popup:
            self.popup.deleteLater()
        self.popup = Popup(self.bookmarks)
        # position above tray icon
        rect = self.tray.geometry()
        x = rect.x() + rect.width()/2 - self.popup.width()/2
        y = rect.y() - self.popup.height() - 4
        self.popup.move(int(x), int(y))
        self.popup.show()

# ---------- Main ----------
if __name__ == '__main__':
    TrayApp().exec()
