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
        session = requests.Session()
        response = session.get(short_url, headers=headers, allow_redirects=True, timeout=15)
        final_url = response.url
        
        # যদি ফেসবুকের লিংক হয়, তবে ওটার ভিডিও আইডি দিয়ে অফিশিয়াল এমবেড স্ট্রাকচার তৈরি করা
        if "facebook.com" in final_url or "fb.watch" in final_url:
            clean_fb = final_url.split("?")[0]
            
            # লিংক থেকে আইডি খোঁজার চেষ্টা (/videos/ID/ বা /watch/?v=ID বা /reels/ID/)
            video_id_match = re.search(r'(?:videos|videos/\d+|watch/\?v=|watch|reels|posts|story)/(?:[a-zA-Z0-9_\-\.]+)/?(\d+)', final_url)
            if not video_id_match:
                video_id_match = re.search(r'v=(\d+)', final_url)
            if not video_id_match:
                video_id_match = re.search(r'/(\d+)(?:/|$)', clean_fb)
                
            if video_id_match:
                fb_id = video_id_match.group(1)
                # এই নির্দিষ্ট ফরম্যাট ফেসবুক আইফ্রেম পলিসি কখনোই ব্লক করতে পারে না ভাই!
                return f"https://www.facebook.com/video/embed?video_id={fb_id}"
            
            return f"https://www.facebook.com/plugins/video.php?href={encodeURIComponent(clean_fb)}&show_text=false"
            
        # টিকটকের ক্ষেত্রে শুধু ট্র্যাকিং প্যারামিটার বাদ দিয়ে ক্লিন ফুল লিংক দেওয়া
        if "tiktok.com" in final_url:
            return final_url.split("?")[0]
            
        return final_url
    except Exception as e:
        print(f"Error expanding URL: {e}")
        return short_url

if __name__ == "__main__":
    response = supabase.table("posts").select("*").execute()
    posts = response.data
    
    for post in posts:
        current_url = post.get("url", "")
        if not current_url:
            continue
            
        if "vt.tiktok.com" in current_url or "vm.tiktok.com" in current_url or "fb.watch" in current_url or "facebook.com/share" in current_url or ("facebook.com" in current_url and "video/embed" not in current_url):
            print(f"Processing link: {current_url}")
            full_url = get_full_url(current_url)
            
            if full_url != current_url:
                supabase.table("posts").update({"url": full_url}).eq("id", post["id"]).execute()
                print(f"Successfully converted and updated to: {full_url}")
