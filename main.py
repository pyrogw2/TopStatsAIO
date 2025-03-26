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
    """Select a folder and populate the file tree."""
    folder = filedialog.askdirectory(title="Select Root Folder")
    if folder:
        for i in tree.get_children():
            tree.delete(i)
        checked_items.clear()
        populate_tree('', folder)
        config["last_path"] = folder
        save_config()
        selected_tree.delete(*selected_tree.get_children())
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
root.configure(bg="#333333")  # Match the Forest theme's dark background color

# Load the Forest theme from the "themes" directory
themes_dir = os.path.join(os.getcwd(), "themes")
forest_dark_path = os.path.join(themes_dir, "forest-dark.tcl")
forest_light_path = os.path.join(themes_dir, "forest-light.tcl")

# Check if the theme files exist
if os.path.exists(forest_dark_path):
    root.tk.call("source", forest_dark_path)
if os.path.exists(forest_light_path):
    root.tk.call("source", forest_light_path)

# Apply the Forest theme (choose "forest-dark" or "forest-light")
ttk.Style().theme_use("forest-dark")  # Use "forest-dark" for dark mode or "forest-light" for light mode

# Make the window resizable
root.rowconfigure(1, weight=1)  # Allow the main content area to expand
root.columnconfigure(0, weight=1)  # Allow horizontal expansion

# Add "Select Folder" button at the top of the main window
select_folder_frame = ttk.Frame(root, padding=10)
select_folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

select_folder_button = ttk.Button(select_folder_frame, text="Select Folder", command=choose_root_folder)
select_folder_button.pack(side="left", padx=5)

selected_path_label = ttk.Label(select_folder_frame, text=f"Current Folder: {config.get('last_path', '')}")
selected_path_label.pack(side="left", padx=10)

# Main layout section
main_frame = ttk.LabelFrame(root, text="File Selection", padding=10)
main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1)

# Treeview container frame
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

# Filter by date section
filter_frame = ttk.LabelFrame(root, text="Filter by Date", padding=10)
filter_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

date_label = ttk.Label(filter_frame, text="Select all logs modified after (YYYY-MM-DD HH:MM):")
date_label.pack(side="left", padx=5)

# Use ttk.Entry with the Forest theme
date_entry = ttk.Entry(filter_frame, width=20)
date_entry.pack(side="left", padx=5)
date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

select_after_button = ttk.Button(filter_frame, text="Select Recent Logs", command=select_files_after_date)
select_after_button.pack(side="left", padx=5)

# Selected files section
selected_frame = ttk.LabelFrame(main_frame, text="Selected Files", padding=10)
selected_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

# Use ttk.Treeview for the selected files list
selected_tree = ttk.Treeview(selected_frame, columns=("File"), show="headings", height=20)
selected_tree.heading("File", text="File")
selected_tree.column("File", anchor="w", width=300)
selected_tree.pack(fill="y", expand=True, pady=5)

# Frame for count label and unselect button
count_frame = ttk.Frame(selected_frame)
count_frame.pack(fill="x", pady=(5, 0))

count_label = ttk.Label(count_frame, text="0 file(s) selected")
count_label.pack(side="left", anchor="w")

unselect_button = ttk.Button(count_frame, text="Unselect All", command=unselect_all)
unselect_button.pack(side="right", anchor="e")

# Track selected files using checkboxes
tree.tag_configure("selected", background="#ccffcc")
checked_items = {}
root_path = config.get("last_path", "")

if root_path:
    print(f"Current Folder: {root_path}")  # Log the current folder instead

last_selected = None

def update_selected_list():
    selected_tree.delete(*selected_tree.get_children())
    count = 0
    for path in sorted(checked_items.keys()):
        display_name = os.path.relpath(path, root_path) if root_path else os.path.basename(path)
        selected_tree.insert("", tk.END, values=(display_name,))
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
    selection = selected_tree.selection()
    if selection:
        selected_name = selected_tree.item(selection[0], "values")[0]
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
selected_tree.bind("<Double-Button-1>", on_listbox_double_click)

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
    progress_popup.title("Processing Files")
    progress_popup.geometry("600x400")
    progress_popup.resizable(False, False)

    # Create a styled frame for the terminal output
    terminal_frame = ttk.Frame(progress_popup, padding=10)
    terminal_frame.pack(fill="both", expand=True)

    # Use a tk.Text widget for terminal-like output
    terminal_output = tk.Text(terminal_frame, height=25, width=80, state="disabled", bg="#3a3a3a", fg="#ffffff", font=("Courier", 10), borderwidth=0)
    terminal_output.pack(fill="both", expand=True)

    def update_terminal_output(message):
        terminal_output.config(state="normal")
        terminal_output.insert(tk.END, message + "\n")
        terminal_output.see(tk.END)  # Scroll to the bottom
        terminal_output.config(state="disabled")

    def process_files():
        processing_complete = threading.Event()  # Event to signal when processing is complete

        def process_zevtc_files():
            try:
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
                    processing_complete.set()  # Signal completion
                    return

                # Use the configuration template from the root of the project directory
                template_conf_file = os.path.join(os.getcwd(), "EliteInsightsConfigTemplate.conf")
                edited_conf_file = os.path.join(temp_dir, "EliteInsightConfig.conf")

                if not os.path.exists(template_conf_file):
                    update_terminal_output(f"Configuration template file not found: {template_conf_file}")
                    processing_complete.set()  # Signal completion
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
                    processing_complete.set()  # Signal completion
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
                        if os.path.isfile(file_path) and file.lower().ends_with(".json.gz"):
                            # Extract the .json.gz file
                            extracted_file_path = os.path.join(processed_folder, os.path.splitext(file)[0])  # Remove .gz extension
                            with gzip.open(file_path, "rb") as gz_file:
                                with open(extracted_file_path, "wb") as json_file:
                                    shutil.copyfileobj(gz_file, json_file)
                            update_terminal_output(f"Extracted: {file} -> {extracted_file_path}")
                    update_terminal_output(f"All .json.gz files have been extracted to: {processed_folder}")
                except Exception as e:
                    update_terminal_output(f"Error extracting .json.gz files: {e}")
                    processing_complete.set()  # Signal completion
                    return

                # Signal that processing is complete
                processing_complete.set()
            except Exception as e:
                update_terminal_output(f"Unexpected error: {e}")
                processing_complete.set()

        # Start the processing in a separate thread
        threading.Thread(target=process_zevtc_files).start()

        # Wait for processing to complete before running the Python script
        def wait_and_run_script():
            processing_complete.wait()  # Wait for the event to be set

            # Run the Python script
            try:
                python_script = os.path.join(config.get("top_stats_path", ""), "tw5_top_stats.py")
                processed_folder_path = os.path.abspath(os.path.join(temp_dir, "ProcessedLogs"))

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

        # Start the script execution in a separate thread
        threading.Thread(target=wait_and_run_script).start()

    # Run the file processing in a separate thread
    threading.Thread(target=process_files).start()

