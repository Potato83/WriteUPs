# [Beginner] Vireo

**Турнир:** KubCTF · **Категория:** web

**Статус:** Решено.

## Кратко

В GraphQL доступны introspection и внутреннее поле `secret`. Схема раскрывает путь к флагу без обхода аутентификации.

## Решение

### 1. Прочитать схему

Introspection корневого Query показывает объект `internal`. У типа Internal доступны `buildRef`, `deployedBy` и `secret`.

### 2. Запросить внутреннее поле

Отправить POST на `/graphql` с JSON-телом:

```json
{"query":"{ internal { buildRef deployedBy secret } }"}
```

Флаг находится в `data.internal.secret`. Независимая проверка повторила запрос и подтвердил значение.

## Флаг

```text
kubstu{v1r30_1ntr0sp3ct10n_869998f1}
```
