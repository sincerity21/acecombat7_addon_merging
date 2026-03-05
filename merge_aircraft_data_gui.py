import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

import merge_aircraft_data as backend  # your existing script

class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, s):
        if s:
            self.widget.configure(state="normal")
            self.widget.insert(tk.END, s)
            self.widget.see(tk.END)
            self.widget.configure(state="disabled")

    def flush(self):
        pass  # needed for file-like interface


class PlaneSelectionDialog(tk.Toplevel):
    """
    Simple modal dialog to allow multi-selection of PlaneStringIDs.
    """
    def __init__(self, parent, plane_ids, title="Select planes"):
        super().__init__(parent)
        self.title(title)
        self.selected = None

        ttk.Label(self, text="Select planes (Ctrl / Shift for multi-select):").pack(
            padx=10, pady=(10, 5)
        )

        # Scrollable listbox for plane selection
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(list_frame, selectmode="extended", height=15)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        for pid in plane_ids:
            self.listbox.insert(tk.END, pid)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(0, 10))

        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)

        self.grab_set()
        self.listbox.focus_set()

    def on_ok(self):
        indices = self.listbox.curselection()
        self.selected = [self.listbox.get(i) for i in indices]
        self.destroy()

    def on_cancel(self):
        self.selected = None
        self.destroy()


class AlphaSortDialog(tk.Toplevel):
    """
    Dialog to input AlphabeticalSortNumber per selected plane.
    """
    def __init__(self, parent, plane_ids):
        super().__init__(parent)
        self.title("AlphabeticalSortNumber per plane")
        self.values = None

        ttk.Label(self, text="Enter AlphabeticalSortNumber for each plane:").pack(
            padx=10, pady=(10, 5)
        )

        self.entries = {}
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        for pid in plane_ids:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=pid, width=12).pack(side="left")
            entry = ttk.Entry(row, width=10)
            entry.insert(0, "0")
            entry.pack(side="left", padx=5)
            self.entries[pid] = entry

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(0, 10))

        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)

        self.grab_set()

    def on_ok(self):
        values = {}
        try:
            for pid, entry in self.entries.items():
                text = entry.get().strip()
                values[pid] = int(text) if text else 0
        except ValueError:
            messagebox.showerror("Error", "All AlphabeticalSortNumber values must be integers.")
            return

        self.values = values
        self.destroy()

    def on_cancel(self):
        self.values = None
        self.destroy()

class DataManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ACE COMBAT 7 DATA-TABLE EDITOR")
        self.geometry("900x520")

        # Base directory and default SourceData/TargetData paths (next to this script/exe)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.source_dir = tk.StringVar(value=os.path.join(self.base_dir, "SourceData"))
        self.target_dir = tk.StringVar(value=os.path.join(self.base_dir, "TargetData"))

        self.create_widgets()
        self.redirect_output()

    def redirect_output(self):
        # Send backend print() output into the log box
        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

    def create_widgets(self):
        # Top frame: directory selection (root + source/target display)
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        # Root folder selector (folder that contains SourceData and TargetData)
        root_frame = ttk.Frame(top)
        root_frame.pack(fill="x", pady=2)
        ttk.Label(root_frame, text="Root folder:").pack(side="left")
        root_entry = ttk.Entry(root_frame, width=60, state="readonly")
        root_entry.insert(0, self.base_dir)
        root_entry.pack(side="left", padx=5)
        ttk.Button(root_frame, text="Browse...", command=lambda: self.browse_root(root_entry)).pack(side="left")

        # SourceData folder (read-only display)
        src_frame = ttk.Frame(top)
        src_frame.pack(fill="x", pady=2)
        ttk.Label(src_frame, text="SourceData folder:").pack(side="left")
        src_entry = ttk.Entry(src_frame, textvariable=self.source_dir, width=60, state="readonly")
        src_entry.pack(side="left", padx=5)

        # TargetData folder (read-only display)
        dst_frame = ttk.Frame(top)
        dst_frame.pack(fill="x", pady=2)
        ttk.Label(dst_frame, text="TargetData folder:").pack(side="left")
        dst_entry = ttk.Entry(dst_frame, textvariable=self.target_dir, width=60, state="readonly")
        dst_entry.pack(side="left", padx=5)

        # Middle frame: buttons for actions
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        # Order: Merge, Replace, Delete
        ttk.Button(btn_frame, text="Merge (1)",
                   command=self.run_merge).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Replace (5)",
                   command=self.run_replace).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete (2)",
                   command=self.run_delete).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Help",
                   command=self.run_help).pack(side="right", padx=5)

        # Bottom frame: log output
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_frame, wrap="word", state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def ensure_source_dir(self):
        path = self.source_dir.get()
        if not path:
            messagebox.showerror("Error", "Please select a SourceData folder first.")
            return None
        if not os.path.isdir(path):
            messagebox.showerror("Error", f"'{path}' is not a valid folder.")
            return None
        return path

    def ensure_target_dir(self):
        path = self.target_dir.get()
        if not path:
            messagebox.showerror("Error", "Please select a TargetData folder first.")
            return None
        if not os.path.isdir(path):
            messagebox.showerror("Error", f"'{path}' is not a valid folder.")
            return None
        return path

    # --- Button callbacks ---

    def browse_root(self, root_entry):
        from tkinter import filedialog

        folder = filedialog.askdirectory(title="Select root folder containing SourceData and TargetData")
        if not folder:
            return

        self.base_dir = folder
        root_entry.configure(state="normal")
        root_entry.delete(0, tk.END)
        root_entry.insert(0, self.base_dir)
        root_entry.configure(state="readonly")

        # Update SourceData and TargetData paths based on the selected root
        self.source_dir.set(os.path.join(self.base_dir, "SourceData"))
        self.target_dir.set(os.path.join(self.base_dir, "TargetData"))

    def run_help(self):
        messagebox.showinfo(
            "ACE COMBAT 7 DATA-TABLE EDITOR - Help",
            (
                "Buttons overview:\n\n"
                "Merge (1): Add NEW planes from SourceData into TargetData.\n"
                " - Uses SkinDataTable, ASS/SkinDataTable, AircraftViewerDataTable, and PlayerPlaneDataTable.\n"
                " - You choose planes from SourceData and set AlphabeticalSortNumber; new rows and NameMap entries are created.\n\n"
                "Replace (5): Update EXISTING planes in TargetData from SourceData.\n"
                " - Replaces skin, viewer, and player-plane rows while preserving IDs/order where needed,\n"
                " - Adds extra skins/viewer rows when SourceData has more entries for that plane.\n\n"
                "Delete (2): Remove selected planes from ALL TargetData tables.\n"
                " - Affects PlayerPlaneDataTable, SkinDataTable, ASS/SkinDataTable, and AircraftViewerDataTable.\n"
            ),
        )

    def run_fix_namemap(self):
        target = self.ensure_target_dir()
        if not target:
            return
        try:
            print("\n=== Running: Fix NameMap (Option 3) ===")
            backend.do_fix_namemap(target)
        except Exception as e:
            messagebox.showerror("Error", f"Error while fixing NameMap:\n{e}")

    def run_fix_skin_numbering(self):
        target = self.ensure_target_dir()
        if not target:
            return
        try:
            print("\n=== Running: Fix Skin Numbering (Option 4) ===")
            backend.do_fix_skin_numbering(target)
        except Exception as e:
            messagebox.showerror("Error", f"Error while fixing skin numbering:\n{e}")

    def run_merge(self):
        source = self.ensure_source_dir()
        target = self.ensure_target_dir()
        if not source or not target:
            return

        try:
            print("\n=== Running: Merge (Option 1) ===")

            # Build the same mapping used in backend.do_merge
            src_skin = os.path.join(source, 'SkinDataTable.json')
            src_viewer = os.path.join(source, 'AircraftViewerDataTable.json')
            src_player = os.path.join(source, 'PlayerPlaneDataTable.json')

            dst_skin = os.path.join(target, 'SkinDataTable.json')
            dst_skin_ass = os.path.join(target, 'ASS', 'SkinDataTable.json')
            dst_viewer = os.path.join(target, 'AircraftViewerDataTable.json')
            dst_player = os.path.join(target, 'PlayerPlaneDataTable.json')

            files_to_process = {
                src_skin:   [dst_skin, dst_skin_ass],
                src_viewer: [dst_viewer],
                src_player: [dst_player],
            }

            avail_planes, display_order, old_data_cache = backend.scan_files_for_planes(files_to_process)

            if not avail_planes:
                messagebox.showinfo(
                    "Info",
                    "No plane string IDs found in SourceData files."
                )
                return

            # 1) Select planes to merge
            select_dialog = PlaneSelectionDialog(
                self,
                display_order,
                title="Select planes to merge from SourceData"
            )
            self.wait_window(select_dialog)

            if not select_dialog.selected:
                print("No planes selected for merge.")
                return

            selected_planes = select_dialog.selected

            # 2) Enter AlphabeticalSortNumber per selected plane
            alpha_dialog = AlphaSortDialog(self, selected_planes)
            self.wait_window(alpha_dialog)

            if alpha_dialog.values is None:
                print("Merge cancelled (no AlphabeticalSortNumber provided).")
                return

            alpha_sorts = alpha_dialog.values

            backend.merge_planes_by_ids(
                source,
                target,
                selected_planes,
                alpha_sorts,
                files_to_process=files_to_process,
                old_data_cache=old_data_cache,
                from_cli=False,
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error while merging planes:\n{e}")

    def run_delete(self):
        target = self.ensure_target_dir()
        if not target:
            return

        try:
            print("\n=== Running: Delete (Option 2) ===")

            # Build the same target_files dict used by backend.do_delete
            target_files = {
                os.path.join(target, 'PlayerPlaneDataTable.json'): [],
                os.path.join(target, 'SkinDataTable.json'): [],
                os.path.join(target, 'ASS', 'SkinDataTable.json'): [],
                os.path.join(target, 'AircraftViewerDataTable.json'): []
            }

            avail_planes, display_order, _ = backend.scan_files_for_planes(target_files)

            if not avail_planes:
                messagebox.showinfo(
                    "Info",
                    "No plane string IDs found in TargetData files. Are the normal files present?"
                )
                return

            dialog = PlaneSelectionDialog(self, display_order, title="Select planes to delete")
            self.wait_window(dialog)

            if not dialog.selected:
                print("No planes selected for deletion.")
                return

            backend.delete_planes_by_ids(target, dialog.selected)
        except Exception as e:
            messagebox.showerror("Error", f"Error while deleting planes:\n{e}")

    def run_replace(self):
        source = self.ensure_source_dir()
        target = self.ensure_target_dir()
        if not source or not target:
            return

        try:
            print("\n=== Running: Replace (Option 5) ===")

            # Build the same mapping used in backend.do_replace
            src_skin = os.path.join(source, 'SkinDataTable.json')
            src_viewer = os.path.join(source, 'AircraftViewerDataTable.json')
            src_player = os.path.join(source, 'PlayerPlaneDataTable.json')

            dst_skin = os.path.join(target, 'SkinDataTable.json')
            dst_skin_ass = os.path.join(target, 'ASS', 'SkinDataTable.json')
            dst_viewer = os.path.join(target, 'AircraftViewerDataTable.json')
            dst_player = os.path.join(target, 'PlayerPlaneDataTable.json')

            files_to_process = {
                src_skin:   [dst_skin, dst_skin_ass],
                src_viewer: [dst_viewer],
                src_player: [dst_player],
            }

            avail_planes, display_order, old_data_cache = backend.scan_files_for_planes(files_to_process)

            if not avail_planes:
                messagebox.showinfo(
                    "Info",
                    "No plane string IDs found in SourceData files."
                )
                return

            dialog = PlaneSelectionDialog(self, display_order, title="Select planes to replace from SourceData")
            self.wait_window(dialog)

            if not dialog.selected:
                print("No planes selected for replace.")
                return

            backend.replace_planes_by_ids(
                source,
                target,
                dialog.selected,
                files_to_process=files_to_process,
                old_data_cache=old_data_cache,
                from_cli=False,
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error while replacing planes:\n{e}")

if __name__ == "__main__":
    app = DataManagerApp()
    app.mainloop()