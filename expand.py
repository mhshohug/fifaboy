import os
import requests
from supabase import create_client, Client

# গিউহাব সিক্রেটস থেকে ক্রেডেনশিয়াল নেওয়া
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def get_full_url(short_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Honor X9b) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    }
    try:
        response = requests.head(short_url, allow_redirects=True, headers=headers, timeout=10)
        return response.url.split("?")[0]
    except:
        return short_url

def process_posts():
    # ডাটাবেজ থেকে সব পোস্ট আনা
    response = supabase.table("posts").select("*").execute()
    posts = response.data
    
    for post in posts:
        current_url = post.get("url", "")
        if not current_url:
            continue
            
        # যদি লিংকটি ফেসবুক বা টিকটকের শর্ট লিংক হয়
        if "vt.tiktok.com" in current_url or "vm.tiktok.com" in current_url or "fb.watch" in current_url or "facebook.com/share" in current_url:
            print(f"Processing short link: {current_url}")
            full_url = get_full_url(current_url)
            
            # ডাটাবেজে ফুল ইউআরএল দিয়ে আপডেট করা
            supabase.table("posts").update({"url": full_url}).eq("id", post["id"]).execute()
            print(f"Updated to full link: {full_url}")

if __name__ == "__main__":
    process_posts()
