import os
import requests
import re
from urllib.parse import quote
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def get_full_url(short_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        session = requests.Session()
        response = session.get(short_url, headers=headers, allow_redirects=True, timeout=15)
        final_url = response.url
        
        # ----------------------------------------------------------------
        # 📘 ফেসবুকের জন্য সম্পূর্ণ আলাদা পাইথন লজিক (বাটন ছাড়া সরাসরি সাইটে দেখানোর জন্য)
        # ----------------------------------------------------------------
        if "facebook.com" in final_url or "fb.watch" in final_url:
            clean_fb = final_url.split("?")[0]
            
            # ফেসবুকের রিল বা ভিডিও থেকে আইডি খোঁজার চেষ্টা
            video_id_match = re.search(r'(?:videos|watch|reels|posts|story)/(?:[a-zA-Z0-9_\-\.]+)/?(\d+)', final_url)
            if not video_id_match:
                video_id_match = re.search(r'v=(\d+)', final_url)
            if not video_id_match:
                video_id_match = re.search(r'/(\d+)/?$', clean_fb)
                
            if video_id_match:
                fb_id = video_id_match.group(1)
                # ফেসবুকের আসল এমবেড লিংক যা আপনার ইনডেক্সের আইফ্রেম সরাসরি রিড করতে পারবে
                return f"https://www.facebook.com/video/embed?video_id={fb_id}"
            
            # আইডি না পাওয়া গেলে নরমাল লিংকটাকে এনকোড করে প্লাগইন ফরম্যাট বানাবে
            encoded_url = quote(clean_fb, safe='')
            return f"https://www.facebook.com/plugins/video.php?href={encoded_url}&show_text=false"
            
        # ----------------------------------------------------------------
        # 🎵 টিকটকের জন্য আগের চেনা লজিক (একদম অক্ষত)
        # ----------------------------------------------------------------
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
            
        # শুধুমাত্র শর্ট বা শেয়ার লিংক পেলেই পাইথন প্রসেস করবে
        if "vt.tiktok.com" in current_url or "vm.tiktok.com" in current_url or "fb.watch" in current_url or "facebook.com/share" in current_url or ("facebook.com" in current_url and "video/embed" not in current_url and "plugins/video.php" not in current_url):
            print(f"Processing: {current_url}")
            full_url = get_full_url(current_url)
            
            if full_url != current_url:
                supabase.table("posts").update({"url": full_url}).eq("id", post["id"]).execute()
                print(f"Updated successfully: {full_url}")

if __name__ == "__main__":
    process_posts()
