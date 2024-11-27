from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget, QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QMessageBox, QGroupBox
)
from qasync import asyncSlot
from ble_manager import BLEManager
import asyncio


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLE Direct Connect")
        self.setGeometry(100, 100, 600, 500)

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

        # Charakteristiken Baum
        self.characteristics_tree = QTreeWidget(self)
        self.characteristics_tree.setHeaderLabels(["UUID", "Eigenschaften"])
        self.characteristics_tree.setSelectionMode(QTreeWidget.MultiSelection)

        # Layouts
        main_layout = QVBoxLayout()
        connection_layout = QHBoxLayout()
        read_write_layout = QHBoxLayout()
        loop_layout = QHBoxLayout()
        characteristics_layout = QVBoxLayout()

        # Connection Group
        connection_group = QGroupBox("Verbindung")
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.disconnect_button)
        connection_group.setLayout(connection_layout)

        # Read/Write Group
        read_write_group = QGroupBox("Lesen/Schreiben")
        read_write_layout.addWidget(self.read_button)
        read_write_layout.addWidget(self.value_label)
        read_write_layout.addWidget(self.write_input)
        read_write_layout.addWidget(self.write_button)
        read_write_group.setLayout(read_write_layout)

        # Loop Group
        loop_group = QGroupBox("Loop-Steuerung")
        loop_layout.addWidget(self.loop_checkbox)
        loop_layout.addWidget(self.loop_rate_dropdown)
        loop_layout.addWidget(self.start_loop_button)
        loop_layout.addWidget(self.stop_loop_button)
        loop_group.setLayout(loop_layout)

        # Characteristics Group
        characteristics_group = QGroupBox("Charakteristiken")
        characteristics_layout.addWidget(self.characteristics_tree)
        characteristics_group.setLayout(characteristics_layout)

        # Main Layout
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(connection_group)
        main_layout.addWidget(read_write_group)
        main_layout.addWidget(loop_group)
        main_layout.addWidget(characteristics_group)

        # Container
        container = QWidget()
        container.setLayout(main_layout)
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
            await self.scan_characteristics()
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
        """Liest die ausgewählte Charakteristik."""
        self.status_label.setText("Status: Lese...")
        selected_items = self.characteristics_tree.selectedItems()
        if not selected_items:
            self.status_label.setText("Status: Fehler - Keine Charakteristik ausgewählt")
            return
        try:
            for item in selected_items:
                char = item.data(0, 1)
                if 'read' in char.properties:
                    value = await self.ble_manager.read_characteristic(char.uuid)
                    self.value_label.setText(f"Gelesener Wert: {value}")
            self.status_label.setText("Status: Fertig")
        except Exception as e:
            self.status_label.setText(f"Status: Fehler - {str(e)}")

    @asyncSlot()
    async def write_characteristic(self):
        """Schreibt Daten in die ausgewählte Charakteristik."""
        self.status_label.setText("Status: Schreiben...")
        data = self.write_input.text()
        if not data:
            self.status_label.setText("Status: Fehler - Kein Eingabetext")
            return
        selected_items = self.characteristics_tree.selectedItems()
        if not selected_items:
            self.status_label.setText("Status: Fehler - Keine Charakteristik ausgewählt")
            return
        try:
            for item in selected_items:
                char = item.data(0, 1)
                if 'write' in char.properties:
                    await self.ble_manager.write_characteristic(char.uuid, data)
            self.status_label.setText("Status: Schreiben abgeschlossen")
        except Exception as e:
            self.status_label.setText(f"Status: Fehler - {str(e)}")

    @asyncSlot()
    async def scan_characteristics(self):
        """Scannt und zeigt verfügbare Charakteristiken an."""
        self.characteristics_tree.clear()
        try:
            characteristics = await self.ble_manager.get_characteristics()
            for char in characteristics:
                item = QTreeWidgetItem([char.uuid, ', '.join(char.properties)])
                item.setData(0, 1, char)
                self.characteristics_tree.addTopLevelItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Scannen der Charakteristiken: {str(e)}")

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
                    selected_items = self.characteristics_tree.selectedItems()
                    for item in selected_items:
                        char = item.data(0, 1)
                        if 'read' in char.properties:
                            value = await self.ble_manager.read_characteristic(char.uuid)
                            if value:
                                self.value_label.setText(f"Gelesener Wert: {value}")
                        if 'write' in char.properties:
                            data = self.write_input.text()
                            await self.ble_manager.write_characteristic(char.uuid, data)

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
