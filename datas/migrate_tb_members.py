def run_migration(connection):
  connection.execute(
      """
        CREATE TABLE IF NOT EXISTS tb_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_viewer INTEGER NOT NULL UNIQUE,
            is_announced INTEGER NOT NULL DEFAULT 0 CHECK (is_announced IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            joined_at TEXT,
            FOREIGN KEY (id_viewer) REFERENCES tb_viewers(id) ON DELETE CASCADE
        )
        """
  )