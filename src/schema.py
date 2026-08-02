import sqlite3

# Realiza uma consulta à tabela de metadados do SQLite para extrair o esquema dos bancos de dados
def get_schema(database_path: str) -> str:
    conn = sqlite3.connect(database_path)
    try:
        rows = conn.execute("""
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
                AND sql IS NOT NULL
                AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        return "\n\n".join(row[0] for row in rows if row[0])
    finally:
        conn.close()