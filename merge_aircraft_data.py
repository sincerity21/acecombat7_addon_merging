import json
import os
import copy
import re
import shutil

# Keep track of files we've backed up this session so we don't overwrite the original backup
BACKED_UP_FILES = set()

def load_uasset_json(filename):
    """Loads a JSON file and returns the full dictionary and the Data array."""
    if not os.path.exists(filename):
        return None, None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data, data['Exports'][0]['Table']['Data']
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None, None

def save_uasset_json(filename, data):
    """Creates a backup of the existing file (once per run), then saves the modified dictionary."""
    global BACKED_UP_FILES
    if os.path.exists(filename) and filename not in BACKED_UP_FILES:
        backup_filename = f"{filename}.bak"
        shutil.copy2(filename, backup_filename)
        print(f" -> Initial backup created: {backup_filename}")
        BACKED_UP_FILES.add(filename)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f" -> Successfully saved changes to {filename}")

def get_prop_value(row, prop_name):
    """Retrieves a specific property value from a row's properties array."""
    for prop in row.get('Value', []):
        if prop.get('Name') == prop_name:
            return prop.get('Value')
    return None

def set_prop_value(row, prop_name, new_value):
    """Updates a specific property value in a row's properties array."""
    for prop in row.get('Value', []):
        if prop.get('Name') == prop_name:
            prop['Value'] = new_value
            return

def get_plane_id(row):
    """Extracts the PlaneStringID from a row."""
    return get_prop_value(row, "PlaneStringID")

def add_to_namemap(path_string, name_map):
    """
    Safely adds a path to the NameMap. If it's a 'Package.Asset' format,
    it makes sure the base Package string is also added as UE expects both.
    """
    count = 0
    if not path_string:
        return count
        
    # Add the full string
    if path_string not in name_map:
        name_map.append(path_string)
        count += 1
        
    # If the path has a dot (e.g. "...AcePlayerPawn_f04e.AcePlayerPawn_f04e_C")
    # UE requires the base package path to also exist in the NameMap
    if '.' in path_string:
        base_pkg = path_string.split('.')[0]
        if base_pkg not in name_map:
            name_map.append(base_pkg)
            count += 1
            
    return count

def update_namemap_from_row(row, data):
    """
    Looks for any property containing 'Reference' in its name.
    If its value is a path, ensures that string exists in the top-level NameMap.
    Returns the number of strings successfully added to the NameMap.
    """
    added_count = 0
    name_map = data.get('NameMap', [])
    
    if not isinstance(name_map, list):
        return added_count

    for prop in row.get('Value', []):
        prop_name = prop.get('Name', '')
        
        # Check if this property is a Reference
        if 'Reference' in prop_name:
            val = prop.get('Value')
            
            # 1. Simple String path
            if isinstance(val, str):
                added_count += add_to_namemap(val, name_map)
                
            # 2. UAssetAPI Dictionary format
            elif isinstance(val, dict):
                # Older UAssetAPI structure
                if 'AssetPathName' in val:
                    added_count += add_to_namemap(val.get('AssetPathName'), name_map)
                
                # Newer UAssetAPI structure (FTopLevelAssetPath)
                elif 'AssetPath' in val and isinstance(val['AssetPath'], dict):
                    asset_name = val['AssetPath'].get('AssetName')
                    added_count += add_to_namemap(asset_name, name_map)
                    
    return added_count

# ----------------- MERGE APPEND FUNCTIONS ----------------- #

