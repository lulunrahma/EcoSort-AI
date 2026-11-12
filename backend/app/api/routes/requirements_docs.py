import os
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/requirements", tags=["Requirements"])

REQUIREMENTS_DIR = os.path.abspath("requirements")

@router.get("")
def list_requirements_files():
    """Lists all specification documents from the requirements folder."""
    if not os.path.exists(REQUIREMENTS_DIR):
        return []

    files = []
    for fname in sorted(os.listdir(REQUIREMENTS_DIR)):
        if fname.endswith(".md"):
            fpath = os.path.join(REQUIREMENTS_DIR, fname)
            stat = os.stat(fpath)
            files.append({
                "filename": fname,
                "title": fname.replace(".md", "").replace("_", " "),
                "size_bytes": stat.st_size,
                "last_modified": stat.st_mtime
            })
    return files

@router.get("/{filename}")
def get_requirement_content(filename: str):
    """Retrieves markdown text of a specific requirement document."""
    # Prevent directory traversal
    safe_filename = os.path.basename(filename)
    fpath = os.path.join(REQUIREMENTS_DIR, safe_filename)

    if not os.path.exists(fpath) or not safe_filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="Requirement document not found.")

    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "filename": safe_filename,
        "content": content
    }

