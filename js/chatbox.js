const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co"; 
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";
const mySupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

let currentUserId = null; // আপনি (যে লগইন করে আছে)
let targetUserId = null;  // আপনি যাকে মেসেজ দিচ্ছেন

async function initChat() {
    // ১. URL থেকে যার সাথে চ্যাট করবেন তার আইডি নেওয়া (?target=USER_ID)
    const urlParams = new URLSearchParams(window.location.search);
    targetUserId = urlParams.get('target');
    
    if (!targetUserId) {
        alert("কোনো ইউজার সিলেক্ট করা হয়নি ভাই!");
        window.location.href = "profile.html";
        return;
    }

    // ২. লগইন করা ইউজারের সেশন চেক
    const { data: { user } } = await mySupabase.auth.getUser();
    if (!user) { window.location.href = "login.html"; return; }
    currentUserId = user.id;

    if (currentUserId === targetUserId) {
        document.getElementById('chatMessagesBox').innerHTML = "<p style='color:#aaa;text-align:center;padding:20px;'>এটি আপনার নিজের চ্যাট রুম ভাই!</p>";
        return;
    }

    // ৩. হেডারের টাইটেল চেঞ্জ করা
    document.querySelector(".chat-header span").innerText = "💬 Private Chat Box";

    // ৪. শুধু আপনাদের দুজনের মধ্যকার (Private) মেসেজ লোড করা
    await loadPrivateChatHistory();
    
    // ৫. রিয়ালটাইম ও ৩ ঘণ্টার অটো-ডিলিট লিসেনার অন করা
    listenToPrivateMessages();
}

async function loadPrivateChatHistory() {
    const box = document.getElementById('chatMessagesBox');
    
    // এই লজিকটি নিশ্চিত করে মেসেজ শুধু আপনাদের দুজনের মধ্যেই লক থাকবে
    const { data, error } = await mySupabase
        .from('messages')
        .select('*')
        .or(`and(sender_id.eq.${currentUserId},receiver_id.eq.${targetUserId}),and(sender_id.eq.${targetUserId},receiver_id.eq.${currentUserId})`)
        .order('created_at', { ascending: true });
        
    if (error) { box.innerHTML = "<p style='color:red;text-align:center;'>Error loading chat</p>"; return; }
    
    box.innerHTML = data.length === 0 ? "<p style='color:#666;text-align:center;margin-top:20px;'>No private messages yet.</p>" : "";
    data.forEach(m => appendMsgUI(m));
    box.scrollTop = box.scrollHeight;
}

function appendMsgUI(m) {
    const box = document.getElementById('chatMessagesBox');
    if (box.querySelector(`[data-msg-id="${m.id}"]`)) return;

    const div = document.createElement('div');
    div.className = `msg-bubble ${m.sender_id === currentUserId ? 'msg-sent' : 'msg-received'}`;
    div.setAttribute("data-msg-id", m.id);
    div.innerText = m.message_text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

async function sendLiveMessage() {
    const input = document.getElementById('chatMessageInput');
    const text = input.value.trim();
    if (!text) return;
    
    input.value = '';
    // মেসেজ ডাটাবেজে সঠিক sender ও receiver আইডি দিয়ে সেভ হবে
    await mySupabase.from('messages').insert({ 
        message_text: text, 
        sender_id: currentUserId,
        receiver_id: targetUserId 
    });
}

function listenToPrivateMessages() {
    mySupabase
        .channel('public:messages')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, payload => {
            const newMsg = payload.new;
            if ((newMsg.sender_id === currentUserId && newMsg.receiver_id === targetUserId) || 
                (newMsg.sender_id === targetUserId && newMsg.receiver_id === currentUserId)) {
                appendMsgUI(newMsg);
            }
        })
        .on('postgres_changes', { event: 'DELETE', schema: 'public', table: 'messages' }, payload => {
            // ডাটাবেজ থেকে ৩ ঘণ্টা পর ডিলিট হলে স্ক্রিন থেকেও ভ্যানিশ হবে
            const oldMsg = document.querySelector(`[data-msg-id="${payload.old.id}"]`);
            if (oldMsg) oldMsg.remove();
        })
        .subscribe();
}

window.onload = initChat;
