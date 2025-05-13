import asyncio
import os
import sys
import argparse
from contextlib import asynccontextmanager
from localmanus.services.db_service import DatabaseService

root_dir = os.path.dirname(__file__)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from localmanus.routers import config, agent

    
@asynccontextmanager
async def lifespan(app: FastAPI):
    # onstartup
    await agent.initialize()
    yield
    # onshutdown

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(config.router)
app.include_router(agent.router)
app.include_router(agent.wsrouter)

# Mount the React build directory
react_build_dir = os.environ.get('UI_DIST_DIR', os.path.join(os.path.dirname(root_dir), "react", "dist"))

app.mount("/assets", StaticFiles(directory=os.path.join(react_build_dir, "assets")), name="assets")

@app.get("/")
async def serve_react_app():
    return FileResponse(os.path.join(react_build_dir, "index.html"))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    args = parser.parse_args()
    import uvicorn
    print("🌟Starting server, UI_DIST_DIR:", os.environ.get('UI_DIST_DIR'))
    uvicorn.run(app, host="127.0.0.1", port=args.port)
