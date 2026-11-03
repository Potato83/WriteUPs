# 21 century man

**Турнир:** Кубок CTF России 2026 · **Категория:** reverse / hardware

**Статус:** Локально восстановлен; приём флага не подтверждён.

## Кратко

Из битстрима FPGA извлекаются координаты нулей комплексной функции. Их визуализация раскрывает строку флага.

## Решение

### 1. Что делает проверялка

Архив содержит `g.bin` — битстрим iCE40 UP5K SG48 — и `problem`, Linux x86-64
GUI на Rust. Программа предлагает нарисовать фигуру и нажать Check. Она
выбирает случайную точку внутри фигуры и отправляет её вычислителю по UART
921600 8N1. Устройство проверяет условие `|g(x,y)| < 1`.

Область координат из клиента:

```text
x ∈ [-3.9, 3.9]
y ∈ [-0.12748074465531917, 0.12748074465531917]
```

Пины из README: 35 — тактовый вход 200 МГц, 6 — UART RX, 9 — UART TX.
Из реверса клиента восстановлен протокол:

| Направление | Формат |
|---|---|
| Запрос | `A5`, float32 LE x, float32 LE y, XOR восьми байт координат |
| Ответ | `5A`, float32 LE real, float32 LE imag, int32 LE exponent, flags, XOR предыдущих 13 байт полезной нагрузки |

Комплексный результат равен `(real + i·imag)·2^exponent`. В `flags` биты
`1`, `2`, `4` означают соответственно inside, pole и zero. Интерфейс выводит
«Possibly valid» после одной удачной точки; сам флаг в интерфейсе не появляется.

### 2. Восстановление таблиц из FPGA

С помощью IceStorm преобразуем битстрим в конфигурацию и Verilog:

```sh
mkdir -p artifacts
iceunpack g.bin artifacts/g.asc
icebox_vlog -s -l -d sg48 artifacts/g.asc > artifacts/g_raw.v
```

Нас интересуют 26 блоков ROM `SB_RAM40_4K`, которые читаются по одному
8-битному адресу. Это 256 записей по 416 бит. У части полей заметно знаковое
расширение: они соответствуют узкому диапазону y, остальные — диапазону x.

Порядок физических битовых линий внутри 16-битного слова переставлен.
Логическому биту `b` соответствует физическая позиция `reverse4(b)`:

```text
0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15
```

После перестановки слово интерпретируется как signed int16. Реальная
координата получается делением на `4096`. Пары x/y восстановлены по двум
деревьям селекторов схемы и независимо подтверждены статистикой повторений
координат. Всего получено `13 × 256 = 3328` пар.

Симуляция выявила записи полюсов: пара ROM `(y13,x20)` и адреса `124–255`
пары `(y7,x10)`. После их исключения остаются 2940 записей, образующих текст.
Полюса в этих диапазонах и нули остальных полей проверялись выборочно;
переход на адресе 124 проверен для каждого адреса от 96 до 128.

Полный скрипт ниже начинает с оригинального `g.bin`, автоматически извлекает
таблицы и сохраняет CSV и изображение. Последний шаг — визуальное чтение
надписи; автоматическое OCR в скрипт не подменяется заранее заданным флагом.

Зависимости: IceStorm 1.1 и Python 3 с matplotlib. Проверочная симуляция
выполнялась Verilator 5.048.

```sh
sudo apt-get install fpga-icestorm python3-matplotlib
# Поместите g.bin из архива задания рядом со скриптом.
python3 solve.py
```

