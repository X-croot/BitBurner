def dark_qss():
    return """
    QMainWindow, QWidget { background:#0f1117; }
    QLabel { color:#e6e9f2; font-size:14px; }
    QLabel.h1 { font-size:26px; font-weight:900; color:#f3f6ff; }
    QLabel.muted { color:#9aa5bd; }
    QFrame#card { background:#121621; border:1px solid #22293a; border-radius:18px; }
    QTableWidget {
        background:#141a25; color:#e6e9f2; border:1px solid #22293a; border-radius:14px; padding:2px;
        gridline-color:#263044; alternate-background-color:#0f141e;
    }
    QHeaderView::section {
        background:#121826; color:#aeb8cc; padding:10px 8px; border:none; border-bottom:1px solid #1e2435;
    }
    QTableWidget::item { selection-background-color:#203054; selection-color:#e8eefc; }
    QLineEdit, QComboBox, QTextEdit, QListView, QTreeView, QAbstractItemView, QSpinBox {
        background:#141a25; color:#e6e9f2; border:1px solid #22293a; border-radius:12px; padding:8px;
        selection-background-color:#2f76ff; selection-color:#0c0e12;
    }
    QProgressBar {
        background:#101420; border:1px solid #22293a; border-radius:12px; text-align:center; color:#d1d9ea; height:20px;
    }
    QProgressBar::chunk {
        border-radius:12px;
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #27d0a5, stop:1 #00ffa3);
    }
    QPushButton {
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1f6feb, stop:1 #5a8cff);
        color:white; border:none; border-radius:14px; padding:10px 18px; font-weight:700;
    }
    QPushButton[secondary="true"] {
        background:#171d2a; border:1px solid #2a3144; color:#d7def0; font-weight:600;
    }
    QPushButton:disabled { background:#141a25; color:#7e879b; border:1px solid #21283a; }
    QPushButton:hover { filter:brightness(112%); }
    QPushButton:pressed { transform:scale(0.985); }
    QToolTip { background:#151a26; color:#e6e9f2; border:1px solid #2a3144; }
    QScrollBar:vertical { background:#0f1117; width:10px; margin:0; }
    QScrollBar::handle:vertical { background:#2a3144; border-radius:5px; min-height:20px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
    QFrame#dropzone { border:1px dashed #3a4a7a; border-radius:18px; }
    QFileDialog QWidget { background:#101520; }
    QFileDialog QTreeView::item, QFileDialog QListView::item { padding:6px; border-radius:8px; }
    QFileDialog QTreeView::item:selected, QFileDialog QListView::item:selected { background:#203054; color:#e8eefc; }
    """