def process_skin_data(plane_id, old_rows, target_filename):
    target_data, target_rows = load_uasset_json(target_filename)
    if target_data is None:
        print(f"Skipping Skin data: Target '{target_filename}' not found.")
        return

    max_prefix = 0
    for row in target_rows:
        current_plane = get_plane_id(row)
        if current_plane and current_plane.endswith("_vr"):
            continue

        m = re.match(r"Row_(\d+)", row.get("Name", ""))
        if m:
            prefix = int(m.group(1)) // 100
            if prefix > max_prefix:
                max_prefix = prefix
                
    next_prefix = max_prefix + 1
    print(f"[{target_filename}] Max prefix found (Ignoring _vr): {max_prefix}. Using new prefix: {next_prefix}")

    count = 0
    suffix = 1
    for row in old_rows:
        if get_plane_id(row) != plane_id: continue
        new_row = copy.deepcopy(row)
        new_id = (next_prefix * 100) + suffix
        new_row["Name"] = f"Row_{new_id}"
        set_prop_value(new_row, "SkinID", new_id)
        set_prop_value(new_row, "SortNumber", new_id)
        target_rows.append(new_row)
        count += 1
        suffix += 1

    if count > 0:
        save_uasset_json(target_filename, target_data)
        print(f" -> Added {count} rows for {plane_id} to {target_filename}")

def process_aircraft_viewer_data(plane_id, old_rows, target_filename):
    target_data, target_rows = load_uasset_json(target_filename)
    if target_data is None: return

    max_prefix = 0
    for row in target_rows:
        current_plane = get_plane_id(row)
        if current_plane and current_plane.endswith("_vr"): continue
        m = re.match(r"Row_(\d+)", row.get("Name", ""))
        if m:
            prefix = int(m.group(1)) // 10
            if prefix > max_prefix: max_prefix = prefix
                
    next_prefix = max_prefix + 1
    print(f"[{target_filename}] Max prefix found (Ignoring _vr): {max_prefix}. Using new prefix: {next_prefix}")

    count = 0
    suffix = 1
    for row in old_rows:
        if get_plane_id(row) != plane_id: continue
        new_row = copy.deepcopy(row)
        new_id = (next_prefix * 10) + suffix
        new_row["Name"] = f"Row_{new_id}"
        set_prop_value(new_row, "AircraftViewerID", new_id)
        target_rows.append(new_row)
        count += 1
        suffix += 1 

    if count > 0:
        save_uasset_json(target_filename, target_data)
        print(f" -> Added {count} rows for {plane_id} to {target_filename}")

def process_player_plane_data(plane_id, old_rows, target_filename, alpha_sort):
    target_data, target_rows = load_uasset_json(target_filename)
    if target_data is None: return

    max_row_num = 0
    max_plane_id = 0
    max_sort_num = 0
    
    for row in target_rows:
        current_plane = get_plane_id(row)
        if current_plane and current_plane.endswith("_vr"): continue
        m = re.match(r"Row_(\d+)", row.get("Name", ""))
        if m:
            num = int(m.group(1))
            if num > max_row_num: max_row_num = num
            
        pid = get_prop_value(row, "PlaneID")
        if isinstance(pid, int) and pid > max_plane_id: max_plane_id = pid
        
        sort_num = get_prop_value(row, "SortNumber")
        if isinstance(sort_num, int) and sort_num > max_sort_num: max_sort_num = sort_num

    next_row_num = max_row_num + 1
    next_plane_id = max_plane_id + 1
    next_sort_num = max_sort_num + 1
    print(f"[{target_filename}] Next IDs (Ignoring _vr) -> Row_{next_row_num}, PlaneID: {next_plane_id}, SortNumber: {next_sort_num}")

    count = 0
    namemap_additions = 0
    for row in old_rows:
        if get_plane_id(row) != plane_id: continue
        new_row = copy.deepcopy(row)
        new_row["Name"] = f"Row_{next_row_num}"
        set_prop_value(new_row, "PlaneID", next_plane_id)
        set_prop_value(new_row, "SortNumber", next_sort_num)
        set_prop_value(new_row, "AlphabeticalSortNumber", alpha_sort)
        namemap_additions += update_namemap_from_row(new_row, target_data)
        target_rows.append(new_row)
        count += 1
        next_row_num += 1
        next_plane_id += 1
        next_sort_num += 1

    if count > 0:
        if namemap_additions > 0:
            print(f" -> Appended {namemap_additions} missing references to NameMap in {target_filename}")
        save_uasset_json(target_filename, target_data)
        print(f" -> Added {count} rows for {plane_id} to {target_filename}")

