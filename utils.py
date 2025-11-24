from config import ALLOWED_EXTENSIONS

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def paginate_query(base_query, params, page, per_page):
    offset = (page - 1) * per_page
    return f"{base_query} LIMIT ? OFFSET ?", params + [per_page, offset]