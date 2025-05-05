# 🤖 OOO를 위한 XXX 에이전트

## 📌 개요
본 프로젝트는 OOO 문제를 해결하기 위해 AI 기반의 에이전트를 설계하고 구현한 것입니다.  
하루 해커톤 내에서 기획 → 설계 → 구현 → 테스트까지를 목표로 합니다.

## 🎯 목표
- [ ] 사용자 페인포인트 해결 (예: 업무 자동화, 콘텐츠 요약 등)
- [ ] LangChain 등 생성형 AI 기술 실전 적용
- [ ] 하루 만에 작동 가능한 데모 제작
- [ ] 팀 내 역할 분담 및 협업 구조 확립

## 👥 팀 구성

| 이름   | 역할                  | 주요 작업                             |
|--------|-----------------------|----------------------------------------|
| 조패캠 | 팀장, 기획 및 관리    | 기획서 작성, UX 설계, README 작성     |
| 홍길동 | 백엔드 개발           | LangChain 모듈 구현                    |
| 김철수 | 데이터 처리 및 모델링 | 데이터 전처리, 벡터 DB 구축            |
| 박영희 | 테스트 및 배포        | 성능 테스트, Streamlit 배포 구성       |

## 🧩 주요 기술 스택
- Python 3.10+
- LangChain
- OpenAI API
- FAISS / Chroma
- Streamlit
- Huggingface Transformers
- 기타: GitHub Copilot, Visily, Canva, Figma 등

## 🗂️ 폴더 구조

```
📦 프로젝트명/
├── 📁 docs/              # 기획서, 발표자료, 레퍼런스
├── 📁 data/              # 원천데이터, 전처리된 데이터
├── 📁 src/               # 실제 코드 (프론트/백엔드/모듈)
│   ├── app/             # 주요 모듈들 (예: main.py)
│   └── utils/           # 보조 함수, 공통 기능
├── 📁 model/             # 모델링 코드, 결과
├── 📁 tests/             # 테스트 코드
├── .gitignore
├── README.md
└── requirements.txt      # 설치 패키지
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

## 🧪 테스트 지표
- 정확도 (Accuracy)
- 응답 속도
- 정보 리드타임
- 업무 생산성 향상 여부 등

## 🧠 주요 기능 및 흐름
- 사용자 질문 → 벡터 DB 검색 → 응답 생성
- 외부 문서 PDF + RAG 구조 적용
- UX 흐름 설계: 입력 → 대화 → 결과 요약

---

## 🔗 참고 리소스
- [LangChain 문서](https://docs.langchain.com/)
- [Huggingface Hub](https://huggingface.co/)
- [OpenAI API 문서](https://platform.openai.com/docs)
- [arXiv 업로드 가이드](https://arxiv.org/help/submit)

---

## 📜 라이선스
본 프로젝트는 MIT 라이선스를 따릅니다. 자유롭게 사용하시되, 출처를 밝혀주세요.

---

## 🙏 감사의 말
이 프로젝트는 패스트캠퍼스 해커톤 실습 환경을 기반으로 설계되었습니다.  
또한 ChatGPT, GitHub Copilot 등 AI 도구의 도움을 받았습니다.
