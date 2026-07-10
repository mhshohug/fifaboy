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

    # ফেসবুকের কড়া স্ক্র্যাপিং ব্লকিং এড়াতে একটি স্ট্যান্ডার্ড ডেস্কটপ ব্রাউজার হেডার
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # allow_redirects=True রাখার ফলে /share/ লিংকটি রিডাইরেক্ট হয়ে আসল লিংকে চলে যাবে
        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url

        check_url = final_url.lower()
        check_short = short_url.lower()

        # ====================== 📸 INSTAGRAM CLEAN LINK ======================
        if "instagram.com" in check_url or "instagram.com" in check_short:
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            return clean_url

        # ====================== 📘 FACEBOOK (১০০% ফিক্সড মেথড) ======================
        if "facebook.com" in check_url or "fb.watch" in check_url or "facebook.com" in check_short:
            # 🎯 জ্যাম কাটানোর ট্রিক: রিডাইরেক্ট হওয়া ফাইনাল ইউআরএল থেকে সরাসরি সব ট্র্যাকিং (?share, ?mibextid, ?igsh) কেটে ফেলা
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            
            # ট্র্যাকিং কাটার পর শেষে স্ল্যাশ থাকলে ওটা প্রমিত করার জন্য কেটে দেওয়া
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
