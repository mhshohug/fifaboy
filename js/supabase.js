const SUPABASE_URL="https://zqsjopjkhtofyepjneby.supabase.co";
const SUPABASE_KEY="sb_publishable_L-eVH8iMcVlLw2OUGB_2Xg_FGfC08uq";

const supabase=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY);

// ---------- AUTH ----------

async function signUp(email,password,username){
    const {data,error}=await supabase.auth.signUp({
        email,
        password,
        options:{data:{username}}
    });

    if(error){
        alert(error.message);
        return false;
    }

    return true;
}

async function signIn(email,password){
    const {data,error}=await supabase.auth.signInWithPassword({
        email,
        password
    });

    if(error){
        alert(error.message);
        return false;
    }

    return true;
}

async function signOut(){
    await supabase.auth.signOut();
    location.href="index.html";
}

async function getUser(){
    const {data}=await supabase.auth.getUser();
    return data.user;
}

// ---------- POSTS ----------

async function getPosts(){
    const {data,error}=await supabase
        .from("posts")
        .select("*")
        .order("created_at",{ascending:false});

    if(error){
        console.log(error);
        return [];
    }

    return data;
}

async function createPost(post){
    const {error}=await supabase
        .from("posts")
        .insert(post);

    if(error){
        alert(error.message);
        return false;
    }

    return true;
}

async function deletePost(id){
    await supabase
        .from("posts")
        .delete()
        .eq("id",id);
}

// ---------- COMMENTS ----------

async function getComments(postId){
    const {data}=await supabase
        .from("comments")
        .select("*")
        .eq("post_id",postId)
        .order("created_at",{ascending:true});

    return data||[];
}

async function addComment(postId,text){
    const user=await getUser();

    if(!user){
        alert("Please login first.");
        return;
    }

    await supabase
        .from("comments")
        .insert({
            post_id:postId,
            user_id:user.id,
            comment:text
        });
}

// ---------- REALTIME ----------

supabase
.channel("posts")
.on(
    "postgres_changes",
    {event:"*",schema:"public",table:"posts"},
    ()=>loadPosts()
)
.subscribe();
