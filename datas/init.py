import importlib.util
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().with_name("viewers.db")
BASE_DIR = Path(__file__).resolve().parent


def initialize_database():
  with sqlite3.connect(DB_PATH) as connection:
    connection.execute("PRAGMA foreign_keys = ON")

    # 1. Create the tracking table first
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tb_migrate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tb_name TEXT NOT NULL,
            migration_file TEXT NOT NULL UNIQUE,
            migrated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()

    # 2. List all migration files and their corresponding table names
    migrations = [
        ("tb_viewers", "migrate_tb_viewers.py"),
        ("tb_members", "migrate_tb_members.py"),
        ("tb_stats", "migrate_tb_stats.py"),
        ("tb_viewers_alter_daily", "migrate_alter_tb_stats.py"),
        ("tb_roles", "migrate_tb_roles.py"),
        ("tb_viewers_alter_roles", "migrate_alter_tb_roles_viewer.py"),
        ("tb_history", "migrate_tb_history.py"),
    ]

    for tb_name, migration_file in migrations:
      cursor = connection.cursor()
      cursor.execute(
          "SELECT 1 FROM tb_migrate WHERE migration_file = ?", (migration_file,)
      )
      is_migrated = cursor.fetchone()

      if not is_migrated:
        print(f"Applying migration: {migration_file} for table '{tb_name}'...")

        file_path = BASE_DIR / migration_file
        if file_path.exists():
          # Dynamically load the individual migration file
          spec = importlib.util.spec_from_file_location(
              migration_file[:-3], file_path
          )
          migration_module = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(migration_module)

          # Run the specific table creation script
          if hasattr(migration_module, "run_migration"):
            migration_module.run_migration(connection)
          else:
            raise AttributeError(
                f"Migration file '{migration_file}' must contain a"
                " 'run_migration(connection)' function."
            )

          # Log the successful migration
          connection.execute(
              """
                INSERT INTO tb_migrate (tb_name, migration_file)
                VALUES (?, ?)
                """,
              (tb_name, migration_file),
          )
          connection.commit()
          print(f"Successfully migrated and logged: {migration_file}")
        else:
          print(f"Warning: Migration file '{migration_file}' not found.")
      else:
        print(f"Skipping (already migrated): {migration_file}")


if __name__ == "__main__":
  initialize_database()