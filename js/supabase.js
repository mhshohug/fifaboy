const SUPABASE_URL="https://zqsjopjkhtofyepjneby.supabase.co";
const SUPABASE_KEY="sb_publishable_L-eVH8iMcVlLw2OUGB_2Xg_FGfC08uq";

const supabase=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY);

// =========================
// AUTH
// =========================

async function signUp(email,password,username){

    const {error}=await supabase.auth.signUp({
        email,
        password,
        options:{
            data:{username}
        }
    });

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

async function signIn(email,password){

    const {error}=await supabase.auth.signInWithPassword({
        email,
        password
    });

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

async function googleLogin(){

    await supabase.auth.signInWithOAuth({
        provider:"google"
    });

}

async function facebookLogin(){

    await supabase.auth.signInWithOAuth({
        provider:"facebook"
    });

}

async function signOut(){

    await supabase.auth.signOut();

    location.href="login.html";

}

async function getUser(){

    const {data}=await supabase.auth.getUser();

    return data.user;

}

async function isAdmin(){

    const user=await getUser();

    if(!user) return false;

    const {data}=await supabase
    .from("profiles")
    .select("role")
    .eq("id",user.id)
    .single();

    return data?.role==="admin";

}
// =========================
// POSTS
// =========================

async function getPosts(){

    const {data,error}=await supabase
    .from("posts")
    .select("*")
    .order("created_at",{ascending:false});

    if(error){
        console.error(error);
        return [];
    }

    return data;

}

async function getPost(id){

    const {data,error}=await supabase
    .from("posts")
    .select("*")
    .eq("id",id)
    .single();

    if(error){
        console.error(error);
        return null;
    }

    return data;

}

async function createPost(title,description,url,platform){

    const user=await getUser();

    if(!user){
        alert("Login Required");
        return false;
    }

    const {error}=await supabase
    .from("posts")
    .insert({
        user_id:user.id,
        title,
        description,
        url,
        platform
    });

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

async function updatePost(id,title,description,url,platform){

    const {error}=await supabase
    .from("posts")
    .update({
        title,
        description,
        url,
        platform
    })
    .eq("id",id);

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

async function deletePost(id){

    const {error}=await supabase
    .from("posts")
    .delete()
    .eq("id",id);

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

// =========================
// PLATFORM DETECT
// =========================

function detectPlatform(link){

    link=link.toLowerCase();

    if(link.includes("youtube.com")||link.includes("youtu.be"))
        return "YouTube";

    if(link.includes("facebook.com"))
        return "Facebook";

    if(link.includes("instagram.com"))
        return "Instagram";

    if(link.includes("tiktok.com"))
        return "TikTok";

    if(link.includes("twitter.com")||link.includes("x.com"))
        return "X";

    return "Unknown";

}

// =========================
// REALTIME POSTS
// =========================

supabase
.channel("posts")
.on(
    "postgres_changes",
    {
        event:"*",
        schema:"public",
        table:"posts"
    },
    ()=>{
        if(typeof loadPosts==="function"){
            loadPosts();
        }
    }
)
.subscribe();
// =========================
// COMMENTS
// =========================

async function getComments(postId){

    const {data,error}=await supabase
    .from("comments")
    .select("*,profiles(username,avatar)")
    .eq("post_id",postId)
    .order("created_at",{ascending:true});

    if(error){
        console.error(error);
        return [];
    }

    return data;

}

async function addComment(postId,comment){

    const user=await getUser();

    if(!user){
        alert("Login Required");
        return false;
    }

    const {error}=await supabase
    .from("comments")
    .insert({
        post_id:postId,
        user_id:user.id,
        comment
    });

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

async function updateComment(id,comment){

    const {error}=await supabase
    .from("comments")
    .update({
        comment,
        edited:true,
        updated_at:new Date().toISOString()
    })
    .eq("id",id);

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

async function deleteComment(id){

    const {error}=await supabase
    .from("comments")
    .delete()
    .eq("id",id);

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

// =========================
// LIKE / DISLIKE
// vote = 1 (Like)
// vote = -1 (Dislike)
// =========================

async function votePost(postId,vote){

    const user=await getUser();

    if(!user){
        alert("Login Required");
        return false;
    }

    const {data}=await supabase
    .from("votes")
    .select("*")
    .eq("post_id",postId)
    .eq("user_id",user.id)
    .maybeSingle();

    if(data){

        await supabase
        .from("votes")
        .update({vote})
        .eq("id",data.id);

    }else{

        await supabase
        .from("votes")
        .insert({
            post_id:postId,
            user_id:user.id,
            vote
        });

    }

    return true;

}

// =========================
// REPORT
// =========================

async function reportPost(postId,reason){

    const user=await getUser();

    if(!user){
        alert("Login Required");
        return false;
    }

    const {error}=await supabase
    .from("reports")
    .insert({
        post_id:postId,
        user_id:user.id,
        reason
    });

    if(error){
        alert(error.message);
        return false;
    }

    return true;

}

// =========================
// SESSION
// =========================

async function isLoggedIn(){

    return await getUser()!=null;

}

supabase.auth.onAuthStateChange((event,session)=>{

    console.log("AUTH:",event);

});
