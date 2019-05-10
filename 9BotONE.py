from struct import pack, unpack
from binascii import hexlify
import time, queue, pygatt

mac = "<your mac address here>"

# rx/tx for Ninebot, means we write to rx and read from tx
rx_char_uuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
tx_char_uuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

def receive_callback(handle, value):
	print("< [%s] %s" % (handle, hexlify(value).upper()))
	for c in value:
		receive_queue.put(c)

def read_response(count=1, timeout=5):
	result = bytearray(count)
	for i in range(0, count):
		result[i] = receive_queue.get(True, timeout)

	return result

def calculate_checksum(data):
	s = 0
	for c in data:
		s += c
	return (s & 0xFFFF) ^ 0xFFFF

def send_packet(command, data):
	# see http://www.gorina.es/9BMetrics/protocol.html
	# 55 AA <len> 09 01 <cmd> [data...] <chk1> <chk2>

	payload = pack("BBBB", len(data) + 2, 0x11, 0x01, command) + data
	checksum = pack("<H", calculate_checksum(payload))

	packet = bytearray("\x55\xAA" + payload + checksum)

	print("> %s" % hexlify(packet).upper())
	device.char_write_handle(write_handle, packet)

def read_registers(offset, length=1):
	# see http://www.gorina.es/9BMetrics/protocol.html
	# <offset> <read length>

	data = bytearray([length])
	send_packet(offset, data)

	i = 0
	result = bytearray(length)
	while i < length:
		packet_header = read_response(6)
		magic_header, curr_len, magic_header2, command = unpack("<HBHB", packet_header)

		curr_len -= 2
		payload = read_response(curr_len)
		read_response(2) #checksum

		for j in range(0, curr_len):
			result[i] = payload[j]
			i += 1

	return result

receive_queue = queue.Queue()

gatt = pygatt.GATTToolBackend()
gatt.start()

device = gatt.connect(mac, address_type=pygatt.BLEAddressType.random)
device.subscribe(tx_char_uuid, callback=receive_callback)

write_handle = device.get_handle(rx_char_uuid)

with open("registers.bin", "w+") as fd:
	data = read_registers(0, 0x80)
	fd.write(data)

	data = read_registers(0x80, 0x80)
	fd.write(data)
