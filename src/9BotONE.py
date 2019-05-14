from struct import pack, unpack
from binascii import hexlify, unhexlify
import sys, queue, pygatt

mac = "<your mac address here>"

# rx/tx for Ninebot, means we write to rx and read from tx
rx_char_uuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
tx_char_uuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

command_read = 0x01
command_write = 0x02

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

def send_packet(command, offset, data):
	# see http://www.gorina.es/9BMetrics/protocol.html
	# 55 AA <len> 11 <cmd> <offset> [data...] <chk1> <chk2> for ONE A1/S2
	# 55 AA <len> 09 <cmd> <offset> [data...] <chk1> <chk2> for others (untested)

	# 5A A5 01    3E 20 01 F8 10 97 FE
	# 5A A5 <len> 3E 20 <cmd> <offset> [data...] <chk1> <chk2> for Ninebot ES2

	#payload = pack("BBBB", len(data) + 2, 0x11, command, offset) + data
	payload = pack("BBBBB", len(data), 0x3E, 0x20, command, offset) + data
	checksum = pack("<H", calculate_checksum(payload))

	packet = bytearray("\x5A\xA5" + payload + checksum)

	print("> %s" % hexlify(packet).upper())
	device.char_write_handle(write_handle, packet)

def read_packet():
	packet_header = read_response(6)
	magic1, curr_len, magic2, offset = unpack("<HBHB", packet_header)
	magic1, curr_len, magic2, magic3, offset = unpack("<HBHBB", packet_header)

	curr_len -= 2
	payload = read_response(curr_len)
	read_response(2) #checksum

	return payload

def read_bytes(offset, length=1):
	# see http://www.gorina.es/9BMetrics/protocol.html
	# 0x01 <offset> <read length>

	data = bytearray([length])
	send_packet(command_read, offset, data)

	i = 0
	result = bytearray(length)
	while i < length:
		payload = read_packet()
		for c in payload:
			result[i] = c
			i += 1

	return result

def write_bytes(offset, data):
	# see http://www.gorina.es/9BMetrics/protocol.html
	# 0x02 <offset> <bytes ...>

	send_packet(command_write, offset, data)
	return read_packet()

receive_queue = queue.Queue()

gatt = pygatt.GATTToolBackend()
gatt.start()

device = gatt.connect(mac, address_type=pygatt.BLEAddressType.random)
device.subscribe(tx_char_uuid, callback=receive_callback)

write_handle = device.get_handle(rx_char_uuid)

if sys.argv[1] == "read":
	pos = int(sys.argv[2], 0)
	length = int(sys.argv[3], 0)

	print("reading %d bytes at %d" % (length, pos))
	data = read_bytes(pos, length)

	print(hexlify(data).upper())

elif sys.argv[1] == "write":
	pos = int(sys.argv[2], 0)
	data = unhexlify(sys.argv[3])
	data = bytearray(data)

	print("writing %d bytes at %d" % (len(data), pos))
	data = write_bytes(pos, data)

	print(hexlify(data).upper())

elif sys.argv[1] == "dump":
	filename = sys.argv[2]
	print("reading all registers and writing to %s" % filename)
	with open(filename, "w+") as fd:
		data = read_bytes(0, 0x80)
		fd.write(data)

		data = read_bytes(0x80, 0x80)
		fd.write(data)

else:
	print("python 9BotONE.py read <offset> <length>")
	print("python 9BotONE.py write <offset> <hex bytes...>")
	print("python 9BotONE.py dump <file>")
