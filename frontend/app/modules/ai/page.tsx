"use client";
import { useState, useRef, useEffect } from 'react';
import Navbar from '../../../components/layout/Navbar';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { useAuth } from '../../../lib/auth-context';
import { useFarm } from '../../../lib/farm-context';
import { api } from '../../../lib/api-client';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Send, User, Mic, MicOff, Volume2, VolumeX, Trash2, Clock, Sparkles, Languages } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
  sources?: string[];
  confidence?: number;
  isStreaming?: boolean;
}

const SUGGESTIONS = {
  en: [
    "How can I improve my soil health?",
    "What irrigation method is most efficient?",
    "How does climate change affect my farm?",
    "How can I prevent soil erosion?",
    "How do carbon credits work?",
  ],
  fa: [
    "ع†ع¯ظˆظ†ظ‡ ط³ظ„ط§ظ…طھ ط®ط§ع©ظ… ط±ط§ ط¨ظ‡ط¨ظˆط¯ ط¯ظ‡ظ…طں",
    "ع©ط¯ط§ظ… ط±ظˆط´ ط¢ط¨غŒط§ط±غŒ ع©ط§ط±ط¢ظ…ط¯طھط± ط§ط³طھطں",
    "طھط؛غŒغŒط±ط§طھ ط§ظ‚ظ„غŒظ…غŒ ع†ع¯ظˆظ†ظ‡ ط¨ط± ظ…ط²ط±ط¹ظ‡ ظ…ظ† ط§ط«ط± ظ…غŒâ€Œع¯ط°ط§ط±ط¯طں",
    "ع†ع¯ظˆظ†ظ‡ ط§ط² ظپط±ط³ط§غŒط´ ط®ط§ع© ط¬ظ„ظˆع¯غŒط±غŒ ع©ظ†ظ…طں",
    "ط§ط¹طھط¨ط§ط±ط§طھ ع©ط±ط¨ظ† ع†ع¯ظˆظ†ظ‡ ع©ط§ط± ظ…غŒâ€Œع©ظ†ظ†ط¯طں",
  ],
};

