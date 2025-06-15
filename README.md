# fix_zotero_path
Python script to fix broken zotero attachment path / automate Locate

# What the script does
1. Connects to Zotero's SQLite database (`zotero.sqlite`)
2. Creates a backup of the database
3. Searches for attachment records in the itemAttachments table
4. Performs simple string replacement on the path field
5. Updates the database with new paths
6. Verifies changes were applied

# Requirement
Python > 3.6
