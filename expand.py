import os
import requests
import re
from supabase import create_client, Client

# সুপাবেস ক্লায়েন্ট ইনিশিয়ালাইজেশন
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_ANON_KEY")
)

def get_full_url(short_url: str) -> str:
    if not short_url:
        return short_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        check_url = short_url.lower()

        # =====================================================================
        # 📸 INSTAGRAM (আপনার আগের সচল কোড - সম্পূর্ণ টাচফ্রি ও নিরাপদ)
        # =====================================================================
        if "instagram.com" in check_url or "ig.me" in check_url:
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(short_url, timeout=12, allow_redirects=True)
            final_url = response.url
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            return clean_url

        # =====================================================================
        # 🎵 TIKTOK (আপনার আগের সচল কোড - সম্পূর্ণ টাচফ্রি ও নিরাপদ)
        # =====================================================================
        if "tiktok.com" in check_url:
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(short_url, timeout=12, allow_redirects=True)
            return response.url.split("?")[0].split("&")[0]

        # =====================================================================
        # 📘 FACEBOOK FIXED ONLY (আলাদা এবং স্বাধীন ব্লক, অন্যগুলোতে ঝামেলা করবে না)
        # =====================================================================
        if "facebook.com" in check_url or "fb.watch" in check_url:
            # গিটহাব সার্ভার ব্লকিং বাইপাস করতে ওএমবেড গেটওয়ে হিট
            oembed_endpoint = f"https://www.facebook.com/plugins/video/oembed.json?url={short_url}"
            try:
                api_res = requests.get(oembed_endpoint, headers=headers, timeout=10)
                if api_res.status_code == 200:
                    html_box = api_res.json().get("html", "")
                    id_match = re.search(r'(?:reel|reels|video|v)/([0-9]{12,20})', html_box)
                    if id_match:
                        return f"https://www.facebook.com/reel/{id_match.group(1)}"
            except Exception as api_err:
                print(f"Facebook API Gateway bypass failed, trying regular method: {api_err}")

            # ওএমবেড কাজ না করলে ব্যাকআপ রিডাইরেক্ট মেথড
            try:
                session = requests.Session()
                session.headers.update(headers)
                response = session.get(short_url, timeout=12, allow_redirects=True)
                final_url = response.url
                
                # রিডাইরেক্ট লোকেশন চেইন থেকে আইডি খোঁজা
                if response.history:
                    for resp in response.history:
                        loc = resp.headers.get('Location', '')
                        id_match_loc = re.search(r'(?:reel|reels|video|v)/([0-9]{12,20})', loc)
                        if id_match_loc:
                            return f"https://www.facebook.com/reel/{id_match_loc.group(1)}"
                
                # পেজের বডি টেক্সট থেকে আইডি খোঁজা
                id_match_content = re.search(r'(?:reel|reels|video|v|audio)/([0-9]{12,20})', final_url + " " + response.text)
                if id_match_content:
                    return f"https://www.facebook.com/reel/{id_match_content.group(1)}"
                
                # কোনো আইডি না পাওয়া গেলে ট্র্যাকিং প্যারামিটার কেটে ক্লিন ইউআরএল ডাটাবেজে রাখা
                clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
                if "/reels/" in clean_url:
                    clean_url = clean_url.replace("/reels/", "/reel/")
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                return clean_url
            except Exception as fb_err:
                print(f"Facebook Fallback failed: {fb_err}")
                return short_url

        return short_url.split("?")[0]

    except Exception as e:
        print(f"Error processing {short_url}: {e}")
        return short_url


def process_posts():
    print("🚀 Starting URL Processor (Safe Mode for Instagram, TikTok & Facebook)...")
    response = supabase.table("posts").select("*").execute()
    posts = response.data or []
    
    updated = 0
    for post in posts:
        current_url = post.get("url", "").strip()
        if not current_url:
            continue

        url_lower = current_url.lower()
        if ("instagram.com" in url_lower or 
            "facebook.com" in url_lower or 
            "fb.watch" in url_lower or 
            "tiktok.com" in url_lower or
            "ig.me" in url_lower):
            
            print(f"Processing → {current_url[:80]}...")
            new_url = get_full_url(current_url)
            
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ Updated Database URL: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
