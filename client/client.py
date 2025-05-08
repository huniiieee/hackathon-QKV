from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

import os, sys, time, asyncio
from dotenv import load_dotenv

from google import genai
from google.genai import types
import json
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

load_dotenv()

# FastAPI 서버 인스턴스
app = FastAPI()

# 전역 객체
#client: Optional[genai.Client] = None
toolslist: Optional[list] = None

class PromptInput(BaseModel):
    prompt: str


gemini_api_key=""

client = genai.Client(api_key=gemini_api_key)

def is_python_code(prompt: str) -> bool:
    keywords = [
        "import ", "def ", "class ", "print(", "for ", "while ",
        "bpy.", "if __name__ == '__main__'", "from ", "lambda ",
        "#", "try:", "except", "async def", "await", "return "
    ]
    return any(kw in prompt for kw in keywords)

def rewrite_prompt(prompt: str) -> str:
        return f"""
        주어진 프롬프트를 확인하고 다음의 법칙을 들을 고려해.

        1. 프롬프트에 파이썬 코드가 포함되어잇다면, 파이썬 부분만 추출해서 'execute_blender_code' function_Call를 사용하는 것을 고려
        2. 블렌더에 뭔가 그려달라는 요청이면 너가 스스로 파이썬 코드를 만들어서 'execute_blender_code' function_Call를 사용하는 것을 고려
        3. 대화 맥락이 기록되지 않으니, 되묻지도 말고 실행할 부분이 있으면 실행
        4. 주어진 프롬프트는 다음과 같습니다:

        \"\"\"{prompt}\"\"\"
        """




# MCP 도구 목록 가져오기 (서버 시작 시 1회 실행)
async def get_mcp_tools_once():
    server_params = StdioServerParameters(command="uvx", args=["blender-mcp"])

    async with stdio_client(server=server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()

            tool_list = [
                types.Tool(
                    function_declarations=[{
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            k: v for k, v in tool.inputSchema.items()
                            if k not in ["additionalProperties", "$schema"]
                        },
                    }]
                )
                for tool in mcp_tools.tools
            ]
            for tool in mcp_tools.tools:
                print(f"🧰 Tool: {tool.name}")
                print(f"📄 Description: {tool.description}")
                print(f"🔧 Parameters: {tool.inputSchema}")
                print()
            return tool_list

# 서버 시작 시 Gemini client & MCP tool 등록
@app.on_event("startup")
async def setup_gemini_and_mcp():
    global client, toolslist
    print("🔌 MCP 도구 로딩 중...")
    toolslist = await get_mcp_tools_once()
    print("✅ 준비 완료.")

# 요청 처리
@app.post("/run")
async def run_mcp(prompt_data: PromptInput):
    global client, toolslist
    print("✅ 툴 목록 확인")
    
    prompt_data.prompt=rewrite_prompt(prompt_data.prompt)
    print(prompt_data.prompt)
    # Gemini에 프롬프트 전달
    response = client.models.generate_content(
        model="gemini-2.5-pro-exp-03-25",
        contents=prompt_data.prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            tools=toolslist
        )
    )
    


    # Gemini가 function_call을 반환한 경우
    if response.candidates[0].content.parts[0].function_call:
        fc = response.candidates[0].content.parts[0].function_call
        #print(f"🛠 Gemini가 선택한 도구: {fc.name} | 인자: {fc.args}")

        # MCP 서버 실행 후 도구 호출
        server_params = StdioServerParameters(command="uvx", args=["blender-mcp"])
        async with stdio_client(server=server_params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                result = await session.call_tool(fc.name, dict(fc.args))

                try:
                    data = json.loads(result.content[0].text)
                    return {"status": "ok", "tool": fc.name, "data": data}
                except:
                    return {"status": "ok", "tool": fc.name, "raw": result.content[0].text}

    else:
        #print(response.text)
        return {
            "status": "no_function_call",
            "message": response.text or "모델이 도구를 호출하지 않았습니다."
        }

# 서버 실행 (터미널에서 python server.py 실행)
if __name__ == "__main__":
    uvicorn.run("client:app", host="0.0.0.0", port=45432, reload=False)





# async def run():
#     # Blender MCP 서버를 subprocess로 실행
#     server_params = StdioServerParameters(
#         command="uvx",  # uvx 명령어로 실행
#         args=["blender-mcp"],  # MCP 도구 이름
#         env=None  # 필요한 경우 환경변수 지정 가능

#     # 클라이언트-서버 연결
#     async with stdio_client(server=server_params) as streams:
#         async with ClientSession(*streams) as session:
#             prompt = f"블렌더 상 도구를 지워줘"  # 사용자 질의 명령
#             await session.initialize()

#             mcp_tools = await session.list_tools()  # 도구 리스트 획득
#             tools = [
#                 types.Tool(
#                     function_declarations=[
#                         {
#                             "name": tool.name,
#                             "description": tool.description,
#                             "parameters": {
#                                 k: v
#                                 for k, v in tool.inputSchema.items()
#                                 if k not in ["additionalProperties", "$schema"]
#                             },
#                         }
#                     ]  # 해당 도구 함수 선언 생성
#                 )
#                 for tool in mcp_tools.tools
#             ]

#             response = client.models.generate_content(
#                 model="gemini-2.5-pro-exp-03-25",
#                 contents=prompt,
#                 config=types.GenerateContentConfig(
#                     temperature=0,
#                     tools=tools,
#                 ),  # LLM 모델에 프롬프트 전달.
#             )

#             if response.candidates[0].content.parts[0].function_call:
#                 function_call = response.candidates[0].content.parts[0].function_call # 함수호출정보

#                 result = await session.call_tool(
#                     function_call.name, arguments=dict(function_call.args)
#                 )  # 도구 함수 호출

#                 print("--- Formatted Result ---") # Add header for clarity
#                 try:
#                     flight_data = json.loads(result.content[0].text)
#                     print(json.dumps(flight_data, indent=2))
#                 except json.JSONDecodeError:
#                     print("MCP server returned non-JSON response:")
#                     print(result.content[0].text)
#                 except (IndexError, AttributeError):
#                      print("Unexpected result structure from MCP server:")
#                      print(result)
#             else:
#                 print("No function call was generated by the model.")
#                 if response.text:
#                      print("Model response:")
#                      print(response.text)



# if __name__ == "__main__":
#     asyncio.run(run())
