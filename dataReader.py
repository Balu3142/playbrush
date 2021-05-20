import asyncio, time
from bleak import BleakClient
import config

globalData = bytearray()
globalDataLen = 0

def callback(sender, data):
    
    global globalData
    global globalDataLen
    
    # Did notification come from the right handle?
    if sender == config.COM_CHAR_HANDLE:
        
        # Is this a response for memory read command?
        if data[0] == 0x30:
        
            len = data[1]
            
            # At the moment we assume the responses come in the correct order.
            # This can be improved in the future.
            
            globalData += data[4:4+len]
            globalDataLen += len
    

async def readMemory(client, startAddr, length):

    global globalData
    global globalDataLen
    
    globalData = bytearray()
    globalDataLen = 0
    await client.start_notify(config.COM_CHAR_HANDLE, callback)
    
    # Build command that will request the given amount of data
    command = b'\x32' + length.to_bytes(2,'little') + startAddr.to_bytes(2,'little')
    await client.write_gatt_char(config.COM_CHAR_HANDLE, command)
    
    while globalDataLen < length:
        await asyncio.sleep(0.3)
        
    return globalData
    
    
async def readEntireFlash(client):

    # Read first page
    # For now let's assume the rest of the pages are empty..
    header = await readMemory(client, 0, 3)
    
    if header[0] != 0x54:
        raise Exception("wrong header")
        
    # If there is measurement data, read it
    if header[2] > 0:
        body = await readMemory(client, 8, header[2])
    
    return body
    

async def run(address):
    async with BleakClient(address) as client:
    
        # Enable status CCCD to keep the connection alive
        await client.write_gatt_descriptor(config.STATUS_CCCD_HANDLE, bytearray(b'\x01\x00'))
        
        # Enable com CCCD for reading data
        await client.write_gatt_descriptor(config.COM_CCCD_HANDLE, bytearray(b'\x01\x00'))
        
        # Move buffered data to flash (to prepare it for reading)
        await client.write_gatt_char(config.COM_CHAR_HANDLE, bytearray(b'\x30'))
                
        # Read all of the data in the flash
        res = await readEntireFlash(client)
        
        print(res)

loop = asyncio.get_event_loop()
loop.run_until_complete(run(config.TOOTHBRUSH_ADDRESS))