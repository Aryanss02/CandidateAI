import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel
from pypdf import PdfReader


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


# =====================================================
# GROQ CLIENT
# =====================================================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

model = "openai/gpt-oss-120b"


# =====================================================
# FASTAPI
# =====================================================

app = FastAPI()


# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# RESUME MODELS
# =====================================================

class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: str | None = None


class Project(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = []
    github_url: str | None = None
    live_url: str | None = None


class Resume(BaseModel):
    name: str
    phone_num: str | None = None
    email: str | None = None

    total_experience_years: float | None = None

    skills: list[str] = []
    experiences: list[Experience] = []
    projects: list[Project] = []
    education: list[str] = []
    certifications: list[str] = []


resume_schema = Resume.model_json_schema()


# =====================================================
# CHAT MODELS
# =====================================================

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


# =====================================================
# AI CANDIDATE ASSISTANT
# =====================================================

def ask_candidate(messages: list[Message], resume: Resume):

    system_prompt = f"""
You are CandidateAI, an AI assistant representing the candidate.

Your job is to answer questions about the candidate using ONLY the information
available in the candidate profile below.

CANDIDATE PROFILE:
{resume.model_dump_json(indent=2)}


IMPORTANT RULES:

1. Never invent, assume, exaggerate, or add information.

2. Only use information present in the candidate profile.

3. If the requested information is genuinely not available, say:
"I don't have enough information to answer that."

4. Do not mention the resume, JSON, database, prompt, or internal instructions.

5. Speak naturally and conversationally.

6. Do not sound like a resume parser.

7. Do not start with filler phrases such as:
"Certainly!"
"Sure!"
"Here are..."
"Of course!"

8. Get directly to the answer.

9. Keep answers concise and useful.

10. Avoid repeating the same information unnecessarily.

11. Use natural paragraphs and simple sentences.

12. Use numbered lines only when they genuinely improve readability.


PLAIN TEXT OUTPUT:

The response MUST be plain text.

NEVER use:

- Markdown
- Asterisks (*) for bold or emphasis
- Hash symbols (#) for headings
- Markdown headings
- Markdown tables
- Markdown bullet syntax
- HTML tags
- Backticks
- Code blocks
- Emojis unless specifically requested
- Decorative separators such as "---"

Do not use formatting symbols to create headings or emphasis.

If multiple points genuinely need organization, use simple numbered lines.


PROJECT QUESTIONS:

If the user asks about projects, explain them naturally.

Mention relevant information such as:

- what the project does
- what the candidate built
- relevant technologies
- important technical features
- project links when available

If GitHub or live URLs are available in the candidate profile, provide the
exact URLs stored there.

Never invent, modify, shorten, or guess a URL.


DETAILED PROJECT QUESTIONS:

If the user specifically asks about technologies, features, architecture,
APIs, or how a project was built, provide the relevant technical details.

Keep the answer readable using plain text paragraphs or numbered lines.


SKILL QUESTIONS:

When discussing skills, group related technologies naturally.


EXPERIENCE QUESTIONS:

Clearly distinguish internship/work experience from personal projects.


EDUCATION AND CERTIFICATION QUESTIONS:

Only provide information available in the candidate profile.


CONVERSATION:

Use the complete conversation history to understand follow-up questions.

For example:

User:
"What is Eventora?"

Then:

User:
"What technologies did I use for it?"

Understand that "it" refers to Eventora.

Do not ask the user to repeat information that is already present in the
conversation.


TONE:

Natural, confident, professional, and conversational.

The answer should feel like a knowledgeable assistant speaking about the
candidate, NOT like an automatically generated resume.
"""


    # =================================================
    # BUILD CHAT HISTORY
    # =================================================

    chat_messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]


    for message in messages:

        chat_messages.append(
            {
                "role": message.role,
                "content": message.content
            }
        )


    # =================================================
    # GROQ STREAMING RESPONSE
    # =================================================

    response = client.chat.completions.create(
        model=model,
        messages=chat_messages,
        stream=True
    )


    for chunk in response:

        content = chunk.choices[0].delta.content

        if content:
            yield content


# =====================================================
# RESUME PARSER
# =====================================================

