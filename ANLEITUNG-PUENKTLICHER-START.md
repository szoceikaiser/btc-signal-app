# Anleitung: Engine pünktlich starten (externer Anstoß)

**Das Problem:** GitHub gibt für zeitgesteuerte Abläufe keine Zusage. Gemessen am
29.07.2026: Von sieben Versuchen je Kerzenschluss kam **genau einer** an, mit ein bis drei
Stunden Verzug — einmal fiel ein Kerzenschluss ganz aus. Mehr Versuche haben nichts
geändert; GitHub bedient das Repo offenbar nur alle paar Stunden.

**Die Lösung:** Es gibt zwei Wege, einen Ablauf zu starten. Der Zeitplan landet in der
Warteschlange der ganzen Plattform. Ein **Anstoß von außen** wird behandelt wie dein
Knopfdruck auf „Run workflow" und läuft sofort. Genau das lassen wir automatisch machen.

Zeitaufwand: etwa 15 Minuten, einmalig. Kosten: 0 €.

**Goldene Regeln (aus Erfahrung):**
- Alles **kopieren statt tippen**.
- Nach jedem Schritt den Kontrollpunkt prüfen.
- Den Zugangsschlüssel aus Schritt 1 **nirgends sonst** einfügen — nicht in eine Datei,
  nicht in einen Chat, auch nicht zu Claude.

---

## Schritt 1 — Zugangsschlüssel erzeugen

Dieser Schlüssel darf **nur eines**: Abläufe in diesem einen Repository starten. Er kann
weder deinen Code lesen noch ändern, und er kommt nicht an deinen Telegram-Token.