# ----------------- REPLACE FUNCTIONS ----------------- #

def process_replace_skin_data(plane_id, old_rows, target_filename):
    target_data, target_rows = load_uasset_json(target_filename)
    if target_data is None: return

    old_plane_rows = [r for r in old_rows if get_plane_id(r) == plane_id]
    if not old_plane_rows: return

    norm_indices = [i for i, r in enumerate(target_rows) if get_plane_id(r) == plane_id]
    if not norm_indices:
        print(f" -> Notice: '{plane_id}' not found in {target_filename}. Cannot replace.")
        return

    # Find the base prefix for existing normal rows
    first_norm_r = target_rows[norm_indices[0]]
    base_skin_id = get_prop_value(first_norm_r, "SkinID")
    if base_skin_id is None:
        m = re.match(r"Row_(\d+)", first_norm_r.get("Name", ""))
        base_skin_id = int(m.group(1)) if m else 0
    base_prefix = base_skin_id // 100

    replaced = 0
    added = 0

    # Insert new rows immediately after the last existing row for this plane
    insert_pos = norm_indices[-1] + 1
    
    for i, old_r in enumerate(old_plane_rows):
        if i < len(norm_indices):
            # Replace existing row
            idx = norm_indices[i]
            norm_r = target_rows[idx]
            new_r = copy.deepcopy(old_r)
            
            # Preserve Normal numbering values
            new_r["Name"] = norm_r["Name"]
            for p in ["SkinID", "SortNumber"]:
                val = get_prop_value(norm_r, p)
                if val is not None: set_prop_value(new_r, p, val)
                
            target_rows[idx] = new_r
            replaced += 1
        else:
            # Append new row using normal base sequence
            suffix = i + 1
            new_id = (base_prefix * 100) + suffix
            new_r = copy.deepcopy(old_r)
            new_r["Name"] = f"Row_{new_id}"
            set_prop_value(new_r, "SkinID", new_id)
            set_prop_value(new_r, "SortNumber", new_id)
            # Keep new rows directly after the existing block for this plane
            target_rows.insert(insert_pos, new_r)
            insert_pos += 1
            added += 1

    if replaced > 0 or added > 0:
        save_uasset_json(target_filename, target_data)
        print(f" -> Replaced {replaced} rows, Added {added} new rows for {plane_id} in {target_filename}")


def process_replace_aircraft_viewer_data(plane_id, old_rows, target_filename):
    target_data, target_rows = load_uasset_json(target_filename)
    if target_data is None: return

    old_plane_rows = [r for r in old_rows if get_plane_id(r) == plane_id]
    if not old_plane_rows: return

    norm_indices = [i for i, r in enumerate(target_rows) if get_plane_id(r) == plane_id]
    if not norm_indices:
        print(f" -> Notice: '{plane_id}' not found in {target_filename}. Cannot replace.")
        return

    first_norm_r = target_rows[norm_indices[0]]
    base_ac_id = get_prop_value(first_norm_r, "AircraftViewerID")
    if base_ac_id is None:
        m = re.match(r"Row_(\d+)", first_norm_r.get("Name", ""))
        base_ac_id = int(m.group(1)) if m else 0
    base_prefix = base_ac_id // 10

    replaced = 0
    added = 0

    # Insert new rows immediately after the last existing row for this plane
    insert_pos = norm_indices[-1] + 1
    
    for i, old_r in enumerate(old_plane_rows):
        if i < len(norm_indices):
            idx = norm_indices[i]
            norm_r = target_rows[idx]
            new_r = copy.deepcopy(old_r)
            
            # Preserve normal tracking IDs
            new_r["Name"] = norm_r["Name"]
            val = get_prop_value(norm_r, "AircraftViewerID")
            if val is not None: set_prop_value(new_r, "AircraftViewerID", val)
            
            target_rows[idx] = new_r
            replaced += 1
        else:
            suffix = i + 1
            new_id = (base_prefix * 10) + suffix
            new_r = copy.deepcopy(old_r)
            new_r["Name"] = f"Row_{new_id}"
            set_prop_value(new_r, "AircraftViewerID", new_id)
            # Keep new rows directly after the existing block for this plane
            target_rows.insert(insert_pos, new_r)
            insert_pos += 1
            added += 1

    if replaced > 0 or added > 0:
        save_uasset_json(target_filename, target_data)
        print(f" -> Replaced {replaced} rows, Added {added} new rows for {plane_id} in {target_filename}")


