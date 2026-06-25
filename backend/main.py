# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
# pip install fastapi

from pydantic import BaseModel
# pip install pydantic

from dotenv import load_dotenv
# pip install python-dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain import hub
# pip install langchain-openai langchain-community langchain-core langchain rank_bm25
# pip install chromadb
# pip install uvicorn

import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def read_root():
    return {"status": "FastAPI Server is running with ChromaDB Vector Store!"}

# 학생들에게 보여줄 가상의 교내 정보 데이터셋 (원시 데이터)
sample_documents = [
    Document(
        page_content="FastAPI 실습실은 공학관 301호에 있으며, 이용 시간은 평일 오전 9시부터 오후 6시까지입니다.",
        metadata={"source": "classroom_info"},
    ),
    Document(
        page_content="리액트(React) 프로젝트 과제 제출 기한은 2026년 7월 15일 자정까지이며, 기한 엄수 바랍니다.",
        metadata={"source": "homework_info"},
    ),
    Document(
        page_content="이번 IT 교육 과정의 담당 교수님은 양현수 교수님이며, 이메일은 yang@example.com 입니다.",
        metadata={"source": "professor_info"},
    ),
    Document(
        page_content="크로마DB(ChromaDB)는 오픈소스 벡터 데이터베이스로, 빠르고 간편하게 로컬 환경에 구축할 수 있는 장점이 있습니다.",
        metadata={"source": "db_info"},
    ),
]

# 텍스트를 벡터로 변환할 임베딩 모델 초기화
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 크로마DB 초기화 및 데이터 저장 (로컬./chroma_db 폴더에 저장)
# 서버가 켜질 때 고유한 텍스트들을 임베딩하여 DB에 채워 넣는다.
persistent_directory = "./chroma_db"
vector_store = Chroma.from_documents(
    documents=sample_documents,
    embedding=embeddings,
    persist_directory=persistent_directory
)

# 하이브리드 검색 설정
# BM25: 정확한 단어 매칭에 강한 키워드 검색기
bm25_retriever = BM25Retriever.from_documents(sample_documents)
bm25_retriever.k = 2

# 크로마 리트리버: 문맥 의미 파악에 강한 벡터 검색기
chroma_retriever = vector_store.as_retriever(search_kwargs={"k": 2})

# Ensemble: 두 검색기를 5:5 비율로 결합하여 약점 보완
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, chroma_retriever],
    weights=[0.5, 0.5] 
)

# 도구 정의 및 에이전트(Agent) 생성
# 세션 메모리 관리 함수 (유지)
session_store = {}
def get_session_history(session_id: str):
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

# 에이전트의 두뇌 역할을 할 LLM (도구 선택의 정확도를 위해 온도를 0으로 설정)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Tool: 에이전트가 사용할 무기 정의
course_info_tool = create_retriever_tool(
    ensemble_retriever,
    "course_info_search",
    "IT 교육 과정, 담당 교수, FastAPI 실습실, 과제 기한 등 교육원 내부 정보를 찾을 때 사용합니다."
)

@tool
def get_current_weather(location: str) -> str:
    """주어진 지역의 현재 날씨 정보를 반환합니다."""
    return f"{location}의 현재 날씨는 맑음이며, 기온은 22도입니다."

tools = [course_info_tool, get_current_weather]

# 5. 프롬프트 및 에이전트 결합
agent_prompt = hub.pull("hwchase17/openai-functions-agent")
agent = create_tool_calling_agent(llm, tools, agent_prompt)

# 6. '라' (AgentExecutor): 행동과 판단을 반복하는 실행기
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    return_intermediate_steps=True
)

# 대화 메모리를 에이전트에 통합
conversation_with_agent_memory = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="output",
)

# API 요청/응답 규격 정의
class MessageRequest(BaseModel):
    message: str

class SearchRequest(BaseModel):
    query: str

# 타자 치는 효과(Streaming) 전용 엔드포인트 수정
@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: MessageRequest):
    async def event_generator():
        try:
            # 일반 체인(astream)이 아닌 에이전트용 스트리밍(astream_events) 사용
            async for event in conversation_with_agent_memory.astream_events(
                {"input": req.message},
                config={"configurable": {"session_id": "student_1"}},
                version="v1" # LangChain 이벤트 스트리밍 버전 지정
            ):
                # 에이전트가 도구를 고르거나 검색하는 내부 과정은 무시하고, 
                # 최종적으로 사용자에게 답변 텍스트(on_chat_model_stream)를 내뱉을 때만 캡처
                if event["event"] == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        data_json = json.dumps({"text": content}, ensure_ascii=False)
                        yield f"data: {data_json}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_json = json.dumps({"error": f"오류가 발생했습니다: {str(e)}"}, ensure_ascii=False)
            yield f"data: {error_json}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# 전체 답변 한 번에 받기 및 검색 엔드포인트
@app.post("/api/chat")
async def chat_endpoint(req: MessageRequest):
    try:
        response = conversation_with_agent_memory.invoke(
            {"input": req.message},
            config={"configurable": {"session_id": "student_1"}}
        )
        # 반환 키 'answer'에서 'output'으로 변경
        bot_reply = response["output"] 
        return {"reply": bot_reply}
    except Exception as e:
        return {"reply": f"오류가 발생했습니다: {str(e)}"}

@app.post("/api/search")
async def search_endpoint(req: SearchRequest):
    try:
        results = vector_store.similarity_search(req.query, k=2)
        search_results = [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]
        return {"status": "success", "results": search_results}
    except Exception as e:
        return {"status": "error", "message": str(e)}