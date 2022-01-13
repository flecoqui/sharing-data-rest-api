# coding: utf-8
import os

import uvicorn

from shared_code.app import app
from shared_code.app_timer import app

port_http = os.getenv("PORT_HTTP", "8000")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(port_http))
