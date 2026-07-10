import os
import requests
import re
from urllib.parse import quote
from supabase import create_client, Client

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_ANON_KEY")
)

def get_full_url(short_url: str) -> str:
    if not short_url:
        return short_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # Initial visit to Facebook to set cookies
        session.get("https://www.facebook.com", timeout=8)

        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url
        html = response.text

        # ====================== FACEBOOK ======================
        if any(x in final_url.lower() for x in ["facebook.com", "fb.watch", "share/r/"]):
            
            # Multiple patterns to extract Video ID
            patterns = [
                r'/video/(\d{10,})',
                r'v=(\d{10,})',
                r'/(\d{15,20})',
                r'video_id["\']?\s*[:=]\s*["\']?(\d+)',
                r'"id":"(\d{10,})"',
                r'"videoID":"(\d{10,})"'
            ]

            video_id = None
            for pattern in patterns:
                match = re.search(pattern, html + " " + final_url)
                if match:
                    video_id = match.group(1)
                    break

            if video_id:
                return f"https://www.facebook.com/video/embed?video_id={video_id}"

            # Ultimate Fallback
            clean_url = final_url.split("?")[0].split("&")[0]
            return f"https://www.facebook.com/plugins/video.php?href={quote(clean_url)}&width=500&show_text=false&height=500"

        # ====================== TIKTOK ======================
        if "tiktok.com" in final_url or "vt.tiktok.com" in short_url or "vm.tiktok.com" in short_url:
            return final_url.split("?")[0].split("&")[0]

        return final_url.split("?")[0]

    except Exception as e:
        print(f"Error processing {short_url}: {e}")
        return short_url


def process_posts():
    print("🚀 Starting URL Processor...")
    response = supabase.table("posts").select("*").execute()
    posts = response.data or []
    
    updated = 0
    for post in posts:
        current_url = post.get("url", "").strip()
        if not current_url:
            continue

        if ("facebook.com" in current_url or 
            "fb.watch" in current_url or 
            "tiktok.com" in current_url):
            
            print(f"Processing → {current_url[:80]}...")
            new_url = get_full_url(current_url)
            
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ Updated: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
