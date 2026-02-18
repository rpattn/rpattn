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
CHECK_INTERVAL = 1  # seconds

build_lock = threading.Lock()

# --- BUILD FUNCTION ---
def build():
    with build_lock:
        print(f"[{time.strftime('%H:%M:%S')}] 🛠 Rebuilding site...")
        try:
            # Load main markdown files
            with open(os.path.join(CONTENT_DIR, "home.md")) as f:
                home_html = markdown.markdown(f.read())
            with open(os.path.join(CONTENT_DIR, "cv.md")) as f:
                cv_html = markdown.markdown(f.read(), extensions=["extra"])

            # Build projects
            projects_html = ""
            if os.path.exists(PROJECTS_DIR):
                for fname in sorted(os.listdir(PROJECTS_DIR)):
                    if fname.endswith(".md"):
                        with open(os.path.join(PROJECTS_DIR, fname)) as f:
                            projects_html += f'<div class="card">{markdown.markdown(f.read())}</div>'

            # Render template
            with open(TEMPLATE_FILE) as f:
                tmpl = Template(f.read())

            # Auto-refresh meta tag
            refresh_tag = '<meta http-equiv="refresh" content="200">'

            output = tmpl.render(
                home_content=home_html,
                cv_content=cv_html,
                projects_grid=projects_html,
                build_time=time.strftime("%Y.%m.%d %H:%M:%S"),
                refresh_tag=refresh_tag
            )

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(OUTPUT_FILE, "w") as f:
                f.write(output)

            print(f"✅ Updated {OUTPUT_FILE}")
        except Exception as e:
            print(f"BUILD ERROR: {e}")

# --- SERVER ---
def serve():
    os.chdir(OUTPUT_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

# --- POLLING WATCHER ---
def poll_changes():
    # Keep track of last modified times
    paths_to_watch = [
        os.path.join(CONTENT_DIR, "home.md"),
        os.path.join(CONTENT_DIR, "cv.md"),
        TEMPLATE_FILE
    ]

    # Include project files
    if os.path.exists(PROJECTS_DIR):
        for fname in os.listdir(PROJECTS_DIR):
            if fname.endswith(".md"):
                paths_to_watch.append(os.path.join(PROJECTS_DIR, fname))

    last_mod_times = {}
    for path in paths_to_watch:
        if os.path.exists(path):
            last_mod_times[path] = os.path.getmtime(path)

    while True:
        changed = False
        # Refresh project files in case new files are added
        current_files = [
            os.path.join(CONTENT_DIR, "home.md"),
            os.path.join(CONTENT_DIR, "cv.md"),
            TEMPLATE_FILE
        ]
        if os.path.exists(PROJECTS_DIR):
            for fname in os.listdir(PROJECTS_DIR):
                if fname.endswith(".md"):
                    current_files.append(os.path.join(PROJECTS_DIR, fname))

        for path in current_files:
            try:
                mtime = os.path.getmtime(path)
                if path not in last_mod_times or mtime != last_mod_times[path]:
                    last_mod_times[path] = mtime
                    changed = True
            except FileNotFoundError:
                continue

        if changed:
            build()

        time.sleep(CHECK_INTERVAL)

# --- MAIN ---
if __name__ == "__main__":
    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    build()  # Initial build

    # Start server thread
    threading.Thread(target=serve, daemon=True).start()

    print("Watching for changes (Ctrl+C to stop)...")
    try:
        poll_changes()
    except KeyboardInterrupt:
        print("\nShutting down...")
