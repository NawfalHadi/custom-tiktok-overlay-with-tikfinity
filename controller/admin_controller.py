import math
from utils.db import add_points, db_connection

def get_admin_viewers_data(request_args):
    """
    Fetches paginated, sorted, and filtered viewer data from viewers.db 
    using the utils/db context manager.
    """
    page = int(request_args.get("page", 1))
    per_page = int(request_args.get("per_page", 10))
    search = request_args.get("search", "").strip()
    sort_by = request_args.get("sort_by", "created_at")
    sort_dir = request_args.get("sort_dir", "desc").lower()
    
    # Filters
    filter_unowned = request_args.get("unowned_only", "0") # "1" for unowned accounts
    filter_member = request_args.get("member_only", "all") # "yes", "no", "all"

    # Whitelist sort columns for security
    valid_sorts = {
        "id": "v.id",
        "username": "v.username",
        "email": "v.email",
        "points": "COALESCE(s.points, 0)",
        "created_at": "v.created_at",
        "joined_at": "m.joined_at"
    }
    order_column = valid_sorts.get(sort_by, "v.created_at")
    order_direction = "ASC" if sort_dir == "asc" else "DESC"

    base_query = """
        FROM tb_viewers v
        LEFT JOIN tb_stats s ON v.id = s.id_viewer
        LEFT JOIN tb_members m ON v.id = m.id_viewer
        LEFT JOIN tb_roles r ON v.id_role = r.id
        WHERE 1=1
    """
    params = []

    # 1. Search filter (username or email)
    if search:
        base_query += " AND (v.username LIKE ? OR v.email LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    # 2. Unowned filter (Viewers who don't have email/password registered)
    if filter_unowned == "1":
        base_query += " AND (v.email IS NULL OR v.password IS NULL OR v.email = '')"

    # 3. Membership filter
    if filter_member == "yes":
        base_query += " AND m.id IS NOT NULL"
    elif filter_member == "no":
        base_query += " AND m.id IS NULL"

    with db_connection() as conn:
        # Convert sqlite3 rows to dictionary format
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        cursor = conn.cursor()

        # Get total count for pagination
        cursor.execute(f"SELECT COUNT(DISTINCT v.id) {base_query}", params)
        count_row = cursor.fetchone()
        total_items = count_row['COUNT(DISTINCT v.id)'] if count_row else 0
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1

        # Fetch paginated rows
        offset = (page - 1) * per_page
        data_sql = f"""
            SELECT 
                v.id,
                v.username,
                v.email,
                v.password,
                v.profile_picture_url,
                v.created_at,
                COALESCE(s.points, 0) AS points,
                CASE WHEN m.id IS NOT NULL THEN 1 ELSE 0 END AS is_member,
                m.id AS member_id,
                m.is_announced,
                m.joined_at,
                CASE WHEN (v.email IS NULL OR v.email = '' OR v.password IS NULL) THEN 1 ELSE 0 END AS is_unowned,
                COALESCE(r.roles_name, 'Viewer') AS role_name,
                v.id_role
            {base_query}
            ORDER BY {order_column} {order_direction}
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_sql, params + [per_page, offset])
        rows = cursor.fetchall()

        # Fetch roles for dropdown selections
        cursor.execute("SELECT id, roles_name FROM tb_roles ORDER BY id ASC")
        roles = cursor.fetchall()

    return {
        "data": rows,
        "roles": roles,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages
        }
    }

def update_viewer_role(viewer_id, role_id):
    """Updates viewer role ID."""
    with db_connection() as conn:
        conn.execute("UPDATE tb_viewers SET id_role = ? WHERE id = ?", (role_id, viewer_id))

def toggle_viewer_membership(viewer_id):
    """Toggles viewer membership in tb_members."""
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tb_members WHERE id_viewer = ?", (viewer_id,))
        existing = cursor.fetchone()
        if existing:
            conn.execute("DELETE FROM tb_members WHERE id_viewer = ?", (viewer_id,))
            return False
        else:
            conn.execute("INSERT INTO tb_members (id_viewer, is_announced, joined_at) VALUES (?, 0, CURRENT_TIMESTAMP)", (viewer_id,))
            return True

def add_points_to_viewer(viewer_id, points):
    """Adds points to a specific viewer using utils/db.py."""
    with db_connection() as conn:
        add_points(conn, viewer_id, points)