```python
#!/usr/bin/env python3
"""Recover the coordinate cloud embedded in the original iCE40 bitstream."""
import csv
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BITSTREAM = ROOT / 'g.bin'
OUT = ROOT / 'artifacts'
# Logical 16-bit word uses the bit-reversed four-bit memory lane index.
LANE = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15]
# Pairs found by tracing the two coordinate selector trees; indices refer to
# 256x16 ROMs in the order emitted by icebox_vlog.
PAIRS = [(1,22), (21,4), (2,14), (15,18), (9,23), (13,20), (5,12),
         (0,24), (19,6), (3,8), (17,16), (11,25), (7,10)]

def signed_word(physical):
    v = sum(((physical >> lane) & 1) << bit for bit, lane in enumerate(LANE))
    return v - 65536 if v >= 32768 else v

def main():
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        asc = Path(tmp) / 'g.asc'
        subprocess.run(['iceunpack', str(BITSTREAM), str(asc)], check=True)
        v = subprocess.run(['icebox_vlog','-s','-l','-d','sg48',str(asc)],
                           check=True, capture_output=True, text=True).stdout
    roms = []
    pattern = r'SB_RAM40_4K #\((.*?)\) (\w+) \((.*?)\n\);'
    for m in re.finditer(pattern, v, re.S):
        params, name, ports = m.groups()
        if 'n346, n352, n315, n347, n427, n350, n64, n351' not in ports:
            continue
        blocks = re.findall(r"INIT_[0-9A-F]\(256'h([0-9a-f]+)\)",params)
        if len(blocks) != 16:
            raise ValueError(f'invalid initialization on {name}')
        words = [signed_word((int(block, 16) >> (16*i)) & 0xffff)
                 for block in blocks for i in range(16)]
        roms.append(words)
    if len(roms) != 26:
        raise ValueError(f'expected 26 coordinate ROMs, got {len(roms)}')
    points = [(roms[x][i], roms[y][i]) for y,x in PAIRS for i in range(256)]
    # The selector order puts poles in pair (13,20) and addresses 124..255
    # of pair (7,10). The transition was checked against the UART simulator.
    zeros = [(roms[x][i], roms[y][i]) for y,x in PAIRS if (y,x)!=(13,20)
             for i in range(124 if (y,x)==(7,10) else 256)]
    csv_path = OUT / 'coordinates.csv'
    with csv_path.open('w', newline='') as f:
        w=csv.writer(f); w.writerow(['x_q12','y_q12']); w.writerows(points)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(8, 1, figsize=(20, 16))
    for i,ax in enumerate(axes):
        ax.scatter([p[0] for p in zeros], [p[1] for p in zeros], s=3, c='black')
        ax.set_xlim(-16000 + 4000*i, -12000 + 4000*i)
        ax.set_ylim(-500, 500); ax.set_aspect('equal'); ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT/'recovered.png', dpi=160)
    print(f'{len(points)} coordinate pairs: {csv_path}')
    print(f'Visualization: {OUT / "recovered.png"}')
if __name__ == '__main__':
    main()

```

Ожидаемый результат: `3328 coordinate pairs` и путь к `artifacts/recovered.png`.
Скрипт сохраняет график в `artifacts/recovered.png`; прочитайте символы по восьми увеличенным фрагментам.

### 3. Проверка и точное чтение

Извлечение повторено из исходного битстрима отдельным скриптом: мультимножества
всех 3328 координат совпали. SHA-256 пользовательского архива совпал с
официальным вложением:

```text
acf60e4f9e9e8e4f0637d8db9296ddb91581921c37f68b7520fbdc988784d610
```

Восстановленная схема симулировалась через настоящий UART-протокол.
Например, пары `(12177,-207)`, `(4349,-207)`, `(-14300,-207)`, `(1481,-207)`
и `(-2225,-6)`, поделённые на 4096, дают точный ноль и `flags=05`.
Полный ответ: `5a0000000000000000000000000505`. Для контрольной точки `(0,0)`
результат ненулевой и `flags=0`.

Разреженные контуры требуют аккуратного чтения. Позиции внутри скобок,
считая от нуля: `8 → 4`, `12 → f`, `4 → e`. В первоначальной транскрипции
последний символ был ошибочно прочитан как `a`; пользователь сообщил
`invalid flag`. Повторная проверка выявила у `e` среднюю горизонтальную
перекладину. Сопоставление с DejaVu Sans, DejaVu Sans Mono и Liberation Sans
поддерживает `e`; для остальных похожих символов на позициях 1, 10, 22 и 31
лучше совпадает `a`.

## Флаг

Флаг восстановлен локально; приём не подтверждён.

Это исправленная локальная транскрипция.
