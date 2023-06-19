from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from github_api import get_user_data, get_all_repo_details
from openai_api import get_repo_feedback, convert_profile_into_paragraph
from langchain_api import get_user
from pymongo import MongoClient

mongo_client = MongoClient('mongodb://localhost:27017/')
mongo = mongo_client['test']

app = Flask(__name__)
CORS(app)

# @app.route('/user-profile', methods=['GET'])
# def get_user_profile():
#     username = request.args.get('username')
#     user_data = get_user_data(username)

#     if user_data:
#         return jsonify(user_data)
#     else:
#         return jsonify({"error": "Failed to fetch user data."}), 500

# @app.route('/repo-details', methods=['GET'])
# def get_repo_details_route():
#     username = request.args.get('username')
#     repo_details = get_all_repo_details(username)
#     if not repo_details:
#         return jsonify({"error": "Failed to fetch repository details."}), 500

#     return jsonify(repo_details)


# @app.route('/summary', methods=['GET'])
# def get_summary():
#     username = request.args.get('username')
#     repo_details = get_all_repo_details(username)

#     if repo_details:
#         language_count = {}
#         total_commits = 0
#         total_prs = 0
#         total_stars = 0

#         for repo in repo_details:
#             language = repo["language"]
#             stars = repo["stars"]
#             commits = repo["commits"]
#             prs = repo["pull_requests"]

#             if language is not None:
#                 if language in language_count:
#                     language_count[language] += 1
#                 else:
#                     language_count[language] = 1

#             total_commits += commits
#             total_prs += prs
#             total_stars += stars

#         top_languages = sorted(language_count.items(), key=lambda x: x[1], reverse=True)[:5]
#         top_stars_repos = sorted(repo_details, key=lambda x: x["stars"], reverse=True)[:5]
#         top_commits_repos = sorted(repo_details, key=lambda x: x["commits"], reverse=True)[:5]
#         top_prs_repos = sorted(repo_details, key=lambda x: x["pull_requests"], reverse=True)[:5]

#         response = {
#             "top_languages": top_languages,
#             "total_commits": total_commits,
#             "total_prs": total_prs,
#             "total_stars": total_stars,
#             "top_stars_repos": top_stars_repos,
#             "top_commits_repos": top_commits_repos,
#             "top_prs_repos": top_prs_repos
#         }

#         return jsonify(response)
#     else:
#         return jsonify({"error": "Failed to fetch repository details."}), 500

# @app.route('/feedback', methods=['GET'])
# def get_feedback():
#     username = request.args.get('username')
#     repo_name = request.args.get('repo_name')

#     if username and repo_name:
#         feedback = get_repo_feedback(username, repo_name)
#         return jsonify({"feedback": feedback})
#     else:
#         return jsonify({"error": "Failed to fetch repository details."}), 500

@app.route('/adduser', methods=['GET'])
@cross_origin()
def add_user():
    username = request.args.get('username')
    profile = get_user_data(username)
    repos = get_all_repo_details(username)
    profile["repos"] = repos
    profiles = mongo.profiles
    # check if profile already exists with id
    if profiles.find_one({"id": profile["id"]}):
        return jsonify({"error": "Profile already exists."}), 500
    profiles.insert_one(profile)
    modified_profile = convert_profile_into_paragraph(profile)
    save_data = {
        username: modified_profile
    }
    # append to profile.txt
    with open("profile.txt", "a") as f:
        string_save_data = str(save_data)
        # add new line
        string_save_data += "\n"
        f.write(string_save_data)

    return jsonify(modified_profile)

@app.route('/talents', methods=['GET'])
@cross_origin()
def get_talents():
    profiles = mongo.profiles
    all_profiles = profiles.find({}, {"_id": 0})
    all_profiles = list(all_profiles)
    return jsonify(all_profiles)

@app.route('/search', methods=['GET'])
@cross_origin()
def search():
    query = request.args.get('query')
    report = get_user(query)
    response = {
        'report': report
    }
    # usernames separated by comma in report remove spaces
    usernames = report.replace(" ", "").split(",")
    profiles = mongo.profiles
    all_profiles = profiles.find({}, {"_id": 0})
    all_profiles = list(all_profiles)
    # filter profiles based on usernames
    filtered_profiles = []
    for profile in all_profiles:
        for username in usernames:
            if profile["login"] == username:
                filtered_profiles.append(profile)
    response["profiles"] = filtered_profiles
    return jsonify(response)

    
@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Welcome to the API."})

if __name__ == "__main__":
    app.run(port=5656, debug=True)


