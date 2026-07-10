// =========================
// FIFABOY APP
// Part 1
// =========================

const feed=document.getElementById("feed");
const search=document.getElementById("search");

let POSTS=[];
let FILTERED_POSTS=[];
let IS_ADMIN=false;

// =========================
// INIT
// =========================

window.addEventListener("load",init);

async function init(){

    try{

        IS_ADMIN=await isAdmin();

    }catch(e){

        IS_ADMIN=false;

    }

    await loadPosts();

    initSearch();

}

// =========================
// LOAD POSTS
// =========================

async function loadPosts(){

    try{

        POSTS=await getPosts();

        FILTERED_POSTS=[...POSTS];

        renderPosts(FILTERED_POSTS);

    }catch(err){

        console.error(err);

        feed.innerHTML=`
        <div class="post">
            <h2>Failed to load posts.</h2>
        </div>`;

    }

}

// =========================
// RENDER
// =========================

function renderPosts(list){

    feed.innerHTML="";

    if(list.length===0){

        feed.innerHTML=`
        <div class="post">
            <h2>No Posts Found</h2>
        </div>`;

        return;

    }

    list.forEach(post=>{

        feed.insertAdjacentHTML(
            "beforeend",
            createCard(post)
        );

    });

}

// =========================
// SEARCH
// =========================

function initSearch(){

    if(!search) return;

    search.addEventListener("input",()=>{

        const text=search.value
        .trim()
        .toLowerCase();

        if(text===""){

            FILTERED_POSTS=[...POSTS];

            renderPosts(FILTERED_POSTS);

            return;

        }

        FILTERED_POSTS=POSTS.filter(post=>{

            return (

                (post.title||"")
                .toLowerCase()
                .includes(text)

                ||

                (post.description||"")
                .toLowerCase()
                .includes(text)

                ||

                (post.platform||"")
                .toLowerCase()
                .includes(text)

            );

        });

        renderPosts(FILTERED_POSTS);

    });

}

// =========================
// CARD
// =========================
function createCard(post){

    return `
    <div class="post">

        ${getEmbed(post)}

        <h2>${escapeHtml(post.title)}</h2>

        <p>${escapeHtml(post.description||"")}</p>

        <div class="actions">

            <button onclick="likePostUI(${post.id})">
                👍 ${post.likes||0}
            </button>

            <button onclick="dislikePostUI(${post.id})">
                👎 ${post.dislikes||0}
            </button>

            <button onclick="openComments(${post.id})">
                💬 Comment
            </button>

            <button onclick="reportPostUI(${post.id})">
                🚩 Report
            </button>

            ${IS_ADMIN?`
            <button onclick="editPostUI(${post.id})">✏ Edit</button>
            <button onclick="deletePostUI(${post.id})">🗑 Delete</button>
            `:""}

        </div>

    </div>
    `;

}
//=========================
// EMBED
//=========================

function getEmbed(post){

    const url=post.url||"";

    if(post.platform==="YouTube"){
        let id="";
        if(url.includes("watch?v=")) id=url.split("watch?v=")[1].split("&")[0];
        else if(url.includes("youtu.be/")) id=url.split("youtu.be/")[1].split("?")[0];

        return `<iframe src="https://www.youtube.com/embed/${id}" loading="lazy" allowfullscreen></iframe>`;
    }

    if(post.platform==="Facebook"){
        return `<div class="preview"><h3>Facebook Video</h3><a href="${url}" target="_blank">Open Original</a></div>`;
    }

    if(post.platform==="Instagram"){
        return `<div class="preview"><h3>Instagram Post</h3><a href="${url}" target="_blank">Open Original</a></div>`;
    }

    if(post.platform==="TikTok"){
        return `<div class="preview"><h3>TikTok Video</h3><a href="${url}" target="_blank">Open Original</a></div>`;
    }

    if(post.platform==="X"){
        return `<div class="preview"><h3>X Post</h3><a href="${url}" target="_blank">Open Original</a></div>`;
    }

    return `<div class="preview"><h3>External Link</h3><a href="${url}" target="_blank">Open Original</a></div>`;

}

//=========================
// HTML SAFE
//=========================

