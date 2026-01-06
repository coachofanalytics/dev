document.addEventListener('DOMContentLoaded', function() {
    const chatBtn = document.getElementById('chatbot-fab');
    const chatWindow = document.getElementById('chatbot-window');
    const closeChat = document.getElementById('close-chat-btn');
    const chatMessages = document.getElementById('chat-messages');
    const chatOptions = document.getElementById('chat-options');

    // Toggle Chat Window
    if(chatBtn) {
        chatBtn.addEventListener('click', () => {
            chatWindow.classList.toggle('hidden');
            if(!chatWindow.classList.contains('hidden') && chatMessages.children.length === 0) {
                // Initial Greeting
                addBotMessage("Hello! I'm your DC48K Assistant. How can I help you today?");
                showMainOptions();
            }
        });
    }

    if(closeChat) {
        closeChat.addEventListener('click', () => {
            chatWindow.classList.add('hidden');
        });
    }

    // Main Options
    function showMainOptions() {
        setOptions([
            { text: "Frequently Asked Questions", action: "faq" },
            { text: "Find a Service", action: "routing" },
            { text: "Contact Support", action: "contact" }
        ]);
    }

    // FAQ Logic
    function showFAQOptions() {
        addBotMessage("What topic do you have a question about?");
        setOptions([
            { text: "Passports & Travel", action: "faq_passport" },
            { text: "Financial Services", action: "faq_finance" },
            { text: "Healthcare", action: "faq_health" },
            { text: "Back to Menu", action: "main" }
        ]);
    }

    // Service Routing Logic
    function showRoutingOptions() {
        addBotMessage("Please tell me what you need help with:");
        setOptions([
            { text: "I lost my documents", action: "route_docs" },
            { text: "I'm in a crisis/emergency", action: "route_crisis" },
            { text: "I need to send money", action: "route_finance" },
            { text: "Back to Menu", action: "main" }
        ]);
    }

    // Handle Option Click
    function handleOption(action) {
        // Clear options temporarily
        chatOptions.innerHTML = '';

        switch(action) {
            case 'main':
                showMainOptions();
                break;
            case 'faq':
                showFAQOptions();
                break;
            case 'routing':
                showRoutingOptions();
                break;
            case 'contact':
                addBotMessage("You can reach us at support@dc48k.org or use the 'Contact Our Experts' button on the Services page.");
                setTimeout(showMainOptions, 2000);
                break;
            
            // FAQs
            case 'faq_passport':
                addBotMessage("For lost passports, please visit our Consular Assistance page. You can request temporary travel documents there.");
                addLink("Go to Consular Services", "/our_service/#consular");
                setTimeout(showMainOptions, 4000);
                break;
            case 'faq_finance':
                addBotMessage("We offer investment advice and remittance info. Check our Financial Planning section.");
                addLink("Go to Financial Planning", "/financial_planning/");
                setTimeout(showMainOptions, 4000);
                break;
            case 'faq_health':
                addBotMessage("Our Healthcare Information service helps you find vetted doctors and insurance guidance.");
                addLink("Go to Healthcare Info", "/our_service/#healthcare");
                setTimeout(showMainOptions, 4000);
                break;

            // Routing
            case 'route_docs':
                addBotMessage("It sounds like you need Document Services.");
                addLink("Go to Document Services", "/services/documents/");
                break;
            case 'route_crisis':
                addBotMessage("Please visit our Crisis Management page immediately.");
                addLink("Go to Crisis Page", "/crisis_page/");
                break;
            case 'route_finance':
                addBotMessage("Our Financial Services can help with that.");
                addLink("Go to Financial Services", "/financial_planning/");
                break;
        }
    }

    // Helper: Add Bot Message
    function addBotMessage(text) {
        const div = document.createElement('div');
        div.className = 'bg-gray-100 p-3 rounded-lg rounded-tl-none self-start mb-2 text-sm text-gray-800 shadow-sm max-w-[85%]';
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Helper: Add Link Button
    function addLink(text, url) {
        const a = document.createElement('a');
        a.href = url;
        a.className = 'block text-center bg-brand-blue text-white py-2 px-4 rounded mt-2 text-sm hover:bg-blue-700 transition';
        a.textContent = text;
        chatMessages.appendChild(a);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Return to menu after a delay
        setTimeout(showMainOptions, 5000);
    }

    // Helper: Set Options
    function setOptions(options) {
        chatOptions.innerHTML = '';
        options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'w-full text-left p-2 border border-brand-blue text-brand-blue rounded hover:bg-blue-50 transition text-sm mb-2';
            btn.textContent = opt.text;
            btn.onclick = () => {
                // User Message (Echo)
                const userDiv = document.createElement('div');
                userDiv.className = 'bg-brand-blue text-white p-3 rounded-lg rounded-tr-none self-end mb-2 text-sm shadow-sm max-w-[85%]';
                userDiv.textContent = opt.text;
                chatMessages.appendChild(userDiv);
                
                handleOption(opt.action);
            };
            chatOptions.appendChild(btn);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
