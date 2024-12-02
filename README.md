# Repository Tracker

API to be used by the user is in app.py. Application logic is in tracker/tracker.py. 

Added repositories are stored in JSON file in db/repository.json (or see config.toml).
Each repository is stored under its ID (number used to update the repository) and contains owner name, repository name and ETag of last event fetch.

Events (selected attributes) for each repository are stored in JSON file db/events.json (or see config.toml). Only the last 500 or 7 days old events (smaller set) are stored.

When user requests statistics, each repository checks if its etag matches, if not, the events for the repository are refreshed. Statistics are counted from stored event data.


Assumptions: 
    - User knows the owner and repository name they want to track. The repository exists and is public. Application is set up with client id and client secret to generate access token, otherwise user will update code to add access token to RepositoryTracker class headers.


## How to use

1. Install requirements from requirements.in file.

2. Setup confuguration in config.toml file. It should be usable as is, if token is not generated register, use your own client id and update configuration or generate your token and use tracker.update_headers(token='your token').

3. Run the app:
```shell
flask run
```

4. Use the API

List repositories:
```shell
curl -X GET <ip-address:port>/list-repositories
```
Add another repository:
```bash
curl -H "Content-Type: application/json" --json "{\"owner\":\"pandas-dev\", \"name\":\"pandas\"}" -X POST <ip-adddress:port>/add-repository
```
Delete repository:
```shell
curl -X DELETE <ip-address:port>/configure-repositories/0
```
List statistics for all repositories:
```shell
curl -X GET <ip-address:port>/
```


## Notes
Due to the time limit I have not finished the solution fully and multiple parts should be improved.

- In several instances the application does not check the validity of the input, either from the user or the GitHub API.
- The responses are lacking proper format.
- The result is listed for all of the repositories and does not offer much information, aside from the average seconds between each event type.
- It's not necessary to store the events, instead we can just store the stats.
- I did not have the time to investigate the pagination of the Github API, but in many cases, the pagination stopped at 3 pages (100 items per page) even before I added filtering for only data newer than 1 week.
- The structure of the code could be much improved as the tracker class is handling almost everything. Logging is missing.
