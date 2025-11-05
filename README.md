# Raspberry Pi Parking Sensor System

A real-time IoT-based parking monitoring system using **Raspberry Pi**, **ultrasonic sensors**, and **OLED display**, integrated with **Firebase Firestore** for live updates. The system detects parking slot availability, updates Firestore, and visually displays the status using LEDs and an OLED screen.

---

## Features

* **Real-time Parking Detection**

  * Monitors 3 parking slots using ultrasonic sensors.
  * Detects vehicles based on distance threshold (default 30 cm).
  * Updates slot availability automatically in Firestore.

* **Firebase Integration**

  * Firestore document `parkslot/slots` stores status of each slot.
  * Keeps a running count of available slots.
  * Updates are transactional to prevent race conditions.

* **Visual Feedback**

  * **LEDs** indicate slot availability: ON = available, OFF = occupied.
  * **OLED Display (128x64)** shows real-time parking info: Available / Total slots.

* **Hardware**

  * Raspberry Pi (GPIO pins)
  * 3 Ultrasonic Sensors (HC-SR04)
  * 3 LEDs
  * OLED display (I2C, 128x64)

* **Safety & Reliability**

  * Minimum and maximum valid sensor distances enforced (2 cm – 400 cm).
  * Graceful handling of exceptions and cleanup of GPIO on shutdown.

---

## Tech Stack

* **Programming Language:** Python 3.x
* **Database:** Firebase Firestore
* **Libraries & Tools:**

  * `firebase_admin` – Firebase Admin SDK
  * `RPi.GPIO` – GPIO control for sensors and LEDs
  * `adafruit_ssd1306` – OLED display driver
  * `PIL` (Pillow) – Drawing text/images on OLED
  * `board` and `busio` – I2C communication
  * `threading` – Concurrent sensor monitoring

---

## Hardware Setup

| Component       | GPIO Pin / Connection   |
| --------------- | ----------------------- |
| Ultrasonic TRIG | As defined in `SENSORS` |
| Ultrasonic ECHO | As defined in `SENSORS` |
| LEDs            | As defined in `SENSORS` |
| OLED Display    | I2C (SCL, SDA)          |

Default GPIO mapping in code:

```python
SENSORS = {
    'slotid1': {'TRIG': 4, 'ECHO': 17, 'LED': 21},
    'slotid2': {'TRIG': 27, 'ECHO': 22, 'LED': 20},
    'slotid3': {'TRIG': 10, 'ECHO': 9, 'LED': 24}
}
```

---

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd parking-sensor-system
```

2. Install Python dependencies:

```bash
pip install firebase-admin adafruit-circuitpython-ssd1306 pillow
```

3. Connect the Raspberry Pi hardware (Ultrasonic sensors, LEDs, OLED).

4. Add your Firebase Admin SDK key:

* Save your service account JSON file as `key.json` in the project root.

---

## Configuration

* **Distance Threshold:** Change `DISTANCE_THRESHOLD = 30` to adjust sensitivity.
* **Update Interval:** Change `UPDATE_INTERVAL = 1` for how frequently sensors are polled.
* **Slots:** Adjust `SENSORS` dictionary to add/remove slots or change GPIO pins.

---

## Usage

1. Run the main script on Raspberry Pi:

```bash
python parking_sensor_system.py
```

2. The system continuously monitors all sensors:

* Updates Firebase with slot availability.
* Lights LEDs for each slot.
* Updates OLED display with current parking status:

```
Parking Status
--------------
Available: 2/3
```

3. Stop the system with **Ctrl+C**, GPIO pins are cleaned up automatically.

---

## Firestore Structure

`parkslot/slots` document:

```json
{
  "slotid1": true,
  "slotid2": false,
  "slotid3": true,
  "available": 2
}
```

* `true` = available, `false` = occupied.
* `available` = total number of free slots.

---

## Functions Overview

* **GPIO & Sensor Functions**

  * `setup_gpio()` – Initialize GPIO pins for sensors and LEDs.
  * `measure_distance(trig_pin, echo_pin)` – Measure distance for vehicle detection.

* **Firebase Functions**

  * `update_slot_status(slot_id, is_available, current_status)` – Update Firestore with slot status.
  * `initialize_slots()` – Create slots document if missing.

* **Display**

  * `display_info(available, total)` – Update OLED with current parking availability.

* **Monitoring**

  * `monitor_sensors()` – Continuously read sensors, update LEDs, OLED, and Firestore.

---

## Notes

* Uses **I2C OLED display** (128x64) to show parking info.
* Measures distances between 2 cm and 400 cm.
* Minimum one-second interval between sensor updates to prevent rapid fluctuations.
* Can be extended to more slots by updating `SENSORS` dictionary.

---

## Future Improvements

* Add more sensors for larger parking lots.
* Integrate with a mobile/web dashboard for remote monitoring.
* Add logging of parking history in Firestore.
* Include automatic notifications when parking is full.
* Add AI-based vehicle detection for better accuracy.

---

## License

MIT License – Open-source and free to use.

---

## Author

Vinayak Magajikondi
