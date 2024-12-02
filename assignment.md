
# Assignment
The objective of this assignment is to track activities on GitHub. To achieve this, utilize [the GitHub Events API](https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#list-repository-events).


- The application can monitor up to **5 configurable repositories**. 
- It **generates statistics** based on a rolling window of either 7 days or 500 events, whichever is less. 
- These statistics are made available to end-users via a REST API. Specifically, the API will show the **average time between consecutive events, separately for each combination of event type and repository name**.
- The application should minimize requests to the GitHub API and retain data through application restarts.


Please include a README file with your solution detailing the steps to run the application and a brief outline of your assumptions. 
Also, include reasonable documentation for fellow engineers and API users.
The assignment should be completed in Python.


It should take no more than 8 hours of cumulative work to finish. 
Please submit the best solution you can deliver within this time frame. 
If you do not manage to finish the solution fully, please report which parts are missing and sketch possible future work.