def process_replace_player_plane_data(plane_id, old_rows, target_filename):
    target_data, target_rows = load_uasset_json(target_filename)
    if target_data is None: return

    old_plane_rows = [r for r in old_rows if get_plane_id(r) == plane_id]
    if not old_plane_rows: return

    for idx, norm_r in enumerate(target_rows):
        if get_plane_id(norm_r) == plane_id:
            old_r = old_plane_rows[0]
            new_r = copy.deepcopy(old_r)
            
            # Preserve Normal numbering and sorting values explicitly
            new_r["Name"] = norm_r["Name"]
            for p in ["PlaneID", "SortNumber", "AlphabeticalSortNumber"]:
                val = get_prop_value(norm_r, p)
                if val is not None: set_prop_value(new_r, p, val)
            
            target_rows[idx] = new_r
            added_refs = update_namemap_from_row(new_r, target_data)
            
            save_uasset_json(target_filename, target_data)
            print(f" -> Replaced row for {plane_id} in {target_filename}.")
            if added_refs > 0:
                print(f" -> Appended {added_refs} missing references to NameMap in {target_filename}.")
            return

    print(f" -> Notice: '{plane_id}' not found in {target_filename}. Cannot replace.")


# ----------------- MENU INTERFACES ----------------- #

def scan_files_for_planes(file_dict):
    """Utility to extract all available plane IDs and their ordering from given files."""
    available = set()
    order = []
    cache = {}
    
    for filename in file_dict.keys():
        _, rows = load_uasset_json(filename)
        if rows:
            cache[filename] = rows
            for r in rows:
                pid = get_plane_id(r)
                if pid:
                    available.add(pid)
                    if 'PlayerPlaneDataTable' in filename and pid not in order:
                        order.append(pid)
                        
    display_order = list(order)
    for pid in sorted(list(available)):
        if pid not in display_order:
            display_order.append(pid)
            
    return available, display_order, cache

def get_user_planes(available_plane_ids):
    raw_input = input("\nEnter the exact PlaneStringIDs, separated by commas (e.g., 'f04e, f15c'): ").strip()
    selected_planes = [p.strip() for p in raw_input.split(',') if p.strip()]
    valid_planes = [p for p in selected_planes if p in available_plane_ids]
    
    for p in selected_planes:
        if p not in available_plane_ids:
            print(f"Warning: '{p}' is not in the list of available planes. Skipping.")
            
    return valid_planes

