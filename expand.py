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
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url
        html = response.text

        check_url = final_url.lower()
        check_short = short_url.lower()

        # ====================== 📸 INSTAGRAM DIRECT FIXED ======================
        if "instagram.com" in check_url or "instagram.com" in check_short:
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            
            # ইনস্টাগ্রামের আসল রিল/পোস্ট আইডি টেনে বের করা
            # যেমন: /reel/DaFmuqwOnZ3 থেকে 'DaFmuqwOnZ3' নিবে
            parts = clean_url.split('/')
            video_id = ""
            for i, part in enumerate(parts):
                if part in ["reel", "p", "tv"] and i + 1 < len(parts):
                    video_id = parts[i+1]
                    break
            
            if video_id:
                # 🎯 ম্যাজিক লিংক: এই স্পেশাল লিংকটা কোনো স্ক্রিপ্ট বা বাটন ছাড়াই সরাসরি আইফ্রেমে ভিডিও দেখায়!
                return f"https://www.instagram.com/p/{video_id}/embed/captioned/"
            
            return f"{clean_url}/embed/"

        # ====================== 📘 FACEBOOK ======================
        if "facebook.com" in check_url or "fb.watch" in check_url or "facebook.com" in check_short:
            if "reel/" in final_url or "videos/" in final_url:
                clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                return clean_url

            og_url_match = re.search(r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']', html)
            if og_url_match:
                fb_real_url = og_url_match.group(1)
                clean_url = fb_real_url.split("?")[0].split("&")[0].split("#")[0]
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                return clean_url

            return final_url.split("?")[0].split("&")[0].split("#")[0]

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
            
            # যদি ডেটাবেজের লিংক আর নতুন জেনারেট হওয়া লিংক আলাদা হয়, তবেই আপডেট করবে
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ Updated: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
