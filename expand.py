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

    # ফেসবুক ও মেটার কড়া সিকিউরিটি লক বাইপাস করার আসল রিয়েল ব্রাউজার হেডারস
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,video/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # রিডাইরেক্ট ফলো করে মেইন ইউআরএল ও এইচটিএমএল ডাটা একসাথে হিট করা
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

        # ====================== 📘 FACEBOOK (১০০% ফুলপ্রুফ ব্যাকআপ মেথড) ======================
        if "facebook.com" in check_url or "fb.watch" in check_url or "facebook.com" in check_short:
            
            # ব্যাকআপ ট্রিক: যদি রিডাইরেক্ট ফেইল করে আবার শর্ট লিংক ফেরত আসে (/share/ ফরম্যাটে)
            if "/share/" in final_url or "fb.watch" in final_url:
                # মেটার এইচটিএমএল মেটা ট্যাগ থেকে আসল রিল ইউআরএল টেনে বের করার জন্য কড়া রেগুলার এক্সপ্রেশন
                meta_match = re.search(r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']', html_content)
                if meta_match:
                    final_url = meta_match.group(1)

            # এবার পেছনের সব জাবিজাবি ট্র্যাকিং এক কোপে সাফ
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

        if ("instagram.com" in current_url or 
            "facebook.com" in current_url or 
            "fb.watch" in current_url or 
            "tiktok.com" in current_url or
            "ig.me" in current_url):
            
            print(f"Processing → {current_url[:80]}...")
            new_url = get_full_url(current_url)
            
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ Updated to Clean URL: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
