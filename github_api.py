import requests
from dotenv import dotenv_values
from tqdm import tqdm
import redis
import json


# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = 'letmein'
REDIS_DB = 0

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB)

env_vars = dotenv_values('.env')

BASE_API = "https://api.github.com"

PER_PAGE = '?per_page=100'

def get_headers():
    personal_access_token = env_vars["PERSONAL_ACCESS_TOKEN"]
    return {
        "Authorization": f"Bearer {personal_access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_user_data(username):
    try:
        # Making a GET request to the GitHub API with the personal access token
        api_url = BASE_API + "/users/" + username + PER_PAGE
        headers = get_headers()
        response = requests.get(api_url, headers=headers)

        # Checking if the request was successful
        if response.status_code == 200:
            user_data = response.json()
            return user_data
        else:
            print("Unable to fetch user data.")
            return None
    except Exception as e:
        print("Something went wrong.")
        print(e)
        return None

def get_repo_details(username, repo_name, repo_url):
    headers = get_headers()
    url = BASE_API + "/repos/" + username + "/" + repo_name + PER_PAGE
    # Fetching repository details
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response.raise_for_status()  # Raise an exception if the request was not successful
        print(f"Fetching details for repository: {repo_name}")
        repo_data = response.json()
        language = repo_data["language"]
        stars = repo_data["stargazers_count"]
        forks = repo_data["forks_count"]
        
        # Fetching number of commits
        commits_url = BASE_API + "/repos/" + username + "/" + repo_name + "/commits"
        commits_response = requests.get(commits_url, headers=headers)
        
        if commits_response.status_code == 200:
            commits_data = commits_response.json()
            commits = len(commits_data)
        else:
            commits = 0
        
        # Fetching number of pull requests
        pull_requests_url = BASE_API + "/repos/" + username + "/" + repo_name + "/pulls"
        pull_requests_response = requests.get(pull_requests_url, headers=headers)
        
        if pull_requests_response.status_code == 200:
            pull_requests_data = pull_requests_response.json()
            pull_requests = len(pull_requests_data)
        else:
            pull_requests = 0
        
        return language, stars, forks, commits, pull_requests
    
    else:
        return None, None, None, None, None

def get_all_repo_details(username):
    cached_data = redis_client.get(username + "_repo_details")
    if cached_data:
        print("Fetching repository details from cache")
        return json.loads(cached_data.decode('utf-8')) 

    api_url = BASE_API + "/users/" + username + "/repos" + PER_PAGE
    headers = get_headers()
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        repo_data = response.json()
        repo_details = []
        print("length of repo_data", len(repo_data))
        with tqdm(total=len(repo_data), desc="Fetching repository details") as pbar:
            for repo in repo_data:
                is_forked = repo["fork"]
                # Skipping forked repositories
                if is_forked:
                    pbar.update(1)
                    continue
                
                repo_name = repo["name"]
                repo_url = repo["html_url"]

                language, stars, forks, commits, pull_requests = get_repo_details(username, repo_name, repo_url)

                if language is not None:
                    repo_detail = {
                        "name": repo_name,
                        "language": language,
                        "stars": stars,
                        "forks": forks,
                        "commits": commits,
                        "pull_requests": pull_requests
                    }
                    repo_details.append(repo_detail)
                else:
                    print(f"Details not found for repository: {repo_name}")

                pbar.update(1)  # Update the progress bar
        redis_client.set(username + "_repo_details", json.dumps(repo_details))
        return repo_details
    else:
        print("Unable to fetch repository data.")
        return None
