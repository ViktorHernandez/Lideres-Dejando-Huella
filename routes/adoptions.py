from flask import Blueprint, request, jsonify, g
from database import get_db
from auth import token_required
from utils import paginate_query

adoptions_bp = Blueprint('adoptions', __name__, url_prefix='/api/v1')

@adoptions_bp.route("/adoptions", methods=["POST"])
@token_required
def request_adoption():
    data = request.get_json(force=True) or {}
    animal_id = data.get("animal_id")
    message = data.get("message")

    if not animal_id:
        return jsonify({"error": "animal_id obligatorio"}), 400

    db = get_db()
    cur = db.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
    if not cur.fetchone():
        return jsonify({"error": "Animal no encontrado"}), 404

    cur = db.execute(
        "INSERT INTO adoption_requests (user_id, animal_id, message) VALUES (?, ?, ?)",
        (g.current_user["id"], animal_id, message)
    )
    db.commit()

    return jsonify({"id": cur.lastrowid, "status": "pending"}), 201

@adoptions_bp.route("/adoptions", methods=["GET"])
@token_required
def list_adoptions():
    db = get_db()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    if g.current_user["role"] == "admin":
        base = """
            SELECT ar.id, ar.user_id, u.name AS user_name, ar.animal_id,
                   a.name AS animal_name, ar.message, ar.status, ar.created_at
            FROM adoption_requests ar
            LEFT JOIN users u ON ar.user_id = u.id
            LEFT JOIN animals a ON ar.animal_id = a.id
            ORDER BY ar.created_at DESC
        """
        params = []
    else:
        base = """
            SELECT ar.id, ar.user_id, u.name AS user_name, ar.animal_id,
                   a.name AS animal_name, ar.message, ar.status, ar.created_at
            FROM adoption_requests ar
            LEFT JOIN users u ON ar.user_id = u.id
            LEFT JOIN animals a ON ar.animal_id = a.id
            WHERE ar.user_id = ?
            ORDER BY ar.created_at DESC
        """
        params = [g.current_user["id"]]

    query, qparams = paginate_query(base, params, page, per_page)
    cur = db.execute(query, qparams)
    items = [dict(r) for r in cur.fetchall()]

    count_query = "SELECT COUNT(*) as cnt FROM adoption_requests" + (" WHERE user_id = ?" if params else "")
    count_cur = db.execute(count_query, params)
    total = count_cur.fetchone()["cnt"]

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": items
    })

@adoptions_bp.route("/adoptions/<int:adoption_id>", methods=["PUT"])
@token_required
def update_adoption_status(adoption_id):
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Sólo administradores pueden cambiar el estado"}), 403

    data = request.get_json(force=True) or {}
    status = data.get("status")

    if status not in ("pending", "approved", "rejected"):
        return jsonify({"error": "status inválido"}), 400

    db = get_db()
    cur = db.execute("SELECT id FROM adoption_requests WHERE id = ?", (adoption_id,))
    if not cur.fetchone():
        return jsonify({"error": "Solicitud no encontrada"}), 404

    db.execute(
        "UPDATE adoption_requests SET status = ? WHERE id = ?",
        (status, adoption_id)
    )
    db.commit()

    cur = db.execute("SELECT * FROM adoption_requests WHERE id = ?", (adoption_id,))
    return jsonify(dict(cur.fetchone()))