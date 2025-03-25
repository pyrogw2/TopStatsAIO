import os
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
import json
import shutil
import tempfile
from tkinter import Toplevel, Label, ttk, messagebox
import subprocess
import threading
import gzip

CONFIG_FILE = "config.json"

# Load saved config or default values
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_path": "", "elite_insights_path": "", "top_stats_path": ""}

# Save config to file
def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

config = load_config()

# Choose root folder
def choose_root_folder():
    folder = filedialog.askdirectory(title="Select Root Folder")
    if folder:
        for i in tree.get_children():
            tree.delete(i)
        checked_items.clear()
        populate_tree('', folder)
        config["last_path"] = folder
        save_config()
        selected_listbox.delete(0, tk.END)
        global root_path
        root_path = folder
        selected_path_label.config(text=f"Current Folder: {root_path}")

# Choose Elite Insights folder
def choose_elite_insights_path():
    path = filedialog.askdirectory(title="Select Elite Insights Folder")
    if path:
        config["elite_insights_path"] = path
        save_config()
        ei_path_label.config(text=f"Elite Insights Folder: {path}")

# Choose Top Stats Parser folder
def choose_top_stats_path():
    path = filedialog.askdirectory(title="Select Top Stats Parser Folder")
    if path:
        config["top_stats_path"] = path
        save_config()
        ts_path_label.config(text=f"Top Stats Parser Folder: {path}")

# Select all files modified after a certain date
def select_files_after_date():
    try:
        date_str = date_entry.get()
        cutoff = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        for item in tree.get_children(""):
            select_if_modified_after(item, cutoff)
        update_selected_list()
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD HH:MM")

def select_if_modified_after(item, cutoff):
    tags = tree.item(item, "tags")
    if not tags or tags[0] == "folder":  # Skip folders or items without valid tags
        for child in tree.get_children(item):
            select_if_modified_after(child, cutoff)
        return

    full_path = tags[0]  # Retrieve the full path from the tags

    if full_path and os.path.isfile(full_path) and full_path.lower().endswith(".zevtc"):
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(full_path))
            if mod_time > cutoff:
                # Only update if the file is not already selected
                if full_path not in checked_items:
                    checked_items[full_path] = True
                    tree.item(item, text="✅ " + os.path.basename(full_path), tags=(full_path,))  # Update tags
        except Exception as e:
            print(f"Error checking file: {e}")

    # Recursively process child items
    for child in tree.get_children(item):
        select_if_modified_after(child, cutoff)

# Unselect all

def unselect_all():
    for path in list(checked_items.keys()):
        del checked_items[path]
    for item in tree.get_children(""):
        clear_tree_checkboxes(item)
    update_selected_list()

def clear_tree_checkboxes(item):
    values = tree.item(item, "values")
    if values and values[0].lower().endswith(".zevtc"):
        tree.item(item, text=os.path.basename(values[0]))
    for child in tree.get_children(item):
        clear_tree_checkboxes(child)

# App window
root = tk.Tk()
root.title("GW2 arcdps File Selector")
root.geometry("1000x800")

# Elite Insights selector at top
ei_selector_frame = ttk.Frame(root)
ei_selector_frame.pack(fill="x", pady=5)

elite_button = ttk.Button(ei_selector_frame, text="Set Elite Insights Folder", command=choose_elite_insights_path)
elite_button.pack(side="left", padx=5)

ei_path_label = ttk.Label(ei_selector_frame, text=f"Elite Insights Folder: {config.get('elite_insights_path', '')}")
ei_path_label.pack(side="left", padx=10)

# Top Stats Parser selector below Elite Insights
ts_selector_frame = ttk.Frame(root)
ts_selector_frame.pack(fill="x", pady=5)

top_stats_button = ttk.Button(ts_selector_frame, text="Set Top Stats Parser Folder", command=choose_top_stats_path)
top_stats_button.pack(side="left", padx=5)

ts_path_label = ttk.Label(ts_selector_frame, text=f"Top Stats Parser Folder: {config.get('top_stats_path', '')}")
ts_path_label.pack(side="left", padx=10)

# Folder selector
top_frame = ttk.Frame(root)
top_frame.pack(fill="x")

select_folder_button = ttk.Button(top_frame, text="Select Folder", command=choose_root_folder)
select_folder_button.pack(side="left", padx=5, pady=5)

