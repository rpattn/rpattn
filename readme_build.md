# R_PATTON.SYS // TERMINAL

A minimalist, high-performance personal portfolio system designed for the intersection of Mechanical Engineering and Full-Stack Development. 

**Architectural Principles:**
- **Zero JavaScript:** Navigation and theming handled entirely via CSS `:has()` and `:target`.
- **Markdown-Driven:** Content decoupled from presentation.
- **Single-File Output:** Compiles to a lightweight, portable `index.html`.
- **Rust-Powered Tooling:** Uses `uv` for ultra-fast dependency management.

---

## 🛠 Setup & Installation

This project uses **uv** for Python package management. If you don't have it on Ubuntu:
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```

## Manage Content
Home: Edit content/home.md.

Projects: Add new .md files to content/projects/. The grid will update automatically.

CV: Edit content/cv.md. Use <span class="item-eng"> or <span class="item-dev"> for specific experience filtering.

3. Build for Production
To generate a static build without starting the server:

```bash
uv run python -c "from build import build; build()"
```