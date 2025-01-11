import machine  # Importiert das Modul für die Steuerung der Hardware (Pins, etc.)
import time  # Importiert das Modul für Zeitfunktionen (Schlafpausen, aktuelle Zeit)
import urequests  # Importiert das Modul für HTTP-Anfragen (POST, GET)
import network  # Importiert das Modul für Netzwerkfunktionen (Wi-Fi, WLAN-Verbindung)
import ds18x20  # Importiert das Modul für den DS18x20 Temperaturfühler
import onewire  # Importiert das Modul für den OneWire Bus, der für den DS18x20 verwendet wird
import os  # Importiert das Modul für Betriebssystemfunktionen (Dateisystem)

debug_bool = False  # Aktiviert den Debug-Modus, der detaillierte Ausgaben ermöglicht.

# WLAN-Zugangsdaten
SSID = '@Home'  # Der WLAN-Name (SSID)
PASSWORD = 'th!s !s a test for wlan'  # Das WLAN-Passwort

# Node-RED URLs
node_red_url_reed = 'http://192.168.0.58:1880/reed_sensor'  # URL für den Reed-Sensor in Node-RED
node_red_url_temp = 'http://192.168.0.58:1880/temp_sensor'  # URL für den Temperatur-Sensor in Node-RED
node_red_url_alert = 'http://192.168.0.58:1880/temp_alert'  # URL für die Temperaturwarnung in Node-RED

# Pin-Definitionen
reed_pin = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)  # Definiert den Pin für den Reed-Sensor (Eingang, Pull-up-Widerstand)
ow_pin = machine.Pin(16)  # Definiert den Pin für den OneWire-Bus (Temperatursensor)

# Initialisierung des OneWire-Busses für den Temperatursensor
ow_bus = onewire.OneWire(ow_pin)  # Initialisiert den OneWire-Bus
ds_sensor = ds18x20.DS18X20(ow_bus)  # Initialisiert den DS18x20 Temperatursensor

# Logdatei Pfad
log_file_path = "log.csv"  # Definiert den Pfad der Logdatei

# WLAN-Verbindung herstellen
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)  # Initialisiert das WLAN im Station-Modus
    wlan.active(True)  # Aktiviert das WLAN
    if not wlan.isconnected():  # Überprüft, ob die Verbindung besteht
        wlan.connect(SSID, PASSWORD)  # Versucht, sich mit dem WLAN zu verbinden
        while not wlan.isconnected():  # Wartet, bis die Verbindung hergestellt ist
            time.sleep(0.5)  # Kurze Pause, um den Status regelmäßig zu prüfen
            if debug_bool:  # Falls der Debug-Modus aktiviert ist
                print(".", end="")  # Ausgabe von Punkten, um den Verbindungsversuch anzuzeigen
    if debug_bool:  # Falls der Debug-Modus aktiviert ist
        print("\nWi-Fi connected:", wlan.ifconfig())  # Gibt die IP-Adresse nach erfolgreicher Verbindung aus

# Daten an Node-RED senden
def send_data(payload, url, retries=3):
    for attempt in range(retries):  # Versucht es mehrfach (mit der angegebenen Anzahl an Versuchen)
        try:
            if debug_bool:  # Falls der Debug-Modus aktiviert ist
                print(f"Sending payload: {payload}")  # Zeigt die gesendeten Daten an
            response = urequests.post(url, json=payload, timeout=30)  # Sendet die POST-Anfrage an Node-RED
            response.close()  # Schließt die Antwort, nachdem sie erhalten wurde
            if response.status_code == 200:  # Erfolgreiche Antwort (HTTP 200)
                return  # Beendet die Funktion
            else:  # Bei einem anderen Statuscode
                print(f"Node-RED error: {response.status_code}")  # Zeigt den Fehlerstatus an
        except Exception as e:  # Fehlerbehandlung bei der Anfrage
            print(f"Error sending data (Attempt {attempt + 1}/{retries}):", e)  # Gibt den Fehler aus
            time.sleep(5)  # Pause zwischen den Versuchen
    print("Failed to send data after multiple attempts.")  # Gibt aus, dass alle Versuche fehlgeschlagen sind

# Temperatur vom DS18x20 Sensor auslesen
def read_temperature():
    devices = ds_sensor.scan()  # Sucht nach verbundenen DS18x20 Geräten
    if not devices:  # Wenn keine Geräte gefunden wurden
        if debug_bool:  # Falls der Debug-Modus aktiviert ist
            print("No DS18x20 devices found.")  # Gibt aus, dass keine Geräte gefunden wurden
        return None  # Gibt None zurück
    ds_sensor.convert_temp()  # Startet die Temperaturmessung
    time.sleep(1)  # Wartet 1 Sekunde, um dem Sensor Zeit zu geben
    return ds_sensor.read_temp(devices[0])  # Gibt die gemessene Temperatur zurück