def do_merge(source_dir, target_dir):
    """
    Merge (add NEW planes) from the SourceData folder into the TargetData folder.
    Both folders use normal file names; no old_ prefix.
    In TargetData the ASS version of SkinDataTable lives under an ASS subfolder.
    """
    print("\n--- OPTION 1: MERGE ---")

    src_skin = os.path.join(source_dir, 'SkinDataTable.json')
    src_viewer = os.path.join(source_dir, 'AircraftViewerDataTable.json')
    src_player = os.path.join(source_dir, 'PlayerPlaneDataTable.json')

    dst_skin = os.path.join(target_dir, 'SkinDataTable.json')
    dst_skin_ass = os.path.join(target_dir, 'ASS', 'SkinDataTable.json')
    dst_viewer = os.path.join(target_dir, 'AircraftViewerDataTable.json')
    dst_player = os.path.join(target_dir, 'PlayerPlaneDataTable.json')

    files_to_process = {
        src_skin:   [dst_skin, dst_skin_ass],
        src_viewer: [dst_viewer],
        src_player: [dst_player],
    }

    print("Scanning SourceData files...")
    avail_planes, display_order, old_data_cache = scan_files_for_planes(files_to_process)
    
    if not avail_planes:
        print("No plane string IDs found in any SourceData files.")
        return

    print("\nAvailable Plane String IDs:")
    for pid in display_order: print(f" - {pid}")

    valid_planes = get_user_planes(avail_planes)
    if not valid_planes:
        return

    alpha_sorts = {}
    if src_player in old_data_cache:
        for plane_id in valid_planes:
            exists = any(get_plane_id(r) == plane_id for r in old_data_cache[src_player])
            if exists:
                while True:
                    try:
                        alpha_sorts[plane_id] = int(input(f"Enter AlphabeticalSortNumber for '{plane_id}': ").strip())
                        break
                    except ValueError:
                        print("Please enter a valid integer.")
            else:
                alpha_sorts[plane_id] = 0

    merge_planes_by_ids(
        source_dir,
        target_dir,
        valid_planes,
        alpha_sorts,
        files_to_process=files_to_process,
        old_data_cache=old_data_cache,
        from_cli=True,
    )


def merge_planes_by_ids(source_dir, target_dir, plane_ids, alpha_sorts,
                        files_to_process=None, old_data_cache=None, from_cli=False):
    """
    Core merge logic used by both CLI and GUI.
    Adds NEW planes from SourceData into TargetData.
    plane_ids: list of PlaneStringIDs to merge.
    alpha_sorts: dict[PlaneStringID -> AlphabeticalSortNumber].
    """

    # If not provided (GUI scenario), rebuild mapping and cache
    if files_to_process is None or old_data_cache is None:
        src_skin = os.path.join(source_dir, 'SkinDataTable.json')
        src_viewer = os.path.join(source_dir, 'AircraftViewerDataTable.json')
        src_player = os.path.join(source_dir, 'PlayerPlaneDataTable.json')

        dst_skin = os.path.join(target_dir, 'SkinDataTable.json')
        dst_skin_ass = os.path.join(target_dir, 'ASS', 'SkinDataTable.json')
        dst_viewer = os.path.join(target_dir, 'AircraftViewerDataTable.json')
        dst_player = os.path.join(target_dir, 'PlayerPlaneDataTable.json')

        files_to_process = {
            src_skin:   [dst_skin, dst_skin_ass],
            src_viewer: [dst_viewer],
            src_player: [dst_player],
        }

        _, _, old_data_cache = scan_files_for_planes(files_to_process)
    else:
        src_skin, src_viewer, src_player = list(files_to_process.keys())

    # Filter requested planes to those that actually exist in SourceData
    available_planes = set()
    for rows in old_data_cache.values():
        for r in rows:
            pid = get_plane_id(r)
            if pid:
                available_planes.add(pid)

    selected_planes = [pid for pid in plane_ids if pid in available_planes]
    if not selected_planes:
        print("No selected planes found in SourceData; nothing to merge.")
        return

    if not from_cli:
        print("\n--- Merging Data ---")

    for plane_id in selected_planes:
        print(f"\n>>> Processing Plane: {plane_id}")
        current_alpha = alpha_sorts.get(plane_id, 0)

        if src_skin in old_data_cache:
            for target in files_to_process[src_skin]:
                process_skin_data(plane_id, old_data_cache[src_skin], target)
        if src_viewer in old_data_cache:
            for target in files_to_process[src_viewer]:
                process_aircraft_viewer_data(plane_id, old_data_cache[src_viewer], target)
        if src_player in old_data_cache:
            for target in files_to_process[src_player]:
                process_player_plane_data(plane_id, old_data_cache[src_player], target, current_alpha)

    print("\nMerge Complete!")

