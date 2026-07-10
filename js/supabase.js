// =========================
// supabase.js - Supabase Client Configuration
// =========================

// ✅ আপনার সঠিক API Key
const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";

// Supabase ক্লায়েন্ট তৈরি করুন
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// =========================
// TEST CONNECTION
// =========================

console.log('🚀 Supabase client initialized!');
console.log('📡 Connected to:', SUPABASE_URL);

// Connection test
supabase.from('profiles').select('count').limit(1)
    .then(() => console.log('✅ Database connection successful!'))
    .catch(err => console.error('❌ Database connection failed:', err.message));

// =========================
// AUTH FUNCTIONS
// =========================

// 📝 Sign Up (register)
async function signUp(email, password, username) {
    try {
        console.log('📝 Creating account for:', email);
        
        const { data, error } = await supabase.auth.signUp({
            email: email,
            password: password,
            options: {
                data: { username: username }
            }
        });

        if (error) {
            console.error('❌ Sign up error:', error);
            alert(error.message);
            return false;
        }

        console.log('✅ Account created!', data.user?.email);
        
        // Auto create profile
        if (data.user) {
            const { error: profileError } = await supabase
                .from('profiles')
                .upsert({
                    id: data.user.id,
                    username: username,
                    role: 'user',
                    created_at: new Date().toISOString()
                });
            
            if (profileError) {
                console.warn('⚠️ Profile creation warning:', profileError);
            } else {
                console.log('✅ Profile created for:', username);
            }
        }
        
        alert('✅ Account created successfully! Please login.');
        window.location.href = 'login.html';
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// 🔐 Sign In (login)
async function signIn(email, password) {
    try {
        console.log('🔐 Signing in:', email);
        
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password
        });

        if (error) {
            console.error('❌ Sign in error:', error);
            
            if (error.message.includes('Email not confirmed')) {
                alert('Please verify your email first.');
            } else {
                alert(error.message);
            }
            return false;
        }

        console.log('✅ Signed in!', data.user?.email);
        alert('Welcome back! 👋');
        window.location.href = 'index.html';
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// 🔓 Sign Out
async function signOut() {
    try {
        await supabase.auth.signOut();
        console.log('👋 User signed out');
        alert('Logged out successfully!');
        window.location.href = 'login.html';
    } catch (error) {
        console.error('❌ Sign out error:', error);
        alert('Error signing out. Please try again.');
    }
}

// 👤 Get Current User
async function getUser() {
    try {
        const { data: { user }, error } = await supabase.auth.getUser();
        
        if (error) {
            console.error('❌ Get user error:', error);
            return null;
        }
        
        return user;
    } catch (error) {
        console.error('❌ Unexpected error:', error);
        return null;
    }
}

// 🔑 Check if User is Admin
async function isAdmin() {
    try {
        const user = await getUser();
        if (!user) return false;

        const { data, error } = await supabase
            .from("profiles")
            .select("role")
            .eq("id", user.id)
            .single();

        if (error) {
            console.error('❌ Admin check error:', error);
            return false;
        }

        return data?.role === "admin";

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        return false;
    }
}

// 🌐 Social Logins
async function googleLogin() {
    try {
        const { error } = await supabase.auth.signInWithOAuth({
            provider: "google",
            options: {
                redirectTo: window.location.origin + '/index.html'
            }
        });

        if (error) {
            console.error('❌ Google login error:', error);
            alert(error.message);
            return false;
        }
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

async function facebookLogin() {
    try {
        const { error } = await supabase.auth.signInWithOAuth({
            provider: "facebook",
            options: {
                redirectTo: window.location.origin + '/index.html'
            }
        });

        if (error) {
            console.error('❌ Facebook login error:', error);
            alert(error.message);
            return false;
        }
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// =========================
// POST FUNCTIONS
// =========================

// 📝 Get All Posts
async function getPosts() {
    try {
        const { data, error } = await supabase
            .from("posts")
            .select("*, profiles(username, avatar)")
            .order("created_at", { ascending: false });

        if (error) {
            console.error('❌ Get posts error:', error);
            return [];
        }
        
        console.log(`📚 Loaded ${data?.length || 0} posts`);
        return data || [];

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        return [];
    }
}

// 📄 Get Single Post
async function getPost(id) {
    try {
        const { data, error } = await supabase
            .from("posts")
            .select("*, profiles(username, avatar)")
            .eq("id", id)
            .single();

        if (error) {
            console.error('❌ Get post error:', error);
            return null;
        }
        
        return data;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        return null;
    }
}

// ✏️ Create Post
async function createPost(title, description, url, platform) {
    try {
        const user = await getUser();
        
        if (!user) {
            alert("Please login first!");
            return false;
        }

        const { error } = await supabase
            .from("posts")
            .insert({
                user_id: user.id,
                title: title,
                description: description || null,
                url: url,
                platform: platform || detectPlatform(url)
            });

        if (error) {
            console.error('❌ Create post error:', error);
            alert(error.message);
            return false;
        }

        console.log('✅ Post created successfully!');
        alert('Post created! 🎉');
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// 🗑️ Delete Post
async function deletePost(id) {
    try {
        const { error } = await supabase
            .from("posts")
            .delete()
            .eq("id", id);

        if (error) {
            console.error('❌ Delete post error:', error);
            alert(error.message);
            return false;
        }

        console.log('✅ Post deleted successfully!');
        alert('Post deleted! 🗑️');
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// =========================
// COMMENT FUNCTIONS
// =========================

// 💬 Get Comments
async function getComments(postId) {
    try {
        const { data, error } = await supabase
            .from("comments")
            .select("*, profiles(username, avatar)")
            .eq("post_id", postId)
            .order("created_at", { ascending: true });

        if (error) {
            console.error('❌ Get comments error:', error);
            return [];
        }
        
        return data || [];

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        return [];
    }
}

// 💬 Add Comment
async function addComment(postId, comment) {
    try {
        const user = await getUser();
        
        if (!user) {
            alert("Please login first!");
            return false;
        }

        const { error } = await supabase
            .from("comments")
            .insert({
                post_id: postId,
                user_id: user.id,
                comment: comment
            });

        if (error) {
            console.error('❌ Add comment error:', error);
            alert(error.message);
            return false;
        }

        console.log('✅ Comment added successfully!');
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// 🗑️ Delete Comment
async function deleteComment(id) {
    try {
        const { error } = await supabase
            .from("comments")
            .delete()
            .eq("id", id);

        if (error) {
            console.error('❌ Delete comment error:', error);
            alert(error.message);
            return false;
        }

        console.log('✅ Comment deleted successfully!');
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// =========================
// VOTE FUNCTIONS
// =========================

// 👍👎 Vote on Post
async function votePost(postId, vote) {
    try {
        const user = await getUser();
        
        if (!user) {
            alert("Please login first!");
            return false;
        }

        // Check if user already voted
        const { data } = await supabase
            .from("votes")
            .select("*")
            .eq("post_id", postId)
            .eq("user_id", user.id)
            .maybeSingle();

        if (data) {
            // Update existing vote
            await supabase
                .from("votes")
                .update({ vote: vote })
                .eq("id", data.id);
        } else {
            // Insert new vote
            await supabase
                .from("votes")
                .insert({
                    post_id: postId,
                    user_id: user.id,
                    vote: vote
                });
        }

        console.log('✅ Vote recorded!');
        return true;

    } catch (error) {
        console.error('❌ Vote error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// =========================
// REPORT FUNCTIONS
// =========================

// 🚨 Report Post
async function reportPost(postId, reason) {
    try {
        const user = await getUser();
        
        if (!user) {
            alert("Please login first!");
            return false;
        }

        const { error } = await supabase
            .from("reports")
            .insert({
                post_id: postId,
                user_id: user.id,
                reason: reason || "No reason provided"
            });

        if (error) {
            console.error('❌ Report error:', error);
            alert(error.message);
            return false;
        }

        console.log('✅ Post reported!');
        alert('Report submitted! 🚨');
        return true;

    } catch (error) {
        console.error('❌ Unexpected error:', error);
        alert('Something went wrong. Please try again.');
        return false;
    }
}

// =========================
// PLATFORM DETECT
// =========================

function detectPlatform(link) {
    if (!link) return "Unknown";
    
    link = link.toLowerCase();
    
    if (link.includes("youtube.com") || link.includes("youtu.be"))
        return "YouTube";
    if (link.includes("facebook.com") || link.includes("fb.com"))
        return "Facebook";
    if (link.includes("instagram.com") || link.includes("instagr.am"))
        return "Instagram";
    if (link.includes("tiktok.com"))
        return "TikTok";
    if (link.includes("twitter.com") || link.includes("x.com"))
        return "X";
    if (link.includes("reddit.com"))
        return "Reddit";
    if (link.includes("linkedin.com"))
        return "LinkedIn";
    if (link.includes("pinterest.com"))
        return "Pinterest";
    if (link.includes("snapchat.com"))
        return "Snapchat";
    if (link.includes("whatsapp.com"))
        return "WhatsApp";
    if (link.includes("telegram.org"))
        return "Telegram";
    if (link.includes("discord.com"))
        return "Discord";
    if (link.includes("twitch.tv"))
        return "Twitch";
    if (link.includes("spotify.com"))
        return "Spotify";
    if (link.includes("soundcloud.com"))
        return "SoundCloud";
    if (link.includes("medium.com"))
        return "Medium";
    if (link.includes("dev.to"))
        return "Dev.to";
    if (link.includes("github.com"))
        return "GitHub";
    
    return "Unknown";
}

// =========================
// AUTH STATE LISTENER
// =========================

supabase.auth.onAuthStateChange((event, session) => {
    console.log('🔄 Auth Event:', event);
    
    switch(event) {
        case 'SIGNED_IN':
            console.log('✅ User signed in:', session?.user?.email);
            break;
        case 'SIGNED_OUT':
            console.log('👋 User signed out');
            break;
        case 'TOKEN_REFRESHED':
            console.log('🔄 Token refreshed');
            break;
        case 'USER_UPDATED':
            console.log('📝 User updated');
            break;
        default:
            console.log('ℹ️ Auth event:', event);
    }
});

// =========================
// PAGE INITIALIZATION
// =========================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 App initialized successfully!');
    
    const user = await getUser();
    const currentPage = window.location.pathname;
    
    // Redirect logic
    const isAuthPage = currentPage.includes('login.html') || 
                      currentPage.includes('register.html') ||
                      currentPage.includes('signup.html');
    
    if (user && isAuthPage) {
        // If logged in and on login/signup page → go to home
        console.log('🔀 Redirecting to home...');
        window.location.href = 'index.html';
    } else if (!user && !isAuthPage && !currentPage.includes('index.html')) {
        // If not logged in and not on auth pages → go to login
        console.log('🔀 Redirecting to login...');
        window.location.href = 'login.html';
    }
    
    // Show user status
    if (user) {
        console.log(`👤 Logged in as: ${user.email}`);
    } else {
        console.log('👤 Not logged in');
    }
});

// =========================
// EXPOSE FUNCTIONS TO HTML
// =========================

// Auth functions
window.signUp = signUp;
window.signIn = signIn;
window.signOut = signOut;
window.googleLogin = googleLogin;
window.facebookLogin = facebookLogin;
window.getUser = getUser;
window.isAdmin = isAdmin;

// Post functions
window.getPosts = getPosts;
window.getPost = getPost;
window.createPost = createPost;
window.deletePost = deletePost;

// Comment functions
window.getComments = getComments;
window.addComment = addComment;
window.deleteComment = deleteComment;

// Vote & Report functions
window.votePost = votePost;
window.reportPost = reportPost;
window.detectPlatform = detectPlatform;

// Export supabase instance
window.supabase = supabase;

console.log('✅ All functions exported successfully!');
console.log('📚 Available functions:', Object.keys(window).filter(key => 
    ['signUp', 'signIn', 'signOut', 'googleLogin', 'facebookLogin', 
     'getUser', 'isAdmin', 'getPosts', 'getPost', 'createPost', 
     'deletePost', 'getComments', 'addComment', 'deleteComment', 
     'votePost', 'reportPost', 'detectPlatform'].includes(key)
));
