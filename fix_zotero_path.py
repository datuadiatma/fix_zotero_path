import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime

def fix_zotero_attachment_paths(test_mode=False):
    # Fix broken attachment file links in Zotero 7 database
    # Changes paths from Windows to macOS OneDrive structure
    
    # IMPORTANT: Close Zotero before running this script!
    
    # Path to your Zotero profile directory
    zotero_profile_path = input("Enter your Zotero profile path (e.g., /Users/username/Zotero): ")
    
    # Path to the Zotero database
    db_path = Path(zotero_profile_path) / "zotero.sqlite"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Make sure Zotero is closed and the path is correct.")
        return
    
    # Create a backup of the database with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(f'.backup_{timestamp}.sqlite')
    print(f"Creating backup at: {backup_path}")
    
    try:
        shutil.copy2(db_path, backup_path)
        # Verify backup was created successfully
        if not backup_path.exists() or backup_path.stat().st_size == 0:
            raise Exception("Backup creation failed - file is missing or empty")
        print(f"Backup verified: {backup_path.stat().st_size} bytes")
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return
    
    try:
        # Connect to the database with timeout
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # Check if database is locked
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("ROLLBACK;")
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                print("Error: Database is locked. Make sure Zotero is completely closed.")
                return
            else:
                raise
        
        # Define the path transformation patterns
        old_base = "C:\\Users\\datua\\OneDrive\\Zotmoov"
        new_base = "/Users/datuadiatma/Library/CloudStorage/OneDrive-Personal/Zotmoov"
        
        # Find all attachment items that need updating
        cursor.execute("""
            SELECT itemID, path 
            FROM itemAttachments 
            WHERE path LIKE ?
        """, (f"%{old_base}%",))
        
        attachments_to_update = cursor.fetchall()
        
        if not attachments_to_update:
            print("No attachments found with the old path.")
            return
        
        if test_mode:
            print(f"TEST MODE: Found {len(attachments_to_update)} attachments, will update only the first 2:")
            attachments_to_update = attachments_to_update[:2]  # Limit to first 2 for testing
        else:
            print(f"Found {len(attachments_to_update)} attachments to update:")
        
        # Show what will be changed
        for item_id, path in attachments_to_update:
            new_attachment_path = path.replace(old_base, new_base)
            # Also fix any remaining backslashes to forward slashes for macOS
            new_attachment_path = new_attachment_path.replace('\\', '/')
            print(f"ID {item_id}: {path} -> {new_attachment_path}")
        
        # Ask for confirmation
        if test_mode:
            confirm = input(f"\nTEST MODE: Proceed with updating these {len(attachments_to_update)} attachments? (y/N): ")
        else:
            confirm = input("\nProceed with updating ALL these paths? (y/N): ")
            
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
        
        # Update the paths within a transaction
        conn.execute("BEGIN TRANSACTION;")
        updated_count = 0
        
        try:
            for item_id, path in attachments_to_update:
                new_attachment_path = path.replace(old_base, new_base)
                # Also fix any remaining backslashes to forward slashes for macOS
                new_attachment_path = new_attachment_path.replace('\\', '/')
                
                # Validate the replacement makes sense
                if old_base not in path:
                    print(f"Warning: Skipping item {item_id} - old path not found in: {path}")
                    continue
                
                cursor.execute("""
                    UPDATE itemAttachments 
                    SET path = ? 
                    WHERE itemID = ?
                """, (new_attachment_path, item_id))
                
                updated_count += 1
            
            # Commit all changes at once
            conn.execute("COMMIT;")
            
        except Exception as e:
            print(f"Error during update: {e}")
            conn.execute("ROLLBACK;")
            raise
        
        print(f"\nSuccessfully updated {updated_count} attachment paths!")
        
        if test_mode:
            print("✅ TEST COMPLETED! Check these 2 attachments in Zotero to verify they work correctly.")
            print("If they work properly, you can run option 3 to fix all remaining attachments.")
        
        # Verify the changes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM itemAttachments 
            WHERE path LIKE ?
        """, (f"%{new_base}%",))
        
        new_count = cursor.fetchone()[0]
        print(f"Verification: {new_count} attachments now have the new path.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        print("Restoring backup...")
        shutil.copy2(backup_path, db_path)
        print("Backup restored. No changes were made.")
        
    finally:
        if conn:
            conn.close()
    
    print("\nDone! You can now start Zotero and check your attachments.")
    print(f"Backup saved at: {backup_path}")

def preview_changes():
    # Preview what changes would be made without actually updating the database
    zotero_profile_path = input("Enter your Zotero profile path: ")
    db_path = Path(zotero_profile_path) / "zotero.sqlite"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        old_base = "C:\\Users\\datua\\OneDrive\\Zotmoov"
        new_base = "/Users/datuadiatma/Library/CloudStorage/OneDrive-Personal/Zotmoov"
        
        cursor.execute("""
            SELECT itemID, path 
            FROM itemAttachments 
            WHERE path LIKE ?
        """, (f"%{old_base}%",))
        
        attachments = cursor.fetchall()
        
        if not attachments:
            print("No attachments found with the old path.")
            return
        
        print(f"Preview: {len(attachments)} attachments would be updated:")
        for item_id, path in attachments:
            new_attachment_path = path.replace(old_base, new_base)
            # Also fix any remaining backslashes to forward slashes for macOS
            new_attachment_path = new_attachment_path.replace('\\', '/')
            print(f"ID {item_id}: {path} -> {new_attachment_path}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Zotero Attachment Path Fixer")
    print("=" * 30)
    print("1. Preview changes (see what would be updated)")
    print("2. Test mode (fix only 2 attachments)")
    print("3. Fix all attachment paths")
    
    choice = input("\nSelect option (1, 2, or 3): ")
    
    if choice == "1":
        preview_changes()
    elif choice == "2":
        print("\n⚠️  TEST MODE - Will update only 2 attachments")
        print("⚠️  IMPORTANT: Close Zotero completely before proceeding!")
        input("Press Enter when Zotero is closed...")
        fix_zotero_attachment_paths(test_mode=True)
    elif choice == "3":
        print("\n⚠️  FULL MODE - Will update ALL attachments")
        print("⚠️  IMPORTANT: Close Zotero completely before proceeding!")
        input("Press Enter when Zotero is closed...")
        fix_zotero_attachment_paths(test_mode=False)
    else:
        print("Invalid choice.")
