from jira import JIRA

jira = JIRA(
    server="urlneeds to be added",
    basic_auth=("email -********", "token -********")
)

issue = jira.create_issue(fields={
    "project": {"key": "AT"},
    "summary": "Signup test case",
    "issuetype": {"name": "QA_Test_Case"},
    "description": "Created via script"
})

print(issue.key)