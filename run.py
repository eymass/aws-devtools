from flask_cors import CORS
import os
from app import app

if __name__ == '__main__':
    from waitress import serve
    print(f"Server started. Listening on port {os.environ.get('PORT', 5000)}.")
    serve(CORS(app), host="0.0.0.0", port=os.environ.get('PORT', 5000))
    print(f"Server stopped.")