selected_path_label = ttk.Label(top_frame, text=f"Current Folder: {config.get('last_path', '')}")
selected_path_label.pack(side="left", padx=10)

# Main layout
main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True)
main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1)

# Treeview container frame using grid
tree_frame = ttk.Frame(main_frame)
tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# Treeview with checkboxes for file selection
tree = ttk.Treeview(tree_frame, columns=("modified",), selectmode="extended")
tree.heading("#0", text="File/Folder")  # Main column for file/folder names
tree.heading("modified", text="Last Modified")  # Secondary column for last modified date
tree.column("#0", width=400)  # Adjust width for file/folder names
tree.column("modified", width=150, anchor="center")  # Adjust width and alignment for last modified date
tree.grid(row=0, column=0, sticky="nsew")

tree_frame.rowconfigure(0, weight=1)
tree_frame.columnconfigure(0, weight=1)

# Scrollbar for tree
tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=tree_scroll.set)
tree_scroll.grid(row=0, column=1, sticky="ns")

# Filter by date section under tree
filter_frame = ttk.Frame(root)
filter_frame.pack(fill="x", pady=5)

date_label = ttk.Label(filter_frame, text="Select all logs modified after (YYYY-MM-DD HH:MM):")
date_label.pack(side="left", padx=5)

date_entry = ttk.Entry(filter_frame, width=20)
date_entry.pack(side="left")
date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

select_after_button = ttk.Button(filter_frame, text="Select Recent Logs", command=select_files_after_date)
select_after_button.pack(side="left", padx=10)

unselect_button = ttk.Button(filter_frame, text="Unselect All", command=unselect_all)
unselect_button.pack(side="left", padx=10)

# Listbox for selected files
selected_frame = ttk.Frame(main_frame)
selected_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

selected_label = ttk.Label(selected_frame, text="Selected .zevtc Files")
selected_label.pack(anchor="nw")

selected_listbox = tk.Listbox(selected_frame, width=60, selectmode="extended")
selected_listbox.pack(fill="y", expand=True)

count_label = ttk.Label(selected_frame, text="0 file(s) selected")
count_label.pack(anchor="nw", pady=(5, 0))

# Track selected files using checkboxes
tree.tag_configure("selected", background="#ccffcc")
checked_items = {}
root_path = config.get("last_path", "")

if root_path:
    selected_path_label.config(text=f"Current Folder: {root_path}")

last_selected = None

def update_selected_list():
    selected_listbox.delete(0, tk.END)
    count = 0
    for path in sorted(checked_items.keys()):
        display_name = os.path.relpath(path, root_path) if root_path else os.path.basename(path)
        selected_listbox.insert(tk.END, display_name)
        count += 1

    count_label.config(text=f"{count} file(s) selected")

    for item in tree.get_children(""):  # Apply highlights to all items
        apply_tree_highlight(item)

def apply_tree_highlight(item):
    tags = tree.item(item, "tags")
    if not tags or tags[0] == "folder":  # Skip folders
        for child in tree.get_children(item):
            apply_tree_highlight(child)
        return

    full_path = tags[0]  # Retrieve the full path from the tags
    if full_path in checked_items:
        tree.item(item, text="✅ " + os.path.basename(full_path), tags=(full_path,))
    else:
        tree.item(item, text=os.path.basename(full_path), tags=(full_path,))
    for child in tree.get_children(item):
        apply_tree_highlight(child)

def on_tree_click(event):
    global last_selected
    region = tree.identify("region", event.x, event.y)
    if region != "tree":
        return

    item_id = tree.identify_row(event.y)
    if not item_id:
        return

    tags = tree.item(item_id, "tags")
    if not tags or tags[0] == "folder":  # Skip folders or items without valid tags
        return

    full_path = tags[0]  # Retrieve the full path from the tags

    # Check if Shift key is pressed
    if event.state & 0x0001 and last_selected:
        # Get all items in the tree
        all_items = []

        def collect_items(item):
            all_items.append(item)
            for child in tree.get_children(item):
                collect_items(child)

        for root_item in tree.get_children(""):
            collect_items(root_item)

        try:
            # Find the indices of the last selected item and the current item
            start_index = all_items.index(last_selected)
            end_index = all_items.index(item_id)

            # Select all items in the range
            for i in range(min(start_index, end_index), max(start_index, end_index) + 1):
                current_item = all_items[i]
                current_tags = tree.item(current_item, "tags")
                if current_tags and current_tags[0].lower().endswith(".zevtc"):
                    current_full_path = current_tags[0]
                    if current_full_path not in checked_items:
                        checked_items[current_full_path] = True
                        tree.item(current_item, text="✅ " + os.path.basename(current_full_path), tags=(current_full_path,))
        except ValueError:
            pass
    else:
        # Toggle selection for the clicked item
        if full_path.lower().endswith(".zevtc"):
            if full_path in checked_items:
                # Deselect the file
                del checked_items[full_path]
                tree.item(item_id, text=os.path.basename(full_path), tags=(full_path,))  # Reset tags
            else:
                # Select the file
                checked_items[full_path] = True
                tree.item(item_id, text="✅ " + os.path.basename(full_path), tags=(full_path,))  # Update tags

    # Update the last selected item
    last_selected = item_id

    # Update the selected listbox and count
    update_selected_list()

