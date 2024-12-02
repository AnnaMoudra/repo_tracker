# Repository Tracker

- API to be used by the user is in app.py. 
- Application logic is in tracker/tracker.py. 

Added repositories are stored in JSON file in db/repository.json (or see config.toml).
Each repository is stored under its ID (number used to update the repository) and contains owner name, repository name and ETag of last event fetch.
```json
    "0": {
        "owner": "pandas-dev",
        "name": "pandas",
        "etag": "W/\"45b5fa682358200006fe831e206281c9d761170403b29f9b1467d18fce190cb5\""
    }
```

Events (selected attributes) for each repository are stored in JSON file db/events.json (or see config.toml). Only the last 500 or 7 days old events (smaller set) are stored.

When user requests statistics, each repository checks against GitHub if its etag matches. If not, the events for the repository are refreshed. 
Statistics are counted from stored event data:

```
{"Bogdanp/awesome-advent-of-code":{"ForkEvent":"3190.0 s (or 0.89 h)","IssueCommentEvent":"5073.0 s (or 1.41 h)","PullRequestEvent":"1091.0 s (or 0.3 h)","PushEvent":"3121.0 s (or 0.87 h)","WatchEvent":"1839.0 s (or 0.51 h)","events_count":101},"boto/boto3":{"CreateEvent":"63567.0 s (or 17.66 h)","DeleteEvent":"None s (or None h)","ForkEvent":"82064.0 s (or 22.8 h)","IssueCommentEvent":"37447.0 s (or 10.4 h)","IssuesEvent":"27515.0 s (or 7.64 h)","PullRequestEvent":"9287.0 s (or 2.58 h)","PullRequestReviewEvent":"None s (or None h)","PushEvent":"30236.0 s (or 8.4 h)","WatchEvent":"46856.0 s (or 13.02 h)","events_count":53},"pandas-dev/pandas":{"ForkEvent":"14768.0 s (or 4.1 h)","IssueCommentEvent":"5079.0 s (or 1.41 h)","IssuesEvent":"25630.0 s (or 7.12 h)","PullRequestEvent":"11959.0 s (or 3.32 h)","PullRequestReviewCommentEvent":"24205.0 s (or 6.72 h)","PullRequestReviewEvent":"31567.0 s (or 8.77 h)","PushEvent":"135532.0 s (or 37.65 h)","WatchEvent":"8456.0 s (or 2.35 h)","events_count":243},"scikit-learn/scikit-learn":{"CreateEvent":"None s (or None h)","ForkEvent":"21357.0 s (or 5.93 h)","IssueCommentEvent":"3707.0 s (or 1.03 h)","IssuesEvent":"24524.0 s (or 6.81 h)","PullRequestEvent":"13124.0 s (or 3.65 h)","PullRequestReviewCommentEvent":"3753.0 s (or 1.04 h)","PullRequestReviewEvent":"3354.0 s (or 0.93 h)","PushEvent":"14106.0 s (or 3.92 h)","WatchEvent":"6999.0 s (or 1.94 h)","events_count":268},"streamlit/streamlit":{"CreateEvent":"32510.0 s (or 9.03 h)","DeleteEvent":"48754.0 s (or 13.54 h)","ForkEvent":"68338.0 s (or 18.98 h)","IssueCommentEvent":"10532.0 s (or 2.93 h)","IssuesEvent":"27208.0 s (or 7.56 h)","PullRequestEvent":"25687.0 s (or 7.14 h)","PullRequestReviewCommentEvent":"4032.0 s (or 1.12 h)","PullRequestReviewEvent":"6250.0 s (or 1.74 h)","PushEvent":"6739.0 s (or 1.87 h)","WatchEvent":"6356.0 s (or 1.77 h)","events_count":250}}
```


#### Assumptions: 

- User knows the owner and repository name they want to track. The repository exists and is public. Application is set up with client id and client secret to generate access token, otherwise user will update code to add access token to RepositoryTracker class headers. Application serves one client at a time.


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
- I did not have the time to investigate the pagination of the Github API, but in many cases, the pagination stopped at 3 pages (100 items per page) even before I added filtering for only data newer than 1 week. If there is a time limit on history, storing events is a good option.
- The structure of the code could be much improved as the tracker class is handling almost everything. Logging is missing.
