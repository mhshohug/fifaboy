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

    # ফেসবুকের বট ডিটেকশন এড়াতে একদম নিখুঁত অ্যান্ড্রয়েড ব্রাউজার হেডার্স
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # ফেসবুকের মোবাইল সাইট থেকে সরাসরি সোর্স কোড ডাউনলোড করা
        response = session.get(short_url, timeout=15, allow_redirects=True)
        html = response.text
        final_url = response.url

        # যদি নরমাল রিডাইরেক্ট কাজ করে আসল রিল লিংক চলে আসে
        if "reel/" in final_url or "videos/" in final_url:
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            return clean_url

        # 🎯 মেইন ট্রিক: যদি ফেসবুক রিডাইরেক্ট ব্লক করে একই শর্ট লিংক রেখে দেয়, 
        # তবে সোর্স কোডের ভেতর লুকিয়ে থাকা ওরিজিনাল ওজি ইউআরএল (og:url) খুঁজে বের করবে
        og_url_match = re.search(r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']', html)
        if not og_url_match:
            og_url_match = re.search(r'content=["\']([^"\']+)["\']\s+property=["\']og:url["\']', html)
            
        if og_url_match:
            fb_real_url = og_url_match.group(1)
            # ওরিজিনাল ইউআরএল এর ট্র্যাকিং প্যারামিটার বাদ দেওয়া
            clean_url = fb_real_url.split("?")[0].split("&")[0].split("#")[0]
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            return clean_url

        # স্ক্রিপ্ট ট্যাগ বা অন্য কোনো কোড থেকে রিল আইডি খোঁজার শেষ চেষ্টা
        id_match = re.search(r'["\']video_id["\']:\s*["\'](\d+)["\']', html)
        if id_match:
            return f"https://www.facebook.com/reel/{id_match.group(1)}"

        # যদি সব মেথড ফেইল করে, তবে ট্র্যাকিং প্যারামিটার ছাড়া ক্লিন ইউআরএল রিটার্ন করবে
        return final_url.split("?")[0].split("&")[0].split("#")[0]

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

        # ফেসবুক বা টিকটকের শর্ট/শেয়ার লিংক কিংবা ভুল ফরম্যাটের লিংক থাকলে প্রসেস করবে
        if ("facebook.com/share" in current_url or 
            "fb.watch" in current_url or 
            "tiktok.com" in current_url or
            "plugins/video.php" in current_url or
            "video/embed" in current_url):
            
            print(f"Processing → {current_url[:80]}...")
            new_url = get_full_url(current_url)
            
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ Updated to Original: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
