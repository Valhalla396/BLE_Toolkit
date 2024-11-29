import sys
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from main_window import MainWindow  # Import der GUI-Klasse

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        sys.exit(loop.run_forever())