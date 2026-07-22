# Anleitung: Telegram-Benachrichtigungen einrichten (von Null)

Für den Fall, dass du Telegram neu einrichten musst (neuer Bot, neues Handy,
Token verloren, neues Repo). Dauer: ~10 Minuten.

Diese Anleitung hat nach jedem Schritt einen **Kontrollpunkt** — erst weitermachen,
wenn er erfüllt ist. Die häufigsten Fehler aus der Praxis sind eingearbeitet.

**Tipp vorweg:** Mach alles am PC. Öffne dazu [web.telegram.org](https://web.telegram.org)
im Browser und melde dich mit deiner Handynummer an — dann kannst du Token & Co.
bequem kopieren, statt am Handy zu frickeln.

---

## Schritt 1: Bot bei BotFather anlegen

1. In Telegram oben auf die **Lupe** → `BotFather` eintippen
2. Den Eintrag **BotFather** mit dem **blauen Verifizierungshäkchen** öffnen
   (es gibt Nachahmer ohne Häkchen — Finger weg!)
3. Unten **Start** drücken
4. Nachricht senden: `/newbot`
5. Erste Frage (Name): frei wählbar, z. B. `BTC Signale`
6. Zweite Frage (Benutzername): muss auf `bot` enden und weltweit einmalig sein,
   z. B. `kaiser_btc_signal_bot` (falls vergeben: Zahl anhängen)

**Kontrollpunkt:** BotFather antwortet mit „Done! …". In dieser Nachricht steht der
**Token** — eine Zeichenkette im Format `123456789:AAH…` **mit Doppelpunkt in der
Mitte**. Ohne diese Nachricht nicht weitermachen.

## Schritt 2: Token kopieren

Token aus der „Done!"-Nachricht komplett kopieren (am PC markieren → Strg+C;
am Handy Finger drauf halten → Kopieren). Der Token muss den Doppelpunkt enthalten
und darf keine Leerzeichen am Anfang/Ende haben.

⚠️ Der Token ist wie ein Passwort. Nie in Dateien, Chats oder den Code schreiben —
er kommt gleich AUSSCHLIESSLICH in die GitHub-Secrets. (Falls er doch mal öffentlich
wird: bei BotFather `/revoke` → neuer Token → Secret aktualisieren.)

## Schritt 3: Dem eigenen Bot schreiben (PFLICHT, wird gern vergessen!)

1. In der „Done!"-Nachricht steht ein Link `t.me/…bot` → anklicken
2. Unten **Start** drücken (oder irgendeine Nachricht schicken, z. B. „Hallo")

**Warum:** Telegram-Bots dürfen dir erst schreiben, nachdem DU ihnen zuerst
geschrieben hast. Ohne diesen Schritt scheitert später alles mit „chat not found".

**Kontrollpunkt:** Der Bot taucht in deiner Chat-Liste auf und dein „Start"/„Hallo"
steht im Chatverlauf.

## Schritt 4: Chat-ID herausfinden

1. Neuen Browser-Tab öffnen
2. In die Adresszeile — als EINE Zeile, ohne Leerzeichen, ohne spitze Klammern:
   `https://api.telegram.org/bot` + **dein Token** + `/getUpdates`
   Beispiel: `https://api.telegram.org/bot123456789:AAHxyzabc/getUpdates`
3. Enter. Es erscheint eine Textseite. Darin die Stelle `"chat":{"id":` suchen —
   die **Zahl direkt dahinter** ist deine Chat-ID (z. B. `7350129846`). Notieren.

**Wenn die Seite nur `{"ok":true,"result":[]}` zeigt:** Schritt 3 nachholen (dem Bot
NOCHMAL eine Nachricht schicken) und die Seite neu laden.
**Wenn `{"ok":false,"error_code":401…}` erscheint:** Token falsch kopiert — zurück
zu Schritt 2.

## Schritt 5: BEIDE Secrets bei GitHub anlegen

Hier passierte der Fehler beim ersten Mal: Es wurde nur EIN Secret gespeichert.
Es müssen **zwei** sein, und beide unter **Repository secrets** (nicht „Variables",
nicht „Environment secrets").

1. Öffne: [Settings → Secrets and variables → Actions](https://github.com/szoceikaiser/btc-signal-app/settings/secrets/actions)
2. Du bist im Reiter **„Secrets"** (nicht „Variables"!)
3. **New repository secret** → Name: `TELEGRAM_BOT_TOKEN` (exakt so — am besten von
   hier kopieren) → Secret: den Token einfügen → **Add secret**
4. NOCHMAL **New repository secret** → Name: `TELEGRAM_CHAT_ID` → Secret: die Zahl
   aus Schritt 4 → **Add secret**

**Kontrollpunkt (wichtig!):** Unter „Repository secrets" stehen jetzt **ZWEI Zeilen**:
`TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID`. Steht dort nur eine → Schritt 5
wiederholen für die fehlende.

## Schritt 6: Testnachricht senden

1. [Actions → Signal-Engine](https://github.com/szoceikaiser/btc-signal-app/actions/workflows/signal.yml)
2. Rechts **Run workflow** → **Haken setzen** bei „Nur Telegram-Testnachricht
   senden" → grüner Knopf
3. ~30 Sekunden warten

**Kontrollpunkt:** Telegram-Nachricht „TESTNACHRICHT — Einrichtung ok" auf dem Handy.

## Wenn keine Nachricht kommt: Fehlerdiagnose

Den Lauf anklicken → Job **„run"** → Zeile **„Telegram-Testnachricht"** aufklappen:

| Im Protokoll steht … | Ursache | Lösung |
|---|---|---|
| `[DRY-RUN]` | Secrets nicht gefunden: fehlen, falsch benannt, im falschen Reiter (Variables) oder als Environment-Secret angelegt | Schritt 5 prüfen — exakte Namen, Reiter „Secrets", „Repository secrets", BEIDE Zeilen vorhanden |
| `Telegram-Fehler: … 401` | Token falsch/unvollständig | Token neu aus BotFather-Nachricht kopieren (mit Doppelpunkt!), Secret `TELEGRAM_BOT_TOKEN` neu setzen (anklicken → Update) |
| `Telegram-Fehler: … 400` / „chat not found" | Chat-ID falsch ODER Schritt 3 (Bot anschreiben) vergessen | Schritt 3 + 4 wiederholen, Secret `TELEGRAM_CHAT_ID` aktualisieren |
| Lauf grün, Protokoll ohne Fehler, trotzdem nichts | Nachricht ging in einen anderen Chat | Chat-ID prüfen (Schritt 4) — es muss die ID aus DEINEM Chat mit dem Bot sein |

Nach jeder Korrektur: Schritt 6 wiederholen.
