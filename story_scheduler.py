import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def api_post(url, data):
    request = Request(url, data=urlencode(data).encode(), method="POST")
    return api_request(request)


def api_get(url, params):
    request = Request(f"{url}?{urlencode(params)}")
    return api_request(request)


def api_request(request):
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"Instagram API request failed: {error}") from error

    if "error" in result:
        error = result["error"]
        raise RuntimeError(
            f"Instagram API error {error.get('code', '')}: "
            f"{error.get('message', 'Unknown error')}"
        )
    return result


def read_queue(path):
    urls = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not urls:
        raise ValueError(f"No video URLs found in {path}")
    for url in urls:
        if not url.startswith("https://"):
            raise ValueError(f"Video URL must use HTTPS: {url}")
    return urls


def publish_story(video_url, user_id, access_token, api_version):
    base_url = f"https://graph.instagram.com/{api_version}/{user_id}"
    container = api_post(
        f"{base_url}/media",
        {
            "media_type": "STORIES",
            "video_url": video_url,
            "access_token": access_token,
        },
    )
    container_id = container["id"]

    for _ in range(60):
        status = api_get(
            f"https://graph.instagram.com/{api_version}/{container_id}",
            {"fields": "status_code", "access_token": access_token},
        )
        status_code = status.get("status_code")
        if status_code == "FINISHED":
            break
        if status_code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram could not process the video: {status}")
        time.sleep(10)
    else:
        raise TimeoutError("Timed out waiting for Instagram to process the video")

    result = api_post(
        f"{base_url}/media_publish",
        {"creation_id": container_id, "access_token": access_token},
    )
    return result["id"]


def main():
    parser = argparse.ArgumentParser(
        description="Publish the next video in a queue as an Instagram Story."
    )
    parser.add_argument("--queue", type=Path, default=Path("videos.txt"))
    parser.add_argument("--state", type=Path, default=Path(".story_scheduler_state.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        urls = read_queue(args.queue)
        today = time.strftime("%Y-%m-%d")
        state = json.loads(args.state.read_text(encoding="utf-8")) if args.state.exists() else {}
        if state.get("last_published_date") == today:
            print(f"A Story has already been published today ({today}).")
            return 0

        index = int(state.get("next_video_index", 0)) % len(urls)
        video_url = urls[index]
        if args.dry_run:
            print(f"Would publish video {index + 1}/{len(urls)}: {video_url}")
            return 0

        user_id = os.environ["IG_USER_ID"]
        access_token = os.environ["IG_ACCESS_TOKEN"]
        api_version = os.environ["IG_GRAPH_API_VERSION"]
        story_id = publish_story(video_url, user_id, access_token, api_version)

        args.state.parent.mkdir(parents=True, exist_ok=True)
        temporary_state = args.state.with_name(args.state.name + ".tmp")
        temporary_state.write_text(
            json.dumps(
                {
                    "last_published_date": today,
                    "next_video_index": (index + 1) % len(urls),
                }
            ),
            encoding="utf-8",
        )
        temporary_state.replace(args.state)
        print(f"Published Instagram Story {story_id} from video {index + 1}.")
        return 0
    except (KeyError, OSError, ValueError, RuntimeError, TimeoutError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
