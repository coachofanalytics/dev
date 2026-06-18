(function(){
  // Namespaced widget to avoid polluting globals
  const NAMESPACE = 'HealthcareChatWidget';
  if(window[NAMESPACE]) return; // already loaded

  const rootId = 'healthcare-chat-root';

  function createNodeFromHTML(html){
    const div = document.createElement('div');
    div.innerHTML = html.trim();
    return div;
  }

  function buildWidget(){
    const container = document.createElement('div');
    container.id = rootId;

    const html = `
      <button class="hc-chat-toggle" aria-label="Open chat">💬</button>
      <div class="hc-chat-window" style="display:none" role="dialog" aria-label="Healthcare chat">
        <div class="hc-header">
          <div>Health Assistant</div>
          <button class="hc-close" aria-label="Close chat" style="background:transparent;border:0;color:#fff;cursor:pointer">✕</button>
        </div>
        <div class="hc-messages"></div>
        <div class="hc-input">
          <textarea placeholder="Ask a health question..." aria-label="Type your message"></textarea>
          <button class="hc-send">Send</button>
        </div>
      </div>
    `;

    // Insert the full HTML into the container (preserve all siblings)
    const frag = createNodeFromHTML(html);
    // move all child nodes from frag into container
    while (frag.firstChild) container.appendChild(frag.firstChild);
    document.body.appendChild(container);
    return container;
  }

  function scrollToBottom(messagesEl){ messagesEl.scrollTop = messagesEl.scrollHeight; }

  async function wikiAnswer(query){
    try{
      // search for a matching page
      const searchUrl = 'https://en.wikipedia.org/w/api.php?action=opensearch&search=' + encodeURIComponent(query) + '&limit=1&namespace=0&format=json&origin=*';
      const sres = await fetch(searchUrl);
      if(!sres.ok) return null;
      const sjson = await sres.json();
      const titles = sjson[1];
      if(titles && titles.length){
        const title = titles[0];
        const sumUrl = 'https://en.wikipedia.org/api/rest_v1/page/summary/' + encodeURIComponent(title);
        const sumRes = await fetch(sumUrl);
        if(!sumRes.ok) return null;
        const sumJson = await sumRes.json();
        if(sumJson.extract) return sumJson.extract + '\n\n(Source: Wikipedia)';
      }
    }catch(e){ console.error('wiki error', e); }
    return null;
  }

  async function duckAnswer(query){
    try{
      // Use DuckDuckGo instant answer via allorigins to avoid CORS issues
      const ddUrlBase = 'https://api.duckduckgo.com/?q=' + encodeURIComponent(query) + '&format=json&no_html=1&skip_disambig=1';
      const proxy = 'https://api.allorigins.win/raw?url=' + encodeURIComponent(ddUrlBase);
      const res = await fetch(proxy);
      if(!res.ok) return null;
      const json = await res.json();
      if(json.AbstractText && json.AbstractText.length) return json.AbstractText + '\n\n(Source: DuckDuckGo)';
      // also try RelatedTopics first item
      if(json.RelatedTopics && json.RelatedTopics.length && json.RelatedTopics[0].Text) return json.RelatedTopics[0].Text;
    }catch(e){ console.error('duck error', e); }
    return null;
  }

  function appendMessage(messagesEl, text, who='bot'){
    const msg = document.createElement('div');
    msg.className = 'hc-msg ' + (who==='user' ? 'user' : 'bot');
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    msg.appendChild(bubble);
    messagesEl.appendChild(msg);
    scrollToBottom(messagesEl);
  }

  function setTyping(messagesEl, on=true){
    const id = 'hc-typing';
    const existing = messagesEl.querySelector('#' + id);
    if(on){
      if(existing) return;
      const el = document.createElement('div'); el.id = id; el.className = 'hc-msg bot';
      el.innerHTML = '<div class="bubble">Typing…</div>';
      messagesEl.appendChild(el);
      scrollToBottom(messagesEl);
    } else {
      if(existing) existing.remove();
    }
  }

  async function handleQuery(query, messagesEl){
    setTyping(messagesEl, true);
    // attempt Wiki
    let ans = await wikiAnswer(query);
    if(ans){ setTyping(messagesEl, false); appendMessage(messagesEl, ans, 'bot'); return; }
    // attempt Duck
    ans = await duckAnswer(query);
    if(ans){ setTyping(messagesEl, false); appendMessage(messagesEl, ans, 'bot'); return; }
    // fallback simple heuristic
    setTyping(messagesEl, false);
    appendMessage(messagesEl, "I couldn't find an exact answer. Try rephrasing or ask a different question. If it's urgent, contact local medical services.", 'bot');
  }

  // build and wire events
  document.addEventListener('DOMContentLoaded', function(){
  const container = buildWidget();
  const toggle = container.querySelector('.hc-chat-toggle');
  const windowEl = container.querySelector('.hc-chat-window');
  const closeBtn = container.querySelector('.hc-close');
  const messagesEl = container.querySelector('.hc-messages');
  const textarea = container.querySelector('.hc-input textarea');
  const sendBtn = container.querySelector('.hc-send');

  // If for some reason elements are missing, do nothing to avoid runtime errors
  if(!toggle || !windowEl || !closeBtn || !messagesEl || !textarea || !sendBtn) return;

    function open(){ windowEl.style.display='flex'; textarea.focus(); }
    function close(){ windowEl.style.display='none'; }

    toggle.addEventListener('click', ()=>{
      if(windowEl.style.display === 'none' || !windowEl.style.display) open(); else close();
    });
    closeBtn.addEventListener('click', close);
    sendBtn.addEventListener('click', async ()=>{
      const text = textarea.value && textarea.value.trim();
      if(!text) return;
      appendMessage(messagesEl, text, 'user');
      textarea.value = '';
      await handleQuery(text, messagesEl);
    });

    textarea.addEventListener('keydown', function(e){
      if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); sendBtn.click(); }
    });

    // welcome message
    appendMessage(messagesEl, 'Hi — I can help with basic health questions and point you to resources. Ask me anything or click the "Find Nearby Hospitals" button on the page to locate care.', 'bot');
  });

  // expose minimal API (no globals for internals)
  window[NAMESPACE] = { open: function(){ const root = document.getElementById(rootId); if(root) { const w = root.querySelector('.hc-chat-window'); if(w) w.style.display='flex'; } } };
})();
