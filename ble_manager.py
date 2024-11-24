import asyncio
from bleak import BleakScanner, BleakClient, AdvertisementData
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# UUIDs
ADVERTISING_SERVICE_UUID = "c8bac71f-579e-4d69-b18e-83639e15e705"  # UUID im Advertising
TARGET_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"  # Ziel-Service
READ_CHARACTERISTIC_UUID = "abcdef01-1234-5678-1234-56789abcdef0"  # Ziel-Charakteristik (Lesen)
WRITE_CHARACTERISTIC_UUID = "abcdef02-1234-5678-1234-56789abcdef0"  # Ziel-Charakteristik (Schreiben)


class BLEManager:
    def __init__(self):
        self.client = None

    async def find_and_connect(self):
        print("Scanne nach BLE-Geräten...")
        devices = await BleakScanner.discover()

        target_device = None
        for device in devices:
            if ADVERTISING_SERVICE_UUID in device.metadata["uuids"]:
                target_device = device
                print(f"Gerät gefunden: {device.name} - {device.address}")
                break

        if not target_device:
            raise Exception("Kein Gerät mit der beworbenen UUID gefunden.")

        self.client = BleakClient(target_device.address)
        await self.client.connect()
        print(f"Verbunden mit {target_device.name}")
        return self.client

    async def read_characteristic(self):
        if not self.client:
            raise Exception("Nicht verbunden.")

        services = self.client.services
        if not services:
            await self.client.get_services()
            services = self.client.services

        test_service = next((s for s in services if s.uuid == TARGET_SERVICE_UUID), None)
        if not test_service:
            raise Exception(f"Service {TARGET_SERVICE_UUID} nicht gefunden.")

        characteristic = next(
            (c for c in test_service.characteristics if c.uuid == READ_CHARACTERISTIC_UUID), None
        )
        if not characteristic:
            raise Exception(f"Charakteristik {READ_CHARACTERISTIC_UUID} nicht gefunden.")

        if "read" in characteristic.properties:
            value = await self.client.read_gatt_char(characteristic.uuid)
            print(f"Debug: Gelesener Wert - {value}")  # Debugging
            return value.decode("utf-8")
        else:
            raise Exception(f"Charakteristik {READ_CHARACTERISTIC_UUID} ist nicht lesbar.")

    async def write_characteristic(self, data):
        if not self.client:
            raise Exception("Nicht verbunden.")

        services = self.client.services
        if not services:
            await self.client.get_services()
            services = self.client.services

        test_service = next((s for s in services if s.uuid == TARGET_SERVICE_UUID), None)
        if not test_service:
            raise Exception(f"Service {TARGET_SERVICE_UUID} nicht gefunden.")

        characteristic = next(
            (c for c in test_service.characteristics if c.uuid == WRITE_CHARACTERISTIC_UUID), None
        )
        if not characteristic:
            raise Exception(f"Charakteristik {WRITE_CHARACTERISTIC_UUID} nicht gefunden.")

        if "write" in characteristic.properties:
            await self.client.write_gatt_char(characteristic.uuid, data.encode("utf-8"))
            print(f"Daten geschrieben: {data}")
        else:
            raise Exception(f"Charakteristik {WRITE_CHARACTERISTIC_UUID} ist nicht beschreibbar.")

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            print("Verbindung getrennt.")
            self.client = None
