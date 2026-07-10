const form=document.getElementById("uploadForm");
const url=document.getElementById("url");
const platform=document.getElementById("platform");

url.oninput=()=>{

    const link=url.value.toLowerCase();

    if(link.includes("youtube")||link.includes("youtu.be"))
        platform.value="YouTube";

    else if(link.includes("facebook"))
        platform.value="Facebook";

    else if(link.includes("instagram"))
        platform.value="Instagram";

    else if(link.includes("tiktok"))
        platform.value="TikTok";

    else if(link.includes("twitter")||link.includes("x.com"))
        platform.value="X";

    else
        platform.value="Unknown";
};

form.onsubmit=async(e)=>{

    e.preventDefault();

    const user=await getUser();

    if(!user){
        alert("Login Required");
        return;
    }

    const {error}=await supabase
    .from("posts")
    .insert({
        user_id:user.id,
        title:title.value,
        description:description.value,
        url:url.value,
        platform:platform.value
    });

    if(error){
        alert(error.message);
        return;
    }

    alert("Post Published");

    location.href="index.html";

};
