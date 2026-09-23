import sqlite3

DB_PATH = "nifty100.db"

tables = [
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios"
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("REMOVING EXACT DUPLICATES")
print("=" * 60)

total_removed = 0

for table in tables:

    print(f"\nProcessing: {table}")

    # Get all columns except the primary key
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    compare_columns = [col for col in columns if col != "id"]

    column_list = ", ".join(f'"{col}"' for col in compare_columns)

    # Find duplicate rows while keeping the lowest ID
    query = f"""
        DELETE FROM "{table}"
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM "{table}"
            GROUP BY {column_list}
        )
    """

    cursor.execute(query)

    removed = cursor.rowcount
    total_removed += removed

    print(f"Rows removed: {removed}")

conn.commit()

print("\n" + "=" * 60)
print(f"TOTAL ROWS REMOVED: {total_removed}")
print("=" * 60)

conn.close()

print("\nDatabase connection closed.")