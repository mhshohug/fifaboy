//=========================
// POST.JS PART 1
//=========================

const params=new URLSearchParams(location.search);

const POST_ID=params.get("id");

let POST=null;

let COMMENTS=[];

//=========================
// LOAD POST
//=========================

async function loadPost(){

    if(!POST_ID){

        document.getElementById("post-container").innerHTML=`
        <div class="post">
        <h2>Post Not Found</h2>
        </div>`;
        return;

    }

    POST=await getPost(POST_ID);

    if(!POST){

        document.getElementById("post-container").innerHTML=`
        <div class="post">
        <h2>Post Not Found</h2>
        </div>`;
        return;

    }

    renderPost();

}

//=========================
// RENDER POST
//=========================

function renderPost(){

    const container=document.getElementById("post-container");

    container.innerHTML=`

    <div class="post">

        ${getEmbed(POST)}

        <h2>${escapeHtml(POST.title)}</h2>

        <p>${escapeHtml(POST.description||"")}</p>

        <div class="actions">

            <button onclick="likeCurrentPost()">

                👍 ${POST.likes||0}

            </button>

            <button onclick="dislikeCurrentPost()">

                👎 ${POST.dislikes||0}

            </button>

            <button onclick="shareCurrentPost()">

                📤 Share

            </button>

            <button onclick="reportCurrentPost()">

                🚩 Report

            </button>

        </div>

    </div>

    `;

}

//=========================
// SHARE
//=========================

function shareCurrentPost(){

    navigator.clipboard.writeText(location.href);

    alert("Link Copied");

}
//=========================
// LOAD COMMENTS
//=========================

async function loadComments(){

    COMMENTS=await getComments(POST_ID);

    renderComments();

}

//=========================
// RENDER COMMENTS
//=========================

function renderComments(){

    const box=document.getElementById("comments");

    if(COMMENTS.length===0){

        box.innerHTML=`
        <div class="post">
            No comments yet.
        </div>`;
        return;

    }

    box.innerHTML="";

    COMMENTS.forEach(c=>{

        box.innerHTML+=`

        <div class="post">

            <h3>

                👤 ${escapeHtml(c.profiles?.username||"User")}

            </h3>

            <p>

                ${escapeHtml(c.comment)}

                ${c.edited?"<small>(edited)</small>":""}

            </p>

            <div class="actions">

                <button onclick="editComment(${c.id},'${encodeURIComponent(c.comment)}')">

                    ✏ Edit

                </button>

                <button onclick="deleteCommentUI(${c.id})">

                    🗑 Delete

                </button>

            </div>

        </div>

        `;

    });

}

//=========================
// ADD COMMENT
//=========================

async function sendComment(text){

    const ok=await addComment(POST_ID,text);

    if(ok){

        await loadComments();

    }

}

//=========================
// EDIT COMMENT
//=========================

async function editComment(id,text){

    text=decodeURIComponent(text);

    const value=prompt("Edit Comment",text);

    if(value===null) return;

    const ok=await updateComment(id,value);

    if(ok){

        await loadComments();

    }

}

//=========================
// DELETE COMMENT
//=========================

async function deleteCommentUI(id){

    if(!confirm("Delete this comment?")) return;

    const ok=await deleteComment(id);

    if(ok){

        await loadComments();

    }

}
//=========================
// LIKE
//=========================

async function likeCurrentPost(){

    const ok=await votePost(POST_ID,1);

    if(ok){

        await loadPost();

    }

}

//=========================
// DISLIKE
//=========================

async function dislikeCurrentPost(){

    const ok=await votePost(POST_ID,-1);

    if(ok){

        await loadPost();

    }

}

//=========================
// REPORT
//=========================

async function reportCurrentPost(){

    const reason=prompt("Report reason");

    if(!reason) return;

    const ok=await reportPost(POST_ID,reason);

    if(ok){

        alert("Report submitted.");

    }

}

//=========================
// REALTIME COMMENTS
//=========================

supabase
.channel("comments-"+POST_ID)
.on(
"postgres_changes",
{
event:"*",
schema:"public",
table:"comments",
filter:`post_id=eq.${POST_ID}`
},
()=>{
loadComments();
}
)
.subscribe();

//=========================
// REALTIME POST
//=========================

supabase
.channel("post-"+POST_ID)
.on(
"postgres_changes",
{
event:"*",
schema:"public",
table:"posts",
filter:`id=eq.${POST_ID}`
},
()=>{
loadPost();
}
)
.subscribe();

//=========================
// INIT
//=========================

window.addEventListener("load",async()=>{

    await loadPost();

    await loadComments();

});

//=========================
// SCROLL TOP
//=========================

window.addEventListener("scroll",()=>{

    const btn=document.getElementById("topBtn");

    if(!btn) return;

    if(window.scrollY>300){

        btn.style.display="flex";

    }else{

        btn.style.display="none";

    }

});

//=========================
// ESC CLEAR COMMENT
//=========================

window.addEventListener("keydown",e=>{

    if(e.key==="Escape"){

        const box=document.getElementById("commentText");

        if(box) box.value="";

    }

});

console.log("post.js loaded");