def do_replace(source_dir, target_dir):
    """
    Replace existing planes in the TargetData folder using data from the SourceData folder.
    Folder structure and naming is the same as in do_merge.
    """
    print("\n--- OPTION 5: REPLACE (Update normal files in TargetData from SourceData) ---")

    src_skin = os.path.join(source_dir, 'SkinDataTable.json')
    src_viewer = os.path.join(source_dir, 'AircraftViewerDataTable.json')
    src_player = os.path.join(source_dir, 'PlayerPlaneDataTable.json')

    dst_skin = os.path.join(target_dir, 'SkinDataTable.json')
    dst_skin_ass = os.path.join(target_dir, 'ASS', 'SkinDataTable.json')
    dst_viewer = os.path.join(target_dir, 'AircraftViewerDataTable.json')
    dst_player = os.path.join(target_dir, 'PlayerPlaneDataTable.json')

    files_to_process = {
        src_skin:   [dst_skin, dst_skin_ass],
        src_viewer: [dst_viewer],
        src_player: [dst_player],
    }

    print("Scanning SourceData files...")
    avail_planes, display_order, old_data_cache = scan_files_for_planes(files_to_process)
    
    if not avail_planes:
        print("No plane string IDs found in any SourceData files.")
        return

    print("\nAvailable Plane String IDs in Source Files:")
    for pid in display_order:
        print(f" - {pid}")

    valid_planes = get_user_planes(avail_planes)
    if not valid_planes:
        return

    replace_planes_by_ids(
        source_dir,
        target_dir,
        valid_planes,
        files_to_process=files_to_process,
        old_data_cache=old_data_cache,
        from_cli=True,
    )


def replace_planes_by_ids(source_dir, target_dir, plane_ids, files_to_process=None, old_data_cache=None, from_cli=False):
    """
    Core replace logic used by both CLI and GUI.
    Replaces existing planes in TargetData using rows from SourceData.
    plane_ids: list of PlaneStringIDs to update.
    """
    # If not provided (GUI scenario), rebuild the mapping and cache
    if files_to_process is None or old_data_cache is None:
        src_skin = os.path.join(source_dir, 'SkinDataTable.json')
        src_viewer = os.path.join(source_dir, 'AircraftViewerDataTable.json')
        src_player = os.path.join(source_dir, 'PlayerPlaneDataTable.json')

        dst_skin = os.path.join(target_dir, 'SkinDataTable.json')
        dst_skin_ass = os.path.join(target_dir, 'ASS', 'SkinDataTable.json')
        dst_viewer = os.path.join(target_dir, 'AircraftViewerDataTable.json')
        dst_player = os.path.join(target_dir, 'PlayerPlaneDataTable.json')

        files_to_process = {
            src_skin:   [dst_skin, dst_skin_ass],
            src_viewer: [dst_viewer],
            src_player: [dst_player],
        }

        _, _, old_data_cache = scan_files_for_planes(files_to_process)
    else:
        # Derive source file paths from provided files_to_process
        src_skin, src_viewer, src_player = list(files_to_process.keys())

    # Filter plane_ids against what actually exists in SourceData
    available_planes = set()
    for rows in old_data_cache.values():
        for r in rows:
            pid = get_plane_id(r)
            if pid:
                available_planes.add(pid)

    selected_planes = [pid for pid in plane_ids if pid in available_planes]

    if not selected_planes:
        print("No selected planes found in SourceData; nothing to replace.")
        return

    if not from_cli:
        print("\n--- Replacing Data ---")

    for plane_id in selected_planes:
        print(f"\n>>> Updating Plane: {plane_id}")

        if src_skin in old_data_cache:
            for target in files_to_process[src_skin]:
                process_replace_skin_data(plane_id, old_data_cache[src_skin], target)

        if src_viewer in old_data_cache:
            for target in files_to_process[src_viewer]:
                process_replace_aircraft_viewer_data(plane_id, old_data_cache[src_viewer], target)

        if src_player in old_data_cache:
            for target in files_to_process[src_player]:
                process_replace_player_plane_data(plane_id, old_data_cache[src_player], target)

    print("\nReplace Complete!")