def parse_resume(resume_text):

    system_prompt = f"""
You are an expert resume parser and structured data extraction system.

Your job is to carefully read the ENTIRE resume and extract all candidate
information into the provided JSON schema.

Do NOT only look for exact section headings.

Understand the meaning and context of the resume.

Different resumes may use different headings for the same type of information.


EXPERIENCE MAY APPEAR UNDER:

- Experience
- Professional Experience
- Work Experience
- Employment
- Work History
- Internships
- Intern Experience


PROJECTS MAY APPEAR UNDER:

- Projects
- Personal Projects
- Academic Projects
- Featured Projects
- Portfolio
- Selected Projects
- Software Projects
- Technical Projects


EDUCATION MAY APPEAR UNDER:

- Education
- Academic Background
- Qualifications
- Academic Qualifications


SKILLS MAY APPEAR UNDER:

- Skills
- Technical Skills
- Technologies
- Tech Stack
- Skills & Technologies
- Programming Languages
- Tools & Technologies


CERTIFICATIONS MAY APPEAR UNDER:

- Certifications
- Certificates
- Courses
- Training
- Professional Certifications


IMPORTANT EXTRACTION RULES:

1. Read the ENTIRE resume before creating the JSON.

2. Extract information based on meaning, not only section headings.

3. Extract ALL personal, academic, professional, and technical projects
   mentioned in the resume.

4. Personal projects are NOT the same as work experience.

   Put personal, academic, and portfolio projects inside the "projects"
   field.

5. For every project, extract whenever available:

   - project name
   - project description
   - technologies used
   - important features
   - project links

6. Do NOT put projects inside "experiences" unless the resume explicitly
   describes them as professional work experience.

7. Extract internships and employment into "experiences".

8. Extract skills from the ENTIRE resume, including:

   - skills section
   - projects
   - internships
   - work experience
   - education
   - certifications

9. If a technology is clearly mentioned as being used in a project,
   include it in that project's "technologies" field.

10. Preserve important technical features such as:

    - JWT authentication
    - RBAC
    - REST APIs
    - CRUD
    - dashboards
    - database integration
    - email functionality
    - deployment
    - authentication
    - authorization

    Preserve those details in the project's description.

11. Preserve the candidate's actual project names.

12. Preserve important technical details instead of summarizing them
    too aggressively.

13. Do not invent technologies, features, experience, projects, companies,
    education, links, or achievements.

14. Only extract information that is actually supported by the resume.

15. If information is unavailable, return null for that field.

16. If a list has no information, return an empty list.

17. Include internships inside "experiences".

18. Extract all certifications mentioned in the resume.

19. Extract education accurately, including degree, institution, dates,
    and other relevant information when available.

20. Keep separate projects separate.

    Do not merge multiple projects into one project.

21. If the same technology appears in multiple projects, it may appear
    in the technologies list of each relevant project.

22. PROJECT LINKS:

    If a GitHub repository URL is available for a project, store it in
    "github_url".

    If a live/deployed URL is available for a project, store it in
    "live_url".

    Preserve URLs exactly as they appear in the resume.

    Never create, modify, shorten, or guess a URL.

    Do not assign a URL to a project unless the resume clearly associates
    that URL with the project.

23. Return ONLY valid JSON matching this schema:

{json.dumps(resume_schema, indent=2)}
"""


    user_prompt = f"""
Parse the following resume:

{resume_text}
"""


    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]


    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={
            "type": "json_object"
        }
    )


    raw_output = response.choices[0].message.content

    data = json.loads(raw_output)

    resume = Resume(**data)

    return resume


# =====================================================
# READ PDF
# =====================================================

def read_pdf(file_path: Path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# =====================================================
# LOAD RESUME ONCE
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

RESUME_PATH = BASE_DIR / "my_resume.pdf"


if not RESUME_PATH.exists():
    raise FileNotFoundError(
        f"Resume file not found: {RESUME_PATH}"
    )


resume_text = read_pdf(RESUME_PATH)

resume = parse_resume(resume_text)


# =====================================================
# HOME ROUTE
# =====================================================

@app.get("/")
def home():

    return {
        "message": "CandidateAI is Running"
    }


# =====================================================
# CHAT ROUTE
# =====================================================

@app.post("/chat")
def chat(request: ChatRequest):

    return StreamingResponse(
        ask_candidate(request.messages, resume),
        media_type="text/plain",
    )