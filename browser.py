import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        # --- REVISED: Standard Window Flags ---
        # Removing FramelessWindowHint restores the native OS titlebar and resizing
        self.setWindowTitle("Codealot Browser")

        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Enable Modern Web Features ---
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        #settings.setAttribute(QWebEngineSettings.ServiceWorkersEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)           # Crucial for modern UI
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        # Tells the website to use its own Dark Mode if it has one
        settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, True)
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--force-dark-mode --enable-features=WebContentsForceDark"

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

        self.add_new_tab(QUrl('https://google.com'), 'Google')
        self.showMaximized()

        # --- Global Engine Fixes ---
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)

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
        
        # Set a very modern User Agent (2026 Chrome)
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        browser.page().profile().setHttpUserAgent(ua)
        
        # Enable persistent cookies (helps with logins)
        browser.page().profile().setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        
        browser.setUrl(qurl)
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

    # REVISED: Removed custom resizeEvent, mouseMoveEvent, and mousePressEvent 
    # as the OS now handles these automatically with the titlebar restored.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())