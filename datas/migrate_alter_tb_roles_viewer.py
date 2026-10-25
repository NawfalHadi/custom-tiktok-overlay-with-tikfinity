def run_migration(connection):
    try:
        connection.execute(
            """
            ALTER TABLE tb_viewers ADD COLUMN id_role INTEGER REFERENCES tb_roles(id) ON DELETE SET NULL
            """
        )
        print("-> [MIGRATION] Berhasil menambahkan kolom 'id_role' ke tabel tb_viewers.")
    except Exception as e:
        print(f"-> [MIGRATION INFO] Kolom id_role mungkin sudah ada atau dilewati: {e}")