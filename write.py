import sqlite3


# The new values we want to save
main_balance = 800000000000000000000
target_name = "Alice"
address = "0x0C3dc736c4D8C7F2990c345a2f031EfCA2E68cf7"
# 1. Connect to the database (it creates the file if it doesn't exist)
with sqlite3.connect("trustwin.db") as conn:
    # 2. Create a cursor object to run commands
    cursor = conn.cursor()
    
    # Update the data securely
    cursor.execute(
        "UPDATE players SET main_balance = ? WHERE address = ?", 
        (str(main_balance), address)
    )
    
    # 5. Save (commit) the changes
    conn.commit()

print("Data saved successfully!")
