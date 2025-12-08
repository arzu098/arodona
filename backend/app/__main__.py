import uvicorn 
from app import app
import os
from pathlib import Path


if __name__ == "__main__":
    import uvicorn
    
    # Check if SSL certificates exist
    backend_dir = Path(__file__).parent.parent
    ssl_cert = backend_dir / "ssl.crt"
    ssl_key = backend_dir / "ssl.key"
    
    if ssl_cert.exists() and ssl_key.exists():
        print(f"Starting with SSL certificates")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=5858,
            ssl_keyfile=str(ssl_key),
            ssl_certfile=str(ssl_cert)
        )
    else:
        print(f"SSL certificates not found, starting without SSL")
        uvicorn.run(app, host="0.0.0.0", port=5858)
