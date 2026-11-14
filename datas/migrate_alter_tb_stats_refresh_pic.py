def run_migration(connection):
    try:
        connection.execute(
            """
            ALTER TABLE tb_stats ADD COLUMN last_refresh_picture TEXT
            """
        )
        print("-> [MIGRATION] Berhasil menambahkan kolom 'last_refresh_picture' ke tabel tb_stats.")
    except Exception as e:
        print(f"-> [MIGRATION INFO] Kolom last_refresh_picture mungkin sudah ada atau dilewati: {e}")