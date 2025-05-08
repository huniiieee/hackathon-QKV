from langchain_community.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings  # HuggingFace 임베딩을 사용
from langchain_core.runnables import RunnableLambda
from langchain.prompts import PromptTemplate
import json
import os
import gradio as gr
from dotenv import load_dotenv
import ngrok
import httpx
import re
import ast
import asyncio

# .env 파일을 사용하여 API 키 로드
load_dotenv()  # 환경 변수 로드
with open("./keys/openai_key.txt", "r") as file:
    OPENAI_API_KEY = file.read().strip()

llm = ChatOpenAI(temperature=1.0, model='gpt-4o-mini', openai_api_key=OPENAI_API_KEY)

# HuggingFace 임베딩 정의 (모델 이름을 전달)
model_name = "all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=model_name)

# FAISS 벡터 DB 로드 (HuggingFace 임베딩 사용)
vector_db = FAISS.load_local("./vectorstore/blender_vector_db", embeddings, allow_dangerous_deserialization=True)


# blender 이미지, 모델 파일 경로
image_path = "C:/blender-mcp/image"
model_path = "C:/blender-mcp/model"

for folder_path in [image_path, model_path]:
    # 폴더가 존재하지 않으면 생성
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"폴더 '{folder_path}'가 생성되었습니다.")
    else:
        print(f"폴더 '{folder_path}'가 이미 존재합니다.")


# model 서버 경로
txt2img_url = "https://15d8-34-32-134-37.ngrok-free.app/image2text"
txt2obj_url = "https://8343-34-71-148-149.ngrok-free.app/generate"
img2txt_url = ""
mcp_url = "http://172.17.0.57:45432/run"


