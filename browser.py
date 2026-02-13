import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        # --- FIX: Enable Frameless Window ---
        # This removes the OS title bar so your custom buttons become the primary ones
        self.setWindowFlags(Qt.FramelessWindowHint)
        

        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setWindowTitle("Codealot Browser")

        # --- 1. Tab Widget ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.setFixedHeight(35) 
        
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; } 
            QTabBar::tab { 
                padding: 6px 20px; color: white; background-color: #101010;
                border-radius: 12px;
                margin:5px;
            }
                                
            QTabBar::tab:selected { background: transparent; }
            QTabBar { qproperty-drawBase: 0; outline: none; border: none; background: #1a1a1a; }
            QTabBar::close-button {
                background-color: #932a3c;
                padding-left:2px;
                border-radius:4px;
                margin:2px;
            }
            QTabBar::close-button:hover {
                background: #e74c3c;
                border-radius: 4px;
            }
        """)

        # Tab Close Button Hover Logic
        self.tabs.setStyleSheet(self.tabs.styleSheet() + """
            QTabBar::close-button { width: 0px; }
            QTabBar::tab:hover QTabBar::close-button { width: 16px; }
            QTabWidget::right-corner { top: 0px; right: 0px; }
        """)

        # --- 2. Navbar ---
        self.navbar = QToolBar()
        self.navbar.setMovable(False)
        self.navbar.setStyleSheet("QToolBar { background: #1a1a1a; border: none; padding: 5px; }")

        # --- 3. Browser Stack ---
        self.browser_stack = QStackedWidget()

        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.navbar)
        self.main_layout.addWidget(self.browser_stack)

        # Actions
        self.add_nav_action(self.style().standardIcon(QStyle.SP_ArrowLeft), "Back", lambda: self.current_browser().back())
        self.add_nav_action(self.style().standardIcon(QStyle.SP_ArrowRight), "Forward", lambda: self.current_browser().forward())
        self.add_nav_action(QIcon.fromTheme("view-refresh"), "Refresh", lambda: self.current_browser().reload())
        self.add_nav_action(QIcon.fromTheme('go-home'), 'Home', self.navigate_home)

        self.searchBar = QLineEdit()
        self.searchBar.returnPressed.connect(self.loadUrl)
        self.searchBar.setStyleSheet("""
            QLineEdit { border-radius: 15px; padding: 5px 15px; background-color: #2b2b2b; color: white; border: 1px solid #3d3d3d; }
            QLineEdit:focus { border: 1px solid #3498db; }
        """)
        self.navbar.addWidget(self.searchBar)

        # New Tab Button
        self.new_tab_btn = QToolButton(self.tabs)
        self.new_tab_btn.setText("+")
        self.new_tab_btn.setFixedSize(28, 28)
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        self.new_tab_btn.setStyleSheet("border: none; background: none; color: white; font-size: 18px;")
        self.tabs.tabBar().installEventFilter(self)

        # Sync Signals
        self.tabs.currentChanged.connect(self.sync_tab_with_browser)

        # --- Window Controls (Floating Overlay) ---
        self.window_controls = QWidget(self) # Parented to 'self' to overlay everything
        self.window_controls.setObjectName("windowControls")
        self.window_controls.setFixedWidth(100)
        self.window_controls.setFixedHeight(35)

        self.controls_layout = QHBoxLayout(self.window_controls)
        self.controls_layout.setContentsMargins(5, 0, 5, 0) 
        self.controls_layout.setSpacing(5)

        self.btn_min = QToolButton()
        self.btn_min.setText("-")
        self.btn_min.clicked.connect(self.showMinimized)

        self.btn_max = QToolButton()
        self.btn_max.setText("▢")
        self.btn_max.clicked.connect(self.toggle_maximize)

        self.btn_close = QToolButton()
        self.btn_close.setText("✕")
        self.btn_close.clicked.connect(self.close)

        for btn in [self.btn_min, self.btn_max, self.btn_close]:
            btn.setFixedSize(22, 22)
            btn.setStyleSheet("""
                QToolButton { 
                    color: white; 
                    border: none; 
                    background: transparent;
                } 
                QToolButton:hover { 
                    background: #3d3d3d; 
                    border-radius: 4px;
                }
            """)
            self.controls_layout.addWidget(btn)
        
        # Specific red hover for close button
        self.btn_close.setStyleSheet(self.btn_close.styleSheet() + "QToolButton:hover { background: #e74c3c; }")

        # Raise the widget so it stays on top of the tabs
        self.window_controls.raise_()

        self.add_new_tab(QUrl('https://google.com'), 'Google')
        self.showMaximized()

        self.setMouseTracking(True)
        self.container.setMouseTracking(True) # Ensure the central widget also tracks\

    # --- Window Dragging Logic (Required for Frameless) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.dragPos)
            event.accept()

    def current_browser(self):
        return self.browser_stack.currentWidget()

    def sync_tab_with_browser(self, i):
        if i == -1: return
        self.browser_stack.setCurrentIndex(i)
        browser = self.browser_stack.widget(i)
        if browser:
            self.searchBar.setText(browser.url().toString())

    def eventFilter(self, obj, event):
        if obj == self.tabs.tabBar() and event.type() == QEvent.Paint:
            if self.tabs.count() > 0:
                last_tab_rect = self.tabs.tabBar().tabRect(self.tabs.count() - 1)
                self.new_tab_btn.move(last_tab_rect.right() + 5, 4)
        return super().eventFilter(obj, event)

    def add_nav_action(self, icon, text, slot):
        action = QAction(icon, text, self)
        action.triggered.connect(slot)
        self.navbar.addAction(action)

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None: qurl = QUrl('https://google.com')
        browser = QWebEngineView()
        browser.setUrl(qurl)
        self.browser_stack.addWidget(browser)
        i = self.tabs.addTab(QWidget(), label) 
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, b=browser: self.update_urlbar(qurl, b))
        browser.loadFinished.connect(lambda _, b=browser: self.tabs.setTabText(self.browser_stack.indexOf(b), b.page().title()))

    def close_current_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)
            w = self.browser_stack.widget(i)
            self.browser_stack.removeWidget(w)
            w.deleteLater()

    def update_urlbar(self, q, browser=None):
        if browser == self.current_browser():
            self.searchBar.setText(q.toString())

    def loadUrl(self):
        text = self.searchBar.text().strip()
        if "." in text and " " not in text:
            url = QUrl(text) if "://" in text else QUrl("https://" + text)
        else:
            url = QUrl(f"https://www.google.com/search?q={text.replace(' ', '+')}")
        self.current_browser().setUrl(url)

    def navigate_home(self):
        if self.current_browser():
            self.current_browser().setUrl(QUrl('https://google.com'))

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    def resizeEvent(self, event):
        """Keep window controls pinned to the top-right corner."""
        super().resizeEvent(event)
        if hasattr(self, 'window_controls'):
            self.window_controls.move(self.width() - self.window_controls.width(), 0)
    def resizeEvent(self, event):
        """Keep window controls and title label correctly positioned."""
        super().resizeEvent(event)
        
        # Position Window Controls (Top Right)
        if hasattr(self, 'window_controls'):
            self.window_controls.move(self.width() - self.window_controls.width(), 0)
            
        # Position Title Label (Centered)
        if hasattr(self, 'title_label'):
            # Calculate center minus half the label's width
            self.title_label.setFixedWidth(200) # Give it enough space for the text
            self.title_label.move((self.width() - self.title_label.width()) // 2, 0)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # If we are near the edge, the mouseMoveEvent handles the resize
            # Otherwise, we prepare for a window drag
            self.dragPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        margin = 15  # Detection zone size
        rect = self.rect()
        pos = event.pos()
        x, y = pos.x(), pos.y()
        w, h = rect.width(), rect.height()

        # 1. Determine Cursor Shape
        cursor = Qt.ArrowCursor
        
        # Check Corners first
        if x <= margin and y <= margin: cursor = Qt.SizeFDiagCursor    # Top-Left
        elif x >= w - margin and y >= h - margin: cursor = Qt.SizeFDiagCursor # Bottom-Right
        elif x <= margin and y >= h - margin: cursor = Qt.SizeBDiagCursor    # Bottom-Left
        elif x >= w - margin and y <= margin: cursor = Qt.SizeBDiagCursor    # Top-Right
        # Check Sides
        elif x <= margin: cursor = Qt.SizeHorCursor    # Left
        elif x >= w - margin: cursor = Qt.SizeHorCursor # Right
        elif y <= margin: cursor = Qt.SizeVerCursor    # Top
        elif y >= h - margin: cursor = Qt.SizeVerCursor # Bottom
        
        self.setCursor(cursor)

        # 2. Execute Resize or Drag
        if event.buttons() == Qt.LeftButton:
            if cursor != Qt.ArrowCursor:
                # Resize Logic
                prev_geo = self.geometry()
                if cursor == Qt.SizeHorCursor:
                    if x <= margin: # Left side
                        new_w = prev_geo.width() + (prev_geo.x() - event.globalPos().x())
                        self.setGeometry(event.globalPos().x(), prev_geo.y(), new_w, prev_geo.height())
                    else: # Right side
                        self.resize(x, h)
                elif cursor == Qt.SizeVerCursor:
                    if y <= margin: # Top side
                        new_h = prev_geo.height() + (prev_geo.y() - event.globalPos().y())
                        self.setGeometry(prev_geo.x(), event.globalPos().y(), prev_geo.width(), new_h)
                    else: # Bottom side
                        self.resize(w, y)
                elif cursor in [Qt.SizeFDiagCursor, Qt.SizeBDiagCursor]:
                    # For simplicity in frameless, we focus on bottom-right corner resizing
                    # but allow the cursor to show for all
                    self.resize(max(self.minimumWidth(), x), max(self.minimumHeight(), y))
            
            # Drag Logic (Clicking in the Tab/Navbar area)
            elif y < 70: 
                self.move(event.globalPos() - self.dragPos)
        
        event.accept()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())