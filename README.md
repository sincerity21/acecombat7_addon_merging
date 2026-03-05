# sincerity's Simple Add-On Merging Tool

A tool made to accomodate my certain needs in optimizing updates to the [Compatibility between add-on plane mods](https://www.nexusmods.com/acecombat7skiesunknown/mods/2154). 

If you're not me, or BelkanLoyalist, you may or may not need this.



### Features:

- **Merge**: Merge add-ons, taking into account the proper row numbering SortNumber rules of Compat. Patch. Will ask the user to manually insert the AlphabeticalSortNumber.
- **Replace**: Replace add-ons (or other planes), in the case there's updates to the add-ons, be it performance stats, ammo counts, or skin count. Takes into account the proper row numbering rules of Compat. Patch.
- **Delete**: Delete entire add-ons, in-case it becomes outdated / unsupported for whatever reason.



### Instructions:

1. Download the executable into an empty folder.
2. Create two folders alongside the executable; a **_SourceData_** and a **_TargetData_**. Inside the **_TargetData_**, make a subfolder, **_ASS_**.
- Inside **_SourceData_**, you will put JSONs from the source add-on, where you'll be copying the data from, to merge, or replace the **_TargetData_** JSONs
- Inside **_TargetData_**, you will put JSONs from the target add-on (E.g. Compat. Patch), where you'll be copying, replace, or delete data into, originating from the **_SourceData_** JSONs
- **NOTE**: The code was made based off JSONs from UAssetAPI / UAssetGUI 1.0.2.0. Support for older versions aren't guaranteed.
3. Use the tool.


<br>

This was vibe-coded with Cursor Pro.

<br>

### Screenshots:


Disclaimer: The two extra "Fix" features here are made redundant by being incorporated into the existing **Merge** and **Replace** features already.

<img width="900" height="1029" alt="image" src="https://github.com/user-attachments/assets/ad559ff8-df7d-4dc6-9ce0-b459a266b624" />
