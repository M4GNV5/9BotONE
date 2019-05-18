var device;
var service;
var write_characteristic;

var last_error;
var disconnect_timeout;

var receive_index = 0;
var receive_buffer = new Uint8Array(8 + 256); //max packet length
var packet_complete_callback = false;
function on_data_receive(event)
{

	var data = event.target.value;
	var array = new Uint8Array(data.buffer);
	receive_buffer.set(array, receive_index);

	receive_index += array.byteLength;

	var packetLen = receive_buffer[2] + 6;
	if(receive_index == packetLen)
	{
		if(packet_complete_callback)
		{
			var packet = new Uint8Array(receive_buffer.slice(0, receive_index));

			receive_index = 0;

			packet_complete_callback(packet);
			packet_complete_callback = false;
		}
		else
		{
			receive_index = 0;
		}
	}
}

function initialize_device(_device)
{
	device = _device;

	return device.getPrimaryService("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
		.then(function(_service) {

			service = _service;
			return service.getCharacteristic("6e400002-b5a3-f393-e0a9-e50e24dcca9e");

		}).then(function(_write_char) {

			write_characteristic = _write_char;
			return service.getCharacteristic("6e400003-b5a3-f393-e0a9-e50e24dcca9e");

		}).then(function(read_char) {
			
			read_char.on('characteristicvaluechanged', on_data_receive);
			return read_char.startNotifications();

		});
}

function calculate_checksum(packet)
{
	var end = packet[2] + 4;
	var sum = 0;
	for(var i = 2; i < end; i++)
		sum += packet[i];

	return (sum & 0xFFFF) ^ 0xFFFF;
}

function send_packet(command, offset, data)
{
	// 55 AA <len> 11 <cmd> <offset> [data...] <chk1> <chk2>

	var packetLen = 8 + data.byteLength;
	var packet = new Uint8Array(packetLen);
	packet[0] = 0x55;
	packet[1] = 0xAA;
	packet[2] = data.byteLength + 2;
	packet[3] = 0x11;
	packet[4] = command;
	packet[5] = offset;
	packet.set(data, 6);

	var checksum = calculate_checksum(packet);
	packet[packetLen - 2] = checksum & 0xFF;
	packet[packetLen - 1] = (checksum >> 8) & 0xFF;

	return write_characteristic.writeValue(packet);
}

function receive_packet()
{
	return new Promise(function(resolve, reject) {

		packet_complete_callback = resolve;

	});
}

function read_register(offset, size)
{
	//cmd for reading is 0x01
	var data = new Uint8Array([size]);
	return send_packet(0x01, offset, data)
		.then(receive_packet)
		.then(function(packet) {

			var view = new DataView(packet.buffer);

			if(view.getUint8(2) != size + 2)
				return Promise.reject("received packages payload does not match requests bytes length");

			switch(size)
			{
				case 1:
					return view.getUint8(6, true);
				
				case 2:
					return view.getUint16(6, true);

				case 4:
					return view.getUint32(6, true);

				default:
					return Promise.reject("Invalid register size, valid are 1/2/4");
			}

		});
}

function write_register(offset, value, size)
{
	var buff = new ArrayBuffer(size);
	var view = new DataView(buff);
	switch(size)
	{
		case 1:
			view.setUint8(0, value, true);
			break;
		
		case 2:
			view.setUint16(0, value, true);
			break;

		case 4:
			view.setUint32(0, value, true);
			break;

		default:
			return Promise.reject("Invalid register size, valid are 1/2/4");
	}

	//cmd for writing is 0x02
	return send_packet(0x02, offset, new Uint8Array(buff))
		.then(receive_packet)
		.then(function(packet) {

			// TODO check if we got an error as response

		});
}

setWatch(function() {

	NRF.wake();

	var interval = setInterval(function()
	{
		digitalPulse(LED3, true, 100);	
	}, 500);

	var connection_promise;
	if(device && device.connected)
	{
		connection_promise = Promise.resolve()
			.then(function()
			{
				clearTimeout(disconnect_timeout);
			});
	}
	else
	{
		connection_promise = NRF.connect("<mac address> random")
			.then(initialize_device);
	}

	var wasLocked;

	connection_promise
		.then(function()
		{
			disconnect_timeout = setTimeout(function()
			{
				device.disconnect();
				device = false;

				digitalPulse(LED3, true, 1000);

				NRF.sleep();
			}, 60000);
		})
		.then(function()
		{
			return read_register(0x70, 1);
		})
		.then(function(locked)
		{
			wasLocked = locked;
			return write_register(0x70, locked ? 0 : 1, 1);
		})
		.then(function()
		{
			clearInterval(interval);

			if(wasLocked)
				digitalPulse(LED2, true, 1000);
			else
				digitalPulse(LED1, true, 1000);
		})
		.catch(function(err)
		{
			last_error = err;
			print(err);

			if(device && device.connected)
				device.disconnect();
			NRF.sleep();

			clearInterval(interval);
			digitalPulse(LED1, true, [100, 100, 100, 100, 100]);
		});

}, BTN, {edge: "rising", debounce: 50, repeat: true});

NRF.sleep();
