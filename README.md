# Logitech Z906 für Home Assistant

Custom Integration für das **Logitech Z906** mit der Firmware [Z906RemoteESP32](https://github.com/kasi09/Z906RemoteESP32). Das Gerät wird im Netzwerk automatisch gefunden und ohne MQTT oder YAML eingerichtet. Zustände kommen live über den Event-Stream des ESP32, auch wenn per Fernbedienung oder Weboberfläche bedient wird.

## Voraussetzungen

- Home Assistant 2025.1 oder neuer
- Z906RemoteESP32 **ab Firmware 2.3.0** (liefert `/info`, `/health` und den mDNS-Dienst `_z906._tcp`)

## Installation

**Manuell:** den Ordner `custom_components/z906` nach `config/custom_components/z906` kopieren und Home Assistant neu starten.

**HACS:** HACS → Benutzerdefinierte Repositories → dieses Repository als Typ *Integration* hinzufügen. Das geht nur, solange das Repository öffentlich ist. Bei einem privaten Repository manuell installieren.

## Einrichtung

- **Automatisch:** Home Assistant meldet *Neues Gerät gefunden: Logitech Z906* → **Hinzufügen**.
- **Manuell:** Einstellungen → Geräte & Dienste → Integration hinzufügen → *Logitech Z906* → IP-Adresse oder Hostname des ESP32.

Ändert sich die IP-Adresse per DHCP, übernimmt die Integration die neue Adresse bei der nächsten Erkennung.

## Entitäten

| Entität | Typ | Funktion |
|---|---|---|
| Logitech Z906 | Mediaplayer | Ein/Aus, Hauptlautstärke, Mute, Eingang (6-Kanal, Cinch, Optisch 1/2, Koaxial, AUX), Klangmodus |
| Klangmodus | Auswahl | 3D, 2.1, 4.1, Aus |
| Dolby/DTS 5.1 | Schalter | 5.1-Dekodierung |
| Center, Rear, Subwoofer | Zahl (0–43) | Pegel wie an der Konsole |
| Temperatur | Sensor | Verstärkertemperatur in °C |
| Eingangspegel | Sensor | Rohwert des Eingangssignals (0 = Stille) |
| WLAN-Signal | Sensor (Diagnose) | RSSI des ESP32 |
| Brownouts | Sensor (Diagnose) | Unterspannungs-Resets seit dem Flashen |
| Laufzeit | Sensor (Diagnose, deaktiviert) | Sekunden seit dem letzten Start |

Antwortet der Verstärker nicht (Subwoofer am Netzschalter aus, Kabel ab), sind die Z906-Entitäten *nicht verfügbar*. WLAN-Signal und Brownouts bleiben sichtbar, solange der ESP32 erreichbar ist.

## Beispiel-Automation

```yaml
automation:
  - alias: Z906 an, wenn der Fernseher angeht
    triggers:
      - trigger: state
        entity_id: media_player.fernseher
        to: "on"
    actions:
      - action: media_player.turn_on
        target:
          entity_id: media_player.logitech_z906
      - action: media_player.select_source
        target:
          entity_id: media_player.logitech_z906
        data:
          source: Optisch 1
```

## Entwicklung

```bash
python -m venv .venv && .venv/bin/pip install pytest-homeassistant-custom-component
.venv/bin/pytest
```

## Lizenz

MIT, siehe [LICENSE](LICENSE).
