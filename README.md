# HR Rozcestník (TrayBookmarks)

Miniaplikace, která sedí v tray liště a otevírá popup se zástupci na interní odkazy (SharePointy, Excely apod.).

## Funkce

- Kliknutím na ikonu **HR** v tray otevřeš seznam odkazů.
- Přidávání nových pomocí tlačítka `+`.
- Mazání odkazů křížkem `×`.
- Ikony se automaticky určují dle typu odkazu:
  - **X** = Excel
  - **S** = SharePoint
  - **L** = Ostatní

## Spuštění

1. **Stažení:** spusť soubor `tray_bookmarks.exe` (Windows, bez instalace).
2. **Uložení:** Odkazy se ukládají do `bookmarks.json` ve stejné složce jako `.exe`.
3. **Trvalost:** Změny zůstanou zachované i po restartu počítače.

## Technické detaily

- Postaveno v **Pythonu** s pomocí **PySide6**.
- Aplikace běží jako **ikonka v tray liště** a neotevírá žádné klasické okno.
- Výška popupu se přizpůsobí počtu odkazů (max 12 bez posuvníku).

## Build (pro vývojáře)

```bash
pip install pyinstaller
pyinstaller tray_bookmarks.py --noconsole --onefile --add-data "bookmarks.json;."
