def run_migration(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tb_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roles_name TEXT NOT NULL UNIQUE
        )
        """
    )