1. Öffne: **https://github.com/settings/personal-access-tokens/new**
   (Das ist der Bereich *Fine-grained tokens* — nicht die alten „classic" Tokens.)
2. **Token name:** `engine-anstoss`
3. **Expiration:** frei wählbar — z. B. *1 year*. Danach musst du ihn erneuern; wenn du
   das vergisst, meldet cron-job.org einen Fehler (`401`).
4. **Repository access:** → **Only select repositories** → in der Liste
   `btc-signal-app` auswählen
5. **Permissions** → **Repository permissions** → in der langen Liste den Eintrag
   **Actions** suchen → rechts auf **Read and write** stellen
   *(„Metadata: Read-only" setzt GitHub automatisch mit dazu — das ist normal.)*
6. Ganz unten **Generate token**
7. Der Schlüssel wird **genau einmal** angezeigt. Kopiere ihn jetzt in die
   Zwischenablage — er beginnt mit `github_pat_`.

**Kontrollpunkt:** In der Übersicht steht dein Token mit dem Zusatz
`1 repository` und `Actions: Read and write`. Steht dort *All repositories*, geh zurück
und stell es auf *Only select repositories*.

---

## Schritt 2 — Konto bei cron-job.org anlegen

1. **https://cron-job.org** → **Sign up** → E-Mail und Passwort → Bestätigungsmail öffnen
2. Einloggen

Der Dienst ist kostenlos und wird in Deutschland betrieben.

---

## Schritt 3 — Auftrag anlegen

Oben rechts **CREATE CRONJOB**. Dann von oben nach unten ausfüllen:

**Titel:**
```
BTC Signal-Engine
```

**URL:** (genau so, in einer Zeile)
```
https://api.github.com/repos/szoceikaiser/btc-signal-app/actions/workflows/signal.yml/dispatches
```

**Zeitplan:** Auf **Custom** umstellen (nicht „Every 15 minutes" o. ä.), dann:

| Feld | Auswahl |
|---|---|
| Zeitzone | **UTC** — wichtig, unsere Kerzen laufen nach UTC |
| Tage / Wochentage / Monate | alle |
| Stunden | **0, 4, 8, 12, 16, 20** — nur diese sechs ankreuzen |
| Minuten | **2** |

**Erweiterte Einstellungen** aufklappen (*Advanced*):

- **Request method:** von `GET` auf **`POST`** umstellen
- **Headers** — drei Zeilen anlegen, jeweils Name und Wert:

  | Name | Wert |
  |---|---|
  | `Accept` | `application/vnd.github+json` |
  | `Authorization` | `Bearer github_pat_DEIN_SCHLUESSEL` |
  | `X-GitHub-Api-Version` | `2022-11-28` |

  Bei `Authorization`: Das Wort `Bearer`, ein Leerzeichen, dann dein Schlüssel aus
  Schritt 1. Also z. B. `Bearer github_pat_11ABC...`

- **Request body:** (genau so, mit den geschweiften Klammern)
  ```
  {"ref":"main"}
  ```

Dann **CREATE**.

---

## Schritt 4 — Sofort testen

Nicht bis zum nächsten Kerzenschluss warten. In der Auftragsliste auf deinen Auftrag
klicken → Knopf **TEST RUN**.

**Kontrollpunkt 1:** cron-job.org zeigt als Antwort **`204 No Content`**. Das sieht nach
nichts aus, ist aber genau richtig — GitHub bestätigt damit „angenommen, läuft".

**Kontrollpunkt 2:** Öffne
[Actions → Signal-Engine](https://github.com/szoceikaiser/btc-signal-app/actions/workflows/signal.yml).
Dort steht jetzt binnen Sekunden ein neuer Lauf — und zwar mit dem Zusatz
**`Manually run`** statt `Scheduled`. Genau daran erkennst du künftig, welche Läufe über
den neuen Weg kamen.

---

## Was sich damit ändert

| | vorher | ab jetzt |
|---|---|---|
| Läufe je Kerzenschluss | 1 (manchmal 0) | 1, zuverlässig |
| Verzug | 1 bis 3 Stunden | wenige Sekunden bis Minuten |

Der GitHub-Zeitplan bleibt zusätzlich bestehen — als Netz, falls cron-job.org einmal
ausfällt. Diese Läufe finden dann meist nichts Neues und beenden sich sofort. Doppelte
Telegram-Nachrichten kann es nicht geben: Die Engine merkt sich, welche Kerze sie zuletzt
ausgewertet hat.

---

## Zur Sicherheit — was der Schlüssel kann und was nicht

**Kann:** Abläufe im Repo `btc-signal-app` starten.

**Kann nicht:** deinen Code lesen oder ändern, deine anderen Repositories anfassen, oder
an deine hinterlegten Geheimnisse (Telegram-Token, Coinalyze-Key) kommen. Die liegen in
den GitHub-Secrets und sind selbst für dich nicht mehr auslesbar.

**Wenn er trotzdem in falsche Hände gerät:** Jemand könnte deine Engine starten — mehr
nicht. Im schlimmsten Fall bekommst du eine Flut alter Trigger auf Telegram (der Ablauf
hat eine Option dafür). Unangenehm, aber kein Schaden an Geld oder Daten.

**Zurückziehen** kannst du ihn jederzeit:
https://github.com/settings/personal-access-tokens → Token anklicken → **Delete**.
Ab diesem Moment ist er wertlos, auch wenn ihn jemand hat.

---

## Wenn etwas schiefgeht

| Antwort von cron-job.org | Ursache | Lösung |
|---|---|---|
| `401 Unauthorized` | Schlüssel falsch kopiert, oder `Bearer ` davor vergessen | Header `Authorization` prüfen — genau `Bearer`, Leerzeichen, Schlüssel |
| `403 Forbidden` | Berechtigung *Actions* steht nicht auf *Read and write* | Schritt 1, Punkt 5 nachholen |
| `404 Not Found` | Repo im URL falsch geschrieben, oder Token nicht für dieses Repo freigegeben | URL prüfen, dann Schritt 1, Punkt 4 |
| `422 Unprocessable` | Request body fehlt oder `main` heißt anders | Body muss exakt `{"ref":"main"}` sein |
| `204 No Content` | **kein Fehler** — das ist der Erfolgsfall | nichts tun |

Bei allem anderen: Bild von der Antwortseite machen und Claude zeigen.
