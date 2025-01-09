# Node-RED Sensor Code

## Übersicht
Dieses Python-Skript ermöglicht die Überwachung eines Reed-Sensors und eines DS18x20-Temperatursensors. Es sendet Sensordaten an Node-RED-HTTP-Endpunkte und protokolliert Ereignisse in einer Logdatei.

## Anforderungen
- MicroPython-kompatibles Gerät (z. B. ESP32 oder ESP8266)
- DS18x20-Temperatursensor
- Reed-Sensor
- WLAN-Verbindung
- Node-RED-Server

## Bibliotheken
Die folgenden MicroPython-Bibliotheken werden benötigt:
- `machine` (für GPIO- und Hardwarezugriff)
- `time` (für Zeitoperationen)
- `urequests` (für HTTP-Anfragen)
- `network` (für WLAN-Verbindungen)
- `ds18x20` (für DS18x20-Sensoren)
- `onewire` (für das OneWire-Protokoll)
- `os` (für Dateiverwaltung)

## Setup
### WLAN-Zugangsdaten
Bearbeite die folgenden Abschnitte im Code, um deine WLAN-Daten anzugeben:

```python
# WLAN-Zugangsdaten (z. B. für Zuhause oder Schule)
SSID = 'DeinSSID'  # Netzwerkname
PASSWORD = 'DeinPasswort'  # Netzwerkpasswort
```

### Node-RED-URLs
Passe die Endpunkte für deinen Node-RED-Server an:

```python
node_red_url_reed = 'http://<IP-Adresse>:1880/reed_sensor'
node_red_url_temp = 'http://<IP-Adresse>:1880/temp_sensor'
node_red_url_alert = 'http://<IP-Adresse>:1880/temp_alert'
```

### Hardware-Anschluss
Verwende die folgenden GPIO-Pins für die Sensoren:
- Reed-Sensor: GPIO 17
- DS18x20-Sensor: GPIO 16

## Funktionen
### `connect_wifi()`
Verbindet das Gerät mit dem angegebenen WLAN.

### `send_data(payload, url, retries=3)`
Sendet Daten als HTTP-POST-Anfrage an den angegebenen Node-RED-Endpunkt. Wiederholt die Anfrage bei Fehlern.

### `read_temperature()`
Liest die Temperatur vom DS18x20-Sensor aus und gibt den Wert zurück.

### `initialize_log_file()`
Initialisiert die Logdatei, falls sie nicht existiert.

### `append_to_log(index, date, time_str, temperature, status)`
Fügt einen neuen Eintrag in die Logdatei hinzu.

### `main()`
Die Hauptschleife zur Überwachung des Reed-Sensors und der Temperatur. Sendet Daten an Node-RED und protokolliert Ereignisse.

## Logging
Das Skript speichert Ereignisse in einer CSV-Datei namens `log.csv` im folgenden Format:

```
Index,Date,Time,Temperature,Status
0,01/01/2025,12:00:00,25.5,1
```

## Nutzung
1. Lade das Skript auf dein MicroPython-Gerät hoch.
2. Passe WLAN-Daten, Node-RED-URLs und Hardware-Anschlüsse an.
3. Starte das Skript.
4. Überprüfe die Logs und Node-RED-Daten.

## Fehlerbehandlung
Das Skript enthält Fehlerbehandlungslogik für:
- WLAN-Verbindungsprobleme
- HTTP-Fehler bei der Datenübertragung
- Temperaturmessfehler

## Beispielausgabe
```
Connecting to Wi-Fi...
Wi-Fi connected: ('192.168.0.100', '255.255.255.0', '192.168.0.1', '8.8.8.8')
Current reed state: 1
Current temperature: 22.5°C
Data sent successfully.
```

---

> **Hinweis**: Weitere Informationen zu Node-RED und dem Einrichten eines MicroPython-Geräts findest du in den entsprechenden Dokumentationen.
