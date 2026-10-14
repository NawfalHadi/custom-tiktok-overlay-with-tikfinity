def run_migration(connection):
  connection.execute(
      """
        CREATE TABLE IF NOT EXISTS tb_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_viewer INTEGER NOT NULL UNIQUE,
            points INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (id_viewer) REFERENCES tb_viewers(id) ON DELETE CASCADE
        )
        """
  )