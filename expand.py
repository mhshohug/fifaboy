import os
import requests
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def get_full_url(short_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        session = requests.Session()
        response = session.get(short_url, headers=headers, allow_redirects=True, timeout=15)
        final_url = response.url
        
        # ফেসবুক বা টিকটক—দুটোর ক্ষেত্রেই শুধু ট্র্যাকিং আইডি (?সহ পরের অংশ) বাদ দিয়ে 
        # একদম ফ্রেশ ওরিজিনাল ফুল লিংকটা রিটার্ন করবে। কোনো প্লাগইন ঝামেলা নেই!
        return final_url.split("?")[0]
    except Exception as e:
        print(f"Error expanding URL: {e}")
        return short_url

def process_posts():
    response = supabase.table("posts").select("*").execute()
    posts = response.data
    
    for post in posts:
        current_url = post.get("url", "")
        if not current_url:
            continue
            
        # শুধুমাত্র শর্ট বা শেয়ার লিংক পেলেই পাইথন প্রসেস করবে
        if "vt.tiktok.com" in current_url or "vm.tiktok.com" in current_url or "fb.watch" in current_url or "facebook.com/share" in current_url:
            print(f"Processing link: {current_url}")
            full_url = get_full_url(current_url)
            
            if full_url != current_url:
                supabase.table("posts").update({"url": full_url}).eq("id", post["id"]).execute()
                print(f"Successfully updated to full link: {full_url}")

if __name__ == "__main__":
    process_posts()
