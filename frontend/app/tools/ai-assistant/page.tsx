// frontend/app/tools/ai-assistant/page.tsx
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Bot, MessageSquare, Sparkles, Loader2 } from 'lucide-react';

export default function AIAssistantToolsPage() {
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<{ prompt: string; response: string }[]>([]);

  if (!user) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            {t('common_please_log_in')}
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleAskQuestion = async () => {
    if (!prompt.trim() || !token) return;

    setIsLoading(true);
    try {
      // const res = await apiClient.post('/api/v1/ai/chat', { message: prompt });
      // const aiResponse = res.data.response;
      // Mock response for demonstration
      const aiResponse = `This is a simulated response from the AI for your query: "${prompt}". The actual backend API call is not made in this static example.`;
      
      setResponse(aiResponse);
      setHistory([{ prompt, response: aiResponse }, ...history]);
      setPrompt('');
    } catch (err) {
      console.error('Error calling AI API:', err);
      setResponse('Sorry, an error occurred while processing your request.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold mb-6">{t('ai_assistant_tools_title')}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                {t('ai_ask_question')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col space-y-4">
                <Textarea
                  placeholder={t('ai_prompt_placeholder')}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={4}
                  disabled={isLoading}
                />
                <Button onClick={handleAskQuestion} disabled={isLoading || !prompt.trim()}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {t('ai_processing')}
                    </>
                  ) : (
                    <>
                      <Bot className="mr-2 h-4 w-4" />
                      {t('ai_submit_query')}
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {response && (
            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-blue-500" />
                  {t('ai_response')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p>{response}</p>
              </CardContent>
            </Card>
          )}
        </div>

        <div>
          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <CardTitle>{t('ai_conversation_history')}</CardTitle>
            </CardHeader>
            <CardContent>
              {history.length > 0 ? (
                <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                  {history.map((item, index) => (
                    <div key={index} className="border-b pb-4 last:border-0 last:pb-0">
                      <p className="font-medium text-sm text-muted-foreground">{t('ai_you')}:</p>
                      <p className="mb-2">{item.prompt}</p>
                      <p className="font-medium text-sm text-muted-foreground">{t('ai_eco_nojin_ai')}:</p>
                      <p>{item.response}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">{t('ai_no_history')}</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}