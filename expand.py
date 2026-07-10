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
        # বড় হাত/ছোট হাতের অক্ষরের ঝামেলা সাফ করা
        check_url = short_url.lower()

        # ====================== 📸 INSTAGRAM CLEAN LINK ======================
        if "instagram.com" in check_url or "ig.me" in check_url:
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(short_url, timeout=12, allow_redirects=True)
            final_url = response.url
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            return clean_url

        # ====================== 📘 FACEBOOK FIXED (আপনার চাওয়া reel/ID ফরম্যাট) ======================
        if "facebook.com" in check_url or "fb.watch" in check_url:
            
            # ট্রিক ১: যদি লিংক অলরেডি /share/r/ ফরম্যাটে থাকে, তবে মেটার সিকিউরিটি ব্লক বাইপাস করতে ওএমবেড এপিআই ডিরেক্ট হিট
            if "/share/r/" in short_url or "/share/" in short_url or "fb.watch" in short_url:
                # ফেসবুকের ওএমবেড প্লাগইন এপিআই যা বট ব্লক করে না
                oembed_endpoint = f"https://www.facebook.com/plugins/video/oembed.json?url={short_url}"
                try:
                    api_res = requests.get(oembed_endpoint, headers=headers, timeout=10)
                    if api_res.status_code == 200:
                        api_data = api_res.json()
                        html_box = api_data.get("html", "")
                        
                        # এপিআই রেসপন্সের এইচটিএমএল থেকে আসল নিউমেরিক আইডি টেনে বের করা
                        id_match = re.search(r'(?:reel|reels|video|v)/([0-9]{12,20})', html_box)
                        if id_match:
                            reel_id = id_match.group(1)
                            # ডিরেক্ট আপনার চাওয়া ক্লিন আউটপুট ফরম্যাট জেনারেট
                            return f"https://www.facebook.com/reel/{reel_id}"
                except Exception as api_err:
                    print(f"API Method Failed: {api_err}")

            # ট্রিক ২: যদি এপিআই ফেইল করে, তবে নরমাল রিডাইরেক্ট ট্রাই করা
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(short_url, timeout=12, allow_redirects=True)
            final_url = response.url
            html_content = response.text

            # রিডাইরেক্ট ইউআরএল বা পেজের ভেতরের ওরিজিনাল আইডি খোঁজা
            combined_search = final_url + " " + html_content
            id_match_backup = re.search(r'(?:reel|reels|video|v|audio)/([0-9]{12,20})', combined_search)
            
            if id_match_backup:
                return f"https://www.facebook.com/reel/{id_match_backup.group(1)}"

            # ট্রিক ৩: যদি ফেসবুক লগইন পেজে আটকে দেয়, তবে টেক্সট থেকে মেইন পার্ট পরিষ্কার করা
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if "/reels/" in clean_url:
                clean_url = clean_url.replace("/reels/", "/reel/")
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            return clean_url

        # ====================== 🎵 TIKTOK ======================
        if "tiktok.com" in check_url:
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(short_url, timeout=12, allow_redirects=True)
            return response.url.split("?")[0].split("&")[0]

        return short_url.split("?")[0]

    except Exception as e:
        print(f"Error processing {short_url}: {e}")
        return short_url


def process_posts():
    print("🚀 Starting URL Processor for Perfect Reel Format...")
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
                print(f"✅ Updated to Clean URL: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
