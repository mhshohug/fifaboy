import os
import requests
import re
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
        # ১. শর্ট লিংক রিডাইরেক্ট করে মেইন বড় লিংক বের করা
        session = requests.Session()
        response = session.get(short_url, headers=headers, allow_redirects=True, timeout=15)
        final_url = response.url
        
        # ২. এটি যদি ফেসবুকের লিংক হয়, তবে ওরিজিনাল এমবেড ইউআরএল তৈরি করা
        if "facebook.com" in final_url or "fb.watch" in final_url:
            clean_fb = final_url.split("?")[0]
            # ফেসবুকের অফিশিয়াল প্লেয়ার লিংক ফরম্যাট যা আইফ্রেম ব্লক করতে পারে না
            embed_url = f"https://www.facebook.com/plugins/video.php?href={clean_fb}&show_text=false"
            return embed_url
            
        # ৩. টিকটকের ক্ষেত্রে ট্র্যাকিং আইডি বাদ দিয়ে ক্লিন লিংক দেওয়া
        if "tiktok.com" in final_url:
            return final_url.split("?")[0]
            
        return final_url
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
            
        # ফেসবুক ও টিকটকের যেকোনো শেয়ার বা শর্ট লিংক পেলেই পাইথন কাজ শুরু করবে
        if "vt.tiktok.com" in current_url or "vm.tiktok.com" in current_url or "fb.watch" in current_url or "facebook.com/share" in current_url or ("facebook.com" in current_url and "plugins/video.php" not in current_url):
            print(f"Processing link: {current_url}")
            full_url = get_full_url(current_url)
            
            if full_url != current_url:
                supabase.table("posts").update({"url": full_url}).eq("id", post["id"]).execute()
                print(f"Successfully converted and updated to: {full_url}")

if __name__ == "__main__":
    process_posts()