# LLM 응답 처리
async def response(message, history):  # 기본값을 빈 문자열로 설정

    # history_langchain_format을 사용하여 대화 기록을 저장
    history_langchain_format = []
    

    #============== R A G ==============

    ## step 1 - select fn_call
   
    # 질문과 retrieved_docs를 포함하는 템플릿 생성
    template = """
    You are a coder for Blender Python program.
    Analyze the question and respond with the appropriate `fn_call` that matches the request.
    The `fn_call` should be provided with no explanation or additional details, only the function name.

    question: {question},

    fn_call: [
        rag_normal(기본 도형을 가지고 모델을 만듭니다. 간단한 모델링에 적합합니다.),
        rag_del(모든 작업물을 삭제하고 초기화합니다.),
        rag_mesh(3d 오브젝트를 생성하여 적용합니다. 정교하고 복잡한 3d 오브젝트로 변경요청했을 때 적합합니다.),
        rag_texture(텍스쳐 이미지를 생성하고 적용합니다. 이미 모델을 만들고 있는 상황에서 사용자가 텍스쳐만 별도로 생성 요청했을 때 적합합니다.),
        
        nomal(블랜더 코드작성과 관련없는 질문입니다. 분류하기 어려우면 이 fn_call로 분류합니다.)
    ]

    answer:
    """
    # 

    # PromptTemplate을 사용하여 템플릿을 처리
    prompt_template = PromptTemplate(input_variables=["question"], template=template)

    # LLMChain 객체 생성
    step_1_llm_chain = LLMChain(llm=llm, prompt=prompt_template)

    # step_1_formatted_prompt 생성: 템플릿에서 사용할 변수를 전달하여 사용
    step_1_formatted_prompt = prompt_template.format(question=message)

    # LLMChain 실행
    fn_call = step_1_llm_chain.run(question=message)

    print(f"요청사항 : {message}, fn_call : {fn_call}")


    ## step 2 - run fn_call

    if "rag_nomal" in fn_call:
        # 벡터 DB에서 관련 정보 검색
        search_results = search_in_db(message, vector_db)

        # 검색된 정보를 시스템 프롬프트에 추가
        retrieved_docs = "\n".join([result.page_content for result in search_results]) 

        # 질문과 retrieved_docs를 포함하는 템플릿 생성
        template = """
        You are coder for Blender python program.
        question을 분석하고, 최적화된 blender python script를 제작하세요.
        object명칭은 각 모델링 요소에 맞게 정확한 명칭으로 제작해주세요.
        retrieved_docs는 Blender python script의 기술문서입니다. 참고하되 관련성이 없다면 무시해도 됩니다.
        question : {question},
        retrieved_docs : {retrieved_docs},
        answer:
        """

        # 시스템 프롬프트에 템플릿 적용
        formatted_prompt = template.format(question=message, retrieved_docs=retrieved_docs)

    elif "rag_del" in fn_call:
        template = """
        You are a coder for Blender Python program.
        question을 분석하여 이미 생성된 blender 모델에서 사용자가 원하는 부분을 삭제하는 script를 작성해주세요. 
        전체 삭제를 원할 경우 전체 모델을 삭제하는 코드를 작성해주세요.

        question: {question},

        answer:
        """

        formatted_prompt = template.format(question=message)

    elif "rag_texture" in fn_call:
        template = """
        당신은 Blender에서 오브젝트에 텍스처를 생성하는 text-to-image 모델을 위한 프롬프트를 만드는 프로그램입니다.
        사용자의 질문을 분석하고, 이를 바탕으로 파이썬 스크립트가 필요한 텍스처 파일명을 오브젝트 명에 맞게 연관 지어 생성하세요.
        각 파일명에 대해 최적화된 텍스처 프롬프트를 작성하되, 여러 개의 텍스처가 필요한 경우에는 파일명.png : 프롬프트 형태로 딕셔너리로 매칭시켜 주세요.
        최종 출력은 딕셔너리 형식이어야 하며, 그 외의 설명은 포함하지 마세요.

        ### 3D 텍스처 생성 원칙:
        - **재질 (Material)**: 텍스처의 기본 재질을 설정합니다. (예: 돌, 금속, 나무, 패브릭 등)
        - **분위기 (Style & Mood)**: 텍스처의 느낌을 설명합니다. (예: 어두운, 신비로운, 웅장한 등)
        - **색상 (Color Palette)**: 주요 색상 조합을 묘사합니다. (예: 어두운 회색, 금속적인 느낌)
        - **세부 표현 (Details)**: 표면 질감, 조명 효과, 해상도 등을 추가하여 텍스처의 특징을 설명합니다.
        - **최종 형식 (Output Format)**: text-to-image AI가 이해할 수 있도록, 텍스처에 대한 간결하고 자연스러운 설명을 제공합니다.

        ---

        **예시 (참고용)**:
        사용자 요청 : "create magic stone gate"
        가능한 프롬프트: "A mystical ancient stone gate texture, glowing runes, moss-covered surface, cinematic lighting."

        ---

        question: {question},

        answer:
        """
        
        # PromptTemplate을 사용하여 템플릿을 처리
        prompt_template = PromptTemplate(input_variables=["question"], template=template)

        # LLMChain 객체 생성
        step_2_llm_chain = LLMChain(llm=llm, prompt=prompt_template)

        # step_2_formatted_prompt 생성: 템플릿에서 사용할 변수를 전달하여 사용
        step_2_formatted_prompt = prompt_template.format(question=message)

        # LLMChain 실행
        texture_dict = step_2_llm_chain.run(question=message)

        print(f"txt2img 요청 : {texture_dict}")

        
        # 문자열에서 '{}' 부분만 추출
        start_index = texture_dict.find('{')  # 첫 번째 '{'의 인덱스
        end_index = texture_dict.rfind('}')  # 마지막 '}'의 인덱스

        if start_index != -1 and end_index != -1 and start_index < end_index:
            dict_str = texture_dict[start_index:end_index + 1]  # '{'와 '}' 사이의 문자열 추출
            try:
                # 추출한 문자열을 파이썬 딕셔너리로 변환
                texture_dict = ast.literal_eval(dict_str)
                print("추출된 딕셔너리:", texture_dict)
            except Exception as e:
                print(f"오류 발생: {e}")
        else:
            try:
                # 만약 텍스트가 이미 딕셔너리 형식이라면 그대로 처리
                texture_dict = ast.literal_eval(texture_dict)
                print("딕셔너리:", texture_dict)
            except Exception as e:
                print(f"문자열을 딕셔너리로 변환할 수 없습니다: {e}")

        # 딕셔너리 요소 가져오기
        first_key = list(texture_dict.keys())[0]
        first_value = texture_dict[first_key]

        data = {
            "prompt": first_value
        }

        save_path = os.path.join(image_path, first_key)
        response = await txt2img_request(txt2img_url, data, save_path)


        template = """
        You are coder for Blender python program.
        question을 분석하고, 최적화된 blender python script를 제작하세요.
        object명칭은 각 모델링 요소에 맞게 정확한 명칭으로 제작해주세요.
        텍스쳐 파일 경로의 파일명을 확인하여 오브젝트에 적합한 텍스쳐 이미지가 있다면 코드에 텍스쳐부분 경로를 적용해주세요.

        question : {question},
        texture path : {texture_path} 

        answer:
        """

        formatted_prompt = template.format(question=message, texture_path = save_path)

    elif "rag_mesh" in fn_call:

        template = """
        You are an expert coder for Blender Python scripts.

        Your goal is to analyze the user's question and generate an optimized Blender Python script that **creates geometry using mesh data directly**, instead of relying on primitive shapes like cubes, spheres, or cylinders.

        When appropriate, **manually define vertices, edges, and faces to construct complex or custom models** via `bpy.data.meshes.new()` and `from_pydata()`.

        Use precise object naming that matches the modeling elements and anatomical or functional intent.

        You may reference the retrieved_docs for Blender API details, but ignore unrelated information.

        If the user asks for a model resembling a real-world object (e.g. human, tree, robot), generate a mesh structure that reflects its geometry with realistic proportions—even in low-poly form—rather than assembling primitives.

        question: {question}

        answer:
        """


        formatted_prompt = template.format(question=message)



        '''

        template = """
        당신은 Blender에서 오브젝트 mesh를 생성하는 모델입니다.
        사용자의 질문을 분석하고, 이를 바탕으로 파이썬 스크립트가 필요한 mesh 오브젝트 명을 출력하세요.
        최종 출력은 오브젝트 이름이며, 그 외의 설명은 포함하지 마세요.

        question: {question},

        answer:
        """
        
        # PromptTemplate을 사용하여 템플릿을 처리
        prompt_template = PromptTemplate(input_variables=["question"], template=template)

        # LLMChain 객체 생성
        step_2_llm_chain = LLMChain(llm=llm, prompt=prompt_template)

        # step_2_formatted_prompt 생성: 템플릿에서 사용할 변수를 전달하여 사용
        step_2_formatted_prompt = prompt_template.format(question=message)

        # LLMChain 실행
        obj_name = step_2_llm_chain.run(question=message)

        print(f"txt2mesh 요청 : {obj_name}")
        
        save_path = os.path.join(model_path, obj_name)
        response = await obj_generate_request(txt2obj_url, obj_name, save_path)


        template = """
        You are coder for Blender python program.
        question을 분석하고, 최적화된 blender python script를 제작하세요.
        object는 obj_path를 참고하여 obj파일을 불러와서 스크립트에 넣어주세요.

        question : {question}
        obj_path : {obj_path} 

        answer:
        """


        formatted_prompt = template.format(question=message, obj_path = save_path)

        '''
        
    elif "rag_all" in fn_call:
        template = """
        You are a coder for Blender Python program.
        사용자가 요청한 기능은 아직 구현이 안되었습니다.
        다른 방식으로 구현해달라고 응답해주세요.
        
        question: {question},

        answer:
        """

        formatted_prompt = template.format(question=message)

    else:
        template = """
        You are a coder for Blender Python program.
        사용자의 질문에 대해 답변해주세요.
        질문이 코드 생성 요청인 경우 질문을 좀 더 구체적으로 할 수 있게 도와주세요.
        질문이 코드 생성 요청이 아닌 경우에도 질문에 대한 답변 해주세요.

        question: {question},

        answer:
        """

        formatted_prompt = template.format(question=message)




    #============== R A G ==============


    # 시스템 메시지에 추가된 템플릿 정보와 함께 업데이트
    history_langchain_format.append(SystemMessage(content=formatted_prompt))
    
    # 기존의 대화 기록을 처리
    for human, ai in history:
        history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))

    # 사용자 입력 메시지를 추가
    history_langchain_format.append(HumanMessage(content=message))

    # LLM을 호출하여 응답 생성
    gpt_response = llm(history_langchain_format)

    # MCP 서버 전송
    await send_final_prompt(gpt_response.content) 

    return gpt_response.content


