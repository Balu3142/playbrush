import asyncio, time
from bleak import BleakClient

address = "50:FA:AB:F2:57:50"

async def run(address):
    async with BleakClient(address) as client:
        await client.write_gatt_descriptor(0x10, bytearray(b'\x01\x00'))
        print("Model Number")
        time.sleep(10)
        print("end")

loop = asyncio.get_event_loop()
loop.run_until_complete(run(address))