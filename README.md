# Instagram Story Scheduler

This small Python program publishes one queued video as an Instagram Story each
time it runs. Schedule it once a day with your operating system's scheduler.
It uses Meta's official Instagram API; it does not automate the Instagram app or
ask for your Instagram password.

## Requirements

- An Instagram **Business or Creator** account with access to Meta's content
  publishing API and the required permissions.
- A video hosting location that gives each video a stable, publicly accessible
  HTTPS URL. The API fetches the video from that URL; it cannot publish a video
  directly from a local file. Do not use expiring URLs or expose private videos.
- Python 3.9 or newer.

## Setup

1. Add one video URL per line to `videos.txt`. Blank lines and lines starting
   with `#` are ignored. The program moves through the list in order and repeats
   from the beginning after the last video.
2. Set the API credentials and version in the environment where the scheduled
   job will run:

   ```sh
   export IG_USER_ID="your-instagram-professional-account-id"
   export IG_ACCESS_TOKEN="your-meta-access-token"
   export IG_GRAPH_API_VERSION="vXX.0"
   ```

   Replace `vXX.0` with a currently supported version. Keep the access token
   private and do not commit it to the repository.
3. Check the queue without publishing:

   ```sh
   python3 story_scheduler.py --dry-run
   ```

4. Run once to publish:

   ```sh
   python3 story_scheduler.py
   ```

The `.story_scheduler_state.json` file records the last successful publication
date and which URL to use next. Keep this file between runs. The date uses the
machine's local timezone; run the job at the time you want the Story to appear.

## Daily scheduling

Use cron, Task Scheduler, or another operating-system scheduler to run
`python3 /absolute/path/to/story_scheduler.py` once per day. Configure the three
environment variables in that scheduled job as well; a cron job may not inherit
variables from an interactive terminal. The script will skip a second run on
the same local calendar day.

The API can reject unsupported video formats, inaccessible URLs, expired tokens,
or accounts without the required access. Check Meta's current Instagram
publishing documentation for supported media requirements and permissions.
