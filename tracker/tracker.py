import requests
from datetime import datetime, timedelta, timezone
import json
from tracker.settings import Settings
import os

settings = Settings()

# Access repositories and other settings
REPOSITORIES_FILE = settings.repositories
EVENTS_FILE = settings.events
ROLLING_WINDOW_DAYS = settings.window_length
MAX_EVENTS = settings.max_events

class RepositoryTracker:
    """ Tracker class """
    repositories: dict = None
    events: dict = None

    def __init__(self):
        self.headers = {
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28"
            }

    def update_headers(self, token: str):
        self.headers["Authorization"] = f"token {token}"

    @staticmethod
    def load_events() -> dict:
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, "r") as file:
                return json.load(file)
        return {}
    
    @staticmethod
    def load_repositories() -> dict:
        if os.path.exists(REPOSITORIES_FILE):
            with open(REPOSITORIES_FILE, "r") as file:
                return json.load(file)
        return {}
        
    def add_repository(self, owner: str, name: str) -> (int, dict):
        self.repositories = self.load_repositories()

        if len(self.repositories) >= 5:
            return 400, {"message": "Error adding repository. Maximum number of repositories (5) reached."}
            
        max_id = 0
        for repo_key, repo in self.repositories.items():
            max_id = int(repo_key) + 1 if int(repo_key) >= max_id else max_id
            if repo["owner"] == owner and repo["name"] == name:
                return 400, {"message": "Error adding repository. Repository already exists."}

        self.repositories[str(max_id)] = {
            "owner": owner,
            "name": name,
            "etag": None
        }
        self._save_repo_file()
        return 201, {"message":"Succesfully added repository.", "data": self.repositories}
            
    def delete_repository(self, repo_id: int) -> (int, dict):
        self.repositories = self.load_repositories()
        repo = {}
        try:
            repo = self.repositories[str(repo_id)]
            del self.repositories[str(repo_id)]
            # save repositories
            self._save_repo_file()
        except Exception as e:
            return 500, {"message": f"Error when deleting repository: {str(e)}"}
        
        try:
            self.events = self.load_events()
            del self.events[str(repo_id)]
            self._save_events_file()
        except Exception as e:
            return 500, {"message": f"Repository deleted. Error when deleting fetched events: {str(e)}", "Deleted": repo}
        
        return 200, {"message": "Repository deleted.", "Deleted": repo}


    def _save_events_file(self):
        with open(EVENTS_FILE, "w") as file:
            json.dump(self.events, file, indent=4)

    def _save_repo_file(self):
        with open(REPOSITORIES_FILE, "w") as file:
            json.dump(self.repositories, file, indent=4)


    @staticmethod
    def _request_events_page(url: str, repo_header: dict, page: int = None):
        if page:
            response = requests.get(url, headers=repo_header, params={"per_page":100, "page":page})
        else:
            response = requests.get(url, headers=repo_header)
            
        return response

    def fetch_events(self) -> (int, dict):
        """
        Fetch new events for all repositories from github and store them for processing.
        """
        self.repositories = self.load_repositories()
        self.events = self.load_events()

        if not bool(self.repositories):
            return 400, {"message": "Error: No repositories configured."}

        for repo_id, repo in self.repositories.items():
            url = f"https://api.github.com/repos/{repo['owner']}/{repo['name']}/events"

            # adding ETag if we got this data in the past
            add_etag = bool(repo["etag"] and repo_id in self.events.keys() and len(self.events[repo_id]) > 0)
            repo_header = {**self.headers, 'if-none-match': repo["etag"]} if add_etag else self.headers

            response = self._request_events_page(url, repo_header, page=1)
            if response.status_code == 200:
                self.repositories[repo_id]['etag'] = response.headers['etag']

                fetch_more = self._store_events(repo_id, response.json())
                page_count = 2
                next_link = response.links['next'].get('url', None)
                last_page = response.links['last'].get('url', None)
                
                while next_link and fetch_more and page_count <=5:            
                    response = self._request_events_page(next_link, self.headers)
                    if response.status_code == 200:
                        fetch_more = self._store_events(repo_id, response.json())
                        if last_page and next_link != last_page:
                            next_link = response.links['next'].get('url', None)
                        else:
                            next_link = None
                
                    else:
                        # TODO this should be handled but isnt :) User may run into 403 code.
                        next_link = None
                        print(response.status_code)
                        print(response.json())
                    page_count += 1

                self._filter_events(repo_id)
                self._save_events_file()
            elif response.status_code == 304:
                print(f"Nothing changed for {repo_id}.")
                continue
            else:
                return response.status_code, {"message": f"Error fetching data for repository {repo_id}: {response}."}  
        self._save_repo_file() # saving new repository etags
        return 200, {"message": "Repository events stored"}

    def _store_events(self, repo_id: str, events) -> bool:
        """
        Process and store events for a specific repository.
        """
        fetch_more = True
        repo_id = str(repo_id)
        if not repo_id in self.events.keys():
            self.events[repo_id] = []

        for event in events:
            event_data = {
                "id": event["id"],
                "type": event["type"],
                "created_at": event["created_at"],
                "repo_name": event["repo"]["name"]
            }
            # Avoid duplicates
            if not any(e["id"] == event_data["id"] for e in self.events[repo_id]):
                self.events[repo_id].append(event_data)
            else:
                fetch_more = False # processing data we already have

        if not fetch_more or not events:
            #print(f"Processing stored data..{fetch_more}, {len(events)}")
            return False

        oldest_date = sorted(self.events[repo_id], key = lambda x: x['created_at'])[0]
        if datetime.strptime(oldest_date["created_at"], "%Y-%m-%dT%H:%M:%SZ").astimezone(timezone.utc) < datetime.now(timezone.utc) - timedelta(days=ROLLING_WINDOW_DAYS):
            fetch_more = False
            #print("Data older than a week.")

        return fetch_more

    def _filter_events(self, repo_id: str):
        """ For repository filters  only the last 500 events or events from the last 7 days whichever is less. """
        self.events[repo_id] = sorted(self.events[repo_id], key = lambda event: event['id'], reverse=True)
        self.events[repo_id] = self.events[repo_id][:MAX_EVENTS]
        self.events[repo_id] = [
            e
            for e in self.events[repo_id]
            if datetime.strptime(e["created_at"], "%Y-%m-%dT%H:%M:%SZ").astimezone(timezone.utc)
            >= datetime.now(timezone.utc) - timedelta(days=ROLLING_WINDOW_DAYS)
        ]

    def calculate_statistics(self) -> dict:
        """
        Calculate the average time between consecutive events for each event type and repository.
        """
        statistics = {}
        self.repositories = self.load_repositories()
        self.events = self.load_events()

        for repo_id, repo in self.repositories.items():
            events = self.events.get(repo_id, [])
            events_total_num = len(events)
            repo_name = repo["owner"]+'/'+ repo["name"]
            # Group events by type
            events_by_type = {}
            for event in events:
                event_type = event["type"]
                if event_type not in events_by_type:
                    events_by_type[event_type] = []
                events_by_type[event_type].append(event)

            # Calculate average time differences for each event type
            repo_stats = {}
            for event_type, event_list in events_by_type.items():
                if len(event_list) > 1:
                    # Sort by timestamp
                    event_list.sort(key=lambda e: e["created_at"])
                    time_diffs = [(
                            datetime.strptime(event_list[i]["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                            - datetime.strptime(event_list[i - 1]["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                        ).total_seconds()
                        for i in range(1, len(event_list))
                    ]
                    avg_time = round(sum(time_diffs) / len(time_diffs), 0)
                    avg_time_h = round(avg_time/60**2, 2)
                else:
                    avg_time = None  # Not enough data to calculate
                    avg_time_h = None
                repo_stats[event_type] = f"{avg_time} s (or {avg_time_h} h)"
                repo_stats['events_count'] = events_total_num

            statistics[repo_name] = repo_stats
        return statistics
