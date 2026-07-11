const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co"; 
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";
const mySupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

let currentUserId = null; 
let targetUserId = null;  

async function initChat() {
    // ১. ব্রাউজারের লিঙ্ক থেকে টার্গেট ইউজারের আইডি (?target=...) বের করা
    const urlParams = new URLSearchParams(window.location.search);
    targetUserId = urlParams.get('target');
    
    if (!targetUserId) {
        alert("কোনো ইউজার সিলেক্ট করা হয়নি ভাই! ব্যাক করা হচ্ছে।");
        window.history.back();
        return;
    }

    // ২. কারেন্ট লগইন থাকা ইউজার সেশন চেক
    const { data: { user } } = await mySupabase.auth.getUser();
    if (!user) { 
        alert("মেসেজ পাঠাতে প্রথমে লগইন করুন!"); 
        window.location.href = "login.html"; 
        return; 
    }
    currentUserId = user.id;

    // নিজের সাথে চ্যাট ব্লক
    if (currentUserId === targetUserId) {
        document.getElementById('chatMessagesBox').innerHTML = "<p style='color:#aaa;text-align:center;padding:20px;'>এটি আপনার নিজের চ্যাট রুম ভাই!</p>";
        return;
    }

    // ৩. চ্যাট হিস্ট্রি লোড এবং রিয়েলটাইম লিসেনার চালু করা
    await loadPrivateChatHistory();
    listenToPrivateMessages();
}

// 📂 ডাটাবেজ থেকে ওয়ান-টু-ওয়ান মেসেজ হিস্ট্রি আনা
async function loadPrivateChatHistory() {
    const box = document.getElementById('chatMessagesBox');
    
    // শুধু আমার পাঠানো বা আমাকে পাঠানো মেসেজ ফিল্টার করবে
    const { data, error } = await mySupabase
        .from('messages')
        .select('*')
        .or(`and(sender_id.eq.${currentUserId},receiver_id.eq.${targetUserId}),and(sender_id.eq.${targetUserId},receiver_id.eq.${currentUserId})`)
        .order('created_at', { ascending: true });
        
    if (error) { 
        box.innerHTML = "<p style='color:red;text-align:center;'>Error loading chat history</p>"; 
        console.error(error);
        return; 
    }
    
    box.innerHTML = data.length === 0 ? "<p class='no-msg-text' style='color:#666;text-align:center;margin-top:20px;'>No private messages yet.</p>" : "";
    data.forEach(m => appendMsgUI(m));
    box.scrollTop = box.scrollHeight;
}

// 📝 ইউআই (UI) তে মেসেজ বাবল যুক্ত করা
function appendMsgUI(m) {
    const box = document.getElementById('chatMessagesBox');
    if (box.querySelector(`[data-msg-id="${m.id}"]`)) return;

    // "No private messages yet" টেক্সট থাকলে তা সরিয়ে ফেলা
    const noMsgText = box.querySelector('.no-msg-text');
    if(noMsgText) noMsgText.remove();

    const div = document.createElement('div');
    // আমি পাঠালে msg-sent, ওপাশ থেকে আসলে msg-received ক্লাস পাবে (আপনার CSS অনুযায়ী)
    div.className = `msg-bubble ${m.sender_id === currentUserId ? 'msg-sent' : 'msg-received'}`;
    div.setAttribute("data-msg-id", m.id);
    div.innerText = m.message_text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

// 🚀 মেসেজ পাঠানো এবং এরর ট্র্যাকিং
async function sendLiveMessage() {
    const input = document.getElementById('chatMessageInput');
    const text = input.value.trim();
    if (!text) return;
    
    input.value = ''; // ইনপুট বক্স সাথে সাথে খালি করা
    
    // ডাটাবেজে পুশ
    const { error } = await mySupabase.from('messages').insert({ 
        message_text: text, 
        sender_id: currentUserId,
        receiver_id: targetUserId 
    });

    // কোনো কারণে সুপাবেস রিজেক্ট করলে সরাসরি অ্যালার্টে এরর মেসেজ দেখাবে
    if(error) {
        alert("মেসেজ যায়নি ভাই! ডাটাবেজ এরর: " + error.message);
        console.error("Supabase Error:", error);
    }
}

// ⚡ রিয়েলটাইম লাইভ মেসেজ আদান-প্রদান (Supabase Broadcast Channel)
function listenToPrivateMessages() {
    mySupabase
        .channel('public:messages')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, payload => {
            const newMsg = payload.new;
            // শুধু আমাদের দুজনের ভেতরের মেসেজ হলে লাইভ স্ক্রিনে দেখাবে
            if ((newMsg.sender_id === currentUserId && newMsg.receiver_id === targetUserId) || 
                (newMsg.sender_id === targetUserId && newMsg.receiver_id === currentUserId)) {
                appendMsgUI(newMsg);
            }
        })
        .subscribe();
}

window.onload = initChat;
