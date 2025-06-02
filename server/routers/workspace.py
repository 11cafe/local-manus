import os
import traceback
import platform
import subprocess
from fastapi import APIRouter, Request
from services.config_service import USER_DATA_DIR

router = APIRouter(prefix="/api")

WORKSPACE_ROOT = os.path.join(USER_DATA_DIR, "workspace")

@router.post("/update_file")
async def update_file(request: Request):
    try:
        data = await request.json()
        path = data["path"]
        full_path = os.path.join(WORKSPACE_ROOT, path)
        content = data["content"]
        with open(full_path, "w") as f:
            f.write(content)
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "path": path}

@router.post("/create_file")
async def create_file(request: Request):
    data = await request.json()
    rel_dir = data["rel_dir"]
    path = os.path.join(WORKSPACE_ROOT, rel_dir, 'Untitled.md')
    # Split the path into directory, filename, and extension
    dir_name, base_name = os.path.split(path)
    name, ext = os.path.splitext(base_name)

    candidate_path = path
    counter = 1
    while os.path.exists(candidate_path):
        # Generate new filename with incremented counter
        new_base = f"{name} {counter}{ext}"
        candidate_path = os.path.join(dir_name, new_base)
        counter += 1
    print('candidate_path', candidate_path)
    os.makedirs(os.path.dirname(candidate_path), exist_ok=True)
    with open(candidate_path, "w") as f:
        f.write("")
    return {"path": os.path.relpath(candidate_path, WORKSPACE_ROOT)}

@router.post("/delete_file")
async def delete_file(request: Request):
    data = await request.json()
    path = data["path"]
    os.remove(path)
    return {"success": True}

@router.post("/rename_file")
async def rename_file(request: Request):
    try:
        data = await request.json()
        old_path = data["old_path"]
        old_path = os.path.join(WORKSPACE_ROOT, old_path)
        new_title = data["new_title"]
        if os.path.exists(old_path):
            new_path = os.path.join(os.path.dirname(old_path), new_title)
            os.rename(old_path, new_path)
            return {"success": True, "path": new_path}
        else:
            return {"error": f"File {old_path} does not exist", "path": old_path}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

@router.post("/read_file")
async def read_file(request: Request):
    try:
        data = await request.json()
        path = data["path"]
        full_path = os.path.join(WORKSPACE_ROOT, path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                content = f.read()
                return {"content": content}
        else:
            return {"error": f"File {path} does not exist", "path": path}
    except Exception as e:
        return {"error": str(e), "path": path}

@router.get("/list_files_in_dir")
async def list_files_in_dir(rel_path: str):
    try:
        full_path = os.path.join(WORKSPACE_ROOT, rel_path)
        files = os.listdir(full_path)
        file_nodes = []
        for file in files:
            file_path = os.path.join(full_path, file)
            file_nodes.append({
                "name": file,
                "is_dir": os.path.isdir(file_path),
                "rel_path": os.path.join(rel_path, file),
                "mtime": os.path.getmtime(file_path)  # Get modification time
            })
        # Sort by modification time in descending order
        file_nodes.sort(key=lambda x: x["mtime"], reverse=True)
        # Remove mtime from response as it was only used for sorting
        for node in file_nodes:
            node.pop("mtime")
        return file_nodes
    except Exception as e:
        return []

@router.post("/reveal_in_explorer")
async def reveal_in_explorer(request: Request):
    try:
        data = await request.json()
        path = data["path"]
        full_path = os.path.join(WORKSPACE_ROOT, path)
        
        if not os.path.exists(full_path):
            return {"error": "File not found"}
            
        system = platform.system()
        
        if system == "Darwin":  # macOS
            subprocess.run(["open", "-R", full_path])
        elif system == "Windows":
            subprocess.run(["explorer", "/select,", full_path])
        elif system == "Linux":
            subprocess.run(["xdg-open", os.path.dirname(full_path)])
        else:
            return {"error": "Unsupported operating system"}
            
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}