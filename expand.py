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

    # ফেসবুকের রিডাইরেক্ট ভাঙার জন্য কড়া মোবাইল ব্রাউজার হেডার
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # রিডাইরেক্ট ফলো করে মেইন ইউআরএল হিট করা
        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url
        
        # ট্রিক: যদি ডিরেক্ট response.url এও ফেসবুকের মেইন লিংক না আসে, তবে রিডাইরেক্ট হিস্ট্রি চেক করা
        if response.history:
            for resp in response.history:
                if "facebook.com/reel/" in resp.headers.get('Location', '') or "facebook.com/videos/" in resp.headers.get('Location', ''):
                    final_url = resp.headers['Location']
                    break

        check_url = final_url.lower()
        check_short = short_url.lower()

        # ====================== 📸 INSTAGRAM CLEAN LINK ======================
        if "instagram.com" in check_url or "instagram.com" in check_short:
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            return clean_url

        # ====================== 📘 FACEBOOK FIXED METHOD ======================
        if "facebook.com" in check_url or "fb.watch" in check_url or "facebook.com" in check_short:
            
            # ফেসবুকের যদি মোবাইল বা ডেস্কটপ আসল রিল/ভিডিও লোকেশন চলে আসে
            if "reel/" in final_url or "reels/" in final_url or "videos/" in final_url or "watch/" in final_url:
                clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                
                # যদি লিংকে /reels/ থাকে, সেটাকে স্ট্যান্ডার্ড /reel/ করে দেওয়া যেন আইফ্রেম রিড করতে পারে
                if "/reels/" in clean_url:
                    clean_url = clean_url.replace("/reels/", "/reel/")
                    
                return clean_url

            # ব্যাকআপ রেগুলার এক্সপ্রেশন (যদি রিডাইরেক্টের পরেও /share/ থেকে যায়)
            html = response.text
            og_url_match = re.search(r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']', html)
            if og_url_match:
                fb_real_url = og_url_match.group(1)
                clean_url = fb_real_url.split("?")[0].split("&")[0].split("#")[0]
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                if "/reels/" in clean_url:
                    clean_url = clean_url.replace("/reels/", "/reel/")
                return clean_url

            # কোনো লজিক কাজ না করলে একদম ফ্রেশ ট্র্যাকিং কাটা লিংক
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
