import asyncio, time
from bleak import BleakClient

address = "50:FA:AB:F2:57:50"

def callback(sender, data):
    print(f"{sender}: {data}")
    


async def readMemory(client):
    await client.start_notify(0x1D, callback)
    await client.write_gatt_char(0x1D, bytearray(b'\x32\x03\x00\x00\x00'))
    
    
    

async def run(address):
    async with BleakClient(address) as client:
    
        # Enable status CCCD to keep the connection alive
        await client.write_gatt_descriptor(0x10, bytearray(b'\x01\x00'))
        
        # Enable com CCCD for reading data
        await client.write_gatt_descriptor(0x1F, bytearray(b'\x01\x00'))
        
        # Move buffered data to flash (to prepare it for reading)
        await client.write_gatt_char(0x1D, bytearray(b'\x30'))
        
        #Read meomry and interpret it
        
        # Read 3 bytes for test
        await readMemory(client)
        
        print("Model Number")
        time.sleep(10)
        print("end")

loop = asyncio.get_event_loop()
loop.run_until_complete(run(address))