def on_listbox_double_click(event):
    selection = selected_listbox.curselection()
    if selection:
        selected_name = selected_listbox.get(selection[0])
        full_path = os.path.join(root_path, selected_name)
        if full_path in checked_items:
            del checked_items[full_path]
            for item in tree.get_children(""):
                reset_tree_checkboxes(item, full_path)
            update_selected_list()

def reset_tree_checkboxes(item, full_path):
    values = tree.item(item, "values")
    if values and os.path.normpath(values[0]) == full_path:
        tree.item(item, text=os.path.basename(full_path))
        return True
    for child in tree.get_children(item):
        if reset_tree_checkboxes(child, full_path):
            return True
    return False

def populate_tree(parent, path):
    try:
        entries = sorted(os.listdir(path), key=lambda x: x.lower())
        for entry in entries:
            full_path = os.path.join(path, entry)  # Combine path and entry
            full_path = os.path.normpath(full_path)  # Normalize the full path
            if os.path.isdir(full_path):
                # Insert folder into the tree and recursively populate its children
                node = tree.insert(parent, "end", text=entry, values=(""))  # No date for folders
                tree.item(node, tags=("folder",))  # Set a placeholder tag for folders
                populate_tree(node, full_path)
            elif entry.lower().endswith(".zevtc"):
                # Get the last modified time of the file
                mod_time = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
                # Insert file into the tree with its last modified date
                node = tree.insert(parent, "end", text=entry, values=(mod_time,))  # Only display the date
                tree.item(node, tags=(full_path,))  # Store the full path in the tags
    except Exception as e:
        print(f"Error reading directory {path}: {e}")

if os.path.exists(root_path):
    populate_tree('', root_path)

tree.bind("<Button-1>", on_tree_click)
selected_listbox.bind("<Double-Button-1>", on_listbox_double_click)

