const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co"; 
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";
const mySupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

let currentUserId = null; 
let targetUserId = null;  

async function initChat() {
    const urlParams = new URLSearchParams(window.location.search);
    targetUserId = urlParams.get('target');
    
    if (!targetUserId) {
        alert("কোনো ইউজার সিলেক্ট করা হয়নি ভাই!");
        window.history.back();
        return;
    }

    const { data: { user } } = await mySupabase.auth.getUser();
    if (!user) { window.location.href = "login.html"; return; }
    currentUserId = user.id;

    if (currentUserId === targetUserId) {
        document.getElementById('chatMessagesBox').innerHTML = "<p style='color:#aaa;text-align:center;padding:20px;'>এটি আপনার নিজের চ্যাট রুম ভাই!</p>";
        return;
    }

    await loadPrivateChatHistory();
    listenToPrivateMessages();
}

async function loadPrivateChatHistory() {
    const box = document.getElementById('chatMessagesBox');
    const { data, error } = await mySupabase
        .from('messages')
        .select('*')
        .or(`and(sender_id.eq.${currentUserId},receiver_id.eq.${targetUserId}),and(sender_id.eq.${targetUserId},receiver_id.eq.${currentUserId})`)
        .order('created_at', { ascending: true });
        
    if (error) { box.innerHTML = "<p style='color:red;text-align:center;'>Error loading chat</p>"; return; }
    
    box.innerHTML = data.length === 0 ? "<p class='no-msg-text' style='color:#666;text-align:center;margin-top:20px;'>No private messages yet.</p>" : "";
    data.forEach(m => appendMsgUI(m));
    box.scrollTop = box.scrollHeight;
}

function appendMsgUI(m) {
    const box = document.getElementById('chatMessagesBox');
    if (box.querySelector(`[data-msg-id="${m.id}"]`)) return;

    const noMsgText = box.querySelector('.no-msg-text');
    if(noMsgText) noMsgText.remove();

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
    
    const { error } = await mySupabase.from('messages').insert({ 
        message_text: text, 
        sender_id: currentUserId,
        receiver_id: targetUserId 
    });

    if(error) { alert("মেসেজ যায়নি ভাই! ডাটাবেজ লক চেক করুন।"); }
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
        .subscribe();
}

window.onload = initChat;
