import machine  # Zugriff auf Hardware-Funktionen wie GPIO-Pins.
import time  # Für zeitbezogene Operationen wie Verzögerungen und Zeitstempel.
import urequests  # Eine leichtgewichtige Bibliothek für HTTP-Anfragen.
import network  # Zur Verwaltung von WLAN-Verbindungen.
import ds18x20  # Bibliothek für DS18x20-Temperatursensoren.
import onewire  # Protokollbibliothek, die von DS18x20-Sensoren benötigt wird.
import os  # Für Datei- und Verzeichnisoperationen.


# WLAN-Zugangsdaten (Schule)
SSID = 'Name'  # Der SSID-Name des WLANs.
PASSWORD = 'Passwort'  # Das Passwort für das WLAN.

# Node-RED HTTP-Endpunkte
node_red_url_reed = 'http://192.168.0.199:1880/reed_sensor'  # Node-RED-URL für Reed-Sensordaten. (Statische IP Adresse unter windows vergeben im Netzwerk der Schule.)
node_red_url_temp = 'http://192.168.0.199:1880/temp_sensor'  # Node-RED-URL für Temperatursensordaten.
node_red_url_alert = 'http://192.168.0.199:1880/temp_alert'  # Node-RED-URL für Temperaturwarnungen.


# Pin-Definitionen für Reed-Schalter (GPIO 17) und DS18x20 (GPIO 16)
reed_pin = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 17 als Eingang mit Pull-Up-Widerstand für den Reed-Schalter.
ow_pin = machine.Pin(16)  # GPIO 16 als Datenpin für den DS18x20-Temperatursensor.

# Initialisierung des OneWire-Busses
ow_bus = onewire.OneWire(ow_pin)  # Einrichtung der OneWire-Kommunikation auf GPIO 16.
ds_sensor = ds18x20.DS18X20(ow_bus)  # Initialisierung des DS18x20-Temperatursensors auf dem OneWire-Bus.

# Pfad der Logdatei
log_file_path = "log.csv"  # Dateipfad zum Speichern der Logs.

# WLAN-Verbindung
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)  # Erstellen einer WLAN-Schnittstelle im Station-Modus.
    wlan.active(True)  # Aktivieren der WLAN-Schnittstelle.
    if not wlan.isconnected():  # Überprüfen, ob keine Verbindung zum WLAN besteht.
        #print("Connecting to Wi-Fi...")  # Debug-Nachricht, die den Verbindungsversuch anzeigt.
        wlan.connect(SSID, PASSWORD)  # Versuch, sich mit dem WLAN zu verbinden.
        while not wlan.isconnected():  # Warten, bis die Verbindung hergestellt ist.
            time.sleep(0.5)  # Verzögerung, um eine schnelle Schleifenausführung zu vermeiden.
            print(".")
    print("Wi-Fi connected:", wlan.ifconfig())  # Anzeigen der Netzwerkkonfiguration des Geräts.

# Daten an Node-RED senden mit Wiederholungslogik bei Fehlern (bei langsamen Netzwerk hilfreich oder Bei störungen desn Responsecodes "200" welcher von NodeRed als bestätigung des Erhaltes der Daten gesendet wird)
def send_data(payload, url, retries=3):
    attempt = 0  # Initialisieren des Wiederholungszählers.
    while attempt < retries:  # Daten bis zur angegebenen Anzahl von Wiederholungen senden.
        try:
            print(f"Sending payload: {payload}")  # Debug-Nachricht, die die gesendeten Daten zeigt.
            response = urequests.post(url, json=payload, timeout=30)  # HTTP-POST-Anfrage an Node-RED senden. Wartezeit von 30 () um auf antwort von NodeRed im netzwerk zu warten 
            response.close()  # Verbindung schließen, um Ressourcen freizugeben.
            if response.status_code == 200:  # Überprüfen, ob der HTTP-Statuscode 200 (OK) ist.
                #print("Data sent successfully.")  # Erfolgsnachricht.
                return  # Funktion verlassen, wenn die Daten erfolgreich gesendet wurden.
            else:
                print(f"Node-RED returned error: {response.status_code}")  # Fehler mit nicht-200-Statuscode protokollieren.  --> print(f"xyz") um print alas String zu formatieren. dies ist nicht unbedingt nötog 
        except Exception as e:  # Abfangen und Behandeln von Ausnahmen während der Anfrage.
            print(f"Error sending data (Attempt {attempt + 1}/{retries}):", e)  # Debug-Nachricht für Fehler.
            attempt += 1  # Erhöhen des Wiederholungszählers.
            time.sleep(5)  # Warten vor dem erneuten Versuch, um das Netzwerk nicht zu überlasten.
    print("Failed to send data after multiple attempts.")  # Fehlermeldung nach dem Ausschöpfen der Wiederholungen.

# Funktion zum Lesen der Temperatur vom DS18x20-Sensor
def read_temperature():
    devices = ds_sensor.scan()  # Erkennen aller DS18x20-Geräte auf dem OneWire-Bus.
    if len(devices) == 0:  # Überprüfen, ob keine Geräte gefunden wurden.
        print("No DS18x20 devices found.")  # Fehlermeldung, wenn keine Sensoren erkannt wurden.
        return None  # None zurückgeben, um einen Fehler anzuzeigen.
    ds_sensor.convert_temp()  # Temperaturumwandlung bei allen erkannten Sensoren auslösen.
    time.sleep(1)  # Warten, bis die Umwandlung abgeschlossen ist (dauert normalerweise 750 ms).
    temperature = ds_sensor.read_temp(devices[0])  # Temperatur des ersten erkannten Geräts auslesen.
    return temperature  # Gemessene Temperatur zurückgeben.

