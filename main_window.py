from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QLabel, QLineEdit, QWidget, QComboBox, QCheckBox
)
from qasync import asyncSlot
from ble_manager import BLEManager
import asyncio


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLE Direct Connect")
        self.setGeometry(100, 100, 400, 400)

        # Status-Label
        self.status_label = QLabel("Status: Nicht verbunden", self)

        # Verbindung und Trennen Buttons
        self.connect_button = QPushButton("Verbinden", self)
        self.disconnect_button = QPushButton("Trennen", self)
        self.disconnect_button.setEnabled(False)

        # Lesen-Button und Ausgabe
        self.read_button = QPushButton("Lesen", self)
        self.read_button.setEnabled(False)
        self.value_label = QLabel("Gelesener Wert: -", self)

        # Schreiben Textbox und Button
        self.write_input = QLineEdit(self)
        self.write_input.setPlaceholderText("Daten zum Schreiben eingeben")
        self.write_button = QPushButton("Schreiben", self)
        self.write_button.setEnabled(False)

        # Loop-Steuerung
        self.loop_checkbox = QCheckBox("Loop aktivieren", self)
        self.loop_rate_dropdown = QComboBox(self)
        self.loop_rate_dropdown.addItems(["1 Hz", "5 Hz", "10 Hz"])  # Abtastraten
        self.start_loop_button = QPushButton("Start Loop", self)
        self.stop_loop_button = QPushButton("Stop Loop", self)
        self.start_loop_button.setEnabled(False)
        self.stop_loop_button.setEnabled(False)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(self.read_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.write_input)
        layout.addWidget(self.write_button)
        layout.addWidget(self.loop_checkbox)
        layout.addWidget(self.loop_rate_dropdown)
        layout.addWidget(self.start_loop_button)
        layout.addWidget(self.stop_loop_button)

        # Container
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # BLE Manager
        self.ble_manager = BLEManager()

        # Loop Steuerung
        self.loop_task = None
        self.loop_active = False

        # Events
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.read_button.clicked.connect(self.read_characteristic)
        self.write_button.clicked.connect(self.write_characteristic)
        self.start_loop_button.clicked.connect(self.start_loop)
        self.stop_loop_button.clicked.connect(self.stop_loop)

    @asyncSlot()
    async def connect_device(self):
        """Verbindet sich mit dem BLE-Gerät."""
        self.status_label.setText("Status: Scanne...")
        try:
            await self.ble_manager.find_and_connect()
            self.status_label.setText("Status: Verbunden")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.read_button.setEnabled(True)
            self.write_button.setEnabled(True)
            self.start_loop_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Status: Fehler - {str(e)}")

    @asyncSlot()
    async def disconnect_device(self):
        """Trennt die Verbindung zum BLE-Gerät."""
        self.status_label.setText("Status: Trenne Verbindung...")
        try:
            await self.ble_manager.disconnect()
            self.status_label.setText("Status: Nicht verbunden")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.read_button.setEnabled(False)
            self.write_button.setEnabled(False)
            self.start_loop_button.setEnabled(False)
            self.stop_loop_button.setEnabled(False)
            self.value_label.setText("Gelesener Wert: -")
        except Exception as e:
            self.status_label.setText(f"Status: Fehler - {str(e)}")

    @asyncSlot()
    async def read_characteristic(self):
        """Liest die Ziel-Charakteristik."""
        self.status_label.setText("Status: Lese...")
        try:
            value = await self.ble_manager.read_characteristic()
            self.value_label.setText(f"Gelesener Wert: {value}")
            self.status_label.setText("Status: Fertig")
        except Exception as e:
            self.status_label.setText(f"Status: Fehler - {str(e)}")

    @asyncSlot()
    async def write_characteristic(self):
        """Schreibt Daten in die Ziel-Charakteristik."""
        self.status_label.setText("Status: Schreiben...")
        data = self.write_input.text()
        if not data:
            self.status_label.setText("Status: Fehler - Kein Eingabetext")
            return
        try:
            await self.ble_manager.write_characteristic(data)
            self.status_label.setText("Status: Schreiben abgeschlossen")
        except Exception as e:
            self.status_label.setText(f"Status: Fehler - {str(e)}")

    def get_loop_interval(self):
        """Gibt das Loop-Intervall basierend auf der Dropdown-Auswahl zurück."""
        rate = self.loop_rate_dropdown.currentText()
        if rate == "1 Hz":
            return 1.0
        elif rate == "5 Hz":
            return 0.2
        elif rate == "10 Hz":
            return 0.1
        return 1.0

    async def loop_operation(self):
        """Führt den Loop-Betrieb aus."""
        while self.loop_active:
            try:
                if self.loop_checkbox.isChecked():
                    # Lesen
                    value = await self.ble_manager.read_characteristic()
                    if value:
                        self.value_label.setText(f"Gelesener Wert: {value}")

                    # Schreiben
                    data = self.write_input.text()
                    await self.ble_manager.write_characteristic(data)

                await asyncio.sleep(self.get_loop_interval())
            except asyncio.CancelledError:
                self.status_label.setText("Loop gestoppt.")
                break
            except Exception as e:
                self.status_label.setText(f"Loop Fehler - {str(e)}")
                self.loop_active = False

    @asyncSlot()
    async def start_loop(self):
        """Startet den Loop."""
        if self.loop_task and not self.loop_task.done():
            return
            
        self.loop_active = True
        self.stop_loop_button.setEnabled(True)
        self.start_loop_button.setEnabled(False)
        self.loop_task = asyncio.create_task(self.loop_operation())

    @asyncSlot()
    async def stop_loop(self):
        """Stoppt den Loop."""
        self.loop_active = False
        if self.loop_task:
            self.loop_task.cancel()
            await self.loop_task  # Ensure the task is awaited properly
        self.stop_loop_button.setEnabled(False)
        self.start_loop_button.setEnabled(True)

    def closeEvent(self, event):
        """Trennt die BLE-Verbindung beim Schließen der Anwendung."""
        self.loop_active = False
        if self.ble_manager.client:
            loop = asyncio.get_event_loop()
            loop.create_task(self.ble_manager.disconnect())
        event.accept()
