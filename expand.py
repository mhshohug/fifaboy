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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # ১. শর্ট লিংকের আসল রিডাইরেক্ট লোকেশন বের করা
        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url
        html_content = response.text

        check_url = final_url.lower()
        check_short = short_url.lower()

        # ====================== 📸 INSTAGRAM CLEAN LINK ======================
        if "instagram.com" in check_url or "instagram.com" in check_short:
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            return clean_url

        # ====================== 📘 FACEBOOK (আপনার চাওয়া পারফেক্ট reel/ID ফরম্যাট) ======================
        if "facebook.com" in check_url or "fb.watch" in check_url or "facebook.com" in check_short:
            
            # মেথড A: যদি রিডাইরেক্ট ইউআরএল বা ওরিজিনাল এইচটিএমএল মেটা ট্যাগের ভেতর ওরিজিনাল রিল আইডি পাওয়া যায়
            combined_text = final_url + " " + html_content
            
            # ফেসবুক রিলের ১৫-১৬ ডিজিটের ইউনিক আইডি খুঁজে বের করার মাস্টার রেগুলার এক্সপ্রেশন
            fb_id_match = re.search(r'(?:reel|reels|video|v|audio)/([0-9]{12,20})', combined_text)
            
            if fb_id_match:
                reel_id = fb_id_match.group(1)
                # ডিরেক্ট আপনার চাওয়া নিখুঁত আউটপুট ফরম্যাট তৈরি
                return f"https://www.facebook.com/reel/{reel_id}"
            
            # মেথড B: ওএমবেড ব্যাকআপ প্লাগইন থেকে আইডি খোঁজা
            oembed_url = f"https://www.facebook.com/plugins/video/oembed.json?url={short_url}"
            try:
                api_res = session.get(oembed_url, timeout=7)
                if api_res.status_code == 200:
                    html_box = api_res.json().get("html", "")
                    api_id_match = re.search(r'(?:reel|reels|video|v)/([0-9]{12,20})', html_box)
                    if api_id_match:
                        return f"https://www.facebook.com/reel/{api_id_match.group(1)}"
            except Exception:
                pass

            # মেথড C: যদি কোনো আইডিই ম্যাচ না করে, তবে অন্তত ট্র্যাকিং কেটে মেইন পার্ট রাখা
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            return clean_url

        # ====================== 🎵 TIKTOK ======================
        if "tiktok.com" in check_url or "tiktok.com" in check_short:
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
