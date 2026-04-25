"""
Management command: import_from_gdoc

Usage:
    python manage.py import_from_gdoc <google_doc_url>

Google Doc must be shared as "Anyone with the link can view".

Google Doc format:
------------------
[TEMPLATE]
Pre-Intermediate (A2)

[SECTION: grammar]

Question prompt here ____.
A) option1
B) correct option *
C) option3
D) option4

[SECTION: vocabulary]
...

Rules:
- Mark correct answer with * at the end: "B) correct answer *"
- Supported skills: grammar, vocabulary, listening, reading
- 3 or 4 options per question
- Leave a blank line between questions
"""

import re
import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import (
    AssessmentTemplate,
    AssessmentSection,
    AssessmentQuestion,
    AssessmentOption,
)


def _extract_doc_id(url: str) -> str | None:
    """Extract Google Doc ID from various URL formats."""
    patterns = [
        r"/document/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _fetch_doc_text(doc_id: str) -> str:
    """Download Google Doc as plain text."""
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    resp = requests.get(export_url, timeout=30)
    resp.raise_for_status()
    return resp.text


def _parse_doc(text: str) -> dict:
    """
    Parse plain-text Google Doc into the same dict structure
    that import_questions.py expects.
    """
    lines = [l.rstrip() for l in text.splitlines()]

    # ── Template name ─────────────────────────────────────────────────────────
    template_name = None
    for i, line in enumerate(lines):
        if re.match(r"\[TEMPLATE\]", line, re.IGNORECASE):
            # next non-empty line is the name
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    template_name = lines[j].strip()
                    break
            break

    if not template_name:
        raise ValueError(
            "Could not find [TEMPLATE] block. "
            "Make sure your doc starts with:\n[TEMPLATE]\nYour Level Name"
        )

    # ── Sections ──────────────────────────────────────────────────────────────
    # ── Sections ──────────────────────────────────────────────────────────────
    SKILL_PATTERN = re.compile(r"\[SECTION:\s*(grammar|vocabulary|listening|reading)\]", re.IGNORECASE)
    PASSAGE_PATTERN = re.compile(r"\[PASSAGE\]", re.IGNORECASE)
    OPTION_PATTERN = re.compile(r"^[A-Da-d][.)]\s+(.+?)(\s+\*\s*)?$")

    sections = []
    current_skill = None
    current_passage = []
    is_parsing_passage = False
    current_questions = []
    current_prompt_lines = []
    current_options = []

    def _flush_question():
        """Save the current question buffer."""
        if not current_prompt_lines:
            return
        prompt = "\n".join(current_prompt_lines).strip()
        if not prompt or not current_options:
            return
        
        q_type = "mcq"
        if current_skill == "reading":
            q_type = "passage"
        elif current_skill == "listening":
            q_type = "audio"

        current_questions.append({
            "prompt": prompt,
            "type": q_type,
            "options": list(current_options),
        })
        current_prompt_lines.clear()
        current_options.clear()

    def _flush_section():
        """Save the current section buffer."""
        if current_skill is None:
            return
        _flush_question()
        if current_questions:
            sections.append({
                "skill": current_skill.lower(),
                "title": f"{current_skill.capitalize()} Section",
                "passage": "\n".join(current_passage).strip(),
                "questions": list(current_questions),
            })
        current_questions.clear()
        current_passage.clear()

    for line in lines:
        # New section header
        m_skill = SKILL_PATTERN.match(line.strip())
        if m_skill:
            _flush_section()
            current_skill = m_skill.group(1).lower()
            current_prompt_lines.clear()
            current_options.clear()
            current_passage.clear()
            is_parsing_passage = False
            continue

        if current_skill is None:
            continue  # before first [SECTION:…]

        # Passage block
        if PASSAGE_PATTERN.match(line.strip()):
            is_parsing_passage = True
            continue
        
        if is_parsing_passage:
            # We assume passage ends when a question starts or a blank line followed by a question
            # But simpler: assume passage is everything until the first question prompt (which starts with a question)
            # Actually, let's look for MCQ options to detect when the passage ends.
            if OPTION_PATTERN.match(line.strip()):
                is_parsing_passage = False
                # The line before might have been the prompt
                if current_passage:
                    # Move the last non-empty line from passage to prompt
                    last_line = current_passage.pop()
                    while last_line.strip() == "" and current_passage:
                        last_line = current_passage.pop()
                    current_prompt_lines.append(last_line)
            else:
                current_passage.append(line)
                continue

        # Option line: A) … or A. …
        m_opt = OPTION_PATTERN.match(line.strip())
        if m_opt:
            opt_text = m_opt.group(1).strip()
            is_correct = bool(m_opt.group(2))  # trailing *
            current_options.append({"text": opt_text, "is_correct": is_correct})
            continue

        # Blank line → end of question
        if not line.strip():
            _flush_question()
            continue

        # Otherwise it's part of the question prompt
        current_prompt_lines.append(line.strip())

    # flush last section
    _flush_section()

    if not sections:
        raise ValueError(
            "No sections found. Make sure you have at least one [SECTION: grammar] block."
        )

    # Validate: each question must have exactly one correct answer
    errors = []
    for sec in sections:
        for i, q in enumerate(sec["questions"], 1):
            correct_count = sum(1 for o in q["options"] if o["is_correct"])
            if correct_count == 0:
                errors.append(
                    f"  [{sec['skill']}] Q{i}: \"{q['prompt'][:60]}\" — no correct answer marked (add *)"
                )
            elif correct_count > 1:
                errors.append(
                    f"  [{sec['skill']}] Q{i}: \"{q['prompt'][:60]}\" — multiple correct answers marked"
                )
    if errors:
        raise ValueError("Validation errors:\n" + "\n".join(errors))

    return {
        "template_name": template_name,
        "pass_percentage": 70.0,
        "sections": sections,
    }


class Command(BaseCommand):
    help = "Import assessment questions from a public Google Doc URL"

    def add_arguments(self, parser):
        parser.add_argument("gdoc_url", type=str, help="Public Google Doc URL")

    def handle(self, *args, **kwargs):
        url = kwargs["gdoc_url"]

        doc_id = _extract_doc_id(url)
        if not doc_id:
            self.stdout.write(self.style.ERROR("Could not extract Google Doc ID from URL."))
            return

        self.stdout.write(f"Fetching Google Doc (id={doc_id})…")
        try:
            text = _fetch_doc_text(doc_id)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Failed to fetch doc: {exc}"))
            self.stdout.write(
                "Make sure the doc is shared as 'Anyone with the link can view'."
            )
            return

        self.stdout.write("Parsing document…")
        try:
            data = _parse_doc(text)
        except ValueError as exc:
            self.stdout.write(self.style.ERROR(str(exc)))
            return

        template_name = data["template_name"]
        sections_data = data["sections"]
        pass_pct = data["pass_percentage"]

        self.stdout.write(
            f"Template: \"{template_name}\"  |  "
            f"Sections: {len(sections_data)}  |  "
            f"Pass: {pass_pct}%"
        )
        for s in sections_data:
            self.stdout.write(f"  [{s['skill']}] {len(s['questions'])} questions")

        try:
            with transaction.atomic():
                template, created = AssessmentTemplate.objects.get_or_create(
                    name=template_name,
                    defaults={"pass_percentage": pass_pct},
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created template: {template.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Using existing template: {template.name}"))

                for seq, sec_data in enumerate(sections_data, start=1):
                    skill = sec_data["skill"]
                    title = sec_data["title"]
                    passage = sec_data.get("passage", "")

                    section, _ = AssessmentSection.objects.get_or_create(
                        template=template,
                        skill=skill,
                        defaults={"title": title, "order": seq, "instructions": passage},
                    )

                    self.stdout.write(f"  → {title} ({len(sec_data['questions'])} questions)")

                    for q_idx, q_data in enumerate(sec_data["questions"], start=1):
                        question = AssessmentQuestion.objects.create(
                            section=section,
                            question_type=q_data["type"],
                            prompt=q_data["prompt"],
                            order=q_idx,
                            marks=1.00,
                        )
                        for opt_idx, opt in enumerate(q_data["options"], start=1):
                            AssessmentOption.objects.create(
                                question=question,
                                text=opt["text"],
                                is_correct=opt["is_correct"],
                                order=opt_idx,
                            )

            total_q = sum(len(s["questions"]) for s in sections_data)
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Done! Imported {total_q} questions into \"{template_name}\"."
                )
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Import failed: {exc}"))
