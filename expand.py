import os
import requests
import re
from urllib.parse import unquote, quote
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def get_full_url(short_url):
    # ফেসবুকের সিকিউরিটি বোকা বানানোর জন্য একদম আসল ব্রাউজারের ফুল হেডার্স
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document'
    }
    try:
        # যদি অলরেডি ভুল প্লাগইন লিংক ডেটাবেজে থাকে, তবে ওটার ভেতর থেকে আসল শর্ট লিংকটা টেনে বের করবে
        if "plugins/video.php" in short_url and "href=" in short_url:
            match_href = re.search(r'href=([^&]+)', short_url)
            if match_href:
                short_url = unquote(match_href.group(1))

        # ফেসবুকের রিডাইরেক্ট লক ভাঙার জন্য সেশন ট্র্যাকিং
        session = requests.Session()
        session.headers.update(headers)
        
        # প্রথমে ফেসবুকের মেইন ডোমেইনে একটা ফেক ভিজিট দেওয়া যাতে কুকি সেট হয়
        try:
            session.get("https://www.facebook.com", timeout=10)
        except:
            pass
            
        # এবার আসল শর্ট লিংকটাকে রিডাইরেক্ট করার জন্য রিকোয়েস্ট পাঠানো
        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url
        
        # যদি এখনো শর্ট লিংকই থেকে যায় (ফেসবুক ব্লক করলে), তবে রেগুলার এক্সপ্রেশন দিয়ে রেসপন্স টেক্সট থেকে আইডি খোঁজা
        if "share/r/" in final_url or "fb.watch" in final_url:
            # ফেসবুকের পেজের ভেতরে কোথাও না কোথাও আসল ওরিজিনাল ইউআরএল বা আইডি গোপন থাকে, সেটা খোঁজা
            id_match = re.search(r'"video_id":"(\d+)"', response.text)
            if id_match:
                return f"https://www.facebook.com/video/embed?video_id={id_match.group(1)}"
            
            url_match = re.search(r'meta property="og:url" content="([^"]+)"', response.text)
            if url_match:
                final_url = url_match.group(1)

        # 📘 ফেসবুকের ফাইনাল প্রসেসিং
        if "facebook.com" in final_url or "fb.watch" in final_url:
            clean_fb = final_url.split("?")[0]
            
            # ওরিজিনাল আইডি খোঁজা
            video_id_match = re.search(r'(?:videos|watch|reels|posts|story)/(?:[a-zA-Z0-9_\-\.]+)/?(\d+)', final_url)
            if not video_id_match:
                video_id_match = re.search(r'v=(\d+)', final_url)
            if not video_id_match:
                video_id_match = re.search(r'/(\d+)/?$', clean_fb)
                
            if video_id_match:
                fb_id = video_id_match.group(1)
                return f"https://www.facebook.com/video/embed?video_id={fb_id}"
            
            # সব ফেইল করলে ক্লিন ওরিজিনাল ইউআরএলটাই সেভ করবে, কোনো প্লাগইন জোড়াতালি দেবে না
            return clean_fb
            
        # 🎵 টিকটকের জন্য আগের সলিড লজিক
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
            
        # ফেসবুকের ভুল প্লাগইন লিংক বা শর্ট লিংক পেলেই পাইথন ওটা টেনে সোজা করবে
        if "vt.tiktok.com" in current_url or "vm.tiktok.com" in current_url or "fb.watch" in current_url or "facebook.com/share" in current_url or "plugins/video.php" in current_url or ("facebook.com" in current_url and "video/embed" not in current_url):
            print(f"Processing: {current_url}")
            full_url = get_full_url(current_url)
            
            if full_url != current_url:
                supabase.table("posts").update({"url": full_url}).eq("id", post["id"]).execute()
                print(f"Updated to: {full_url}")

if __name__ == "__main__":
    process_posts()
