from flask import Blueprint, request, jsonify, g
from database import get_db
from auth import token_required
from utils import paginate_query

animals_bp = Blueprint('animals', __name__, url_prefix='/api/v1')

@animals_bp.route("/animals", methods=["GET"])
def list_animals():
    db = get_db()
    breed = request.args.get("breed")
    age = request.args.get("age")
    q = request.args.get("q")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    base = "SELECT * FROM animals"
    conditions = []
    params = []
    if breed:
        conditions.append("breed = ?")
        params.append(breed)
    if age:
        conditions.append("age = ?")
        params.append(age)
    if q:
        conditions.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if conditions:
        base += " WHERE " + " AND ".join(conditions)
    base += " ORDER BY id DESC"
    query, qparams = paginate_query(base, params, page, per_page)
    cur = db.execute(query, qparams)
    items = [dict(r) for r in cur.fetchall()]
    count_query = "SELECT COUNT(*) as cnt FROM animals" + (" WHERE " + " AND ".join(conditions) if conditions else "")
    count_cur = db.execute(count_query, params)
    total = count_cur.fetchone()["cnt"]
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": items
    })

@animals_bp.route("/animals/<int:animal_id>", methods=["GET"])
def get_animal(animal_id):
    db = get_db()
    cur = db.execute("SELECT * FROM animals WHERE id = ?", (animal_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Animal no encontrado"}), 404
    cur_media = db.execute("SELECT id, media_type, file_path, title, description, uploaded_at FROM animal_media WHERE animal_id = ? ORDER BY uploaded_at DESC", (animal_id,))
    media = [dict(m) for m in cur_media.fetchall()]
    return jsonify(dict(row) | {"media": media})

@animals_bp.route("/animals", methods=["POST"])
@token_required
def add_animal():
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Sólo administradores pueden crear animales"}), 403
    data = request.get_json(force=True) or {}
    name = data.get("name")
    age = data.get("age")
    breed = data.get("breed")
    description = data.get("description")
    if not name:
        return jsonify({"error": "name obligatorio"}), 400
    db = get_db()
    cur = db.execute("INSERT INTO animals (name, age, breed, description) VALUES (?, ?, ?, ?)",
                     (name, age, breed, description))
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": name}), 201

@animals_bp.route("/animals/<int:animal_id>", methods=["PUT"])
@token_required
def update_animal(animal_id):
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Sólo administradores pueden actualizar animales"}), 403
    data = request.get_json(force=True) or {}
    fields = []
    params = []
    for key in ("name", "age", "breed", "description"):
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return jsonify({"error": "Nada que actualizar"}), 400
    params.append(animal_id)
    db = get_db()
    db.execute(f"UPDATE animals SET {', '.join(fields)} WHERE id = ?", params)
    db.commit()
    cur = db.execute("SELECT * FROM animals WHERE id = ?", (animal_id,))
    return jsonify(dict(cur.fetchone()))

@animals_bp.route("/animals/<int:animal_id>", methods=["DELETE"])
@token_required
def delete_animal(animal_id):
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Sólo administradores pueden eliminar animales"}), 403
    db = get_db()
    db.execute("DELETE FROM animal_media WHERE animal_id = ?", (animal_id,))
    db.execute("DELETE FROM adoption_requests WHERE animal_id = ?", (animal_id,))
    db.execute("DELETE FROM comments WHERE animal_id = ?", (animal_id,))
    db.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
    db.commit()
    return jsonify({"deleted": animal_id})

@animals_bp.route("/animals/<int:animal_id>/media", methods=["GET"])
def animal_media(animal_id):
    db = get_db()
    cur = db.execute("SELECT id, media_type, file_path, title, description, uploaded_at FROM animal_media WHERE animal_id = ? ORDER BY uploaded_at DESC", (animal_id,))
    return jsonify([dict(r) for r in cur.fetchall()])