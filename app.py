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

    try:
        names = os.listdir(path)
        total = len(names)

        start = (page - 1) * per_page
        end = start + per_page
        names = names[start:end]

        items = []
        for name in names:
            full = os.path.join(path, name)
            items.append({
                "name": name,
                "path": full,
                "is_dir": os.path.isdir(full),
                "size": os.path.getsize(full) if os.path.isfile(full) else None
            })

        return jsonify({
            "path": path,
            "items": items,
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
