# РакушкаBreach

**Турнир:** SolarCTF · **Категория:** forensics

**Статус:** Решено.

## Кратко

Следы ShellBags указывают нужный LNK. UUID node из его TrackerDataBlock — XOR-ключ скрытого NTFS-потока Excel-файла.

## Решение

### 1. Прочитать NTFS и повреждённый hive

В `solar_forensic.zip` находится динамический VHD: размер 64 MiB, блоки 2 MiB, NTFS начинается с offset 65536. В todo.txt указан ключ `dr0pp3d_th3_k3y`; повторяющийся XOR снимает маску с NTUSER.DAT. Первые 20 байт заголовка дополнительно обнулены, но hbin и nk/vk cells читаются напрямую.

### 2. Проследить ShellBags к LNK

В `Software/Microsoft/Windows/Shell/BagMRU` порядок SolarGrid — `[2,1,0,3]`, первым идёт Export. Его порядок `[2,0,1,3]` выделяет `drop_link.lnk`; у Reports порядок `[1,0,2,3]` выделяет `report_q3.xlsx`. ShellBags подтверждают просмотр объектов, но сами по себе не доказывают передачу файлов.

### 3. Извлечь ключ и расшифровать ADS

TrackerDataBlock LNK начинается с offset 157. Droid File GUID содержит bytes `f0e8d7c6b5a3d811aa63aabbcc112233`; последние шесть байт node — `aa bb cc 11 22 33`. Ими выполнить повторяющийся XOR 44 байт ADS `report_q3.xlsx:metadata`. Использовать бинарные байты, а не ASCII-строку `aabbcc112233`. Независимый разбор исходника подтвердил флаг.

## Флаг

```text
SOLARCTF{sh3llb4g_m4nual_pars1ng_is_th3_w4y}
```
