import machine
import time
import urequests
import network
import ds18x20
import onewire
import os
import ntptime

DEBUG = True
RETRY_ATTEMPTS = 3
SENSOR_READ_INTERVAL = 4  # Sensorabfrageintervall in Sekunden
TEMP_ALERT_THRESHOLD = 2  # Temperaturunterschied in °C

# Netzwerk-Konfiguration (SSID, Passwort und URL des Node-RED-Servers)
WIFI_CONFIG = [
    {"ssid": "G101", "password": "G101bbzvk", "url": "http://192.168.0.199:1880"},
    {"ssid": "@Home", "password": "th!s !s a test for wlan", "url": "http://192.168.0.58:1880"},
    {"ssid": "Pixel_4813", "password": "9ad702b6c353", "url": "http://10.242.217.27:1880"}
]

NODE_RED_BASE_URL = ""  # Wird später aus der Konfiguration gesetzt

ENDPOINTS = {
    "reed": "/reed_sensor",
    "temp": "/temp_sensor",
    "alert": "/temp_alert"
}

# Hardware-Pins
PIN_CONFIG = {
    "reed": 17,
    "onewire": 16
}

ow = onewire.OneWire(machine.Pin(PIN_CONFIG["onewire"]))
ds = ds18x20.DS18X20(ow)
devices = ds.scan()
reed = machine.Pin(PIN_CONFIG["reed"], machine.Pin.IN, machine.Pin.PULL_UP)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    global NODE_RED_BASE_URL  
    
    for network_config in WIFI_CONFIG:
        if DEBUG:
            print(f"Verbinde mit {network_config['ssid']}...")
        
        wlan.connect(network_config["ssid"], network_config["password"])
        
        for _ in range(20):
            if wlan.isconnected():
                if DEBUG:
                    print("Verbunden!")
                    print("IP:", wlan.ifconfig()[0])
                NODE_RED_BASE_URL = network_config["url"]
                if DEBUG:
                    print(f"Verwendete URL für Node-RED: {NODE_RED_BASE_URL}")
                sync_time()
                return True
            time.sleep(0.5)
    
    if DEBUG:
        print("Keine WLAN-Verbindung möglich")
    return False

def sync_time():
    try:
        ntptime.settime()
        if DEBUG:
            print("Zeit synchronisiert:", time.localtime())
    except Exception as e:
        if DEBUG:
            print("Zeitsynchronisation fehlgeschlagen:", e)

def get_formatted_time():
    t = time.localtime()
    return (
        f"{t[2]:02d}/{t[1]:02d}/{t[0]}",
        f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
    )

def read_temperature():
    try:
        ds.convert_temp()
        time.sleep_ms(750)
        return ds.read_temp(devices[0]) if devices else None
    except Exception as e:
        if DEBUG:
            print("Temperaturmessfehler:", e)
        return None

def send_data(url, data):
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = urequests.post(url, json=data, timeout=10)
            response.close()
            if response.status_code == 200:
                return True
        except Exception as e:
            if DEBUG:
                print(f"Sendefehler (Versuch {attempt+1}):", e)
            time.sleep(2)
    return False


class DataLogger:
    def __init__(self, filename="log.csv"):
        self.filename = filename
        self.index = 0
        self.initialize_log()

    def initialize_log(self):
        try:
            with open(self.filename, "r") as f:
                pass
        except OSError:
            with open(self.filename, "w") as f:
                f.write("Index,Date,Time,Temperature,Status\n")

    def get_last_index(self):
        try:
            with open(self.filename, "r") as f:
                lines = f.readlines()
                if len(lines) > 1:
                    return int(lines[-1].split(',')[0])
        except Exception as e:
            if DEBUG:
                print("Logindex Fehler:", e)
        return 0

    def log_entry(self, temp, status):
        self.index = self.get_last_index() + 1
        date, current_time = get_formatted_time()
        entry = f"{self.index},{date},{current_time},{temp or 'N/A'},{status}\n"
        
        with open(self.filename, "a") as f:
            f.write(entry)


def main():
    logger = DataLogger()
    last_reed_state = reed.value()
    last_temp = read_temperature()


    if not connect_wifi():
        return

    # Initialzustand senden, Erstausführung
    send_data(NODE_RED_BASE_URL + ENDPOINTS["reed"], {"reed_state": last_reed_state})
    
    while True:
        # Reed-Sensor prüfen
        current_reed = reed.value()

        if current_reed != last_reed_state:
            temp = read_temperature()
            if temp is not None:
                last_temp = temp  # Setze die Temperatur beim Öffnen/Schließen des Reed-Sensors
                logger.log_entry(temp, current_reed)
                send_data(NODE_RED_BASE_URL + ENDPOINTS["reed"], {"reed_state": current_reed})
            last_reed_state = current_reed

        # Temperaturüberwachung, nur wenn die Reed-Sensoränderung vorliegt
        if last_temp is not None:
            current_temp = read_temperature()
            if current_temp is not None:
                temp_difference = last_temp - current_temp
                if DEBUG:
                    print(f"Letzte gemessene Temperatur nach öffnen/schließen des Fensters: {last_temp} °C")
                    print(f"Aktuelle Temperatur: {current_temp} °C")
                    print(f"Temperaturdifferenz: {temp_difference} °C")  # Debug-Ausgabe für Differenz

                # Überprüfen, ob der Temperaturabfall von mindestens 2°C vorhanden ist
                if temp_difference >= TEMP_ALERT_THRESHOLD and current_temp < last_temp:
                    send_data(NODE_RED_BASE_URL + ENDPOINTS["alert"], {"temperature": current_temp})

                    last_temp = current_temp

                # Temperaturwert weiterverfolgen und zur Node-RED-API senden
                send_data(NODE_RED_BASE_URL + ENDPOINTS["temp"], {"temperature": current_temp})
                

        time.sleep(SENSOR_READ_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if DEBUG:
            print("Programm beendet")
    except Exception as e:
        if DEBUG:
            print("Kritischer Fehler:", e)

