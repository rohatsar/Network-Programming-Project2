# Multi-User Chat System (Network Programming - Project 02)

A multi-threaded TCP chat server, console client, optional TCP relay, and WebSocket live monitoring page, written in Python.

Features: public broadcast, private messages (`/msg`), nickname validation, rate limiting, persistent file logging, live monitoring, and relay forwarding.

> Note: Client and server messages are displayed in Turkish.

## 1. Requirements

- Python 3.x
- `websocket-server` (used only for the live monitoring WebSocket)

The chat server, client and relay use only the standard library (`socket`, `threading`, `datetime`, `time`).

```bash
pip install websocket-server
```

## 2. Project Files

| File | Description |
|---|---|
| `chat_server.py` | TCP chat server. Handles clients with one thread each, routes messages, enforces rate limits, writes logs, and broadcasts live metrics over WebSocket. |
| `chat_client.py` | Console TCP client. Connects directly to the server or through the relay. |
| `relay.py` | Optional TCP relay (T07). Accepts client connections, adds a `*` prefix to the nickname, and forwards traffic to and from the main server. |
| `frontend.html` | Monitoring dashboard. Shows active user count, processed message count and live server logs. |
| `sohbet_kayitlari.txt` | Log file created by the server (appended on every run). |

## 3. How to Run

### Step 1: Start the server

```bash
python chat_server.py
```

Press Enter to use the detected local IP, then enter the chat port (default `1903`) and the WebSocket monitoring port (default `2182`). The console prints the WebSocket address, for example `ws://192.168.1.106:2182`.

### Step 2: Open the monitoring page

Open `frontend.html` in a browser, enter the WebSocket address printed by the server, and click **Bağlan**. Open it before the clients connect, because it only shows events that happen after it connects.

### Step 3: Start clients

```bash
python chat_client.py
```

Enter the server IP, port (`1903`) and a nickname.

### Step 4: Start the relay (optional, T07)

```bash
python relay.py
```

Enter the main server IP and port (`1903`), then the relay port (default `2003`). Connect a client to the **relay port** instead of the server port. The client is registered as a `*`-prefixed nickname (for example `*Rohat`).

## 4. Client Commands

| Command | Description |
|---|---|
| any text | Public message to all connected users |
| `/msg <nickname> <message>` | Private message to one user (nicknames cannot contain spaces) |
| `/liste` | Shows the list of connected users |
| `cikis` | Disconnects from the server |

## 5. Rules and Behavior

- **Nicknames:** If a nickname is taken, a numeric suffix is added (`Rohat`, `Rohat1`, `Rohat2`). Empty nicknames and nicknames starting with `*` are rejected on direct connections. Only the relay can register `*`-prefixed nicknames.
- **Message length:** Messages longer than 500 characters are rejected.
- **Rate limit:** More than 5 messages within 10 seconds mutes the user for 15 seconds. While muted, the user receives the remaining time on each attempt.
- **Cleanup:** When a client exits or its connection drops, the server removes it from the user list, announces it to the others and logs it.

## 6. Protocol Summary

All messages are text lines ending with `\n` (UTF-8).

| Message | Direction | Meaning |
|---|---|---|
| `NICK:<name>` | client -> server | Register a nickname |
| `RELAY_NICK:<name>` | relay -> server | Register a nickname through the relay (the `*` prefix is added by the relay) |
| `OK:<name>` | server -> client | Registration accepted, assigned nickname |
| `HATA:<text>` | server -> client | Error message |
| `EXIT` | client -> server | Sent when the user types `cikis` |

Monitoring packets sent over WebSocket have the format `active_users|total_messages|log_line`. Because log lines can also contain `|`, the page splits only on the first two separators.

## 7. Log File

Each line has the format `[YYYY-MM-DD HH:MM:SS] TYPE: details`. Event types:
`SERVER`, `BAGLANTI`, `PUBLIC`, `PRIVATE`, `HATA`, `RATE_LIMIT`, `CIKIS`, `AYRILMA`.

## 8. Test Scenarios and Screenshots

| Test | Screenshot | What it shows |
|---|---|---|
| T01 Public chat | `Test1.png` | Public messages with timestamps seen by all clients |
| T02 Private chat | `Test2.png` | `/msg` delivered only to the target, third client sees nothing, offline target error |
| T03 Nicknames | `Test3_1.png`, `Test3_2.png`, `Test3_3.png` | Duplicate names get a numeric suffix; `*` prefixed and empty nicknames are rejected |
| T04 Disconnect | `Test4.png` | Exit with `cikis` and connection drop, user removed from the list and announced |
| T05 Rate limit | `Test5.png` | 15 second mute after 5 messages in 10 seconds, with countdown |
| T06 Logs and live monitoring | `Test6_1.png`, `Test6_2.png` | Live counters and log stream on the monitoring page, matching entries in `sohbet_kayitlari.txt` |
| T07 Relay (optional) | `Test7.png` | Client connected through the relay gets `*Rohat`, exchanges messages with a direct client, and is cleaned up on exit |

## 9. Known Limitations

- **Exit command:** The client sends `EXIT` when the user types `cikis`, but the server only recognizes `cikis` as an exit command. The `EXIT` line is therefore handled as a normal public message (counted and logged as `PUBLIC`) and no `CIKIS` log entry is written. The user is still removed from the list and announced through the normal disconnect handling (`AYRILMA`).
- **Nicknames with spaces:** `/msg` splits on spaces, so private messages cannot target nicknames that contain spaces.
- **Broadcast locking:** The server holds the user-list lock while sending to all clients, so one very slow client can delay others.