def search_in_db(query, vector_db, k=5):
    """
    벡터 DB에서 관련 문서 검색
    """
    # HuggingFaceEmbeddings을 사용하여 쿼리 임베딩 생성
    query_embedding = embeddings.embed_query(query)
    
    # 벡터 DB에서 가장 관련성이 높은 k개의 문서 반환
    results = vector_db.similarity_search_by_vector(query_embedding, k)
    return results



# FastAPI 서버에 리퀘스트를 보내는 비동기 함수
async def txt2img_request(endpoint_url: str, data: dict, save_path: str):
    # 타임아웃 설정 (예: 60초로 설정)
    timeout = httpx.Timeout(60.0)  # 타임아웃을 60초로 설정

    async with httpx.AsyncClient(timeout=timeout) as client:
        # FastAPI 서버에 POST 요청을 보냄
        response = await client.post(endpoint_url, json=data)
        print(f"request 완료")

        # 비동기적으로 20초 대기
        await asyncio.sleep(20)
        print(f"timeout 20 완료")

        # 응답 상태 코드 확인
        if response.status_code == 200:
            print(f"response 완료")
            # 응답에서 이미지를 파일로 저장
            with open(save_path, 'wb') as f:
                f.write(response.content)  # 이미지를 로컬 파일로 저장
            print(f"이미지 저장 완료 : {save_path}")

            # 성공적인 응답 반환
            return {"message": "Image generated successfully", "image_path": save_path}




