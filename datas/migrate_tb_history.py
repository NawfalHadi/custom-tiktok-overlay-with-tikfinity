def run_migration(connection):
  connection.execute(
      """
        CREATE TABLE IF NOT EXISTS tb_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_viewer INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_viewer) REFERENCES tb_viewers(id) ON DELETE CASCADE
        )
        """
  )