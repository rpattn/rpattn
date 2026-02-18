import os
import time
import markdown
import threading
import http.server
import socketserver
from jinja2 import Template

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
PROJECTS_DIR = os.path.join(CONTENT_DIR, "projects")
TEMPLATE_FILE = os.path.join(BASE_DIR, "template.html")
OUTPUT_DIR = os.path.join(BASE_DIR, "public")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")
PORT = 5500
CHECK_INTERVAL = 1

build_lock = threading.Lock()

def build():
    with build_lock:
        print(f"[{time.strftime('%H:%M:%S')}] 🛠 Rebuilding site...")
        try:
            # Main Pages
            with open(os.path.join(CONTENT_DIR, "home.md")) as f:
                home_html = markdown.markdown(f.read())
            with open(os.path.join(CONTENT_DIR, "cv.md")) as f:
                cv_html = markdown.markdown(f.read(), extensions=["extra"])

            # Projects Grid
            projects_html = ""
            if os.path.exists(PROJECTS_DIR):
                project_files = sorted([f for f in os.listdir(PROJECTS_DIR) if f.endswith(".md")])
                for i, fname in enumerate(project_files):
                    with open(os.path.join(PROJECTS_DIR, fname)) as f:
                        content = markdown.markdown(f.read())
                        proj_id = f"proj-toggle-{i}"
                        checked = "checked" if i == 0 else ""
                        
                        projects_html += f'''
                        <div class="card-wrapper">
                            <input type="checkbox" id="{proj_id}" class="card-toggle" {checked}>
                            <label for="{proj_id}" class="card">
                                {content}
                            </label>
                        </div>
                        '''

            with open(TEMPLATE_FILE) as f:
                tmpl = Template(f.read())

            output = tmpl.render(
                home_content=home_html,
                cv_content=cv_html,
                projects_grid=projects_html,
                build_time=time.strftime("%Y.%m.%d %H:%M:%S"),
                refresh_tag='<meta http-equiv="refresh" content="300">'
            )

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(OUTPUT_FILE, "w") as f:
                f.write(output)

            print(f"✅ Updated {OUTPUT_FILE}")
        except Exception as e:
            print(f"BUILD ERROR: {e}")

def serve():
    os.chdir(OUTPUT_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

def get_all_paths():
    """Returns a list of all files we want to monitor for changes."""
    paths = [
        os.path.join(CONTENT_DIR, "home.md"),
        os.path.join(CONTENT_DIR, "cv.md"),
        TEMPLATE_FILE
    ]
    if os.path.exists(PROJECTS_DIR):
        for fname in os.listdir(PROJECTS_DIR):
            if fname.endswith(".md"):
                paths.append(os.path.join(PROJECTS_DIR, fname))
    return paths

def poll_changes():
    """Monitors file modification times and triggers build() on change."""
    # Initial state
    last_mtimes = {path: os.path.getmtime(path) for path in get_all_paths() if os.path.exists(path)}
    
    while True:
        time.sleep(CHECK_INTERVAL)
        current_paths = get_all_paths()
        changed = False
        
        for path in current_paths:
            if not os.path.exists(path):
                continue
            
            mtime = os.path.getmtime(path)
            # If file is new or modified
            if path not in last_mtimes or mtime > last_mtimes[path]:
                last_mtimes[path] = mtime
                changed = True
        
        # Check if any files were deleted
        deleted_paths = [path for path in last_mtimes if path not in current_paths]
        if deleted_paths:
            for path in deleted_paths:
                del last_mtimes[path]
            changed = True

        if changed:
            build()

if __name__ == "__main__":
    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Run initial build
    build()
    
    # Start server
    threading.Thread(target=serve, daemon=True).start()
    
    print(f"Watching {len(get_all_paths())} files for changes...")
    try:
        poll_changes()
    except KeyboardInterrupt:
        print("\nShutting down...")