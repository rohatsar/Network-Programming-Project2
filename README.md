# Multi-User Chat System (Project 02)

A multi-user TCP chat server I wrote in Python. It comes with a console client, an optional relay, and a WebSocket page for live monitoring.

The chat messages themselves are in Turkish, this README is in English.

## Requirements

Python 3 and `websocket-server` for the monitoring part:

```
pip install websocket-server
```

Everything else uses the standard library (`socket`, `threading`, `datetime`, `time`).

## Files

- `chat_server.py`: the server. It starts one thread per client, passes messages along, applies the rate limit, writes the log and sends the live numbers over WebSocket.
- `chat_client.py`: the console client. It connects to the server or to the relay.
- `relay.py`: the relay for T07. It accepts a client, puts a `*` in front of the nickname and forwards the traffic to the main server.
- `frontend.html`: the live monitoring page (active users, message count, logs).
- `sohbet_kayitlari.txt`: the log file written by the server.

## How to run

1. Start the server with `python chat_server.py`. Press Enter for the IP, use 1903 for the chat port and 2182 for the WebSocket port. The console prints the `ws://IP:2182` address.
2. Open `frontend.html` in a browser, type that address and click Bağlan. Open it before the clients connect, because the page only shows events that happen after it connects.
3. Start a client with `python chat_client.py`, then enter the server IP, port 1903 and a nickname.
4. Relay (optional): run `python relay.py`, enter the IP and port of the main server, then the relay port (2003). Connect the client to the relay port instead of the server port and you get a name like `*Rohat`.

## Commands

- Plain text goes to everyone.
- `/msg name message` goes only to that user. It does not work with names that contain spaces, because the command is split on spaces.
- `/liste` shows who is connected.
- `cikis` leaves the chat.

## Rules

- If a nickname is already taken, a number is added to the end (`Rohat`, `Rohat1`, `Rohat2`). Empty nicknames and nicknames starting with `*` are rejected. A `*` is only possible through the relay.
- Messages longer than 500 characters are rejected.
- More than 5 messages in 10 seconds mutes the user for 15 seconds. If the user keeps writing while muted, the remaining time is shown.
- When a client leaves or its connection drops, the server removes it from the list and tells the others.

## Protocol

Every message is one line ending with `\n`. A client registers with `NICK:name`, and the relay sends `RELAY_NICK:*name`. The server answers with `OK:name` or `HATA:...`. When the user types `cikis`, the client sends `EXIT` to the server. The packet sent to the monitoring page looks like `active|total|log`. Log lines can also contain `|`, so the page only splits on the first two of them.

## Log file

Each line looks like `[date time] TYPE: ...`. The types are `SERVER`, `BAGLANTI`, `PUBLIC`, `PRIVATE`, `HATA`, `RATE_LIMIT`, `CIKIS` and `AYRILMA`.

## Tests

Screenshots:

- T01 public chat: `Test1.png`
- T02 private message and offline recipient error: `Test2.png`
- T03 nickname conflict and `*` rule: `Test3_1.png`, `Test3_2.png`, `Test3_3.png`
- T04 exit and connection loss: `Test4.png`
- T05 rate limit: `Test5.png`
- T06 log file and live monitoring: `Test6_1.png`, `Test6_2.png`
- T07 relay: `Test7.png`

## Known issue

When the user types `cikis`, the client sends `EXIT` to the server, but the server only recognizes the word `cikis` as an exit command. Because of that, `EXIT` is broadcast like a normal message and no `CIKIS` line is written to the log. The user is still removed from the list when the connection closes, and an `AYRILMA` line is written.
