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

Ответ GraphQL содержит значение в `data.internal.secret`.

## Флаг

Флаг найден.
