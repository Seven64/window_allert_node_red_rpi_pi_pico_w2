# Node-RED Sensor Code

## Übersicht
Dieses Python-Skript überwacht einen Reed-Sensor und einen DS18x20-Temperatursensor. Es sendet Sensordaten an Node-RED-HTTP-Endpunkte und protokolliert Ereignisse in einer Logdatei.

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
- `ntptime` (für Zeitsynchronisation)

## Setup
### WLAN-Zugangsdaten
Bearbeite die folgenden Abschnitte im Code, um deine WLAN-Daten anzugeben:

```python
WIFI_CONFIG = [
    {"ssid": "SSID_1", "password": "PASSWORD_1"},
    {"ssid": "SSID_2", "password": "PASSWORD_2"}
]
```

### Node-RED-URLs
Passe die Endpunkte für deinen Node-RED-Server an:

```python
NODE_RED_BASE_URL = "http://192.168.0.199:1880"
ENDPOINTS = {
    "reed": "/reed_sensor",
    "temp": "/temp_sensor",
    "alert": "/temp_alert"
}
```

### Hardware-Anschluss
Verwende die folgenden GPIO-Pins für die Sensoren:
- Reed-Sensor: GPIO 17
- DS18x20-Sensor: GPIO 16

## Funktionen
### `connect_wifi()`
Verbindet das Gerät mit einem der angegebenen WLAN-Netzwerke. Falls eine Verbindung erfolgreich ist, wird die Systemzeit synchronisiert.

### `sync_time()`
Synchronisiert die Systemzeit mit einem NTP-Server.

### `get_formatted_time()`
Liefert das aktuelle Datum und die aktuelle Uhrzeit als formatierte Zeichenkette.

### `read_temperature()`
Liest die Temperatur vom DS18x20-Sensor aus und gibt den Wert zurück.

### `send_data(url, data)`
Sendet JSON-Daten an den angegebenen Node-RED-Endpunkt per HTTP-POST-Anfrage mit Wiederholungsmechanismus bei Fehlern.

### `DataLogger`
Eine Klasse zur Verwaltung der Logdatei:
- `initialize_log()`: Erstellt die Logdatei, falls sie nicht existiert.
- `get_last_index()`: Holt den letzten Index aus der Logdatei.
- `log_entry(temp, status)`: Speichert einen neuen Eintrag in die Logdatei.

### `main()`
Die Hauptschleife zur Überwachung des Reed-Sensors und der Temperatur. Es werden Daten an Node-RED gesendet und Ereignisse protokolliert. Bei plötzlichen Temperaturabfällen wird eine Alarmmeldung gesendet.

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
Verbinde mit G101...
Verbunden!
IP: 192.168.0.100
Zeit synchronisiert: (2025, 1, 1, 12, 0, 0, 2, 1)
Current reed state: 1
Current temperature: 22.5°C
Data sent successfully.
```

---

> **Hinweis**: Weitere Informationen zu Node-RED und dem Einrichten eines MicroPython-Geräts findest du in den entsprechenden Dokumentationen.
