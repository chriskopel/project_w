import os

# Define the folder path to ignore
folder_to_ignore = "C:/Users/Owner/Documents/Data Projects/GitHub/Apps/project_w/2024_10_28__all_in_one/data"

# Define the path to the .gitignore file in your project
gitignore_path = os.path.join("C:/Users/Owner/Documents/Data Projects/GitHub/Apps/project_w", ".gitignore")

# Convert the folder path to a relative path if desired (optional)
# relative_folder_to_ignore = os.path.relpath(folder_to_ignore, start="C:/Users/Owner/Documents/Data Projects/GitHub/Apps/project_w")

# Path to add in .gitignore (converts backslashes to forward slashes)
ignore_entry = folder_to_ignore.replace("\\", "/") + "/\n"

# Check if .gitignore exists; if not, create it
if not os.path.exists(gitignore_path):
    with open(gitignore_path, "w") as f:
        f.write("# Git ignore file\n")

# Read .gitignore contents to ensure no duplicate entries
with open(gitignore_path, "r") as f:
    lines = f.readlines()

# Append the ignore entry only if it's not already present
if ignore_entry not in lines:
    with open(gitignore_path, "a") as f:
        f.write(ignore_entry)

print(f"Added '{ignore_entry.strip()}' to .gitignore.")
