const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co"; 
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";
const mySupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

let currentUserId = null; // যে চ্যাট ওপেন করেছে (লগইন ইউজার)
let targetUserId = null;  // যার সাথে চ্যাট করা হচ্ছে (ইউজার বা অ্যাডমিন)

async function initChat() {
    // ১. URL থেকে টার্গেট ইউজারের আইডি রিড করা (?target=USER_ID)
    const urlParams = new URLSearchParams(window.location.search);
    targetUserId = urlParams.get('target');
    
    // সেফটি গার্ড: যদি কোনো আইডি না থাকে, তবে অটোমেটিক আপনার (অ্যাডমিন) আইডিতে রিডিরেক্ট করবে
    if (!targetUserId) {
        targetUserId = "4969b84d-057a-47f1-a143-3c235dc1b132"; // আপনার মেইন অ্যাডমিন আইডি
    }

    // ২. কারেন্ট লগইন ইউজার সেশন চেক
    const { data: { user } } = await mySupabase.auth.getUser();
    if (!user) { 
        window.location.href = "login.html"; 
        return; 
    }
    currentUserId = user.id;

    // যদি ইউজার নিজের আইডিতেই চ্যাট ওপেন করার চেষ্টা করে
    if (currentUserId === targetUserId) {
        document.getElementById('chatMessagesBox').innerHTML = "<p style='color:#aaa;text-align:center;padding:20px;'>আপনি নিজের প্রোফাইল চ্যাটে আছেন ভাই। অন্য কারও সাথে চ্যাট করতে তার আইডি লিংক ব্যবহার করুন।</p>";
        return;
    }

    // ৩. টার্গেট ইউজারের নাম ডাইনামিকালি লোড করা (হেডারে দেখানোর জন্য)
    loadTargetUserName();

    // ৪. প্রাইভেট মেসেজ হিস্ট্রি লোড (Sender & Receiver ফিল্টারিং)
    await loadPrivateChatHistory();
    
    // ৫. সুপাবেস রিয়ালটাইম লিসেনার চালু করা
    listenToPrivateMessages();
}

// 👤 টার্গেট ইউজারের নাম ডাটাবেজ থেকে এনে হেডার আপডেট করার ফাংশন
async function loadTargetUserName() {
    const { data: profile } = await mySupabase
        .from('profiles')
        .select('role')
        .eq('id', targetUserId)
        .maybeSingle();
        
    const headerTitle = document.querySelector(".chat-header span");
    if (profile && profile.role === 'admin') {
        headerTitle.innerText = "💬 Chat with Admin (🛡️)";
    } else {
        headerTitle.innerText = "💬 Private Chat Room";
    }
}

// 📜 নির্দিষ্ট দুজনের মধ্যকার চ্যাট হিস্ট্রি লোড
async function loadPrivateChatHistory() {
    const box = document.getElementById('chatMessagesBox');
    
    const { data, error } = await mySupabase
        .from('messages')
        .select('*')
        .or(`and(sender_id.eq.${currentUserId},receiver_id.eq.${targetUserId}),and(sender_id.eq.${targetUserId},receiver_id.eq.${currentUserId})`)
        .order('created_at', { ascending: true });
        
    if (error) { 
        box.innerHTML = "<p style='color:red;text-align:center;'>Failed to load messages.</p>"; 
        return; 
    }
    
    box.innerHTML = data.length === 0 ? "<p style='color:#666;text-align:center;margin-top:20px;'>No private messages yet. Start conversation!</p>" : "";
    
    data.forEach(m => appendMsgUI(m));
    box.scrollTop = box.scrollHeight;
}

// 🎨 চ্যাট বাবলের ইউআই রেন্ডার
function appendMsgUI(m) {
    const box = document.getElementById('chatMessagesBox');
    
    // ডুপ্লিকেট মেসেজ রেন্ডার প্রোটেকশন
    if (box.querySelector(`[data-msg-id="${m.id}"]`)) return;

    const div = document.createElement('div');
    div.className = `msg-bubble ${m.sender_id === currentUserId ? 'msg-sent' : 'msg-received'}`;
    div.setAttribute("data-msg-id", m.id);
    div.innerText = m.message_text;
    
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

// ✉️ লাইভ মেসেজ সেন্ড লজিক
async function sendLiveMessage() {
    const input = document.getElementById('chatMessageInput');
    const text = input.value.trim();
    if (!text) return;
    
    input.value = '';
    
    // ডাটাবেজে সঠিক sender এবং receiver ম্যাপিং
    await mySupabase.from('messages').insert({ 
        message_text: text, 
        sender_id: currentUserId,
        receiver_id: targetUserId 
    });
}

// ⚡ রিয়ালটাইম ওয়ান-টু-ওয়ান ফিল্টারিং এবং অটো-ডিলিট লাইভ সিঙ্ক
function listenToPrivateMessages() {
    mySupabase
        .channel('public:messages')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, payload => {
            const newMsg = payload.new;
            // শুধু কারেন্ট ইউজার এবং টার্গেট ইউজারের মধ্যকার মেসেজই স্ক্রিনে আসবে
            if ((newMsg.sender_id === currentUserId && newMsg.receiver_id === targetUserId) || 
                (newMsg.sender_id === targetUserId && newMsg.receiver_id === currentUserId)) {
                appendMsgUI(newMsg);
            }
        })
        .on('postgres_changes', { event: 'DELETE', schema: 'public', table: 'messages' }, payload => {
            // ৩ ঘণ্টা পর ব্যাকএন্ড ট্রিগার মেসেজ মুছলে স্ক্রিন থেকেও লাইভ রিমুভ হবে
            const oldMsg = document.querySelector(`[data-msg-id="${payload.old.id}"]`);
            if (oldMsg) oldMsg.remove();
        })
        .subscribe();
}

window.onload = initChat;
