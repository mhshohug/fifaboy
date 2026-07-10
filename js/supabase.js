// =========================
// SUPABASE CONFIG
// =========================

const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

console.log('✅ Supabase connected');

// =========================
// SIGN UP
// =========================

// =========================
// AUTH FUNCTIONS  ← এই সেকশন খুঁজো
// =========================

// 📝 Sign Up (register)  ← এই ফাংশনটা রিপ্লেস করো
async function signUp(email, password, username) {
    console.log('➡️ Function called');
    
    try {
        console.log('1️⃣ SignUp started for:', email);
        
        const response = await supabase.auth.signUp({
            email: email,
            password: password,
            options: {
                data: { username: username }
            }
        });

        console.log('2️⃣ Full response:', JSON.stringify(response));

        if (response.error) {
            console.error('❌ Error:', response.error);
            alert('❌ ' + response.error.message);
            return false;
        }

        if (response.data && response.data.user) {
            console.log('3️⃣ User ID:', response.data.user.id);
            
            const profileResult = await supabase
                .from('profiles')
                .upsert({
                    id: response.data.user.id,
                    username: username,
                    role: 'user'
                });
            
            console.log('4️⃣ Profile result:', profileResult);
            
            if (profileResult.error) {
                console.error('❌ Profile error:', profileResult.error);
                alert('⚠️ ' + profileResult.error.message);
                return false;
            }
            
            alert('✅ Account created!');
            window.location.href = 'login.html';
            return true;
        }
        
        console.log('⚠️ No user in response');
        return false;

    } catch (error) {
        console.error('❌ Catch error:', error);
        alert('💥 ' + error.message);
        return false;
    }
}

// =========================
// SIGN OUT
// =========================

async function signOut() {
    await supabase.auth.signOut();
    window.location.href = 'login.html';
}

// =========================
// GET USER
// =========================

async function getUser() {
    const { data } = await supabase.auth.getUser();
    return data.user;
}

// =========================
// SOCIAL LOGIN
// =========================

async function googleLogin() {
    await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: window.location.origin + '/index.html' }
    });
}

async function facebookLogin() {
    await supabase.auth.signInWithOAuth({
        provider: "facebook",
        options: { redirectTo: window.location.origin + '/index.html' }
    });
}

// =========================
// POSTS
// =========================

async function getPosts() {
    const { data, error } = await supabase
        .from("posts")
        .select("*")
        .order("created_at", { ascending: false });
    
    if (error) {
        console.error(error);
        return [];
    }
    return data;
}

async function createPost(title, description, url, platform) {
    const user = await getUser();
    if (!user) {
        alert("Login Required");
        return false;
    }

    const { error } = await supabase
        .from("posts")
        .insert({
            user_id: user.id,
            title,
            description,
            url,
            platform
        });

    if (error) {
        alert(error.message);
        return false;
    }
    return true;
}

async function deletePost(id) {
    const { error } = await supabase
        .from("posts")
        .delete()
        .eq("id", id);

    if (error) {
        alert(error.message);
        return false;
    }
    return true;
}

// =========================
// COMMENTS
// =========================

async function getComments(postId) {
    const { data, error } = await supabase
        .from("comments")
        .select("*, profiles(username, avatar)")
        .eq("post_id", postId)
        .order("created_at", { ascending: true });

    if (error) {
        console.error(error);
        return [];
    }
    return data;
}

async function addComment(postId, comment) {
    const user = await getUser();
    if (!user) {
        alert("Login Required");
        return false;
    }

    const { error } = await supabase
        .from("comments")
        .insert({
            post_id: postId,
            user_id: user.id,
            comment
        });

    if (error) {
        alert(error.message);
        return false;
    }
    return true;
}

async function deleteComment(id) {
    const { error } = await supabase
        .from("comments")
        .delete()
        .eq("id", id);

    if (error) {
        alert(error.message);
        return false;
    }
    return true;
}

// =========================
// VOTES
// =========================

async function votePost(postId, vote) {
    const user = await getUser();
    if (!user) {
        alert("Login Required");
        return false;
    }

    const { data } = await supabase
        .from("votes")
        .select("*")
        .eq("post_id", postId)
        .eq("user_id", user.id)
        .maybeSingle();

    if (data) {
        await supabase
            .from("votes")
            .update({ vote })
            .eq("id", data.id);
    } else {
        await supabase
            .from("votes")
            .insert({
                post_id: postId,
                user_id: user.id,
                vote
            });
    }
    return true;
}

// =========================
// REPORT
// =========================

async function reportPost(postId, reason) {
    const user = await getUser();
    if (!user) {
        alert("Login Required");
        return false;
    }

    const { error } = await supabase
        .from("reports")
        .insert({
            post_id: postId,
            user_id: user.id,
            reason
        });

    if (error) {
        alert(error.message);
        return false;
    }
    return true;
}

// =========================
// PLATFORM DETECT
// =========================

function detectPlatform(link) {
    link = link.toLowerCase();
    if (link.includes("youtube.com") || link.includes("youtu.be")) return "YouTube";
    if (link.includes("facebook.com")) return "Facebook";
    if (link.includes("instagram.com")) return "Instagram";
    if (link.includes("tiktok.com")) return "TikTok";
    if (link.includes("twitter.com") || link.includes("x.com")) return "X";
    return "Unknown";
}

// =========================
// IS ADMIN
// =========================

async function isAdmin() {
    const user = await getUser();
    if (!user) return false;

    const { data } = await supabase
        .from("profiles")
        .select("role")
        .eq("id", user.id)
        .single();

    return data?.role === "admin";
}

// =========================
// EXPOSE TO HTML
// =========================

window.signUp = signUp;
window.signIn = signIn;
window.signOut = signOut;
window.googleLogin = googleLogin;
window.facebookLogin = facebookLogin;
window.getUser = getUser;
window.isAdmin = isAdmin;
window.getPosts = getPosts;
window.createPost = createPost;
window.deletePost = deletePost;
window.getComments = getComments;
window.addComment = addComment;
window.deleteComment = deleteComment;
window.votePost = votePost;
window.reportPost = reportPost;
window.detectPlatform = detectPlatform;
window.supabase = supabase;

console.log('✅ All functions loaded!');
