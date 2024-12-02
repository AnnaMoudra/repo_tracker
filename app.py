from flask import Flask, jsonify, redirect, session, request, url_for
from tracker.tracker import RepositoryTracker
from flask_oauthlib.client import OAuth
import os
from tracker.settings import Settings

settings = Settings()

# Access repositories and other settings
REPOSITORIES = settings.repositories
GITHUB_CLIENT_ID = settings.github_client_id
GITHUB_CLIENT_SECRET = settings.github_client_secret
ROLLING_WINDOW_DAYS = settings.window_length
MAX_EVENTS = settings.max_events


app = Flask(__name__)
app.secret_key = os.urandom(24)
tracker = RepositoryTracker()

# OAuth configuration
if GITHUB_CLIENT_ID:
    oauth = OAuth(app)
    github = oauth.remote_app(
        "github",
        consumer_key=GITHUB_CLIENT_ID,  # Replace with your GitHub Client ID
        consumer_secret=GITHUB_CLIENT_SECRET,  # Replace with your GitHub Client Secret
        base_url="https://api.github.com/",
        request_token_url=None,
        access_token_method="POST",
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
    )


# Route to start OAuth login
@app.route("/")
def index():
    if GITHUB_CLIENT_ID:
        return redirect(url_for("login"))
    return redirect(url_for('get_statistics'))

#@github.tokengetter
#def get_github_token():
#    return session.get("github_token")[0]

@app.route("/login")
def login():
    if GITHUB_CLIENT_ID:
        return github.authorize(callback=url_for("authorized", _external=True))
    return jsonify({"message": "No client id found. Update config."}), 404


# Callback route for GitHub OAuth
@app.route("/callback")
def authorized():
    resp = github.authorized_response()
    if resp is None or "access_token" not in resp:
        return "Access denied: reason={} error={}".format(
            request.args["error"], request.args["error_description"]
        )

    # Store the access token in the session
    session["github_token"] = (resp["access_token"], "")

    if "github_token" not in session:
        return redirect(url_for("login"))

    tracker.update_headers(resp["access_token"])
    return redirect(url_for("get_repositories"))


@app.route("/list-repositories", methods=["GET"])
def get_repositories():
    """ Show list of repositories in configuration. """
    repos = tracker.load_repositories() 
    if not bool(repos):
        return jsonify({"message": "No repositories found."}), 404

    return jsonify(repos)


@app.route("/configure-repositories/<int:repo_id>", methods=["DELETE"])
def delete_repository(repo_id):
    """ Delete a repository using ID. """
    repositories = tracker.load_repositories()

    if str(repo_id) not in repositories.keys():
        return jsonify({"message": "Repository not found."}), 404

    status, resp_object = tracker.delete_repository(repo_id)
    return jsonify(resp_object), status


@app.route("/add-repository", methods=["POST"])
def add_repository():
    """ Add a new repository. Missing validation that repository exists in github etc. """
    data = request.get_json()
    if not data or "owner" not in data or "name" not in data:
        return jsonify({"message": "Invalid request. 'owner' and 'name' are required."}), 400

    status, resp_object = tracker.add_repository(data["owner"], data["name"])
    return jsonify(resp_object), status


@app.route("/statistics", methods=["GET"])
def get_statistics():
    status, message = tracker.fetch_events()
    if status != 200:
        return jsonify(message), status

    stats = tracker.calculate_statistics()
    return jsonify(stats), 200


if __name__ == "__main__":
    app.run(host='127.0.0.1')
