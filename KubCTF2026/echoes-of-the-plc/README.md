# Echoes of the PLC

**Турнир:** KubCTF · **Категория:** forensics

**Статус:** Решено.

## Кратко

MQTT-манифест указывает скрытую связку Modbus и ICMP. XOR двух потоков и zlib восстанавливают журнал с флагом.

## Решение

### 1. Найти инструкцию в MQTT

Топик `facility/maintenance/calibration-manifest` задаёт Modbus/TCP unit 7, function 0x04, сортировку по transaction ID и маску из ICMP Echo Reply с identifier 3199. Заметный поток UDP/9001 с BKP3 оказывается отвлекающим.

### 2. Собрать два потока

Извлечь девять ответов Modbus с TID 0x4001–0x4009. Для каждого TID взять данные ICMP с `sequence = TID − 0x4000`. Склеить потоки в этом порядке, выполнить побайтовый XOR, затем zlib.decompress. Получается 139-байтный журнал. Независимый повтор на исходном PCAP подтвердил строку флага.

## Флаг

```text
KubSTU{modbus_echoes_keep_the_secret}
```
