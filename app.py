from flask import Flask, request, jsonify, render_template
import os
import shutil
import platform

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/list", methods=["GET"])
def list_items():
    default_path = "C:\\" if platform.system() == "Windows" else "/"
    path = request.args.get("path", default_path)

    if not os.path.exists(path):
        return jsonify({"error": "Path not found"}), 404

    page = int(request.args.get("page", 1))
    per_page = 50

    sort = request.args.get("sort", "name")     # name | size | date
    order = request.args.get("order", "asc")    # asc | desc
    filter_raw = request.args.get("filter", "")
    filters = [f.strip() for f in filter_raw.split(",") if f.strip()]

    search_query = request.args.get("search", "").lower()

    try:
        entries = []
        for name in os.listdir(path):
            full = os.path.join(path, name)
            is_dir = os.path.isdir(full)

            size = os.path.getsize(full) if not is_dir else None
            try:
                mtime = os.path.getmtime(full)
            except:
                mtime = None

            item = {
                "name": name,
                "path": full,
                "is_dir": is_dir,
                "size": size,
                "date": mtime
            }

            entries.append(item)

        # ---------- FILTER ----------
        def matches_filter(item):
            n = item["name"].lower()

            if search_query and search_query not in n:
                return False

            if not filters:
                return True

            exts = {
                "images": (".png",".jpg",".jpeg",".gif",".webp",".svg"),
                "videos": (".mp4",".mkv",".webm",".mov",".avi"),
                "audio": (".mp3",".wav",".m4a"),
                "pdf": (".pdf",),
                "documents": (".txt",".log",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".pdf"),
                "code": (".py",".js",".html",".css",".cpp",".java",".ts",".json"),
                "zip": (".zip",".rar",".7z")
            }

            for f in filters:
                if f in exts and n.endswith(exts[f]):
                    return True

            return False


        entries = [e for e in entries if matches_filter(e)]

        # ---------- SORT ----------
        folders = [e for e in entries if e["is_dir"]]
        files = [e for e in entries if not e["is_dir"]]

        key_map = {
            "name": lambda x: x["name"].lower(),
            "size": lambda x: (x["size"] or 0),
            "date": lambda x: (x["date"] or 0),
        }

        reverse = (order == "desc")

        folders.sort(key=key_map.get(sort, key_map["name"]), reverse=reverse)
        files.sort(key=key_map.get(sort, key_map["name"]), reverse=reverse)

        # folders first ALWAYS (like Windows Explorer)
        entries = folders + files

        # ---------- PAGINATION ----------
        total = len(entries)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = entries[start:end]

        return jsonify({
            "path": path,
            "items": page_items,
            "page": page,
            "per_page": per_page,
            "total": total
        })

    except PermissionError:
        return jsonify({"error": "Access denied"}), 403



@app.route("/delete", methods=["POST"])
def delete_item():
    data = request.json
    path = data.get("path")

    if not path or not os.path.exists(path):
        return jsonify({"error": "Invalid path"}), 400

    try:
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)   # deletes folder + inside files
        return jsonify({"status": "deleted"})
    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500


from flask import send_file
@app.route("/preview")
def preview():
    path = request.args.get("path")

    if not path or not os.path.exists(path):
        return "Not Found", 404

    try:
        lower = path.lower()

        # Images
        if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            return send_file(path)

        # PDF
        if lower.endswith(".pdf"):
            return send_file(path, mimetype="application/pdf")

        # Video
        if lower.endswith((".mp4", ".webm", ".avi", ".mov", ".mkv")):
            return send_file(path)
        
        # Audio
        if lower.endswith((".mp3", ".wav", ".m4a")):
            return send_file(path)


        # Text
        if lower.endswith((".txt", ".log", ".py", ".json", ".html", ".css", ".js")):
            with open(path, "r", errors="ignore") as f:
                return f.read()

        return "Preview not supported yet", 415

    except PermissionError:
        return "Access Denied", 403



if __name__ == "__main__":
    app.run(debug=True)
