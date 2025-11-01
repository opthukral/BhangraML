
import csv
import os
import sys
from typing import Dict, List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_youtube_client():
    api_key = os.getenv("YOUTUBE_API_KEY", DEFAULT_API_KEY).strip()
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set YOUTUBE_API_KEY env var or edit DEFAULT_API_KEY."
        )
    return build("youtube", "v3", developerKey=api_key)


def resolve_channel_id(youtube, handle_or_id: str) -> str:
    """Resolve a channel handle (e.g., @gabroo-tv) or ID into a channel ID.

    Returns a YouTube channel ID like UCxxxxxxxxxxxxxxxxxxxxxx.
    """
    text = handle_or_id.strip()
    if text.startswith("UC") and len(text) >= 20:
        return text

    # Try new forHandle parameter if available
    try:
        req = youtube.channels().list(part="id", forHandle=text.lstrip("@"))
        res = req.execute()
        items = res.get("items", [])
        if items:
            return items[0]["id"]
    except TypeError:
        # forHandle not supported in this client discovery; fall back to search
        pass
    except HttpError:
        # Continue to fallback
        pass

    # Fallback: search for channel
    q = text.lstrip("@")
    res = youtube.search().list(part="snippet", type="channel", q=q, maxResults=5).execute()
    items = res.get("items", [])
    if not items:
        raise RuntimeError(f"Could not resolve channel for '{handle_or_id}'")
    return items[0]["snippet"]["channelId"]


def get_uploads_playlist_id(youtube, channel_id: str) -> str:
    res = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    items = res.get("items", [])
    if not items:
        raise RuntimeError(f"Channel not found for id {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def list_all_video_ids(youtube, uploads_playlist_id: str) -> List[str]:
    video_ids: List[str] = []
    page_token = None
    while True:
        res = (
            youtube.playlistItems()
            .list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )
        for item in res.get("items", []):
            vid = item["contentDetails"]["videoId"]
            video_ids.append(vid)
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return video_ids


def chunked(seq: List[str], size: int) -> List[List[str]]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


def fetch_video_details(youtube, video_ids: List[str]) -> List[Dict]:
    results: List[Dict] = []
    for batch in chunked(video_ids, 50):
        res = (
            youtube.videos()
            .list(
                part="snippet,contentDetails,statistics,status",
                id=",".join(batch),
                maxResults=50,
            )
            .execute()
        )
        results.extend(res.get("items", []))
    return results


def iso8601_duration_to_str(iso: str) -> str:
    # Return the original ISO 8601 duration; parsing to seconds is optional
    return iso or ""


def to_row(item: Dict) -> Dict:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    vid = item.get("id", "")
    title = snippet.get("title", "")
    published_at = snippet.get("publishedAt", "")
    year = published_at[:4] if published_at else ""
    duration = iso8601_duration_to_str(content.get("duration", ""))
    tags = snippet.get("tags", []) or []
    return {
        "video_id": vid,
        "title": title,
        "published_at": published_at,
        "year": year,
        "duration": duration,
        "view_count": stats.get("viewCount", ""),
        "like_count": stats.get("likeCount", ""),
        "comment_count": stats.get("commentCount", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "category_id": snippet.get("categoryId", ""),
        "tags": ";".join(tags),
        "description": snippet.get("description", ""),
    }


def save_csv(rows: List[Dict], path: str) -> None:
    if not rows:
        print("No rows to write.")
        return
    fieldnames = [
        "video_id",
        "title",
        "published_at",
        "year",
        "duration",
        "view_count",
        "like_count",
        "comment_count",
        "channel_title",
        "category_id",
        "tags",
        "description",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {len(rows)} rows to {path}")


def main():
    # Defaults for Gabroo TV
    default_handle = "@gabroo-tv"
    output_path = "gabroo_videos_full.csv"

    handle_or_id = sys.argv[1] if len(sys.argv) > 1 else default_handle
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    yt = get_youtube_client()
    try:
        channel_id = resolve_channel_id(yt, handle_or_id)
        print(f"Channel ID: {channel_id}")

        uploads_id = get_uploads_playlist_id(yt, channel_id)
        print("Fetching video ids…")
        video_ids = list_all_video_ids(yt, uploads_id)
        print(f"Found {len(video_ids)} videos")

        print("Fetching video details…")
        details = fetch_video_details(yt, video_ids)
        rows = [to_row(item) for item in details]
        save_csv(rows, output_path)
    except HttpError as e:
        print(f"YouTube API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
