import asyncio, time
from bleak import BleakClient
import config

globalData = bytearray()
globalDataLen = 0

# Called by COM notification
def callback(sender, data):
    
    global globalData
    global globalDataLen
    
    # Did notification come from the right handle?
    if sender == config.COM_CHAR_HANDLE:
        
        # Is this a response for memory read command?
        if data[0] == 0x30:
        
            # Second byte contains the length of incoming data
            len = data[1]
            
            # At the moment we assume the responses come in the correct order.
            # This can be improved in the future.
            
            globalData += data[4:4+len]
            globalDataLen += len
    
# Read 'length' bytes of data starting from 'startAddr' location in the flash
async def readMemory(client, startAddr, length):

    global globalData
    global globalDataLen
    
    globalData = bytearray()
    globalDataLen = 0
    
    # Register callback for the notifications
    await client.start_notify(config.COM_CHAR_HANDLE, callback)
    
    # Build command that will request the given amount of data
    command = b'\x32' + length.to_bytes(2,'little') + startAddr.to_bytes(2,'little')
    await client.write_gatt_char(config.COM_CHAR_HANDLE, command)
    
    # Wait until the toothbrush responds with the requested data
    while globalDataLen < length:
        await asyncio.sleep(0.3)
        
    return globalData
    
# Read all data from flash
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
    
# Print Mode 6 data
def printResult(data):
        startTime = int.from_bytes(data[0:4], 'little')
        endTime = int.from_bytes(data[4:8], 'little')
        
        print(f"Measurement start time: {startTime}")
        print(f"Measurement end time: {endTime}")
        print('Cluster 1: '+''.join(format(x, '02x') for x in data[8:10]))
        print('Cluster 2: '+''.join(format(x, '02x') for x in data[10:12]))
        print('Cluster 3: '+''.join(format(x, '02x') for x in data[12:14]))
        print('Cluster 4: '+''.join(format(x, '02x') for x in data[14:16]))
        print()
    

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
        
        print(len(res))
        printResult(res[0:16])
        printResult(res[16:32])
        


loop = asyncio.get_event_loop()
loop.run_until_complete(run(config.TOOTHBRUSH_ADDRESS))