# Funktion um Logdatei zu initialisieren
def initialize_log_file():
    if not log_file_path in os.listdir():  # Überprüfen, ob die Logdatei nicht existiert.
        with open(log_file_path, "w") as log_file:  # Datei im Schreibmodus erstellen und öffnen. with open(path, "w") umd die datei in jedem fall zu schließen. datei.close wird somit nicht benötigt!
            log_file.write("Index,Date,Time,Temperature,Status\n")  # CSV-Kopfzeile schreiben mit absatz, damit immer untereinander geschrieben wird

# Zur Logdatei hinzufügen
def append_to_log(index, date, time_str, temperature, status):
    with open(log_file_path, "a") as log_file:  # Logdatei im Anhangsmodus öffnen.
        log_file.write(f"{index},{date},{time_str},{temperature},{status}\n")  # Neuen Eintrag in das Log schreiben.

# Hauptschleife zum kontinuierlichen Überprüfen des Reed-Schalter-Zustands und der Temperatur
def main():
    reed_last_state = reed_pin.value()  # Speichern des Anfangszustands des Reed-Schalters.
    temp_last_value = None  # Initialisieren des letzten Temperaturwerts als None.
    temp_last_time = time.ticks_ms()  # Speichern des Zeitstempels der letzten Temperaturmessung in Millisekunden.
    log_index = 0  # Initialisieren des Log-Eintragsindex.

    try:
        connect_wifi()  # Verbindung mit WLAN herstellen.
        initialize_log_file()  # Sicherstellen, dass die Logdatei initialisiert ist.

        while True:  # Endlosschleife zur Überwachung der Sensoren.
            reed_state = reed_pin.value()  # Aktuellen Zustand des Reed-Schalters auslesen.
            print(f"Current reed state: {reed_state}")  # Debug-Nachricht für den Reed-Zustand.

            if reed_state != reed_last_state:  # Überprüfen, ob sich der Reed-Schalter-Zustand geändert hat.
                print(f"Reed state changed: {reed_state}")  # Debug-Nachricht für Zustandsänderung.
                reed_last_state = reed_state  # Aktualisieren des gespeicherten Zustands.

                current_time = time.localtime()  # Abrufen des aktuellen Datums und der Uhrzeit.
                date_str = f"{current_time[2]:02d}/{current_time[1]:02d}/{current_time[0]}"  # Formatieren des Datums als String.
                # Erklärung: {:02d} stellt sicher, dass immer zwei Ziffern angezeigt werden. Beispiel:
                # 'Keine Ziffern: {:02d}, 1 Ziffer: {:02d}, 2: {:02d}, 3: {:02d}'.format(0, 7, 42, 151)
                # Ausgabe: 'Keine Ziffern: 00, 1 Ziffer: 07, 2: 42, 3: 151'
                time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"  # Formatieren der Uhrzeit als String.

                if temp_last_value is not None:  # Überprüfen, ob ein gültiger Temperaturwert verfügbar ist.
                    temperature = temp_last_value  # Verwenden des letzten bekannten Temperaturwerts.
                else:
                    temperature = "N/A"  # Standardmäßig "N/A" verwenden, wenn keine Temperatur verfügbar ist.

                append_to_log(log_index, date_str, time_str, temperature, reed_state)  # Ereignis protokollieren.
                log_index += 1  # Log-Index erhöhen.

                send_data({"reed_state": reed_state}, node_red_url_reed)  # Reed-Zustand an Node-RED senden.

            temp_value = read_temperature()  # Aktuelle Temperatur auslesen.
            if temp_value is not None:  # Überprüfen, ob die Temperaturmessung erfolgreich war.
                print(f"Current temperature: {temp_value}°C")  # Debug-Nachricht für die Temperatur.

                current_time = time.ticks_ms()  # Aktuellen Zeitstempel in Millisekunden abrufen.

                if temp_last_value is not None:
                    if temp_value - temp_last_value >= 5 or temp_last_value - temp_value >= 5:
                        time_diff = time.ticks_diff(current_time, temp_last_time)
                        if time_diff <= 600000:
                            print(f"Significant temperature change detected: {temp_value}°C")
                            send_data({"alert": "Temperature changed by 5°C within 10 minutes", "temperature": temp_value}, node_red_url_alert)

                temp_last_value = temp_value  # Aktualisieren des gespeicherten Temperaturwerts.
                temp_last_time = current_time  # Aktualisieren des Zeitstempels der letzten Temperaturmessung.

                send_data({"temperature": temp_value}, node_red_url_temp)  # Temperatur an Node-RED senden.
            else:
                print("Temperature reading failed.")  # Fehlermeldung für fehlgeschlagene Temperaturmessung.

            time.sleep(2)  # 2 Sekunden warten vor der nächsten Iteration.

    except Exception as e:  # Abfangen aller Laufzeitausnahmen.
        print("An error occurred:", e)  # Fehlermeldung ausgeben.
    except KeyboardInterrupt:  # Abfangen eines manuellen Programmstopps (z. B. Strg+C).
        print("Program stopped.")  # Benutzer über Programmbeendigung informieren.

# Hauptschleife ausführen
main()  # Programm starten, indem die Hauptfunktion ausgeführt 