def edit_conf_file(template_path, output_path, temp_dir):
    """Edit the Elite Insights configuration file."""
    try:
        with open(template_path, "r") as template_file:
            lines = template_file.readlines()

        # Modify the OutLocation and DPSReportUserToken lines
        with open(output_path, "w") as output_file:
            for line in lines:
                if line.startswith("OutLocation="):
                    output_file.write(f"OutLocation={temp_dir}\n")
                elif line.startswith("DPSReportUserToken="):
                    output_file.write(f"DPSReportUserToken={config.get('DPSReportUserToken', '')}\n")
                else:
                    output_file.write(line)
    except Exception as e:
        print(f"Error editing .conf file: {e}")

def open_config_window():
    """Open the configuration popup window."""
    config_window = Toplevel(root)
    config_window.title("Configuration")
    config_window.geometry("500x400")
    config_window.resizable(False, False)
    config_window.configure(bg="#333333")  # Match the Forest theme's dark background color

    # Configuration frame
    top_buttons_frame = ttk.LabelFrame(config_window, text="Configuration", padding=10)
    top_buttons_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Elite Insights Folder
    elite_frame = ttk.Frame(top_buttons_frame)
    elite_frame.pack(fill="x", pady=5)

    elite_button = ttk.Button(elite_frame, text="Set Elite Insights Folder", command=lambda: browse_folder(elite_entry))
    elite_button.pack(side="left", padx=5)

    elite_entry = ttk.Entry(elite_frame, width=50)
    elite_entry.insert(0, config.get("elite_insights_path", ""))
    elite_entry.pack(side="left", padx=10)

    # Top Stats Parser Folder
    top_stats_frame = ttk.Frame(top_buttons_frame)
    top_stats_frame.pack(fill="x", pady=5)

    top_stats_button = ttk.Button(top_stats_frame, text="Set Top Stats Parser Folder", command=lambda: browse_folder(top_stats_entry))
    top_stats_button.pack(side="left", padx=5)

    top_stats_entry = ttk.Entry(top_stats_frame, width=50)
    top_stats_entry.insert(0, config.get("top_stats_path", ""))
    top_stats_entry.pack(side="left", padx=10)

    # DPSReportUserToken
    token_frame = ttk.Frame(top_buttons_frame)
    token_frame.pack(fill="x", pady=5)

    token_label = ttk.Label(token_frame, text="DPSReportUserToken:")
    token_label.pack(side="left", padx=5)

    token_entry = ttk.Entry(token_frame, width=50)
    token_entry.insert(0, config.get("DPSReportUserToken", ""))
    token_entry.pack(side="left", padx=10)

    # Save Button
    save_button = ttk.Button(config_window, text="Save", command=lambda: save_and_close_config(config_window, elite_entry, top_stats_entry, token_entry))
    save_button.pack(anchor="e", padx=10, pady=10)

def browse_folder(entry_widget):
    """Open a folder dialog and set the selected path in the entry widget."""
    folder = filedialog.askdirectory(title="Select Folder")
    if folder:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, folder)

def save_and_close_config(config_window, elite_entry, top_stats_entry, token_entry):
    """Save the changes and close the configuration popup."""
    config["elite_insights_path"] = elite_entry.get()
    config["top_stats_path"] = top_stats_entry.get()
    config["DPSReportUserToken"] = token_entry.get()
    save_config()
    config_window.destroy()  # Close the configuration popup

# Add "Generate Aggregate" and "Select Recent Logs" buttons at the bottom
generate_button = ttk.Button(root, text="Generate Aggregate", command=generate_aggregate, style="Accent.TButton")
generate_button.grid(row=3, column=0, sticky="e", padx=10, pady=10)  # Align to the right

# Add "Config" button at the bottom-left
config_button = ttk.Button(root, text="Config", command=open_config_window)
config_button.grid(row=3, column=0, sticky="w", padx=10, pady=10)

root.mainloop()
