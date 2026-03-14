"""
app/services/career_copilot.py
--------------------------------
AI Career Copilot — New Feature #3

An intelligent career mentor that answers career questions with
structured, actionable, step-by-step guidance.

Architecture:
  • A rich, curated knowledge base maps intent patterns → guidance.
  • Intent is detected via keyword matching (fast, offline, predictable).
  • Responses are templated but filled with contextual detail.
  • For questions outside the knowledge base, a graceful fallback
    provides general career coaching advice.

This runs entirely offline — no LLM API key required.
Swap _generate_response() for an OpenAI/Anthropic call if desired.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Knowledge base entry
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeEntry:
    keywords: frozenset[str]          # trigger words (any match → use this entry)
    title: str                        # response heading
    steps: list[str]                  # numbered guidance
    resources: list[str] = field(default_factory=list)
    pro_tip: str = ""


# ---------------------------------------------------------------------------
# Career knowledge base
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE: list[KnowledgeEntry] = [
    KnowledgeEntry(
        keywords=frozenset({"ai engineer", "machine learning engineer", "ml engineer", "ai"}),
        title="How to Become an AI / Machine Learning Engineer",
        steps=[
            "Master Python and its data stack: NumPy, Pandas, and Matplotlib.",
            "Learn core ML concepts: supervised / unsupervised learning, bias-variance trade-off, regularisation.",
            "Study deep learning with PyTorch or TensorFlow — start with CNNs and RNNs.",
            "Work through the fast.ai or DeepLearning.AI specialisation courses.",
            "Build 3-5 end-to-end projects (Kaggle competitions are ideal).",
            "Learn MLOps basics: model serving, Docker, and experiment tracking (MLflow).",
            "Contribute to open-source ML libraries to build credibility.",
            "Apply for ML internships or junior roles; target companies using AI in their core product.",
        ],
        resources=["fast.ai", "deeplearning.ai", "Papers With Code", "Kaggle"],
        pro_tip="Read at least 2 ML papers per week from arXiv to stay current.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"data scientist", "data science"}),
        title="How to Become a Data Scientist",
        steps=[
            "Build a strong statistics foundation: distributions, hypothesis testing, regression.",
            "Learn Python (Pandas, Scikit-Learn, Seaborn) or R.",
            "Master SQL — most data scientist roles require it daily.",
            "Study A/B testing and experimentation design.",
            "Practice storytelling with data using Tableau or Power BI.",
            "Complete the Google Data Analytics or IBM Data Science certificate.",
            "Build a portfolio of projects that tell a business story with data.",
            "Network in data science communities (Kaggle, Towards Data Science, LinkedIn).",
        ],
        resources=["Kaggle", "Mode Analytics", "StatQuest YouTube", "towards data science"],
        pro_tip="Focus on the 'so what?' — employers hire data scientists who can explain impact, not just run models.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"backend", "backend engineer", "api", "server-side"}),
        title="How to Become a Backend Engineer",
        steps=[
            "Pick a primary language: Python (FastAPI/Django), Go, or Java (Spring Boot).",
            "Learn REST API design principles and HTTP fundamentals.",
            "Master a relational database (PostgreSQL) and an ORM.",
            "Understand caching strategies (Redis), message queues (RabbitMQ/Kafka).",
            "Learn Docker and basic Kubernetes for containerised deployments.",
            "Study system design patterns: microservices vs monolith, CQRS, event sourcing.",
            "Practise on LeetCode (medium difficulty) and system design interviews.",
            "Build and deploy a production-grade API project.",
        ],
        resources=["System Design Primer (GitHub)", "Designing Data-Intensive Applications (book)", "FastAPI docs"],
        pro_tip="Read the 12-Factor App methodology — it's the gold standard for cloud-native backend services.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"frontend", "frontend engineer", "react", "web developer", "ui"}),
        title="How to Become a Frontend Engineer",
        steps=[
            "Master HTML, CSS, and vanilla JavaScript deeply before frameworks.",
            "Learn React (most in-demand) and TypeScript.",
            "Understand state management: Context API, Redux, or Zustand.",
            "Learn responsive design, accessibility (WCAG), and web performance.",
            "Study testing: Jest, React Testing Library, and Cypress.",
            "Build projects deploying to Vercel or Netlify.",
            "Learn basic REST API consumption and async patterns (fetch, Axios).",
            "Contribute to open-source React projects.",
        ],
        resources=["javascript.info", "react.dev", "css-tricks.com", "Frontend Masters"],
        pro_tip="A polished portfolio site is itself your best frontend project — make it exceptional.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"devops", "sre", "infrastructure", "cloud", "kubernetes", "docker"}),
        title="How to Become a DevOps / SRE Engineer",
        steps=[
            "Get comfortable with Linux command line and bash scripting.",
            "Master Docker, then Kubernetes (get the CKA certificate).",
            "Learn one cloud provider deeply: AWS, GCP, or Azure.",
            "Implement CI/CD pipelines using GitHub Actions or Jenkins.",
            "Study infrastructure-as-code: Terraform and Ansible.",
            "Learn observability: Prometheus, Grafana, and distributed tracing.",
            "Understand SRE principles: SLOs, SLAs, error budgets, and incident management.",
            "Automate everything — if you do it twice, script it.",
        ],
        resources=["Google SRE Book (free online)", "A Cloud Guru", "KodeKloud", "Linux Foundation"],
        pro_tip="Get AWS Solutions Architect Associate certified — it's the most recognised cloud cert globally.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"switch career", "career change", "transition", "change field"}),
        title="How to Successfully Switch Tech Careers",
        steps=[
            "Identify transferable skills from your current role.",
            "Research which target role has the lowest skill gap from your current position.",
            "Dedicate 1-2 hours daily to structured learning (courses, books, projects).",
            "Build a portfolio of 3 projects in the target field before applying.",
            "Network actively: attend meetups, join Discord communities, engage on LinkedIn.",
            "Apply for bridge roles (e.g. a marketer moving to product management).",
            "Be transparent in interviews about your transition — frame it as a strength.",
            "Give yourself a 6-18 month realistic timeline; consistent effort beats intensity.",
        ],
        pro_tip="Leverage your domain expertise — a healthcare professional moving to health-tech AI has a unique edge.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"salary", "negotiate", "raise", "compensation", "pay"}),
        title="How to Negotiate a Higher Salary in Tech",
        steps=[
            "Research market rates on Glassdoor, Levels.fyi, and LinkedIn Salary.",
            "Know your 'walk-away' number before any negotiation begins.",
            "Always negotiate — 85% of employers expect it.",
            "Anchor high: your first number should be 15-20% above your target.",
            "Use total compensation framing: base, equity, bonus, PTO, remote flexibility.",
            "Back your ask with data: market rates + your specific impact and achievements.",
            "Practise the negotiation conversation out loud at least 5 times.",
            "Get every offer in writing before resigning from your current role.",
        ],
        pro_tip="Levels.fyi is the most reliable compensation benchmark for tech roles globally.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"interview", "coding interview", "technical interview", "leetcode"}),
        title="How to Crack Technical / Coding Interviews",
        steps=[
            "Study core data structures: arrays, linked lists, trees, graphs, heaps, tries.",
            "Master the top algorithms: BFS/DFS, binary search, two pointers, sliding window, DP.",
            "Solve 150-200 LeetCode problems (focus on Medium; avoid grinding Easy).",
            "Practise system design with Grokking System Design or the System Design Primer.",
            "Do mock interviews with peers or on platforms like Pramp or interviewing.io.",
            "Use the STAR method for behavioural questions.",
            "Learn Big-O notation well — every solution needs complexity analysis.",
            "Apply early and often — interviewing is a skill that requires repetition.",
        ],
        resources=["LeetCode", "NeetCode.io", "Grokking the Coding Interview", "interviewing.io"],
        pro_tip="Solve the same problem multiple times — pattern recognition matters more than memorisation.",
    ),
    KnowledgeEntry(
        keywords=frozenset({"remote", "remote work", "work from home", "freelance"}),
        title="How to Land and Thrive in a Remote Tech Role",
        steps=[
            "Build async communication skills — most remote teams live in writing.",
            "Create a public portfolio: GitHub, blog, or YouTube — remote hiring is portfolio-driven.",
            "Apply on remote-first job boards: Remote.co, We Work Remotely, Remotive.",
            "Show timezone overlap willingness in applications.",
            "Set up a professional home office setup for video interviews.",
            "Develop strong project management habits: Notion, Trello, or Linear.",
            "Build your personal brand on LinkedIn — remote visibility matters.",
            "Aim for companies that are remote-first, not remote-tolerated.",
        ],
        resources=["Remote.co", "We Work Remotely", "Remotive.io", "Loom (async video)"],
        pro_tip="Your GitHub contribution graph is your remote resume — keep it consistently green.",
    ),
]

# Fallback for unrecognised questions
FALLBACK_RESPONSE = {
    "answer": (
        "That's a great career question! Here's a universal framework for career growth in tech:\n\n"
        "1. Identify your target role and research the exact skills required.\n"
        "2. Audit your current skill set and quantify the gap.\n"
        "3. Build a 90-day learning plan with concrete milestones.\n"
        "4. Create public work: GitHub projects, blog posts, or talks.\n"
        "5. Network intentionally — most tech jobs are never publicly posted.\n"
        "6. Apply consistently and treat each rejection as diagnostic data.\n"
        "7. Negotiate every offer — compensation compounds over time.\n\n"
        "For a more specific answer, try asking about a particular role "
        "(e.g. 'How do I become an AI engineer?') or topic "
        "(e.g. 'How do I negotiate my salary?')."
    ),
    "topic": "General Career Guidance",
    "resources": ["LinkedIn Learning", "Coursera", "freeCodeCamp", "GitHub"],
    "confidence": "general",
}


class CareerCopilotService:
    """Answers career questions with structured, step-by-step mentorship."""

    def answer(self, question: str) -> dict:
        question_clean = question.strip().lower()
        logger.info("Career copilot question: %s", question[:120])

        entry = self._find_best_match(question_clean)

        if entry is None:
            logger.debug("No specific match found — using fallback response")
            return FALLBACK_RESPONSE

        response_text = self._format_response(entry)
        return {
            "answer": response_text,
            "topic": entry.title,
            "resources": entry.resources,
            "confidence": "high",
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _find_best_match(text: str) -> KnowledgeEntry | None:
        """Return the KnowledgeEntry whose keywords best match the question."""
        best_entry: KnowledgeEntry | None = None
        best_score = 0

        for entry in KNOWLEDGE_BASE:
            score = sum(1 for kw in entry.keywords if kw in text)
            if score > best_score:
                best_score = score
                best_entry = entry

        return best_entry if best_score > 0 else None

    @staticmethod
    def _format_response(entry: KnowledgeEntry) -> str:
        lines = [f"**{entry.title}**\n"]
        for i, step in enumerate(entry.steps, 1):
            lines.append(f"{i}. {step}")

        if entry.pro_tip:
            lines.append(f"\n💡 Pro Tip: {entry.pro_tip}")

        if entry.resources:
            lines.append(f"\n📚 Resources: {', '.join(entry.resources)}")

        return "\n".join(lines)
