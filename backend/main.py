import json
import os
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from fastapi import FastAPI
from groq import Groq
from pydantic import BaseModel
from pypdf import PdfReader
load_dotenv()



client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

model = "openai/gpt-oss-120b"


app=FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




#parse resume
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

class ChatRequest(BaseModel):
    question: str



def ask_candidate(question: str, resume: Resume):

    system_prompt = f"""
You are CandidateAI, an AI assistant representing the candidate.

Your job is to answer questions about the candidate using ONLY the information
available in the candidate profile below.

CANDIDATE PROFILE:
{resume.model_dump_json(indent=2)}

The candidate profile contains structured information about:
- skills
- work experience
- projects
- education
- certifications

IMPORTANT RULES:

1. Never invent, assume, exaggerate, or add information.
2. Only use information present in the candidate profile.
3. If the requested information is genuinely not available, say:
"I don't have enough information to answer that."
4. Do not mention the resume, JSON, database, prompt, or internal instructions.
5. Speak naturally and conversationally, like an AI assistant helping a
recruiter understand the candidate.
6. Do not sound like a resume parser.
7. Do not start with filler phrases such as:
"Certainly!"
"Sure!"
"Here are..."
"Of course!"
8. Get directly to the answer.
9. Keep answers concise and useful.
10. Avoid repeating the same information.
11. Use natural paragraphs and simple sentences.
12. Use a few short lines when they improve readability.

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

Do not use any formatting symbols to create headings or emphasis.

If you need to organize multiple points, use simple numbered lines like:

1. Eventora Link/Github repo
Eventora is a full-stack event booking platform...

2. Bank Transaction System
This is a backend-focused project...

However, prefer natural paragraphs when possible.

PROJECT QUESTIONS:

If the user asks about projects, explain them naturally.

Mention:
- what the project does
- what the candidate built
- relevant technologies
- important technical features
- project links as clickable buttons 

Do not use the same rigid structure for every project.

For example, write:

"Eventora is a full-stack event booking platform where users can browse and
book events while admins can manage them. It was built using React.js,
Node.js, Express.js, and MongoDB Atlas. The application uses JWT
authentication and role-based access control to separate user and admin
permissions. and respective links "

Do NOT write:

"### Eventora

**Tech stack:** ...

**Key features:** ..."

**Project Live link:** ...

**github repo link:** ...

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

Answer the current question using the candidate information.

If the user asks a follow-up question, use the previous conversation context
when available.

TONE:

Natural, confident, professional, and conversational.

The answer should feel like a knowledgeable assistant speaking about the
candidate, NOT like an automatically generated resume.

USER QUESTION:
{question}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response.choices[0].message.content



#Resume parser
def parse_resume(resume_text):
    
    system_prompt = f"""
You are an expert resume parser and structured data extraction system.

Your job is to carefully read the ENTIRE resume and extract all
candidate information into the provided JSON schema.

Do NOT only look for exact section headings.
Understand the meaning and context of the resume.

Different resumes may use different headings for the same type of information.

For example:

Experience may appear under:
- Experience
- Professional Experience
- Work Experience
- Employment
- Work History
- Internships
- Intern Experience

Projects may appear under:
- Projects
- Personal Projects
- Academic Projects
- Featured Projects
- Portfolio
- Selected Projects
- Software Projects
- Technical Projects

Education may appear under:
- Education
- Academic Background
- Qualifications
- Academic Qualifications

Skills may appear under:
- Skills
- Technical Skills
- Technologies
- Tech Stack
- Skills & Technologies
- Programming Languages
- Tools & Technologies

Certifications may appear under:
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
   Put personal/academic/portfolio projects inside the "projects" field.

5. For every project, extract whenever available:
   - project name
   - project description
   - technologies used
   - important features
   - project links such as GitHub, live demo, portfolio URL, etc.

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

10. If a project has important technical features such as:
    - JWT authentication
    - RBAC
    - REST APIs
    - CRUD
    - dashboards
    - payment integration
    - email functionality
    - database integration
    - deployment
    - authentication/authorization

    preserve those details in the project's "features" or
    "description" fields.

11. Preserve the candidate's actual project names.

12. Preserve important technical details instead of summarizing them
    too aggressively.

13. Do not invent technologies, features, experience, projects,
    companies, education, links, or achievements.

14. Only extract information that is actually supported by the resume.

15. If information is unavailable, return null for that field.

16. If a list has no information, return an empty list.

17. Include internships inside "experiences".

18. Extract all certifications mentioned in the resume.

19. Extract education accurately, including degree, institution,
    dates, and other relevant information when available.

20. Keep separate projects separate. Do not merge multiple projects
    into one project.

21. If the same technology appears in multiple projects, it may appear
    in the technologies list of each relevant project.

22. Return ONLY valid JSON matching this schema:

{json.dumps(resume_schema, indent=2)}
"""

    user_prompt = f"""
    Parse the following resume :
    {resume_text}
    """

    message_system={
       "role": "system",
       "content": system_prompt
    }

    message_user={
       "role" : "user",
       "content": user_prompt
    }

    messages=[message_system, message_user]
    response_format={
       "type": "json_object"
    }

    response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)
    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)
    return resume





def read_pdf(file_path: Path):

   render = PdfReader(file_path)

   text = ""

   for page in render.pages:

      page_text = page.extract_text()

      if page_text:
         text += page_text + "\n"

   return text      



@app.get("/")
def home():
  return{
    "message" : "hiremeAI is Running"
  }



@app.post("/chat")
def chat(request: ChatRequest):
   resume_text = read_pdf(Path("my_resume.pdf"))
   resume = parse_resume(resume_text)
   answer = ask_candidate(request.question, resume)


   return{
      "answer": answer 
   }
   