# Logdatei initialisieren
def initialize_log_file():
    if log_file_path not in os.listdir():  # Überprüft, ob die Logdatei bereits existiert
        with open(log_file_path, "w") as log_file:  # Erstellt die Logdatei
            log_file.write("Index,Date,Time,Temperature,Status\n")  # Schreibt die Headerzeile in die Logdatei
        return 0  # Wenn die Datei neu erstellt wurde, startet der Index bei 0
    else:
        # Wenn die Logdatei existiert, den höchsten Index aus der Datei ermitteln
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()
            last_line = lines[-1] if lines else None
            if last_line:
                last_index = int(last_line.split(",")[0])  # Der Index befindet sich in der ersten Spalte
                return last_index + 1  # Erhöht den letzten Index um 1
            return 0  # Falls die Datei leer ist, startet der Index bei 0

# Eintrag zur Logdatei hinzufügen
def append_to_log(index, date, time_str, temperature, status):
    with open(log_file_path, "a") as log_file:  # Öffnet die Logdatei zum Anhängen
        log_file.write(f"{index},{date},{time_str},{temperature},{status}\n")  # Fügt einen neuen Logeintrag hinzu

# Temperaturdifferenz prüfen (nur bei sinkender Temperatur)
def check_temperature_difference(last_temp, current_temp):
    if last_temp is not None and current_temp is not None:  # Überprüft, ob beide Temperaturwerte vorhanden sind
        if current_temp < last_temp:  # Nur bei einer sinkenden Temperatur eine Änderung feststellen
            temp_diff = last_temp - current_temp  # Berechne die Differenz
            if temp_diff >= 2:  # Wenn die Temperatur um mindestens 2°C gesunken ist
                return temp_diff  # Gibt die Differenz zurück
    return None  # Gibt None zurück, wenn keine signifikante Differenz festgestellt wurde

# Hauptlogik
def main():
    reed_last_state = reed_pin.value()  # Liest den letzten Zustand des Reed-Sensors
    temp_last_value = None  # Initialisiert die Variable für den letzten Temperaturwert
    log_index = initialize_log_file()  # Ruft die Funktion auf, um den Logindex zu ermitteln
    alert_sent = False  # Initialisiert den Alarm-Status

    try:
        connect_wifi()  # Stellt die WLAN-Verbindung her

        while True:  # Startet eine Endlosschleife
            reed_state = reed_pin.value()  # Liest den aktuellen Zustand des Reed-Sensors
            if reed_state != reed_last_state:  # Wenn sich der Zustand des Reed-Sensors geändert hat
                reed_last_state = reed_state  # Aktualisiert den letzten Zustand
                temp_value = read_temperature()  # Liest die aktuelle Temperatur
                if temp_value is not None:  # Wenn die Temperatur erfolgreich gelesen wurde
                    temp_last_value = temp_value  # Setzt den letzten bekannten Temperaturwert

                current_time = time.localtime()  # Holt die aktuelle Zeit
                date_str = f"{current_time[2]:02d}/{current_time[1]:02d}/{current_time[0]}"  # Formatiert das Datum
                time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"  # Formatiert die Uhrzeit

                temperature = temp_last_value if temp_last_value is not None else "N/A"  # Setzt die Temperatur (falls vorhanden)
                append_to_log(log_index, date_str, time_str, temperature, reed_state)  # Fügt einen Logeintrag hinzu
                log_index += 1  # Erhöht den Log-Index
                send_data({"reed_state": reed_state}, node_red_url_reed)  # Sendet den Zustand des Reed-Sensors an Node-RED

            # Temperaturänderung prüfen
            temp_value = read_temperature()  # Liest die aktuelle Temperatur
            if temp_value is not None:  # Wenn die Temperatur erfolgreich gelesen wurde
                temp_diff = check_temperature_difference(temp_last_value, temp_value)  # Prüft die Temperaturdifferenz
                if temp_diff is not None:  # Wenn eine signifikante Temperaturänderung festgestellt wurde
                    # Alarm senden, wenn eine signifikante Temperaturverringerung festgestellt wurde
                    send_data({"alert": "Temperature decreased significantly", "temperature": temp_value}, node_red_url_alert)
                    # Danach keine separate Temperatur mehr senden
                    alert_sent = True  # Alarm wurde gesendet
                    temp_last_value = temp_value  # Setzt den letzten bekannten Temperaturwert
            else:  # Wenn die Temperaturmessung fehlschlägt
                if debug_bool:  # Falls der Debug-Modus aktiviert ist
                    print("Temperature reading failed.")  # Gibt aus, dass die Temperaturmessung fehlgeschlagen ist

            time.sleep(4)  # Pause vor der nächsten Iteration

            # Reset-Flag für den nächsten Loop
            alert_sent = False  # Setzt das Flag für den Alarm zurück

    except Exception as e:  # Fehlerbehandlung für die Hauptlogik
        print(f"Error in main loop: {e}")  # Gibt den Fehler aus

# Starten der Hauptfunktion
main()  # Ruft die Hauptfunktion auf und startet das Programm

