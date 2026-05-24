import os
import sys
import logging
from app import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("serve")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    
    if sys.platform == "win32":
        logger.info(f"Detected Windows OS. Starting production server using Waitress on port {port}...")
        try:
            from waitress import serve
            serve(app, host="0.0.0.0", port=port)
        except ImportError:
            logger.error("Waitress is not installed. Please run: pip install waitress")
            sys.exit(1)
    else:
        logger.info(f"Detected Linux/Unix OS.")
        logger.info(f"To run the production server, it is recommended to use gunicorn:")
        logger.info(f"  gunicorn -w 4 -b 0.0.0.0:{port} serve:app")
        logger.info("Falling back to Waitress (if installed) or basic Werkzeug server for now...")
        
        try:
            from waitress import serve
            serve(app, host="0.0.0.0", port=port)
        except ImportError:
            app.run(host="0.0.0.0", port=port)