# 비동기 요청 함수
async def obj_generate_request(endpoint_url: str, object_name: str, save_path: str):
    data = {"object": object_name}
    timeout = httpx.Timeout(60.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(endpoint_url, json=data)
        print("🔁 요청 전송 완료")

        # 비동기 대기
        await asyncio.sleep(5)
        print("⏱️ 대기 완료")

        if response.status_code == 200:
            result = response.json()
            mesh_text = result.get("mesh", "")
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(mesh_text)
            
            print(f"✅ .obj 저장 완료: {save_path}")
            return {"message": "OBJ mesh generated", "file_path": save_path}
        else:
            print(f"❌ 오류 발생: {response.status_code} - {response.text}")
            return {"error": f"Request failed with status {response.status_code}"}



# 비동기 요청 함수 (최종 프롬프트 전송용)
async def send_final_prompt(prompt: str):
    url = mcp_url
    data = {"prompt": prompt}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            print("🔁 MCP 서버 프롬프트 전송 완료")

            if response.status_code == 200:
                result = response.json()
                print("✅ MCP 서버 응답 수신 완료 : ", result)
                return result
            else:
                print(f"❌ MCP 서버 오류 발생: {response.status_code} - {response.text}")
                return {"error": f"Request failed with status {response.status_code}"}
        except Exception as e:
            print(f"🚨 MCP 서버 예외 발생: {e}")
            return {"error": str(e)}

# 인터페이스 생성
gr.ChatInterface(
    fn=response,   # LLM 응답처리 콜백함수 설정
    textbox=gr.Textbox(placeholder="Talk", container=False, scale=7),
    chatbot=gr.Chatbot(height=500),
    title="Blender-MCP",
    theme="soft",
).launch(share=True)
