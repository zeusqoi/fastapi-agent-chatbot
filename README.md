### FastAPI Agent Chatbot
FastAPI와 React를 활용한 LangChain Agent · Hybrid RAG 기반 AI 챗봇 실습 프로젝트

### 프로젝트 소개
백엔드는 FastAPI를 사용하여 REST API 서버를 구축하고, 프론트엔드는 React(Vite)를 사용하여 사용자 인터페이스를 구현하였다. OpenAI API와 LangChain Agent를 활용하여 사용자의 질문을 분석한 뒤, 적절한 도구(Tool)를 스스로 선택하여 답변을 생성하도록 구성하였다.

문서 검색에는 ChromaDB 벡터 검색과 BM25 키워드 검색을 결합한 Hybrid RAG 방식을 적용하였다. 또한 Conversation Memory를 통해 이전 대화 내용을 유지하며, Streaming Response를 적용하여 답변이 생성되는 과정을 실시간으로 확인할 수 있다. 이를 통해 Agent 기반 LLM 서비스와 Hybrid RAG의 동작 원리를 학습할 수 있다.

### 기술 스택
#### Backend
- Python
- FastAPI
- LangChain
- OpenAI API
- ChromaDB
- BM25 Retriever
- Ensemble Retriever
- OpenAI Embeddings
- Python-dotenv

#### Frontend
- React
- Vite
- JavaScript
- CSS

### 실행 방법
#### Backend
```bash
cd backend
uvicorn main:app --reload --port 8080
```

#### Frontend
```bash
cd frontend/product-app
npm install
npm run dev -- --port 3000
```

### 주요 기능
#### AI Agent 챗봇
- OpenAI API 기반 자연어 대화
- LangChain Agent를 활용한 Tool Calling
- Conversation Memory를 통한 대화 기록 유지
- FastAPI REST API 기반 채팅 서비스

#### Hybrid RAG 검색
- OpenAI Embedding 기반 벡터 검색
- ChromaDB Vector Store 활용
- BM25 키워드 검색 적용
- Ensemble Retriever를 통한 Hybrid Search
- 질문과 가장 관련성이 높은 문서 검색

#### Tool Calling
- 질문의 의도를 분석하여 적절한 도구 자동 선택
- 교내 정보 검색 도구(Retriever Tool)
- 날씨 조회 Tool 예제 제공
* Agent 기반 다중 도구 활용

#### Streaming Response
- Server-Sent Events(SSE) 기반 실시간 응답
- 답변 생성 과정을 순차적으로 출력
- 에이전트의 검색 및 응답 과정을 사용자에게 자연스럽게 제공

#### 프론트엔드
- React 기반 사용자 인터페이스
- 실시간 스트리밍 채팅
- Agent 상태(검색 중, 답변 생성 중) 표시
- Markdown 기반 답변 출력
- FastAPI API 연동

### 프로젝트 구조
```text
fastapi-agent-chatbot
├── backend
│   ├── main.py
│   └── requirements.txt
│
└── frontend
    └── product-app
        ├── src
        │   ├── App.jsx
        │   └── App.css
        └── package.json
```

### 프로젝트 목적
- FastAPI를 활용한 REST API 개발 학습
- React 기반 프론트엔드 구현
- OpenAI API를 활용한 LLM 서비스 개발
- LangChain Agent 활용 방법 학습
- Tool Calling 및 Agent 구조 이해
- ChromaDB 벡터 데이터베이스 활용
- BM25와 벡터 검색을 결합한 Hybrid RAG 이해
- Streaming Response 구현 학습
- 백엔드와 프론트엔드 연동 학습
