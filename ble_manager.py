import asyncio
from bleak import BleakScanner, BleakClient
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class BLEManager:
    def __init__(self):
        self.client = None

    async def scan(self):
        devices = await BleakScanner.discover()
        return devices

    async def connect_to_device(self, address):
        self.client = BleakClient(address)
        await self.client.connect()
        print(f"Verbunden mit {address}")
        return self.client

    async def get_characteristics(self):
        """Scannt und gibt verfügbare Charakteristiken zurück."""
        if not self.client:
            raise Exception("Nicht verbunden.")

        services = self.client.services
        if not services:
            await self.client.get_services()
            services = self.client.services

        characteristics = []
        for service in services:
            for char in service.characteristics:
                characteristics.append(char)
        return characteristics

    async def read_characteristic(self, uuid):
        """Liest eine Charakteristik basierend auf der UUID."""
        if not self.client:
            raise Exception("Nicht verbunden.")
        value = await self.client.read_gatt_char(uuid)
        print(f"Debug: Gelesener Wert - {value}")  # Debugging
        return value.decode("utf-8")

    async def write_characteristic(self, uuid, data):
        """Schreibt Daten in eine Charakteristik basierend auf der UUID."""
        if not self.client:
            raise Exception("Nicht verbunden.")
        await self.client.write_gatt_char(uuid, data.encode("utf-8"))
        print(f"Daten geschrieben: {data}")

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            print("Verbindung getrennt.")
            self.client = None