export default function AIChatPage() {
  const { t, direction, language } = useI18n();
  const { colors } = useTheme();
  const { isAuthenticated } = useAuth();
  const { selectedFarm } = useFarm();
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'ai',
      content: language === 'fa' 
        ? 'ط³ظ„ط§ظ…! ظ…ظ† ط¯ط³طھغŒط§ط± ظ‡ظˆط´ظ…ظ†ط¯ ط§ع©ظˆ ظ†ظˆعکغŒظ† ظ‡ط³طھظ…. ط¯ط±ط¨ط§ط±ظ‡ ط®ط§ع©طŒ ط¢ط¨طŒ ط§ظ‚ظ„غŒظ…طŒ ظپط±ط³ط§غŒط´ ظˆ ع©ط±ط¨ظ† ط§ط² ظ…ظ† ط¨ظ¾ط±ط³غŒط¯.'
        : 'Hello! I'm Eco Nojin's AI assistant. Ask me about soil, water, climate, erosion, or carbon credits.',
      timestamp: new Date(),
      sources: [],
      confidence: 1.0,
    }
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [streamMode, setStreamMode] = useState<'sse' | 'ws'>('sse');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  
  const currentLang = language === 'fa' ? 'fa' : 'en';

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Voice recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = currentLang === 'fa' ? 'fa-IR' : 'en-US';
      
      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };
      
      recognitionRef.current.onerror = () => setIsListening(false);
      recognitionRef.current.onend = () => setIsListening(false);
    }
  }, [currentLang]);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition not supported in this browser');
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const speak = (text: string) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = currentLang === 'fa' ? 'fa-IR' : 'en-US';
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onstart = () => setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return;
    
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg: Message = {
      id: aiMsgId,
      role: 'ai',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    
    setMessages(prev => [...prev, userMsg, aiMsg]);
    const question = input.trim();
    setInput('');
    setIsStreaming(true);

    try {
      if (streamMode === 'sse') {
        // SSE streaming
        const token = localStorage.getItem('auth_token');
        const response = await fetch('http://127.0.0.1:8000/api/v1/ai/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            question,
            language: currentLang,
            farm_id: selectedFarm?.id,
          }),
        });
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        
        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('
');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.type === 'token') {
                    fullContent += data.content;
                    setMessages(prev => prev.map(m => 
                      m.id === aiMsgId ? { ...m, content: fullContent } : m
                    ));
                  } else if (data.type === 'complete') {
                    setMessages(prev => prev.map(m =>
                      m.id === aiMsgId ? {
                        ...m,
                        content: fullContent,
                        isStreaming: false,
                        sources: data.sources,
                        confidence: data.confidence,
                      } : m
                    ));
                  }
                } catch {}
              }
            }
          }
        }
      } else {
        // Fallback to regular API
        const res = await api.post<any>('/api/v1/ai/chat', {
          question,
          language: currentLang,
          farm_id: selectedFarm?.id,
        });
        if (res.success && res.data) {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId ? {
              ...m,
              content: res.data.answer,
              isStreaming: false,
              sources: res.data.sources,
              confidence: res.data.confidence,
            } : m
          ));
        }
      }
    } catch (e) {
      setMessages(prev => prev.map(m =>
        m.id === aiMsgId ? {
          ...m,
          content: 'Error: Could not connect to AI service',
          isStreaming: false,
        } : m
      ));
    }
    
    setIsStreaming(false);
  };

  const clearChat = () => {
    setMessages([messages[0]]);
  };

  const suggestions = SUGGESTIONS[currentLang] || SUGGESTIONS.en;

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 20px' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, #8b5cf6, #ec4899)`,
            padding: '32px', borderRadius: '24px', color: 'white',
            marginBottom: '24px', position: 'relative', overflow: 'hidden',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              width: '56px', height: '56px', borderRadius: '16px',
              background: 'rgba(255,255,255,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Bot size={32} />
            </div>
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                {t('module_ai')}
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                {selectedFarm 
                  ? `Chatting about ${selectedFarm.name}`
                  : 'Agricultural AI assistant with voice support'}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Chat Container */}
        <div style={{
          background: colors.cardBg,
          border: `1px solid ${colors.border}`,
          borderRadius: '20px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          height: 'calc(100vh - 280px)',
          minHeight: '500px',
        }}>
          {/* Messages */}
          <div style={{
            flex: 1, overflowY: 'auto', padding: '24px',
            display: 'flex', flexDirection: 'column', gap: '16px',
          }}>
            {messages.length === 1 && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '0.85rem', color: colors.textMuted, marginBottom: '12px' }}>
                  <Sparkles size={14} style={{ display: 'inline', marginRight: '6px' }} />
                  {currentLang === 'fa' ? 'ظ¾غŒط´ظ†ظ‡ط§ط¯ط§طھ:' : 'Try asking:'}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {suggestions.map((s, i) => (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                      onClick={() => { setInput(s); }}
                      style={{
                        padding: '8px 14px', borderRadius: '100px',
                        background: `${colors.primary}15`,
                        color: colors.primary,
                        border: `1px solid ${colors.primary}30`,
                        cursor: 'pointer', fontSize: '0.85rem',
                        fontFamily: 'inherit',
                      }}
                    >
                      {s}
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    display: 'flex',
                    gap: '12px',
                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                  }}
                >
                  {/* Avatar */}
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '50%',
                    background: msg.role === 'ai'
                      ? 'linear-gradient(135deg, #8b5cf6, #ec4899)'
                      : `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', flexShrink: 0,
                  }}>
                    {msg.role === 'ai' ? <Bot size={20} /> : <User size={20} />}
                  </div>

                  {/* Message bubble */}
                  <div style={{
                    maxWidth: '75%',
                    padding: '12px 16px',
                    borderRadius: '16px',
                    background: msg.role === 'ai' ? colors.bg : `${colors.primary}15`,
                    border: `1px solid ${msg.role === 'ai' ? colors.border : colors.primary + '30'}`,
                    color: colors.text,
                    lineHeight: 1.6,
                    fontSize: '0.95rem',
                  }}>
                    {msg.content.split('
').map((line, i) => (
                      <div key={i} style={{ marginBottom: '4px' }}>
                        {line.startsWith('**') && line.endsWith('**') ? (
                          <strong>{line.slice(2, -2)}</strong>
                        ) : line.startsWith('- ') ? (
                          <div style={{ paddingLeft: '12px' }}>â€¢ {line.slice(2)}</div>
                        ) : (
                          line || <br />
                        )}
                      </div>
                    ))}
                    
                    {msg.isStreaming && (
                      <span style={{
                        display: 'inline-block',
                        width: '8px', height: '16px',
                        background: colors.primary,
                        marginLeft: '2px',
                        animation: 'blink 1s infinite',
                      }} />
                    )}
                    
                    {/* Sources + actions */}
                    {!msg.isStreaming && msg.role === 'ai' && msg.content && (
                      <div style={{
                        marginTop: '10px', paddingTop: '10px',
                        borderTop: `1px solid ${colors.border}`,
                        display: 'flex', alignItems: 'center', gap: '8px',
                        fontSize: '0.75rem', color: colors.textMuted,
                      }}>
                        {msg.confidence !== undefined && (
                          <span>
                            {Math.round(msg.confidence * 100)}% match
                          </span>
                        )}
                        {msg.sources && msg.sources.length > 0 && (
                          <>
                            <span>â€¢</span>
                            <span>{msg.sources.join(', ')}</span>
                          </>
                        )}
                        <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
                          <button
                            onClick={() => speak(msg.content)}
                            style={{
                              background: 'none', border: 'none', cursor: 'pointer',
                              padding: '4px', borderRadius: '4px',
                              display: 'flex', alignItems: 'center',
                            }}
                            title="Read aloud"
                          >
                            <Volume2 size={14} color={colors.textMuted} />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div style={{
            padding: '16px 20px',
            borderTop: `1px solid ${colors.border}`,
            background: colors.cardBg,
          }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <motion.button
                whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
                onClick={toggleListening}
                style={{
                  width: '44px', height: '44px', borderRadius: '50%',
                  background: isListening ? colors.danger : `${colors.accent}20`,
                  border: isListening ? `2px solid ${colors.danger}` : `1px solid ${colors.border}`,
                  color: isListening ? 'white' : colors.accent,
                  cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
                title={isListening ? 'Stop listening' : 'Voice input'}
              >
                {isListening ? <MicOff size={18} /> : <Mic size={18} />}
              </motion.button>

              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder={currentLang === 'fa' ? 'ط³ظˆط§ظ„ ط®ظˆط¯ ط±ط§ ط¨ظ¾ط±ط³غŒط¯...' : 'Ask me anything about farming...'}
                disabled={isStreaming}
                style={{
                  flex: 1, padding: '12px 16px',
                  borderRadius: '12px',
                  border: `1px solid ${colors.border}`,
                  background: colors.bg,
                  color: colors.text,
                  fontFamily: 'inherit',
                  fontSize: '0.95rem',
                }}
              />

              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={sendMessage}
                disabled={isStreaming || !input.trim()}
                style={{
                  padding: '12px 20px',
                  background: isStreaming || !input.trim()
                    ? colors.textMuted
                    : `linear-gradient(135deg, #8b5cf6, #ec4899)`,
                  color: 'white', border: 'none',
                  borderRadius: '12px', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '6px',
                  fontFamily: 'inherit', fontWeight: '600',
                  boxShadow: isStreaming ? 'none' : '0 4px 12px rgba(139, 92, 246, 0.4)',
                }}
              >
                <Send size={16} />
                {isStreaming ? '...' : 'Send'}
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
                onClick={clearChat}
                style={{
                  width: '44px', height: '44px', borderRadius: '50%',
                  background: `${colors.textMuted}20`,
                  border: `1px solid ${colors.border}`,
                  color: colors.textMuted,
                  cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
                title="Clear chat"
              >
                <Trash2 size={16} />
              </motion.button>
            </div>

            {isListening && (
              <div style={{
                marginTop: '10px', padding: '8px 12px',
                background: `${colors.danger}15`,
                border: `1px solid ${colors.danger}30`,
                borderRadius: '8px',
                fontSize: '0.85rem', color: colors.danger,
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <div style={{
                  width: '8px', height: '8px', borderRadius: '50%',
                  background: colors.danger,
                  animation: 'blink 1s infinite',
                }} />
                Listening... speak now
              </div>
            )}

            {isSpeaking && (
              <div style={{
                marginTop: '10px', padding: '8px 12px',
                background: `${colors.accent}15`,
                border: `1px solid ${colors.accent}30`,
                borderRadius: '8px',
                fontSize: '0.85rem', color: colors.accent,
                display: 'flex', alignItems: 'center', gap: '8px',
                justifyContent: 'space-between',
              }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Volume2 size={14} />
                  Speaking...
                </span>
                <button onClick={stopSpeaking} style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: colors.accent, fontSize: '0.8rem',
                }}>
                  Stop
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Info footer */}
        <div style={{
          marginTop: '16px', padding: '12px 16px',
          background: colors.cardBg, borderRadius: '12px',
          border: `1px solid ${colors.border}`,
          fontSize: '0.8rem', color: colors.textMuted,
          display: 'flex', alignItems: 'center', gap: '12px',
          flexWrap: 'wrap',
        }}>
          <Sparkles size={14} color={colors.primary} />
          <span>AI powered by agricultural knowledge base</span>
          <span>â€¢</span>
          <span>Voice input/output via Web Speech API</span>
          <span>â€¢</span>
          <span>Streaming responses</span>
        </div>
      </div>

      <style jsx global>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>

      <Footer />
    </div>
  );
}