def do_delete(target_dir):
    """
    Delete selected planes from the normal files in the TargetData folder.
    """
    print("\n--- OPTION 2: DELETE ---")
    target_files = {
        os.path.join(target_dir, 'PlayerPlaneDataTable.json'): [],
        os.path.join(target_dir, 'SkinDataTable.json'): [],
        os.path.join(target_dir, 'ASS', 'SkinDataTable.json'): [],
        os.path.join(target_dir, 'AircraftViewerDataTable.json'): []
    }

    print("Scanning normal *.json files in TargetData...")
    avail_planes, display_order, _ = scan_files_for_planes(target_files)

    if not avail_planes:
        print("No plane string IDs found. Are the normal files present?")
        return

    print("\nAvailable Plane String IDs currently in your files:")
    for pid in display_order:
        print(f" - {pid}")

    valid_planes = get_user_planes(avail_planes)
    if not valid_planes:
        return

    delete_planes_by_ids(target_dir, valid_planes)

def delete_planes_by_ids(target_dir, plane_ids):
    """
    Core deletion logic used by both CLI and GUI.
    Deletes all rows with PlaneStringID in plane_ids from TargetData tables.
    """
    target_files = {
        os.path.join(target_dir, 'PlayerPlaneDataTable.json'): [],
        os.path.join(target_dir, 'SkinDataTable.json'): [],
        os.path.join(target_dir, 'ASS', 'SkinDataTable.json'): [],
        os.path.join(target_dir, 'AircraftViewerDataTable.json'): []
    }

    print("\n--- Deleting Data ---")
    for file in target_files.keys():
        data, rows = load_uasset_json(file)
        if data is None:
            continue

        original_len = len(rows)
        new_rows = [r for r in rows if get_plane_id(r) not in plane_ids]

        if len(new_rows) < original_len:
            data['Exports'][0]['Table']['Data'] = new_rows
            save_uasset_json(file, data)
            print(f" -> Deleted {original_len - len(new_rows)} rows from {file}")
        else:
            print(f" -> No rows matched for deletion in {file}")

    print("\nDelete Complete!")

def do_fix_namemap(target_dir):
    """
    Fix NameMap references in PlayerPlaneDataTable.json inside the TargetData folder.
    """
    print("\n--- OPTION 3: FIX NAMEMAP (PlayerPlaneDataTable) ---")
    target_filename = os.path.join(target_dir, 'PlayerPlaneDataTable.json')

    data, rows = load_uasset_json(target_filename)
    if data is None:
        print(f"Error: {target_filename} not found.")
        return

    print(f"Scanning '{target_filename}' (Normal File) for missing NameMap references...")
    total_added = sum(update_namemap_from_row(row, data) for row in rows)
        
    if total_added > 0:
        print(f"Found and added {total_added} missing reference string(s).")
        save_uasset_json(target_filename, data)
        print("NameMap successfully fixed!")
    else:
        print("NameMap is already up to date.")

