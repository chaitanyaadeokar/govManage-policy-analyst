import { useState, useRef, useEffect } from 'react';
import { API_URL } from '../types';
import { MessageSquare, Send, User, Bot, Trash2, Zap, Copy, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

const STARTER_PROMPTS = [
  "What is ISO 27001 and how does it apply to a fintech company?",
  "Draft an AI Governance policy for the Healthcare sector.",
  "What are the main GDPR obligations for data controllers?",
  "Summarize the key controls in NIST AI Risk Management Framework.",
];

export default function AiPolicyChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        "Hello! I'm your AI Governance Advisor. I can answer questions about compliance frameworks, draft policy language, explain regulatory requirements, or help you generate complete policy packs.\n\nWhat would you like to explore today?",
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleSend = async (overrideInput?: string) => {
    const text = (overrideInput ?? input).trim();
    if (!text) return;

    const userMessage: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsTyping(true);

    try {
      const res = await fetch(`${API_URL}/chat/reporting`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          policy_text: '',
          history: messages,
          report_type: 'general',
        }),
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: "Chat cleared. What would you like to explore?",
      },
    ]);
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="w-full h-[calc(100vh-64px)] flex flex-col bg-white animate-in relative">
      
      {/* Header */}
      <div className="flex-none px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-white z-10 shadow-sm sticky top-0">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <MessageSquare className="text-indigo-600" size={20} /> AI Governance Advisor
          </h2>
          <p className="text-slate-500 text-xs mt-0.5 ml-7">Powered by Agentic AI</p>
        </div>
        <button
          className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-rose-500 transition-colors px-3 py-1.5 rounded-md hover:bg-rose-50"
          onClick={clearChat}
          title="Clear chat"
        >
          <Trash2 size={14} /> Clear
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pb-32">
        <div className="max-w-4xl mx-auto px-4 py-8">
          
          {/* Starter prompts */}
          {messages.length === 1 && (
            <div className="mb-10 text-center animate-in" style={{ animationDelay: '0.2s' }}>
              <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-indigo-100">
                <Bot size={32} />
              </div>
              <h3 className="text-2xl font-semibold text-slate-800 mb-2">How can I help you govern today?</h3>
              <p className="text-slate-500 mb-8 max-w-lg mx-auto">
                I can orchestrate background agents, analyze risk landscapes, or draft comprehensive compliance policies for your organization.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto text-left">
                {STARTER_PROMPTS.map((p, i) => (
                  <button
                    key={i}
                    className="p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-400 hover:shadow-md text-sm text-slate-600 hover:text-indigo-700 transition-all flex items-start gap-3 group"
                    onClick={() => handleSend(p)}
                  >
                    <Zap size={16} className="text-indigo-400 shrink-0 mt-0.5 group-hover:text-indigo-600 transition-colors" />
                    <span className="leading-relaxed">{p}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="space-y-8">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-4 ${m.role === 'user' ? 'justify-end' : 'justify-start'} group`}>
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-1">
                    <Bot size={16} />
                  </div>
                )}

                <div
                  className={`relative max-w-[85%] ${
                    m.role === 'user'
                      ? 'bg-slate-100 text-slate-800 rounded-2xl p-4 px-5 text-[15px] leading-relaxed font-medium shadow-sm'
                      : 'text-slate-700 py-1'
                  }`}
                >
                  {m.role === 'assistant' ? (
                    <div className="markdown-body prose prose-slate prose-sm sm:prose-base max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {m.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap">{m.content}</div>
                  )}

                  {/* Copy Button for Assistant */}
                  {m.role === 'assistant' && (
                    <button
                      onClick={() => copyToClipboard(m.content, i)}
                      className="absolute -right-10 top-2 p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                      title="Copy to clipboard"
                    >
                      {copiedIndex === i ? <CheckCircle2 size={16} className="text-green-500" /> : <Copy size={16} />}
                    </button>
                  )}
                </div>

                {m.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center shrink-0 mt-1">
                    <User size={16} />
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-4 justify-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-1">
                  <Bot size={16} />
                </div>
                <div className="py-2 flex items-center gap-1.5">
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        </div>
      </div>

      {/* Input Area (Floating) */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 px-4 pointer-events-none">
        <div className="max-w-4xl mx-auto relative pointer-events-auto">
          <div className="relative shadow-lg rounded-2xl bg-white border border-slate-200 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50 transition-all">
            <textarea
              ref={textareaRef}
              rows={1}
              className="w-full resize-none bg-transparent border-none focus:ring-0 py-4 pl-4 pr-14 max-h-[200px] text-slate-800 custom-scrollbar"
              placeholder="Ask me to suggest frameworks or generate a policy..."
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              disabled={isTyping}
              style={{ minHeight: '56px' }}
            />
            <button
              className="absolute right-2 bottom-2 p-2.5 bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl disabled:opacity-40 disabled:hover:bg-indigo-600 transition-colors shadow-sm"
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
            >
              <Send size={16} className={isTyping ? "opacity-50" : ""} />
            </button>
          </div>
          <div className="text-center mt-2">
            <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
              Shift + Enter for new line • Enter to send
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
