import { useState, useRef, useEffect } from 'react';
import { API_URL } from '../types';
import { MessageSquare, Send, User, Bot, Trash2, Zap, Copy, CheckCircle2, FileText, Download, Mail } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

type InteractiveForm = {
  title: string;
  description: string;
  multi_select: boolean;
  options: { id: string; label: string }[];
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
  const [sessionId, setSessionId] = useState<string>(() => {
    const saved = localStorage.getItem('chatSessionId');
    if (saved) return saved;
    const newId = `session_${Math.random().toString(36).substring(2, 15)}`;
    localStorage.setItem('chatSessionId', newId);
    return newId;
  });
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [activeForm, setActiveForm] = useState<InteractiveForm | null>(null);
  const [selectedOptions, setSelectedOptions] = useState<Set<string>>(new Set());
  
  // Drag state
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartPos = useRef({ x: 0, y: 0 });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, activeForm]);

  useEffect(() => {
    const lastMsg = messages[messages.length - 1];
    if (lastMsg?.role === 'assistant') {
      const match = lastMsg.content.match(/<INTERACTIVE_FORM>([\s\S]*?)<\/INTERACTIVE_FORM>/);
      if (match) {
        try {
          const form = JSON.parse(match[1]);
          setActiveForm(form);
          setSelectedOptions(new Set());
          setPosition({ x: 0, y: 0 });
        } catch (e) {
          console.error("Failed to parse form", e);
        }
      } else {
        setActiveForm(null);
      }
    } else {
      setActiveForm(null);
      setPosition({ x: 0, y: 0 });
    }
  }, [messages]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        setPosition({
          x: e.clientX - dragStartPos.current.x,
          y: e.clientY - dragStartPos.current.y
        });
      }
    };
    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  useEffect(() => {
    async function fetchSession() {
      try {
        const res = await fetch(`${API_URL}/chat/session/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
          }
        }
      } catch (err) {
        console.error("Failed to load chat session", err);
      }
    }
    fetchSession();
  }, [sessionId]);

  const handleEmailPolicy = async (policyId: string) => {
    if (!confirm("Are you sure you want to email this policy to the organization mailing list?")) return;
    try {
      const res = await fetch(`${API_URL}/policies/email/${policyId}`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        alert("Email sent successfully!");
      } else {
        alert("Error sending email: " + data.error);
      }
    } catch(e) {
      alert("Network error sending email.");
    }
  };

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
          session_id: sessionId,
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
    const newId = `session_${Math.random().toString(36).substring(2, 15)}`;
    localStorage.setItem('chatSessionId', newId);
    setSessionId(newId);
    setMessages([
      {
        role: 'assistant',
        content: "New conversation started. I have cleared my memory of the previous chat. What would you like to explore?",
      },
    ]);
  };

  const copyToClipboard = (text: string, index: number) => {
    const cleanText = text
      .replace(/<INTERACTIVE_FORM>[\s\S]*?<\/INTERACTIVE_FORM>/g, '')
      .replace(/<POLICY_CARD>[\s\S]*?<\/POLICY_CARD>/g, '')
      .trim();
    navigator.clipboard.writeText(cleanText);
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
                        {m.content.replace(/<INTERACTIVE_FORM>[\s\S]*?<\/INTERACTIVE_FORM>/g, '').replace(/<POLICY_CARD>[\s\S]*?<\/POLICY_CARD>/g, '').trim()}
                      </ReactMarkdown>
                      {(() => {
                        const match = m.content.match(/<POLICY_CARD>([\s\S]*?)<\/POLICY_CARD>/);
                        if (match) {
                          try {
                            const card = JSON.parse(match[1]);
                            return (
                              <div className="mt-4 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                                <div className="flex items-center gap-3 mb-3">
                                  <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                                    <FileText size={20} />
                                  </div>
                                  <div>
                                    <h4 className="font-semibold text-slate-800 m-0 leading-tight">{card.title}</h4>
                                    <p className="text-xs text-slate-500 m-0">Generated Policy Document</p>
                                  </div>
                                </div>
                                <div className="flex gap-2 mt-3">
                                  <a 
                                    href={`${API_URL}/policies/download/${card.id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors no-underline"
                                  >
                                    <Download size={14} /> Download PDF
                                  </a>
                                  <button
                                    onClick={() => handleEmailPolicy(card.id)}
                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
                                  >
                                    <Mail size={14} /> Review & Email
                                  </button>
                                </div>
                              </div>
                            );
                          } catch(e) {}
                        }
                        return null;
                      })()}
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

      {/* Interactive Form Floating Widget */}
      {activeForm && (
        <div 
          className="absolute bottom-[140px] left-1/2 z-20 w-full max-w-md pointer-events-auto"
          style={{ transform: `translate(calc(-50% + ${position.x}px), ${position.y}px)` }}
        >
          <div className="bg-white rounded-2xl shadow-2xl border border-indigo-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200 mx-4">
            <div 
              className="p-5 pb-3 cursor-grab active:cursor-grabbing bg-slate-50/50 border-b border-slate-100"
              onMouseDown={(e) => {
                setIsDragging(true);
                dragStartPos.current = { x: e.clientX - position.x, y: e.clientY - position.y };
              }}
            >
              <h3 className="text-lg font-bold text-slate-800 mb-1 pointer-events-none">{activeForm.title}</h3>
              <p className="text-sm text-slate-600 pointer-events-none">{activeForm.description}</p>
            </div>
            <div className="p-5 pt-3">
              <div className="space-y-2 max-h-[35vh] overflow-y-auto custom-scrollbar pr-2">
                {activeForm.options.map((opt) => (
                  <label key={opt.id} className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${selectedOptions.has(opt.id) ? 'border-indigo-400 bg-indigo-50/50' : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'}`}>
                    <input 
                      type={activeForm.multi_select ? "checkbox" : "radio"} 
                      name="interactive_form_option"
                      className="mt-0.5 h-4 w-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-600 cursor-pointer"
                      checked={selectedOptions.has(opt.id)}
                      onChange={(e) => {
                        const newSet = new Set(selectedOptions);
                        if (activeForm.multi_select) {
                          if (e.target.checked) newSet.add(opt.id);
                          else newSet.delete(opt.id);
                        } else {
                          newSet.clear();
                          newSet.add(opt.id);
                        }
                        setSelectedOptions(newSet);
                      }}
                    />
                    <div>
                      <div className="font-semibold text-slate-800 text-[13px]">{opt.id}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{opt.label}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex justify-end gap-2">
              <button 
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
                onClick={() => setActiveForm(null)}
              >
                Dismiss
              </button>
              <button 
                className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50 disabled:hover:bg-indigo-600 shadow-sm"
                disabled={selectedOptions.size === 0 || isTyping}
                onClick={() => {

                  let responseText = `I select: ${Array.from(selectedOptions).join(', ')}`;
                  if (input.trim()) {
                    responseText += `\nAdditional instructions: ${input.trim()}`;
                    setInput('');
                  }
                  setActiveForm(null);
                  handleSend(responseText);
                }}
              >
                Confirm Selection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Input Area (Floating) */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 px-4 pointer-events-none z-10">
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
