// upload.js - সম্পূর্ণ রেডি কোড
const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co"; 
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";

// সরাসরি সুপাবেস ক্লায়েন্ট ইনিশিয়াল করা হলো যাতে undefined এরর না আসে
const mySupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const form = document.getElementById("uploadForm");
const url = document.getElementById("url");
const platform = document.getElementById("platform");
let currentUserId = null;

// পেজ লোড হলে ইউজার চেক করা
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const { data: { user } } = await mySupabase.auth.getUser();
        if (!user) {
            alert("পোস্ট করতে প্রথমে লগইন করুন!");
            window.location.href = "login.html";
        } else {
            currentUserId = user.id;
        }
    } catch (e) {
        console.error("Auth check failed:", e);
    }
});

// সোশ্যাল মিডিয়া লিংক ডিটেক্টর লজিক (আপনার অরিজিনাল কোডটিই রাখা হয়েছে)
if (url && platform) {
    url.oninput = () => {
        const link = url.value.toLowerCase();

        if (link.includes("youtube") || link.includes("youtu.be"))
            platform.value = "YouTube";
        else if (link.includes("facebook"))
            platform.value = "Facebook";
        else if (link.includes("instagram"))
            platform.value = "Instagram";
        else if (link.includes("tiktok"))
            platform.value = "TikTok";
        else if (link.includes("twitter") || link.includes("x.com"))
            platform.value = "X";
        else if (link.trim() === "")
            platform.value = "";
        else
            platform.value = "Community"; // Unknown এর জায়গায় Community দিলে ফিডের সাথে সুন্দর ম্যাচ করে
    };
}

// ফর্ম সাবমিট হ্যান্ডেলার
if (form) {
    form.onsubmit = async (e) => {
        e.preventDefault();

        if (!currentUserId) {
            alert("Login Required");
            window.location.href = "login.html";
            return;
        }

        const title = document.getElementById("title");
        const description = document.getElementById("description");
        const submitBtn = form.querySelector("button[type='submit']");

        try {
            if (submitBtn) {
                submitBtn.innerText = "Publishing...";
                submitBtn.disabled = true;
            }

            // সুপাবেসের posts টেবিলে ডাটা ইনসার্ট
            const { error } = await mySupabase
                .from("posts")
                .insert({
                    user_id: currentUserId,
                    title: title.value.trim(),
                    description: description.value.trim(),
                    url: url.value.trim() || null,
                    platform: platform.value || "Community"
                });

            if (error) throw error;

            alert("Post Published successfully!");
            window.location.href = "index.html";

        } catch (err) {
            alert("Error: " + err.message);
            console.error(err);
        } finally {
            if (submitBtn) {
                submitBtn.innerText = "Publish Post";
                submitBtn.disabled = false;
            }
        }
    };
}
