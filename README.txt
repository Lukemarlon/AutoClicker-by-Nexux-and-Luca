AUTO CLICKER – ANLEITUNG
=========================

DATEIEN IN DIESEM ORDNER
--------------------------
- AutoClicker.py    -> der Quellcode
- icon.ico          -> eigenes Icon für die exe
- version_info.txt  -> Datei-Eigenschaften der exe (Firma, Produktname, Version...)
- build.bat          -> baut mit einem Doppelklick automatisch die fertige exe


SCHNELLSTART
--------------
1. Alle 4 Dateien in EINEN Ordner legen (nicht auf mehrere Ordner verteilen).
2. Python muss installiert sein (python.org), Haken bei "Add to PATH" setzen.
3. Doppelklick auf "build.bat".
4. Warten, bis "FERTIG: dist\AutoClicker.exe" erscheint.
5. Die fertige Datei liegt danach in einem neuen Unterordner "dist".

Diese exe:
- läuft eigenständig, es muss auf dem Ziel-PC kein Python installiert sein
- öffnet kein Konsolenfenster (--noconsole)
- hat ein eigenes Icon statt des Standard-Python-Symbols
- zeigt unter Rechtsklick -> Eigenschaften -> Details ganz normale
  Angaben wie bei anderen Programmen auch (Firma: NexuxGames,
  Produktname: Auto Clicker, Version 1.0.0.0) statt Python-Hinweisen


MANUELL BAUEN (falls du build.bat nicht nutzen willst)
----------------------------------------------------------
    pip install pynput pyinstaller pillow
    python -m PyInstaller --onefile --noconsole --name AutoClicker --icon=icon.ico --version-file=version_info.txt --clean AutoClicker.py

Falls "pyinstaller" als Befehl nicht gefunden wird, immer "python -m PyInstaller ..."
verwenden (siehe oben) statt "pyinstaller ...".


FUNKTIONEN
----------
- Aktion wählen: Linksklick, Rechtsklick, Mittelklick oder eine beliebige Taste
- Intervall in Millisekunden: 0 = so schnell wie möglich, nach oben keine Grenze
- Start/Stopp per Button ODER per Hotkey (Standard F6, änderbar über "Ändern")
- Live-Klickzähler während des Laufens
- Fenster ist skalierbar, Inhalt scrollt automatisch, falls er nicht komplett
  auf den Bildschirm passt
- Oberfläche passt sich automatisch an den Windows Hell-/Dunkelmodus an
- Credits-Bereich fest am unteren Rand: "NexuxGames · Provider: Luca"


HINWEIS ZU ANTIVIRENPROGRAMMEN
---------------------------------
Manche Antivirenprogramme melden selbstgebaute Autoclicker (auch als exe)
gelegentlich fälschlich als verdächtig, weil sie Mausklicks/Tastendrücke
simulieren. Das ist bei diesem Tool normal und unbedenklich – es greift
nicht ins Netzwerk ein und hat keine versteckten Funktionen. Falls Windows
Defender die Datei blockiert: unter "Windows-Sicherheit -> Viren- und
Bedrohungsschutz -> Zulassungen" eine Ausnahme für die exe hinzufügen.
