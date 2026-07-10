import os
import requests
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # ১. শর্ট বা শেয়ার লিংকটিকে আসল বড় লিংকে রূপান্তর করা
        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url

        # ====================== FACEBOOK ======================
        if "facebook.com" in final_url or "fb.watch" in final_url:
            # লিংকের পেছনের সব ট্র্যাকিং (?rdid=..., ?share_url=...) এক কোপে কেটে বাদ দেওয়া
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            
            # ট্রেইলিং স্ল্যাশ থাকলে তা বাদ দিয়ে একদম ক্লিন ওরিজিনাল লিংক রাখা
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
                
            return clean_url

        # ====================== TIKTOK ======================
        if "tiktok.com" in final_url:
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

        # ফেসবুক বা টিকটকের শর্ট/শেয়ার বা আগের ভুল এমবেড/প্লাগইন লিংক থাকলে তা প্রসেস করবে
        if ("facebook.com" in current_url or 
            "fb.watch" in current_url or 
            "tiktok.com" in current_url or
            "plugins/video.php" in current_url or
            "video/embed" in current_url):
            
            print(f"Processing → {current_url[:80]}...")
            new_url = get_full_url(current_url)
            
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ Updated: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