def do_fix_skin_numbering(target_dir):
    """
    Fix skin numbering in SkinDataTable.json and ASS/SkinDataTable.json inside the TargetData folder.
    """
    print("\n--- OPTION 4: FIX SKIN NUMBERING ---")
    for filename in [
        os.path.join(target_dir, 'SkinDataTable.json'),
        os.path.join(target_dir, 'ASS', 'SkinDataTable.json')
    ]:
        data, rows = load_uasset_json(filename)
        if data is None:
            continue

        print(f"Scanning '{filename}' to fix skin numbering...")
        planes_seen = []
        rows_by_plane = {}
        
        for row in rows:
            pid = get_plane_id(row)
            if not pid or pid.endswith("_vr"): continue 
                
            if pid not in planes_seen:
                planes_seen.append(pid)
                rows_by_plane[pid] = []
            rows_by_plane[pid].append(row)
            
        changes_made = 0
        for pid in planes_seen:
            plane_rows = rows_by_plane[pid]
            if not plane_rows:
                continue
            
            first_row = plane_rows[0]
            first_skin_id = get_prop_value(first_row, "SkinID")
            
            if first_skin_id is None:
                m = re.match(r"Row_(\d+)", first_row.get("Name", ""))
                first_skin_id = int(m.group(1)) if m else None
                if first_skin_id is None:
                    continue 
            
            base_prefix = first_skin_id // 100
            suffix = 1
            for row in plane_rows:
                expected_id = (base_prefix * 100) + suffix
                if get_prop_value(row, "SkinID") != expected_id:
                    row["Name"] = f"Row_{expected_id}"
                    set_prop_value(row, "SkinID", expected_id)
                    set_prop_value(row, "SortNumber", expected_id)
                    changes_made += 1
                suffix += 1

        # Regroup rows so that all skins for a plane are contiguous
        new_rows = []
        grouped = set()

        for row in rows:
            pid = get_plane_id(row)

            # Keep non-plane and VR rows exactly where they are
            if not pid or pid.endswith("_vr") or pid not in rows_by_plane:
                new_rows.append(row)
                continue

            # First encounter of this plane: insert the whole fixed block
            if pid not in grouped:
                plane_rows = rows_by_plane[pid]
                # Ensure block is ordered by SkinID
                plane_rows = sorted(
                    plane_rows,
                    key=lambda r: get_prop_value(r, "SkinID") or 0
                )
                new_rows.extend(plane_rows)
                grouped.add(pid)
            # Subsequent occurrences of this pid are skipped (already added)

        regrouped = new_rows != rows
        if regrouped:
            data['Exports'][0]['Table']['Data'] = new_rows

        if changes_made > 0 or regrouped:
            if changes_made > 0:
                print(f" -> Fixed {changes_made} mismatched row numbers in {filename}.")
            if regrouped:
                print(f" -> Regrouped skin rows by plane in {filename}.")
            save_uasset_json(filename, data)
        else:
            print(f" -> All skin numbering and grouping in {filename} are already correct.")

def main():
    while True:
        print("\n" + "="*50)
        print("     ACE COMBAT 7 DATA-TABLE EDITOR     ")
        print("="*50)
        print(" 1. Merge   (Add NEW planes from SourceData to TargetData)")
        print(" 2. Delete  (Remove planes from TargetData files)")
        print(" 3. NameMap (Fix references in TargetData PlayerPlaneData)")
        print(" 4. Skins   (Fix Skin numbering sequentially in TargetData)")
        print(" 5. Replace (Update EXISTING planes in TargetData from SourceData)")
        print(" 6. Exit")
        print("="*50)
        
        choice = input("Select an option (1-6): ").strip()
        
        if choice == '1':
            source_dir = input("Enter SourceData folder path: ").strip()
            target_dir = input("Enter TargetData folder path: ").strip()
            do_merge(source_dir, target_dir)
        elif choice == '2':
            target_dir = input("Enter TargetData folder path: ").strip()
            do_delete(target_dir)
        elif choice == '3':
            target_dir = input("Enter TargetData folder path: ").strip()
            do_fix_namemap(target_dir)
        elif choice == '4':
            target_dir = input("Enter TargetData folder path: ").strip()
            do_fix_skin_numbering(target_dir)
        elif choice == '5':
            source_dir = input("Enter SourceData folder path: ").strip()
            target_dir = input("Enter TargetData folder path: ").strip()
            do_replace(source_dir, target_dir)
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()