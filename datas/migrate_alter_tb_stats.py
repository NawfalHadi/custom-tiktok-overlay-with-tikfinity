def run_migration(connection):
    try:
        connection.execute(
            """
            ALTER TABLE tb_viewers ADD COLUMN last_daily_claim TEXT
            """
        )
        print("-> [MIGRATION] Berhasil menambahkan kolom 'last_daily_claim' ke tabel tb_viewers.")
    except Exception as e:
        print(f"-> [MIGRATION INFO] Kolom mungkin sudah ada atau dilewati: {e}")