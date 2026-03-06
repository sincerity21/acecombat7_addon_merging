# sincerity's ACE COMBAT 7 DATA-TABLE EDITOR

A tool made to accomodate my certain needs in optimizing updates to the [Compatibility between add-on plane mods](https://www.nexusmods.com/acecombat7skiesunknown/mods/2154). 

If you're not me, or BelkanLoyalist, you may or may not need this.


### What it does

The editor works on JSON exports of UE DataTables (from UAssetAPI / UAssetGUI 1.0.2.0) and, optionally, on localization DATs (`Cmn.dat` + `A.dat`–`M.dat`) to automate the repetitive, error‑prone parts of merging plane and localization data:

- **Merge**  
  - Add **new planes** from a source add‑on into a target data set (e.g. Compat Patch).
  - Updates:
    - `PlayerPlaneDataTable.json`
    - `SkinDataTable.json`
    - `ASS/SkinDataTable.json`
    - `AircraftViewerDataTable.json`
  - Preserves proper ID/row numbering rules and asks you for each plane’s `AlphabeticalSortNumber`.

- **Replace**  
  - Update **existing planes** in the target from a source add‑on when:
    - Stats, ammo counts, or skin count change.
  - Replaces relevant rows while keeping important IDs / sort order stable.
  - Adds extra skins/viewer rows if the source has more entries for a given plane.

- **Delete**  
  - Remove selected planes from **all** target tables:
    - `PlayerPlaneDataTable.json`
    - `SkinDataTable.json`
    - `ASS/SkinDataTable.json`
    - `AircraftViewerDataTable.json`  
  - Useful when an add‑on becomes outdated or unsupported.
  - Useful when an add‑on becomes outdated or unsupported.

- **Localization (optional)**  
  - If **both** `SourceData/Localization` and `TargetData/Localization` exist, the tool also processes:
    - `Cmn.dat`
    - `A.dat`–`M.dat` (one per language, as in the base game)
  - **Merge**:
    - Imports variables from the source CMN into the target CMN.
    - Copies strings from the source DATs into the target DATs.
    - Pads target DATs so all languages have enough entries.
    - Creates **`.bak` backups** (`Cmn.dat.bak`, `A.dat.bak`, …) in the target folder the first time you touch them.
  - **Replace**:
    - Adds any **new** variables/strings from source into target.
    - For **existing** variables:
      - If the target string is empty and the source has text → the source text overwrites the target.
      - If both have non‑empty but different text → the tool **does not overwrite** and logs a “requires manual edit” line per language.

All plane‑data operations work at the JSON level; you still use UAssetAPI/UAssetGUI to go from `.uasset` ⇄ JSON. Localization support works directly on the game’s encrypted/compressed DATs via the bundled C# tools.


### Setup

1. **Download / unpack the release**  
   You should end up with a folder that looks roughly like this (names may vary slightly across releases):

   ```text
   <root>/
     Ace7DataTableEditor.exe
     Ace7-Localization-Format/
       ... (bundled C# localization tools; normally you don't need to touch these)
     SourceData/
       PlayerPlaneDataTable.json
       SkinDataTable.json
       AircraftViewerDataTable.json
       Localization/              (optional, for localization merge)
         Cmn.dat
         A.dat
         ...
         M.dat
     TargetData/
       PlayerPlaneDataTable.json
       SkinDataTable.json
       AircraftViewerDataTable.json
       ASS/
         SkinDataTable.json
       Localization/              (optional, for localization merge/replace)
         Cmn.dat
         A.dat
         ...
         M.dat
   ```

   - **SourceData**  
     - Put the JSONs exported from the **source add‑on** (the one you are copying *from*).
     - Optionally, put the **localization files** for that add‑on under `SourceData/Localization` (`Cmn.dat` and `A.dat`–`M.dat`).
   - **TargetData**  
     - Put the JSONs from the **target add‑on / compat patch** (the one you are copying *into*).
     - Optionally, put the **target localization** under `TargetData/Localization` (`Cmn.dat` and `A.dat`–`M.dat`).  
       - `Cmn.dat.bak`, `A.dat.bak`, … will be created here automatically the first time you run a localization merge/replace.
   - **ASS**  
     - Holds the ASS variant of `SkinDataTable.json` used by the compat patch.

2. **Run the tool**
   - Double‑click the EXE.
   - Use the **Root folder** Browse button to point at the folder that contains `SourceData` and `TargetData`.
   - Use:
     - **Merge** to add new planes,
     - **Replace** to update existing planes,
     - **Delete** to remove planes completely.
   - If both `SourceData/Localization` and `TargetData/Localization` are present, Merge/Replace will also:
     - Run the bundled localization CLI to update `Cmn.dat` and the 13 language DATs.
     - Create `.bak` copies of the target localization files (once).
     - Print any conflicts (where manual editing is required) into the log.

> **Note:** The JSON structure is based on UAssetAPI / UAssetGUI **1.0.2.0**.  
> Older/other versions may export slightly different JSON; support for those isn’t guaranteed.


### Running from source instead of the EXE

If you prefer to run the editor directly from the Python script (`merge_aircraft_data_gui.py`) instead of using the compiled `.exe`:

1. **Install Python 3.x**  
   - Make sure Python is installed and added to your PATH.  
   - On Windows, you should be able to run `python --version` or `py --version` in a terminal.

2. **Install any dependencies**  
   - The GUI uses only the Python standard library (`tkinter`, `json`, etc.), so there are **no extra pip packages** required.
   - On Windows, `tkinter` is usually included with the standard Python installer.

3. **Set up the folder structure**  
   - Same as for the EXE:

     ```text
     <root>/
       merge_aircraft_data_gui.py
       SourceData/
         PlayerPlaneDataTable.json
         SkinDataTable.json
         AircraftViewerDataTable.json
       TargetData/
         PlayerPlaneDataTable.json
         SkinDataTable.json
         AircraftViewerDataTable.json
         ASS/
           SkinDataTable.json
     ```

4. **Run the GUI**

   From a terminal in `<root>`:

   ```powershell
   cd "<root>"
   python merge_aircraft_data_gui.py
   ```

   or, if your system uses the launcher:

   ```powershell
   py merge_aircraft_data_gui.py
   ```

5. **Use it exactly like the EXE**  
   - The GUI behavior and features are identical:
     - Use the **Root folder** Browse button to choose the folder that contains `SourceData` and `TargetData`.
     - Use **Merge**, **Replace**, and **Delete** as described above.
   - **Localization from source**:
     - Works the same way as in the EXE, but requires the C# localization tools (`Ace7-Localization-Format` and the `Ace7LocalizationMerge` CLI) to be present and built in the repository root, just like in the release bundle.


### Credits & third‑party code

- **CUE4Parse**  
  - Unreal Engine archive / package parsing library by FabianFG and contributors.  
  - Repository: [FabianFG/CUE4Parse](https://github.com/FabianFG/CUE4Parse/)  
  - Licensed under the [Apache License 2.0](https://github.com/FabianFG/CUE4Parse/blob/master/LICENSE).  
  - This project uses CUE4Parse (directly or via bundled tools) in accordance with Apache‑2.0 and retains the original LICENSE and NOTICE files.

- **Ace7Ed and Ace7‑Localization‑Format (GreenTrafficLight)**  
  - Original C# tooling and localization format for ACE COMBAT 7 by GreenTrafficLight.  
  - Repositories:  
    - [GreenTrafficLight/Ace7Ed](https://github.com/GreenTrafficLight/Ace7Ed)  
    - [GreenTrafficLight/Ace7-Localization-Format](https://github.com/GreenTrafficLight/Ace7-Localization-Format/)  
  - The bundled `Ace7-Localization-Format` folder and its DLLs come from these projects, with additional glue code and automation wrapped around them in this editor.

- **This editor**  
  - Python GUI and merge/replace/delete automation written by sincerity, with help from Cursor Pro.


### Screenshots

> Note: Earlier versions had explicit “Fix NameMap” and “Fix Skins” buttons;  
> those behaviors are now folded into the Merge/Replace logic and internal maintenance passes.

<img width="900" height="1029" alt="image" src="https://github.com/user-attachments/assets/ad559ff8-df7d-4dc6-9ce0-b459a266b624" />
