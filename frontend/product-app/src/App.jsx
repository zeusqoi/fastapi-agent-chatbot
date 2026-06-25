// App.jsx

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  // 단순 로딩이 아니라 에이전트의 상태를 세분화하여 저장
  const [agentStatus, setAgentStatus] = useState('idle'); // idle | thinking | typing
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || agentStatus !== 'idle') return;

    const userMessage = input;
    setInput('');
    
    // 사용자 메시지 추가 및 AI 답변 대기열 생성
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: '' },
    ]);
    
    // 에이전트가 도구를 고르고 검색하는 '생각 중' 상태로 전환
    setAgentStatus('thinking');

    try {
      const response = await fetch('http://localhost:8080/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.body) throw new Error('스트리밍을 지원하지 않는 브라우저입니다.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botReply = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            
            if (dataStr === '[DONE]') {
              break; 
            }

            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                
                if (parsed.error) {
                  botReply += `\n**[오류 발생]** ${parsed.error}`;
                } else if (parsed.text) {
                  // 첫 번째 글자가 도착하면 '타이핑 중' 상태로 전환
                  if (agentStatus !== 'typing') setAgentStatus('typing');
                  botReply += parsed.text;
                }

                setMessages((prev) => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1].content = botReply;
                  return newMessages;
                });
              } catch (err) {
                console.error('JSON 파싱 에러:', err, dataStr);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('통신 에러:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '서버와 연결할 수 없습니다.' }
      ]);
    } finally {
      setAgentStatus('idle'); // 모든 작업 완료 후 대기 상태로 복귀
    }
  };

  return (
    <div className="chat-container" style={{ maxWidth: '800px', margin: '0 auto', height: '100vh', display: 'flex', flexDirection: 'column', fontFamily: 'sans-serif' }}>
      
      {/* 헤더 영역 */}
      <header style={{ padding: '20px', backgroundColor: '#282c3425', color: 'white', textAlign: 'center' }}>
        <h2 style={{ margin: 0 }}>자율 에이전트 RAG 도우미</h2>
        <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#aaa' }}>알아서 도구를 선택하고 답변합니다.</p>
      </header>

      {/* 대화창 영역 */}
      <div className="chat-box" style={{ flex: 1, padding: '20px', overflowY: 'auto', backgroundColor: '#f0f2f5' }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#888', marginTop: '50px' }}>
            궁금한 내용을 물어보세요! 날씨를 묻거나 실습실 위치를 물어보면 에이전트가 스스로 도구를 판단합니다.
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: '20px'
            }}>
              <div style={{
                maxWidth: '75%',
                padding: '12px 18px',
                borderRadius: '15px',
                backgroundColor: msg.role === 'user' ? '#0084ff' : '#ffffff',
                color: msg.role === 'user' ? '#fff' : '#333',
                boxShadow: '0 2px 5px rgba(0,0,0,0.05)',
                lineHeight: '1.6',
                fontSize: '15px'
              }}>
                {msg.role === 'user' ? (
                  msg.content
                ) : (
                  msg.content === '' && agentStatus === 'thinking' ? (
                    <span style={{ color: '#888', fontStyle: 'italic' }}>
                      🔍 에이전트가 질문을 분석하고 적절한 도구를 검색 중입니다.
                    </span>
                  ) : (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  )
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 폼 영역 */}
      <form onSubmit={sendMessage} style={{ display: 'flex', padding: '20px', backgroundColor: '#fff', borderTop: '1px solid #ddd' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={agentStatus !== 'idle'}
          placeholder={
            agentStatus === 'thinking' ? '에이전트가 판단 중입니다.' : 
            agentStatus === 'typing' ? '답변을 작성하는 중입니다.' : '메시지를 입력하세요.'
          }
          style={{ flex: 1, padding: '15px', borderRadius: '10px', border: '1px solid #ccc', marginRight: '10px', fontSize: '16px', outline: 'none' }}
        />
        <button 
          type="submit" 
          disabled={agentStatus !== 'idle' || !input.trim()}
          style={{ padding: '0 25px', borderRadius: '10px', border: 'none', backgroundColor: agentStatus !== 'idle' ? '#ccc' : '#0084ff', color: '#fff', fontSize: '16px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          전송
        </button>
      </form>
    </div>
  );
}

export default App;