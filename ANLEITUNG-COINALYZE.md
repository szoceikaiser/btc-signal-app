# Anleitung: Kostenlosen Coinalyze-API-Key holen und hinterlegen

Coinalyze liefert uns **historisches Open Interest, Funding und echte Liquidationen**
(aggregiert über die großen Börsen) — kostenlos. Damit sieht die Engine endlich, was
Furkan sieht: welcher Dip hält und wann er kippt. Du machst das **einmal** im Browser,
danach nutzt die Engine die Daten automatisch.

**Goldene Regeln (aus Erfahrung):**
- Den Key **kopieren, nicht abtippen** — ein Tippfehler und nichts funktioniert.
- Den Key **niemandem zeigen** und **nicht** in eine Datei/Chat schreiben. Er gehört
  ausschließlich in die GitHub-Secrets (dort ist er sicher versteckt, wie der Telegram-Token).
- Nach jedem Schritt den **Kontrollpunkt** prüfen.

---

## Schritt 1 — Bei Coinalyze kostenlos anmelden

1. Öffne **https://coinalyze.net/**
2. Oben rechts **Sign up** (Registrieren) — mit E-Mail (kostenlos, keine Zahlung).
3. E-Mail bestätigen (Bestätigungslink im Postfach anklicken).

**Kontrollpunkt 1:** Du bist eingeloggt und siehst dein Konto (oben rechts dein Name/E-Mail).

---

## Schritt 2 — API-Key erzeugen

1. Öffne die API-Seite: **https://api.coinalyze.net/v1/doc/**
   (oder im Konto-Menü auf „API" / „API Key" klicken).
2. Dort gibt es einen Knopf wie **Generate API Key** / **Create Key**. Klicke ihn.
3. Es erscheint eine lange Zeichenkette (dein Key). **Markiere sie und kopiere sie**
   (Strg+C). Er sieht ungefähr so aus: `a1b2c3d4-....` (Buchstaben/Zahlen).

**Kontrollpunkt 2:** Du hast den Key in der Zwischenablage. Lass das Browser-Fenster offen,
falls du ihn nochmal kopieren musst.

---

## Schritt 3 — Key als GitHub-Secret hinterlegen (wie beim Telegram-Token)

1. Öffne die Secrets-Seite deines Repos:
   **https://github.com/szoceikaiser/btc-signal-app/settings/secrets/actions**
2. Grüner Knopf **New repository secret**.
3. Feld **Name** (EXAKT so, groß, mit Unterstrichen — kopieren):
   ```
   COINALYZE_API_KEY
   ```
4. Feld **Secret**: den kopierten Key einfügen (Strg+V).
5. **Add secret**.

**Kontrollpunkt 3:** In der Liste steht jetzt ein Secret namens **COINALYZE_API_KEY**
(der Wert selbst wird nie angezeigt — das ist richtig so).

---

## Schritt 4 — mir Bescheid geben

Schreib mir **„Coinalyze-Key ist drin"**. Dann baue ich die Anbindung fertig, und wir
testen mit einem Engine-Lauf, ob die Daten von den GitHub-Servern ankommen (Coinalyze ist
— anders als Binance-Futures — nicht US-blockiert, aber wir prüfen es einmal live).

**Falls etwas hakt** (Key-Knopf nicht gefunden, Fehlermeldung): schick mir einen Screenshot
oder beschreib, was du siehst — ich führe dich durch.
