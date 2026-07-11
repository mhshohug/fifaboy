import os
import time
import requests
from supabase import create_client
from urllib.parse import urlparse, parse_qs

# সুপাবেস কানেকশন
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_ANON_KEY")
)

def get_final_facebook_url(short_url, retries=3):
    """
    ফেসবুক শেয়ার লিংক রিডাইরেক্ট করে আসল রিল লিংক বের করবে
    
    Args:
        short_url: ফেসবুকের শেয়ার লিংক
        retries: পুনরায় চেষ্টার সংখ্যা
    
    Returns:
        পরিষ্কার করা লিংক
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for attempt in range(retries):
        try:
            # GET রিকোয়েস্ট (HEAD এর পরিবর্তে, কারণ কিছু সাইট HEAD সাপোর্ট করে না)
            response = requests.get(
                short_url, 
                headers=headers, 
                allow_redirects=True, 
                timeout=15,
                stream=True
            )
            
            final_url = response.url
            
            # ট্র্যাকিং প্যারামিটার কেটে ফেলা
            parsed = urlparse(final_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # ফেসবুকের রিল ইউআরএল ফরম্যাট ঠিক করা
            clean_url = clean_url.replace("/reels/", "/reel/")
            clean_url = clean_url.replace("/videos/", "/reel/")  # ভিডিওকেও রিলে কনভার্ট
            
            # শেষে স্ল্যাশ থাকলে রিমুভ করা
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            
            return clean_url
            
        except requests.exceptions.Timeout:
            print(f"⏱️ টাইমআউট, আবার চেষ্টা করছি... (Attempt {attempt + 1}/{retries})")
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ রিকোয়েস্ট এরর: {e}")
            if attempt == retries - 1:
                return short_url
            time.sleep(3)
            
        except Exception as e:
            print(f"⚠️ অন্যান্য এরর: {e}")
            return short_url
    
    return short_url

def is_valid_facebook_url(url):
    """চেক করে লিংকটি ভ্যালিড ফেসবুক ইউআরএল কিনা"""
    if not url:
        return False
    
    # শুধুমাত্র শেয়ার লিংক চেক করা
    valid_patterns = [
        "facebook.com/share/r/",
        "facebook.com/reel/",
        "facebook.com/reels/",
        "fb.com/share/r/",
        "fb.com/reel/"
    ]
    
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in valid_patterns)

def fix_database(batch_size=50, limit=None):
    """
    ডাটাবেজের ফেসবুক লিংক ফিক্স করা
    
    Args:
        batch_size: কতটি পোস্ট একসাথে প্রসেস করবে
        limit: সর্বোচ্চ কতটি পোস্ট প্রসেস করবে (None = সব)
    """
    print("🚀 ডাটাবেজ ফিক্সিং শুরু হচ্ছে...")
    
    # কুয়েরি বিল্ড করা
    query = supabase.table("posts").select("*")
    
    # শুধুমাত্র ফেসবুক লিংক যুক্ত পোস্ট নেওয়া (পার্টিশন ফিল্টার)
    # নোট: সুপাবেসে লাইক কোয়েরি সীমিত, তাই আমরা সব নিয়ে ফিল্টার করব
    # অথবা আপনি আলাদা করে is_facebook কলাম যোগ করতে পারেন
    
    response = query.execute()
    all_posts = response.data or []
    
    # ফেসবুক পোস্ট ফিল্টার করা
    posts_to_fix = [
        post for post in all_posts 
        if is_valid_facebook_url(post.get("url", ""))
    ]
    
    total_posts = len(posts_to_fix)
    
    if total_posts == 0:
        print("📭 ফেসবুক শেয়ার লিংক পাওয়া যায়নি!")
        return
    
    print(f"📊 মোট {total_posts} টি ফেসবুক পোস্ট পাওয়া গেছে")
    
    # লিমিট প্রয়োগ
    if limit:
        posts_to_fix = posts_to_fix[:limit]
        total_posts = len(posts_to_fix)
        print(f"🔢 {total_posts} টি পোস্ট প্রসেস করা হবে (লিমিট: {limit})")
    
    updated_count = 0
    error_count = 0
    
    # ব্যাচ আকারে প্রসেস করা
    for i in range(0, total_posts, batch_size):
        batch = posts_to_fix[i:i+batch_size]
        
        print(f"\n📦 ব্যাচ {i//batch_size + 1}: {len(batch)} টি পোস্ট প্রসেস করা হচ্ছে...")
        
        for idx, post in enumerate(batch, 1):
            url = post.get("url", "")
            post_id = post.get("id")
            
            print(f"\n🔄 [{i+idx}/{total_posts}] ফিক্স করছি: {url[:80]}...")
            
            try:
                new_url = get_final_facebook_url(url)
                
                if new_url and new_url != url:
                    # ডাটাবেজ আপডেট করা
                    update_response = supabase.table("posts").update({
                        "url": new_url,
                        "updated_at": "now()"  # যদি updated_at কলাম থাকে
                    }).eq("id", post_id).execute()
                    
                    if update_response.data:
                        print(f"✅ আপডেট হয়েছে: {new_url[:80]}...")
                        updated_count += 1
                    else:
                        print(f"❌ আপডেট ব্যর্থ হয়েছে")
                        error_count += 1
                else:
                    print(f"⏭️ স্কিপ: ইউআরএল একই বা খালি")
                    
            except Exception as e:
                print(f"❌ পোস্ট ID {post_id} আপডেটে এরর: {e}")
                error_count += 1
            
            # রেট লিমিট এড়ানোর জন্য স্লিপ
            if idx % 5 == 0:
                time.sleep(1)
        
        # ব্যাচ শেষে বিরতি
        time.sleep(2)
    
    print("\n" + "="*50)
    print(f"🎉 কাজ শেষ!")
    print(f"✅ সফল: {updated_count} টি")
    print(f"❌ ব্যর্থ: {error_count} টি")
    print(f"📊 মোট: {total_posts} টি")
    print("="*50)

def add_facebook_flag_column():
    """ফেসবুক পোস্ট শনাক্ত করার জন্য আলাদা কলাম যোগ করা"""
    try:
        # সুপাবেসে ALTER TABLE কাজ করে না, তাই আলাদা টেবিল বা অ্যাপ্রোচ নিতে হবে
        # অথবা প্রোগ্রাম্যাটিকভাবে ফিল্ড যোগ করা
        print("💡 সুপাবেসে ALTER TABLE সাপোর্টেড নয়।")
        print("   আপনি supabase dashboard থেকে manually কলাম যোগ করতে পারেন:")
        print("   - is_facebook (boolean, default: false)")
        print("   - original_url (text)")
        print("   - last_checked (timestamp)")
    except Exception as e:
        print(f"⚠️ কলাম যোগ করতে ব্যর্থ: {e}")

if __name__ == "__main__":
    print("ফেসবুক ইউআরএল ফিক্সার টুল")
    print("-" * 30)
    
    # কমান্ড লাইন আর্গুমেন্ট পার্সিং (সহজ ভার্সন)
    import sys
    
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"🔢 লিমিট: {limit} টি পোস্ট")
        except ValueError:
            print("⚠️ ভুল ইনপুট! পুরো ডাটাবেজ প্রসেস করা হবে")
    
    # ব্যাকআপ তৈরি করুন (ঐচ্ছিক)
    print("💡 প্রথমে ডাটাবেজ ব্যাকআপ নিন!")
    confirm = input("চালিয়ে যেতে চান? (y/N): ").strip().lower()
    
    if confirm == 'y':
        fix_database(limit=limit)
    else:
        print("❌ বাতিল করা হয়েছে")
