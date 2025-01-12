import machine
import time
import urequests
import network
import ds18x20
import onewire
import os

"""
Beim setzen der Werte 'True'/'False' werden die Print Ausgaben aktiviert oder deaktiviert.
Dies ist nötig um den Betrieb des Raspberry Pi Pico 2W an einer Powerbank zu ermöglichen, da dort kein Terminal Existiert, an das der RPi seine Ausgaben senden kann.
"""

DEBUG = True

NODE_RED_URL_REED = 'http://192.168.0.58:1880/reed_sensor'
NODE_RED_URL_TEMP = 'http://192.168.0.58:1880/temp_sensor'
NODE_RED_URL_ALERT = 'http://192.168.0.58:1880/temp_alert'

REED_PIN = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)
OW_PIN = machine.Pin(16)

ow_bus = onewire.OneWire(OW_PIN)
ds_sensor = ds18x20.DS18X20(ow_bus)

WIFI_FILE_PATH = "wifi.txt"
LOG_FILE_PATH = "log.csv"

def read_wifi_credentials():
    """
    Liest 'SSID' und 'PASSWORT' aus der Textdatei 'wifi.txt' aus.
    Erwartet wird folgendes Format: 'SSID,Password'.
    """
    try:
        with open(WIFI_FILE_PATH, 'r') as file:
            line = file.readline().strip()
            ssid, password = line.split(',')
            return ssid, password
    except Exception as e:
        if DEBUG:
            print(f"Fehler beim Lesen der Wi-Fi-Anmeldedaten: {e}")
        return None, None

def connect_wifi():
    """
    Stellt eine Verbindung zum Wi-Fi-Netzwerk her, indem die Anmeldedaten aus 'wifi.txt' verwendet werden.
    """
    ssid, password = read_wifi_credentials()

    if ssid is None or password is None:
        if DEBUG:
            print("Wi-Fi-Anmeldedaten fehlen oder sind falsch.")
        return

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
            if DEBUG:
                print(".", end="")
    
    if DEBUG:
        print("\nWi-Fi verbunden:", wlan.ifconfig())

def send_data(payload, url, retries=3):
    """
    Sendet Daten an den angegebenen Node-RED-Endpunkt mit einer Wiederholungslogik.
    """
    for attempt in range(retries):
        try:
            if DEBUG:
                print(f"Sende Nutzdaten: {payload}")
            response = urequests.post(url, json=payload, timeout=30)
            response.close()

            if response.status_code == 200:
                return
            else:
                print(f"Node-RED gab einen Fehler zurück: {response.status_code}")
        except Exception as e:
            print(f"Fehler beim Senden der Daten (Versuch {attempt + 1}/{retries}):", e)
            time.sleep(5)
    print("Fehler beim Senden der Daten nach mehreren Versuchen.")

def read_temperature():
    """
    Liest die Temperatur vom DS18x20-Sensor aus.
    """
    devices = ds_sensor.scan()
    
    if not devices:
        if DEBUG:
            print("Keine DS18x20-Geräte gefunden.")
        return None

    ds_sensor.convert_temp()
    time.sleep(1)
    temperature = ds_sensor.read_temp(devices[0])
    
    return temperature

def initialize_log_file():
    """
    Initialisiert die Logdatei, wenn sie noch nicht existiert.
    """
    if LOG_FILE_PATH not in os.listdir():
        with open(LOG_FILE_PATH, "w") as log_file:
            log_file.write("Index,Date,Time,Temperature,Status\n")

def get_last_log_index():
    """
    Liest den letzten Index aus der Logdatei. Wenn die Datei leer ist oder nicht existiert, wird 0 zurückgegeben.
    """
    try:
        with open(LOG_FILE_PATH, "r") as log_file:
            lines = log_file.readlines()
            if len(lines) > 0:
                # Die letzte Zeile hat den höchsten Index
                last_line = lines[-1]
                last_index = int(last_line.split(',')[0])  # Der Index ist die erste Zahl in der Zeile
                return last_index + 1  # Starten beim nächsten Index
    except OSError:  # Falls die Datei nicht existiert
        return 0  # Wenn die Datei leer oder nicht vorhanden ist, fangen wir bei 0 an

def append_to_log(index, date, time_str, temperature, status):
    """
    Fügt einen neuen Eintrag in die Logdatei ein.
    """
    with open(LOG_FILE_PATH, "a") as log_file:
        log_file.write(f"{index},{date},{time_str},{temperature},{status}\n")
    log_index += 1  # Erhöhen des Index nach jedem Log-Eintrag
        

def check_temperature_difference(last_temp, current_temp):
    """
    Überprüft, ob die Temperatur gesenkt wurde und die Differenz einen Schwellenwert von 2°C überschreitet.
    """
    if last_temp is not None and current_temp is not None:
        temp_diff = last_temp - current_temp  # Temperaturdifferenz (abfallend)
        if temp_diff >= 2:  # Wenn die Temperatur um 2°C oder mehr gesenkt wurde
            return temp_diff
    return None  # Keine signifikante Abkühlung

def main():
    reed_last_state = REED_PIN.value()
    temp_last_value = None
    log_index = get_last_log_index()  # Hole den letzten Index aus der Logdatei
    alert_sent = False

    try:
        connect_wifi()
        initialize_log_file()

        # Einmalige Initialisierung des Reed-Sensors und Senden des aktuellen Status
        reed_state = REED_PIN.value()
        send_data({"reed_state": reed_state}, NODE_RED_URL_REED)

        while True:
            reed_state = REED_PIN.value()
            if DEBUG:
                print(f"Aktueller Reed-Zustand: {reed_state}")

            if reed_state != reed_last_state:
                reed_last_state = reed_state

                temp_value = read_temperature()
                if temp_value is not None:
                    temp_last_value = temp_value

                current_time = time.localtime()
                date_str = f"{current_time[2]:02d}/{current_time[1]:02d}/{current_time[0]}"
                time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"

                temperature = temp_last_value if temp_last_value is not None else "N/A"

                append_to_log(log_index, date_str, time_str, temperature, reed_state)

                send_data({"reed_state": reed_state}, NODE_RED_URL_REED)

            temp_value = read_temperature()
            if temp_value is not None:
                temp_diff = check_temperature_difference(temp_last_value, temp_value)
                if temp_diff is not None:
                    if not alert_sent:
                        send_data({"alert": "Temperaturabfall erkannt", "temperature": temp_value}, NODE_RED_URL_ALERT)
                        alert_sent = True
                    temp_last_value = temp_value

                if temp_diff is not None:
                    send_data({"temperature": temp_value}, NODE_RED_URL_TEMP)

            else:
                if DEBUG:
                    print("Temperaturmessung fehlgeschlagen.")

            time.sleep(4)
            alert_sent = False

    except Exception as e:
        print(f"Fehler in der Hauptschleife: {e}")

main()
