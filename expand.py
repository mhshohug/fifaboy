import os
import requests
from supabase import create_client

# সুপাবেস কানেকশন
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_ANON_KEY")
)

def get_final_facebook_url(short_url):
    """ফেসবুক শেয়ার লিংক রিডাইরেক্ট করে আসল রিল লিংক বের করবে"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # ফেসবুকের শেয়ার লিংক ফলো করা
        response = requests.head(short_url, headers=headers, allow_redirects=True, timeout=10)
        final_url = response.url
        
        # ট্র্যাকিং প্যারামিটার (?mibextid=...) কেটে ফেলা
        clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
        
        # যদি লিংকে 'reels' থাকে, তবে সেটাকে 'reel' করে ফেলা (ইউনিফাইড ফরম্যাটের জন্য)
        clean_url = clean_url.replace("/reels/", "/reel/")
        
        return clean_url
    except:
        return short_url

def fix_database():
    print("🚀 ডাটাবেজ ফিক্সিং শুরু হচ্ছে...")
    # সব পোস্ট আনা
    response = supabase.table("posts").select("*").execute()
    posts = response.data or []
    
    updated_count = 0
    for post in posts:
        url = post.get("url", "")
        # শুধুমাত্র ফেসবুক লিংক চেক করা
        if url and "facebook.com" in url and "share/r" in url:
            print(f"ফিক্স করছি: {url}")
            new_url = get_final_facebook_url(url)
            
            if new_url != url:
                # ডাটাবেজ আপডেট করা
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ আপডেট হয়েছে: {new_url}")
                updated_count += 1
    
    print(f"🎉 কাজ শেষ! মোট {updated_count} টি পোস্ট আপডেট হয়েছে।")

if __name__ == "__main__":
    fix_database()
