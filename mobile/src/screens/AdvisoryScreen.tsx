/** Advisory screen for React Native — chat-style AI advisory. */

import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useBilingual } from '../hooks/useBilingual';
import { fetchAdvice } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function AdvisoryScreen() {
  const { fa, lang } = useBilingual();
  const isFa = lang === 'fa';
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = useCallback(async () => {
    const q = input.trim();
    if (!q || q.length < 3) return;
    setLoading(true);
    setInput('');
    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: 'user', content: q, timestamp: new Date() }]);
    try {
      const result = await fetchAdvice(q);
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: 'assistant', content: result.answer ?? '', timestamp: new Date() },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: 'assistant', content: isFa ? 'خطا در دریافت مشاوره' : 'Error fetching advice', timestamp: new Date() },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, isFa]);

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.messagesContainer} contentContainerStyle={styles.messages}>
        {messages.length === 0 && (
          <View style={styles.emptyState}>
            <Ionicons name="chatbubble" size={48} color="#86868b" />
            <Text style={styles.emptyTitle}>{isFa ? 'سؤال کشاورزی خود را بپرسید' : 'Ask a farming question'}</Text>
          </View>
        )}
        {messages.map((msg) => (
          <View key={msg.id} style={[styles.message, msg.role === 'user' ? styles.userMessage : styles.assistantMessage]}>
            <Text style={styles.messageText}>{msg.content}</Text>
          </View>
        ))}
        {loading && (
          <View style={styles.assistantMessage}>
            <Text style={styles.messageText}>{isFa ? 'در حال تحلیل…' : 'Analyzing…'}</Text>
          </View>
        )}
      </ScrollView>
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder={isFa ? 'سؤال کشاورزی خود را بنویسید…' : 'Ask a farming question…'}
          placeholderTextColor="#86868b"
          onSubmitEditing={handleSend}
        />
        <TouchableOpacity style={styles.sendButton} onPress={handleSend} disabled={input.trim().length < 3 || loading}>
          <Ionicons name="send" size={20} color="#ffffff" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f7' },
  messagesContainer: { flex: 1 },
  messages: { padding: 16, paddingBottom: 80 },
  emptyState: { alignItems: 'center', paddingTop: 60 },
  emptyTitle: { fontSize: 14, color: '#86868b', marginTop: 12 },
  message: { maxWidth: '85%', padding: 12, borderRadius: 16, marginBottom: 8 },
  userMessage: { alignSelf: 'flex-end', backgroundColor: '#2d6a4f', borderBottomRightRadius: 4 },
  assistantMessage: { alignSelf: 'flex-start', backgroundColor: '#ffffff', borderBottomLeftRadius: 4 },
  messageText: { fontSize: 14, color: '#1d1d1f' },
  inputContainer: { flexDirection: 'row', padding: 12, backgroundColor: '#ffffff', borderTopWidth: 1, borderColor: '#e5e5e5' },
  input: { flex: 1, backgroundColor: '#f5f5f7', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: '#1d1d1f' },
  sendButton: { backgroundColor: '#0071e3', borderRadius: 20, padding: 10, marginLeft: 8, justifyContent: 'center' },
});
