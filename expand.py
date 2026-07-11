import os
import requests
import re
from supabase import create_client

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
    }

    try:
        check_url = short_url.lower()

        # =====================================================================
        # 📸 INSTAGRAM (সম্পূর্ণ টাচফ্রি ও নিরাপদ - আগের সচল কোড)
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
        # 🎵 TIKTOK (সম্পূর্ণ টাচফ্রি ও নিরাপদ - আগের সচল কোড)
        # =====================================================================
        if "tiktok.com" in check_url:
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(short_url, timeout=12, allow_redirects=True)
            return response.url.split("?")[0].split("&")[0]

        # =====================================================================
        # 📘 FACEBOOK FIXED ONLY (আপনার চাওয়া নিখুঁত রিল আইডি এক্সট্র্যাক্টর)
        # =====================================================================
        if "facebook.com" in check_url or "fb.watch" in check_url:
            
            # ১. ওএমবেড এপিআই গেটওয়ে হিট (যা ব্লক ছাড়াই শেয়ার লিংকের আসল পেজ সোর্স দেয়)
            oembed_endpoint = f"https://www.facebook.com/plugins/video/oembed.json?url={short_url}"
            try:
                api_res = requests.get(oembed_endpoint, headers=headers, timeout=10)
                if api_res.status_code == 200:
                    html_box = api_res.json().get("html", "")
                    
                    # একদম নিখুঁত আইডি ফিল্টার (যেমন: 1278160674259398)
                    id_match = re.search(r'(?:reel|reels|video|v|id=)(?:/|=)?([0-9]{12,20})', html_box)
                    if id_match:
                        return f"https://www.facebook.com/reel/{id_match.group(1)}"
            except Exception as e:
                print(f"Facebook API Gateway failed: {e}")

            # ২. ব্যাকআপ ফলব্যাক: যদি সরাসরি ইউআরএল এর ভেতরেই আইডি থেকে থাকে
            id_match_direct = re.search(r'(?:reel|reels|video|v)/([0-9]{12,20})', short_url)
            if id_match_direct:
                return f"https://www.facebook.com/reel/{id_match_direct.group(1)}"

            return short_url

        return short_url.split("?")[0]

    except Exception as e:
        print(f"Error processing {short_url}: {e}")
        return short_url

def process_posts():
    print("🚀 ডাটাবেজে আপনার দেওয়া উদাহরণ অনুযায়ী ফেসবুক রিল ফিক্সার চালু হচ্ছে...")
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
            
            new_url = get_full_url(current_url)
            
            # যদি নতুন ইউআরএল তৈরি হয়, তবেই ডাটাবেজে পুশ হবে
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ ডাটাবেজ সফলভাবে আপডেট: {current_url} → {new_url}")
                updated += 1

    print(f"\n🎉 কাজ শেষ! মোট {updated} টি ফেসবুক লিংক ফিক্স করা হয়েছে।")

if __name__ == "__main__":
    process_posts()
