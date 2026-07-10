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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,video/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        # ১. শর্ট লিংকের আসল রিডাইরেক্ট লোকেশন বের করা
        response = session.get(short_url, timeout=15, allow_redirects=True)
        final_url = response.url
        html_content = response.text

        check_url = final_url.lower()
        check_short = short_url.lower()

        # ====================== 📸 INSTAGRAM CLEAN LINK ======================
        if "instagram.com" in check_url or "instagram.com" in check_short:
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            return clean_url

        # ====================== 📘 FACEBOOK OEMBED API HACK (১০০% ফুলপ্রুফ) ======================
        if "facebook.com" in check_url or "fb.watch" in check_url or "facebook.com" in check_short:
            
            # ট্রিক: ফেসবুক যদি লগইন পেজে আটকে দেয়, তবে মেটার অফিশিয়াল এপিআই রেসপন্স থেকে ওরিজিনাল ইউআরএল বের করা
            if "/share/" in final_url or "fb.watch" in final_url or "login" in final_url:
                # ফেসবুকের ওরিজিনাল ওএমবেড এন্ডপয়েন্ট যা কোনো ব্লক ছাড়াই ডাটা দেয়
                oembed_url = f"https://www.facebook.com/plugins/video/oembed.json?url={short_url}"
                try:
                    api_res = session.get(oembed_url, timeout=10)
                    if api_res.status_code == 200:
                        api_data = api_res.json()
                        # এপিআই ডাটা থেকে ওরিজিনাল রিল/ভিডিও ইউআরএল নেওয়া
                        author_url = api_data.get("author_url", "")
                        html_box = api_data.get("html", "")
                        
                        # এইচটিএমএল ব্লকের ভেতর থেকে ওরিজিনাল রিল আইডি লিংক টেনে বের করা
                        href_match = re.search(r'href=["\'](https://www\.facebook\.com/[^"\']+)["\']', html_box)
                        if href_match:
                            final_url = href_match.group(1)
                except Exception as api_err:
                    print(f"oEmbed API Error, falling back to regex: {api_err}")

            # যদি এপিআই ফেইল করে, তবে সেকেন্ডারি ব্যাকআপ হিসেবে মেটা ট্যাগ চেক
            if "/share/" in final_url or "fb.watch" in final_url or "login" in final_url:
                meta_match = re.search(r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']', html_content)
                if meta_match:
                    final_url = meta_match.group(1)

            # পেছনের ট্র্যাকিং জাবিজাবি সব সাফ
            clean_url = final_url.split("?")[0].split("&")[0].split("#")[0]
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
                
            return clean_url

        # ====================== 🎵 TIKTOK ======================
        if "tiktok.com" in check_url or "tiktok.com" in check_short:
            return final_url.split("?")[0].split("&")[0]

        return final_url.split("?")[0]

    except Exception as e:
        print(f"Error processing {short_url}: {e}")
        return short_url


def process_posts():
    print("🚀 Starting URL Processor with oEmbed Fix...")
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
            
            print(f"Processing → {current_url[:80]}...")
            new_url = get_full_url(current_url)
            
            if new_url != current_url:
                supabase.table("posts").update({"url": new_url}).eq("id", post["id"]).execute()
                print(f"✅ Updated to Clean URL: {new_url}")
                updated += 1

    print(f"\n🎉 Finished! {updated} posts updated.")

if __name__ == "__main__":
    process_posts()
