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

    items = []
    try:
        for name in os.listdir(path):
            full = os.path.join(path, name)
            items.append({
                "name": name,
                "path": full,
                "is_dir": os.path.isdir(full),
                "size": os.path.getsize(full) if os.path.isfile(full) else None
            })
        return jsonify({"path": path, "items": items})
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



if __name__ == "__main__":
    app.run(debug=True)