function escapeHtml(text){

    if(!text) return "";

    return text
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;")
    .replace(/'/g,"&#039;");

}

//=========================
// COMMENTS PAGE
//=========================

function openComments(id){

    location.href=`post.html?id=${id}`;

}

//=========================
// COPY LINK
//=========================

async function copyPostLink(id){

    const url=`${location.origin}${location.pathname}?post=${id}`;

    try{

        await navigator.clipboard.writeText(url);

        alert("Link Copied");

    }catch{

        prompt("Copy Link",url);

    }

}

//=========================
// SHARE
//=========================

function sharePost(id){

    const url=`${location.origin}${location.pathname}?post=${id}`;

    if(navigator.share){

        navigator.share({
            title:"FIFABOY",
            text:"Check this post",
            url
        });

    }else{

        copyPostLink(id);

    }

}
//=========================
// LIKE
//=========================

async function likePostUI(id){

    const ok=await votePost(id,1);

    if(ok) await loadPosts();

}

//=========================
// DISLIKE
//=========================

async function dislikePostUI(id){

    const ok=await votePost(id,-1);

    if(ok) await loadPosts();

}

//=========================
// REPORT
//=========================

async function reportPostUI(id){

    const reason=prompt("Report reason:");

    if(!reason) return;

    const ok=await reportPost(id,reason);

    if(ok) alert("Report submitted.");

}

//=========================
// ADMIN DELETE
//=========================

async function deletePostUI(id){

    if(!IS_ADMIN) return;

    if(!confirm("Delete this post?")) return;

    const ok=await deletePost(id);

    if(ok){
        alert("Post deleted.");
        loadPosts();
    }

}

//=========================
// ADMIN EDIT
//=========================

async function editPostUI(id){

    if(!IS_ADMIN) return;

    const post=POSTS.find(p=>p.id===id);

    if(!post) return;

    const title=prompt("Title",post.title);
    if(title===null) return;

    const description=prompt("Description",post.description||"");
    if(description===null) return;

    const url=prompt("Video URL",post.url);
    if(url===null) return;

    const platform=detectPlatform(url);

    const ok=await updatePost(
        id,
        title,
        description,
        url,
        platform
    );

    if(ok){
        alert("Post updated.");
        loadPosts();
    }

}

//=========================
// REFRESH
//=========================

async function refreshPosts(){

    await loadPosts();

}

//=========================
// AUTO REFRESH
//=========================

setInterval(refreshPosts,15000);
//=========================
// REALTIME
//=========================

supabase
.channel("posts-live")
.on(
    "postgres_changes",
    {
        event:"*",
        schema:"public",
        table:"posts"
    },
    ()=>loadPosts()
)
.subscribe();

//=========================
// AUTH STATE
//=========================

supabase.auth.onAuthStateChange(async(event)=>{

    if(event==="SIGNED_OUT"){

        IS_ADMIN=false;
        POSTS=[];
        FILTERED_POSTS=[];
        renderPosts([]);

        return;

    }

    if(event==="SIGNED_IN"){

        IS_ADMIN=await isAdmin();
        await loadPosts();

    }

});

//=========================
// LOGOUT
//=========================

async function logout(){

    await signOut();

}

//=========================
// PROFILE
//=========================

async function openProfile(){

    const user=await getUser();

    if(!user){

        location.href="login.html";
        return;

    }

    location.href="profile.html";

}

//=========================
// LOGIN
//=========================

function openLogin(){

    location.href="login.html";

}

//=========================
// UPLOAD
//=========================

async function openUpload(){

    if(await isAdmin()){

        location.href="admin.html";

    }else{

        alert("Admin Only");

    }

}

//=========================
// LOADING
//=========================

function showLoading(){

    feed.innerHTML=`
    <div class="post">
        <h2>Loading...</h2>
    </div>`;

}

//=========================
// ERROR
//=========================

function showError(msg){

    feed.innerHTML=`
    <div class="post">
        <h2>${msg}</h2>
    </div>`;

}
//=========================
// SCROLL TOP
//=========================

function scrollTopPage(){

    window.scrollTo({
        top:0,
        behavior:"smooth"
    });

}

//=========================
// RELOAD
//=========================

async function reloadFeed(){

    showLoading();

    await loadPosts();

}

//=========================
// WINDOW FOCUS
//=========================

window.addEventListener("focus",()=>{

    loadPosts();

});

//=========================
// ONLINE
//=========================

window.addEventListener("online",()=>{

    loadPosts();

});

//=========================
// OFFLINE
//=========================

window.addEventListener("offline",()=>{

    showError("No Internet Connection");

});

//=========================
// ESC KEY
//=========================

document.addEventListener("keydown",e=>{

    if(e.key==="Escape"){

        search.value="";
        FILTERED_POSTS=[...POSTS];
        renderPosts(FILTERED_POSTS);

    }

});

//=========================
// ENTER SEARCH
//=========================

if(search){

    search.addEventListener("keydown",e=>{

        if(e.key==="Enter"){

            e.preventDefault();

        }

    });

}

//=========================
// GO HOME
//=========================

function goHome(){

    location.href="index.html";

}

//=========================
// INIT
//=========================

(async()=>{

    showLoading();

    try{

        IS_ADMIN=await isAdmin();

    }catch{

        IS_ADMIN=false;

    }

    await loadPosts();

})();

//=========================
// DEBUG
//=========================

console.log("⚽ FIFABOY Ready");



