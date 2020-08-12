# Export DM conversations form Slack

To do so, follow two steps:

## (1) Clone this repo
`git clone git@github.com:margaritageleta/slack-export-history.git`

## (2) Create a Slack App
Go to https://api.slack.com/apps and go straight to `Create New App`. Choose your Workspace and press `Create App`. Then, click on your app and go to `Add features and functionality` -> `Permissions` -> `Scopes` and add the following scopes in `User Token Scopes` (be careful, `User Token Scopes` NOT `Bot Token Scopes`):

+ `channels:history`
+ `channels:read`
+ `groups:history`
+ `groups:read`
+ `im:history`
+ `im:read`
+ `mpim:history`
+ `mpim:read`
+ `users:read`

Then install the app in your workspace (you can go to `OAuth & Permissions` section and press `Reinstall app`), accept the permissions and copy the OAuth Access Token. 


## We are ready to download the messages

Go ahead to the terminal and run `python3 slack.py --token COPY_YOUR_OAUTH_TOKEN_HERE`. Choose the DM conversation you want to export and we are done! 
