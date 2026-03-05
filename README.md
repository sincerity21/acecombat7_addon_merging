# sincerity's ACE COMBAT 7 DATA-TABLE EDITOR

A tool made to accomodate my certain needs in optimizing updates to the [Compatibility between add-on plane mods](https://www.nexusmods.com/acecombat7skiesunknown/mods/2154). 

If you're not me, or BelkanLoyalist, you may or may not need this.


### What it does

The editor works on JSON exports of UE DataTables (from UAssetAPI / UAssetGUI 1.0.2.0) and automates the repetitive, error‑prone parts of merging plane data:

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

All operations work at the JSON level; you still use UAssetAPI/UAssetGUI to go from `.uasset` ⇄ JSON.


### Setup

1. **Download the executable**  
   Place `merge_aircraft_data_gui.exe` into an otherwise empty folder.

2. **Create the expected folder structure next to the EXE**  

   ```text
   <root>/
     merge_aircraft_data_gui.exe
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

   - **SourceData**  
     - Put the JSONs exported from the **source add‑on** (the one you are copying *from*).
   - **TargetData**  
     - Put the JSONs from the **target add‑on / compat patch** (the one you are copying *into*).
   - **ASS**  
     - Holds the ASS variant of `SkinDataTable.json` used by the compat patch.

3. **Run the tool**
   - Double‑click the EXE.
   - Use the **Root folder** Browse button to point at the folder that contains `SourceData` and `TargetData`.
   - Use:
     - **Merge** to add new planes,
     - **Replace** to update existing planes,
     - **Delete** to remove planes completely.

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




This was vibe‑coded with Cursor Pro.


### Screenshots

> Note: Earlier versions had explicit “Fix NameMap” and “Fix Skins” buttons;  
> those behaviors are now folded into the Merge/Replace logic and internal maintenance passes.

<img width="900" height="1029" alt="image" src="https://github.com/user-attachments/assets/ad559ff8-df7d-4dc6-9ce0-b459a266b624" />
