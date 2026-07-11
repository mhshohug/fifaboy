const SUPABASE_URL = "https://zqsjopjkhtofyepjneby.supabase.co"; 
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxc2pvcGpraHRvZnllcGpuZWJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NTQ4MTEsImV4cCI6MjA5OTIzMDgxMX0.BgUuO9jdDzWNX2tzTw49LQGeaNq59Qv2pbw9CbmkbBU";
const mySupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function initChat() {
    const { data: { user } } = await mySupabase.auth.getUser();
    if (!user) { window.location.href = "login.html"; return; }
    
    // মেসেজ লোড
    const { data } = await mySupabase.from('messages').select('*').order('created_at');
    const box = document.getElementById('chatMessagesBox');
    box.innerHTML = data.map(m => `<div class="msg-bubble ${m.sender_id === user.id ? 'msg-sent' : 'msg-received'}">${m.message_text}</div>`).join('');
    
    // রিয়েলটাইম লিসেনার
    mySupabase.channel('public:messages').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, p => {
        const div = document.createElement('div');
        div.className = `msg-bubble ${p.new.sender_id === user.id ? 'msg-sent' : 'msg-received'}`;
        div.innerText = p.new.message_text;
        document.getElementById('chatMessagesBox').appendChild(div);
    }).subscribe();
}

async function sendLiveMessage() {
    const input = document.getElementById('chatMessageInput');
    await mySupabase.from('messages').insert({ message_text: input.value, sender_id: (await mySupabase.auth.getUser()).data.user.id });
    input.value = '';
}
window.onload = initChat;
