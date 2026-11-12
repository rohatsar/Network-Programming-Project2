# Multi-User Chat System (Network Programming - Project 02)

A multi-threaded TCP chat server, console client, TCP relay, and WebSocket live monitoring implementation in Python. Supports public broadcasting, private messaging (`/msg`), nickname validation, rate limiting, persistent file logging, and optional relay forwarding.

---

## 1. Requirements & Dependencies
The core TCP server, client, and relay use Python's standard libraries (`socket`, `threading`, `datetime`, `time`). The live monitoring WebSocket server uses `websocket-server`:
- Python 3.x
- `websocket-server`

Install the required package via pip:
```bash
pip install websocket-server
2. Project File Structure
chat_server.py: Main TCP chat server handling multiple clients via threads, message routing, rate limiting, persistent logging, and WebSocket live metrics broadcasting.

chat_client.py: Console-based TCP client for connecting directly to the server or via the relay.

relay.py: Optional TCP relay server (T07) that accepts client connections, prepends * to their nicknames, and forwards traffic to and from the main server.

frontend.html: Real-time HTML/JavaScript monitoring dashboard connected via WebSocket to display active user count, processed message count, and live server logs.

sohbet_kayitlari.txt: Persistent log file storing all server events, connections, public/private messages, rate-limit triggers, and disconnections.

3. How to Run (Execution Order)
Step 1: Start the Main Server
Run chat_server.py. Press Enter to use the detected local IP, set the TCP chat port (default: 1903), and set the WebSocket monitoring port (default: 2182):

Bash
python chat_server.py
Step 2: Open Live Monitoring (frontend.html)
Open frontend.html in a web browser, enter the WebSocket address displayed in the server console (e.g., ws://192.168.1.106:2182), and click Bağlan.

Step 3: Start Direct Clients
Open new terminal windows and run chat_client.py. Enter the server IP, port (1903), and a desired nickname:

Bash
python chat_client.py
Step 4: Start the Relay (Optional - T07)
To test relayed connections, run relay.py, specify the main server IP and port (1903), and set a relay listening port (e.g., 1904 or 2003):

Bash
python relay.py
Then connect a client (python chat_client.py) to the relay port (2003). The client will automatically be assigned a * prefixed nickname (e.g., *Rohat).

4. Available Client Commands
Public Message: Type any text and press Enter to broadcast to all connected users.

Private Message: /msg <target_nickname> <message> (sends a direct message only to the specified user).

Active User List: /liste (requests the current list of connected nicknames).

Exit: cikis (cleanly disconnects from the server).

5. Verified Test Scenarios & Screenshots
All test scenarios (T01 – T07) have been verified and documented with screenshots:

Test1.png (T01 - Public Chat): Real-time public message exchange between connected clients with timestamps.

Test2.png (T02 - Private Chat): Private /msg routing between specific clients without leaking to third parties, plus offline target error handling.

Test3_1.png, Test3_2.png, Test3_3.png (T03 - Nicknames): Automatic numeric suffix assignment (Rohat, Rohat1, Rohat2) for duplicate names and rejection of * prefixed or empty nicknames on direct connections.

Test4.png (T04 - Disconnection): Clean disconnection handling via cikis and automatic removal from the active user list.

Test5.png (T05 - Rate Limiting): Automatic 15-second mute enforcement when exceeding 5 messages within 10 seconds, complete with countdown feedback.

Test6_1.png, Test6_2.png (T06 - Logs & Live Monitoring): Real-time updates on frontend.html and matching persistent entries in sohbet_kayitlari.txt.

Test7(optional).png (T07 - Relay): Client connecting through relay.py, receiving the * prefix (*Rohat), and clean teardown on exit.
