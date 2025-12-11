from app import app
from config import APP_HOST, APP_PORT

if __name__ == "__main__":
    print(f"API lista en http://{APP_HOST}:{APP_PORT}/")
    app.run(host=APP_HOST, port=APP_PORT, debug=True, threaded=True)