def generate_aggregate():
    if not checked_items:
        # Show an error popup if no files are selected
        messagebox.showerror("No Files Selected", "Please select at least one file to generate the aggregate.")
        return

    # Create a temporary folder
    temp_dir = tempfile.mkdtemp()
    print(f"Temporary folder created: {temp_dir}")

    # Create a popup window for progress
    progress_popup = Toplevel(root)
    progress_popup.title("")  # Remove the title text
    progress_popup.geometry("600x400")  # Adjust the size to look like a terminal
    progress_popup.resizable(False, False)  # Disable resizing

    # Terminal-like output using a Text widget
    terminal_output = tk.Text(progress_popup, height=25, width=80, state="disabled", bg="black", fg="white", font=("Courier", 10), borderwidth=0)
    terminal_output.pack(fill="both", expand=True)  # Fill the entire popup window

    def update_terminal_output(message):
        terminal_output.config(state="normal")
        terminal_output.insert(tk.END, message + "\n")
        terminal_output.see(tk.END)  # Scroll to the bottom
        terminal_output.config(state="disabled")

    def process_files():
        # Copy files with progress
        total_files = len(checked_items)
        update_terminal_output(f"Copying {total_files} selected files to temporary folder...")
        for i, full_path in enumerate(checked_items.keys(), start=1):
            try:
                shutil.copy(full_path, temp_dir)
                progress = int((i / total_files) * 50)  # ASCII progress bar length
                progress_bar = "[" + "#" * progress + "-" * (50 - progress) + "]"
                update_terminal_output(f"{progress_bar} {i}/{total_files} - Copied: {os.path.basename(full_path)}")
            except Exception as e:
                update_terminal_output(f"Error copying file {full_path}: {e}")

        # Locate the Elite Insights executable
        ei_exec = None
        elite_insights_path = config.get("elite_insights_path", "")
        if os.path.exists(os.path.join(elite_insights_path, "GuildWars2EliteInsights.exe")):
            ei_exec = os.path.join(elite_insights_path, "GuildWars2EliteInsights.exe")
        elif os.path.exists(os.path.join(elite_insights_path, "GuildWars2EliteInsights-CLI.exe")):
            ei_exec = os.path.join(elite_insights_path, "GuildWars2EliteInsights-CLI.exe")
        else:
            update_terminal_output("No valid Guild Wars 2 Elite Insights executable found.")
            return

        # Use the configuration template from the root of the project directory
        template_conf_file = os.path.join(os.getcwd(), "EliteInsightsConfigTemplate.conf")
        edited_conf_file = os.path.join(temp_dir, "EliteInsightConfig.conf")

        if not os.path.exists(template_conf_file):
            update_terminal_output(f"Configuration template file not found: {template_conf_file}")
            return

        # Edit the .conf file to set OutLocation to the temporary folder
        edit_conf_file(template_conf_file, edited_conf_file, temp_dir)

        # Process .zevtc files using Elite Insights
        try:
            update_terminal_output("Processing .zevtc files with Elite Insights...")
            zevtc_files = [file for file in os.listdir(temp_dir) if file.lower().endswith(".zevtc")]
            for i, file in enumerate(zevtc_files, start=1):
                file_path = os.path.join(temp_dir, file)
                command = [ei_exec, "-c", edited_conf_file, file_path]
                update_terminal_output(f"[{i}/{len(zevtc_files)}] Processing: {file}")
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                update_terminal_output(result.stdout.strip())
                if result.returncode != 0:
                    update_terminal_output(f"Error: {result.stderr.strip()}")
        except Exception as e:
            update_terminal_output(f"Error processing files with Elite Insights: {e}")
            return

        # Extract .json.gz files to .json in a new subfolder
        processed_folder = os.path.join(temp_dir, "ProcessedLogs")
        os.makedirs(processed_folder, exist_ok=True)

        # Ensure the folder is writable
        import stat
        os.chmod(processed_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        try:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path) and file.lower().endswith(".json.gz"):
                    # Extract the .json.gz file
                    extracted_file_path = os.path.join(processed_folder, os.path.splitext(file)[0])  # Remove .gz extension
                    with gzip.open(file_path, "rb") as gz_file:
                        with open(extracted_file_path, "wb") as json_file:
                            shutil.copyfileobj(gz_file, json_file)
                    update_terminal_output(f"Extracted: {file} -> {extracted_file_path}")
            update_terminal_output(f"All .json.gz files have been extracted to: {processed_folder}")
        except Exception as e:
            update_terminal_output(f"Error extracting .json.gz files: {e}")
            return

        # Run the Python script
        try:
            python_script = os.path.join(config.get("top_stats_path", ""), "tw5_top_stats.py")
            processed_folder_path = os.path.abspath(processed_folder)

            # Properly escape the paths by wrapping them in quotes
            command = ["python", f'"{python_script}"', "-i", f'"{processed_folder_path}"']
            update_terminal_output(f"Running Python script: {' '.join(command)}")

            # Run the command
            result = subprocess.run(" ".join(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            update_terminal_output(result.stdout.strip())
            if result.returncode != 0:
                update_terminal_output(f"Error: {result.stderr.strip()}")
                return
            update_terminal_output("Python script completed successfully.")
        except Exception as e:
            update_terminal_output(f"Error running Python script: {e}")
            return

        # Close the popup after completion
        update_terminal_output("Processing complete!")

    # Run the file processing in a separate thread
    threading.Thread(target=process_files).start()

def edit_conf_file(template_path, output_path, temp_dir):
    try:
        with open(template_path, "r") as template_file:
            lines = template_file.readlines()

        # Modify the OutLocation line
        with open(output_path, "w") as output_file:
            for line in lines:
                if line.startswith("OutLocation="):
                    output_file.write(f"OutLocation={temp_dir}\n")
                else:
                    output_file.write(line)
    except Exception as e:
        print(f"Error editing .conf file: {e}")

# Add "Generate Aggregate" button at the bottom right
generate_button = ttk.Button(root, text="Generate Aggregate", command=generate_aggregate)
generate_button.pack(side="bottom", anchor="se", padx=10, pady=10)

root.mainloop()
