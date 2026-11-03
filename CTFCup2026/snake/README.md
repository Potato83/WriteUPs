# snake: homm3 edition

**Турнир:** Кубок CTF России 2026 · **Категория:** misc

**Статус:** Решено.

## Кратко

Бот проходит по гамильтонову циклу на шестиугольном поле и собирает еду до заполнения всех 61 клеток.

## Решение

Поле радиуса 4 содержит `1 + 3R(R+1) = 61` клетку. Направления `0…5` соответствуют смещениям в массиве `DIRS`; сервер принимает ходы через `/ws` и возвращает новое состояние после каждого хода.

Маршрут начинается в `(0, -1)`, проходит через каждую клетку ровно один раз и возвращается к началу. Дожидаясь ответа сервера перед следующим ходом, бот не сталкивается с телом и рано или поздно собирает всю еду. Запустите код в консоли браузера на странице задания:

```javascript
(() => {
    const DIRS = [
        [1, 0],
        [1, -1],
        [0, -1],
        [-1, 0],
        [-1, 1],
        [0, 1]
    ];

    const route =
        "5112233444455550000111122223555544433322211105344550011244321";

    // Generate coordinate -> direction map
    const moves = new Map();
    let q = 0, r = -1;

    for (const ch of route) {
        const d = Number(ch);

        moves.set(`${q},${r}`, d);

        q += DIRS[d][0];
        r += DIRS[d][1];
    }

    // Validate Hamiltonian cycle
    if (moves.size !== 61 || q !== 0 || r !== -1) {
        throw Error("Invalid Hamiltonian cycle");
    }

    console.log("[+] Cycle verified: 61 cells");

    // Connect directly to game server
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws`);

    let count = 0;
    let started = false;

    ws.onopen = () => {
        console.log("[+] Connected to game server");
    };

    ws.onmessage = ({data}) => {
        const s = JSON.parse(data);

        if (s.type !== "state") return;

        // Victory: server sends the flag
        if (s.won) {
            console.log("========== FLAG ==========");
            console.log(s.message);
            console.log("==========================");

            alert("FLAG: " + s.message);
            ws.close();
            return;
        }

        if (!s.alive) {
            console.error("[-] Game over");
            ws.close();
            return;
        }

        // Start from a fresh game
        if (!started && s.snake.length !== 1) {
            ws.send(JSON.stringify({type: "reset"}));
            return;
        }

        started = true;

        if (s.radius !== 4) {
            console.error("Unexpected board radius");
            ws.close();
            return;
        }

        // Find the next direction
        const head = s.snake[0];
        const dir = moves.get(`${head.q},${head.r}`);

        if (dir === undefined) {
            console.error("Head outside route", head);
            ws.close();
            return;
        }

        count++;

        if (count % 50 === 0) {
            console.log(
                `[+] Moves: ${count}, Length: ${s.length}/${s.target}`
            );
        }

        // Send one move per server state
        setTimeout(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: "move",
                    dir: dir
                }));
            }
        }, 12);
    };

    ws.onerror = (err) => console.error(err);
})();
```

После достижения длины 61 сервер возвращает `won: true` и флаг в `message`. По журналу задачи флаг принят.

## Флаг

Флаг найден.
