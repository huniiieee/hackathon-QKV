# 🤖 SceneForge AI: MCP, A Multimodal Agent for Generative 3D Art and Scripting in Blender 

## 📌 개요
사용자가 자연어로 입력한 3D 객체 생성 요청을 Blender 내에서 자동으로 구현해주는 AI 기반 모델링 지원 플랫폼입니다. 
본 시스템은 텍스트 명령을 실시간으로 분석하고, 해당 내용을 Blender에서 실행 가능한 Python 코드로 변환 및 실행함으로써, 
전문 지식 없이도 누구나 고급 3D 작업을 수행할 수 있도록 설계되었습니다.

```

## 🚀 실행 방법

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 실행

```bash
streamlit run src/app/main.py
```

> `.env` 파일이 필요한 경우 OpenAI API KEY 또는 기타 환경변수를 정의해두세요.

---

## 🔗 래퍼런스
 https://huggingface.co/Zhengyi/LLaMA-Mesh
 https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5
 https://github.com/ahujasid/blender-mcp
 https://docs.blender.org/api/current/index.html
 https://github.com/CompVis/stable-diffusion
 https://daddynkidsmakers.blogspot.com

---

## 📜 라이선스
본 프로젝트는 MIT 라이선스를 따릅니다. 자유롭게 사용하시되, 출처를 밝혀주세요.

