import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import RPi.GPIO as GPIO
import time
import threading

# OLED Libraries
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# Initialize Firebase Admin SDK
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Constants
DISTANCE_THRESHOLD = 30  # cm to detect car
UPDATE_INTERVAL = 1  # seconds between sensor readings

# GPIO Setup for 5 Ultrasonic Sensors + LEDs
SENSORS = {
    'slotid1': {'TRIG': 4, 'ECHO': 17, 'LED': 21},
    'slotid2': {'TRIG': 27, 'ECHO': 22, 'LED': 20},
    'slotid3': {'TRIG': 10, 'ECHO': 9, 'LED': 24}
}

# OLED Setup (128x64)
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

def setup_gpio():
    """Initialize GPIO pins for ultrasonic sensors and LEDs"""
    GPIO.setmode(GPIO.BCM)
    for sensor in SENSORS.values():
        GPIO.setup(sensor['TRIG'], GPIO.OUT)
        GPIO.setup(sensor['ECHO'], GPIO.IN)
        GPIO.setup(sensor['LED'], GPIO.OUT)
        GPIO.output(sensor['TRIG'], False)
        GPIO.output(sensor['LED'], False)
    print("Sensor and LED initialization completed")

def measure_distance(trig_pin, echo_pin):
    """Measure distance using ultrasonic sensor"""
    try:
        # Trigger ultrasonic measurement
        GPIO.output(trig_pin, True)
        time.sleep(0.00001)
        GPIO.output(trig_pin, False)

        # Wait for echo start
        pulse_start = time.time()
        timeout = pulse_start + 0.1
        while GPIO.input(echo_pin) == 0:
            if time.time() > timeout:
                return None
            pulse_start = time.time()

        # Wait for echo end
        pulse_end = time.time()
        timeout = pulse_end + 0.1
        while GPIO.input(echo_pin) == 1:
            if time.time() > timeout:
                return None
            pulse_end = time.time()

        # Calculate distance
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 2)

        return distance if 2 < distance < 400 else None
    except Exception as e:
        print(f"Error measuring distance: {str(e)}")
        return None

def update_slot_status(slot_id, is_available, current_status):
    """Update slot status in Firebase"""
    try:
        slots_ref = db.collection('parkslot').document('slots')
        if current_status.get(slot_id) != is_available:
            transaction = db.transaction()

            @firestore.transactional
            def update_in_transaction(transaction, slots_ref):
                slots = slots_ref.get(transaction=transaction).to_dict()
                old_status = slots.get(slot_id, True)
                if old_status != is_available:
                    current_available = slots.get('available', 0)
                    if is_available:
                        current_available += 1
                    else:
                        current_available -= 1

                    transaction.update(slots_ref, {
                        slot_id: is_available,
                        'available': current_available
                    })

                    print(f"Updated {slot_id}: {'Available' if is_available else 'Occupied'}")
                    print(f"Total available slots: {current_available}")

            update_in_transaction(transaction, slots_ref)
            current_status[slot_id] = is_available
    except Exception as e:
        print(f"Error updating slot status: {str(e)}")

def display_info(available, total):
    """Display parking info on OLED"""
    oled.fill(0)
    oled.show()
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    # Title
    draw.text((5, 5), "Parking Status", font=font, fill=255)
    draw.line((0, 20, 128, 20), fill=255)

    # Main info
    draw.text((5, 30), f"Available: {available}/{total}", font=font, fill=255)

    # Show on screen
    oled.image(image)
    oled.show()

def monitor_sensors():
    """Continuously monitor all sensors and update Firebase, LEDs, and OLED"""
    current_status = {}
    total_slots = len(SENSORS)
    available_slots = total_slots

    try:
        while True:
            available_slots = 0

            for slot_id, pins in SENSORS.items():
                distance = measure_distance(pins['TRIG'], pins['ECHO'])
                if distance is not None:
                    is_available = distance > DISTANCE_THRESHOLD
                    update_slot_status(slot_id, is_available, current_status)

                    # LED control: ON if available, OFF if occupied
                    GPIO.output(pins['LED'], GPIO.HIGH if is_available else GPIO.LOW)

                    if is_available:
                        available_slots += 1

                time.sleep(0.1)

            # Update OLED display
            display_info(available_slots, total_slots)

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping sensor monitoring...")
        GPIO.cleanup()
    except Exception as e:
        print(f"Error in monitor_sensors: {str(e)}")
        GPIO.cleanup()

def initialize_slots():
    """Initialize slots document if it doesn't exist"""
    try:
        slots_ref = db.collection('parkslot').document('slots')
        if not slots_ref.get().exists:
            slots_ref.set({
                'slotid1': True,
                'slotid2': True,
                'slotid3': True,
                'available': 3
            })
            print("Initialized slots document")
    except Exception as e:
        print(f"Error initializing slots: {str(e)}")

def main():
    """Main function to run the parking sensor system"""
    print("=== Parking Sensor System ===")
    print("Press Ctrl+C to exit")

    initialize_slots()
    try:
        setup_gpio()
        time.sleep(2)
        monitor_sensors()
    except KeyboardInterrupt:
        print("\nShutting down sensor system...")
    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
