# 9BotONE

This repository contains some scripts and tools for communicating with my
Ninebot ONE S2. It could work with other scooters too but might need some
adjustment.

## Ressources
The following docs helped me a lot when fiddling with the bluetooth protocol.
Some of these are actually related to other similar scooters like the
Ninebot ES2 or the Xiaomi M365.

- https://github.com/etransport/ninebot-docs/wiki/protocol
- https://github.com/fgorina/9BMetrics/issues/6
- https://wiki.scooterhacking.org/index.php/Ninebot_ES/SNSC_models
- https://wiki.scooterhacking.org/index.php/Ninebot_ES/SNSC_ESC_documentation

## 9BotONE.py

Python script which connects to a ninebot and can read/write/dump registers.
It runs using `pygatt` using BlueZ (Linux bluetooth stack).

```sh
# change the mac address in the file

python 9BotONE.py read <offset> <length>
python 9BotONE.py write <offset> <hex bytes...>
python 9BotONE.py dump <file>
```

## Web tool

I initially wrote a javascript implementation of the ninebot tool for the
keyfob, but it turns out the bluetooth API of the puckjs is the same as the
(experimental) WebBluetooth API. So with a few extra lines i was able to
read/write registers from the webbrowser.

You can try it yourself here: https://m4gnus.de/ninebot/src/

## Keyfob

Having to take out my phone, disable mobile internet (so the app doesn't send my
data to the "cloud"), enable bluetooth, open the app and finally click lock took
too long, so i created a key fob using a [puckjs](https://www.puck-js.com/)
which locks my scooter by simply clicking one button. Click the image for a demo
video:

[![](https://i.m4gnus.de/868d6.png)](https://i.m4gnus.de/2019-05/2019-05-18T16%3A56.mp4)
