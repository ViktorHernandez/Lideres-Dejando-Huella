from flask import Blueprint, request, jsonify, g
from database import get_db
from auth import token_required
from utils import paginate_query

comments_bp = Blueprint('comments', __name__, url_prefix='/api/v1')

@comments_bp.route("/comments", methods=["POST"])
@token_required
def add_comment():
    data = request.get_json(force=True) or {}
    animal_id = data.get("animal_id")
    text = data.get("text")
    if not all([animal_id, text]):
        return jsonify({"error": "animal_id y text obligatorios"}), 400
    db = get_db()
    cur = db.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
    if not cur.fetchone():
        return jsonify({"error": "Animal no encontrado"}), 404
    cur = db.execute("INSERT INTO comments (user_id, animal_id, text) VALUES (?, ?, ?)",
                     (g.current_user["id"], animal_id, text))
    db.commit()
    return jsonify({"id": cur.lastrowid, "text": text}), 201

@comments_bp.route("/comments", methods=["GET"])
def list_comments():
    animal_id = request.args.get("animal_id")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    db = get_db()
    if animal_id:
        base = "SELECT c.id, c.user_id, u.name as user_name, c.animal_id, c.text, c.created_at FROM comments c LEFT JOIN users u ON c.user_id = u.id WHERE c.animal_id = ? ORDER BY c.created_at DESC"
        params = [animal_id]
    else:
        base = "SELECT c.id, c.user_id, u.name as user_name, c.animal_id, c.text, c.created_at FROM comments c LEFT JOIN users u ON c.user_id = u.id ORDER BY c.created_at DESC"
        params = []
    query, qparams = paginate_query(base, params, page, per_page)
    cur = db.execute(query, qparams)
    items = [dict(r) for r in cur.fetchall()]
    count_query = "SELECT COUNT(*) as cnt FROM comments" + (" WHERE animal_id = ?" if animal_id else "")
    count_cur = db.execute(count_query, params)
    total = count_cur.fetchone()["cnt"]
    return jsonify({"page": page, "per_page": per_page, "total": total, "items": items})

@comments_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@token_required
def delete_comment(comment_id):
    db = get_db()
    cur = db.execute("SELECT user_id FROM comments WHERE id = ?", (comment_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Comentario no encontrado"}), 404
    if g.current_user["role"] != "admin" and row["user_id"] != g.current_user["id"]:
        return jsonify({"error": "No tienes permiso para eliminar este comentario"}), 403
    db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    db.commit()
    return jsonify({"deleted": comment_id})