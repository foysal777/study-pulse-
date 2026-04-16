import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from students.models import AssessmentTemplate, AssessmentSection, AssessmentQuestion, AssessmentOption

class Command(BaseCommand):
    help = 'Import assessment questions from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The path to the JSON file containing the questions')

    def handle(self, *args, **kwargs):
        json_file_path = kwargs['json_file']

        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {json_file_path}"))
            return

        with open(json_file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"Invalid JSON Format: {e}"))
                return

        template_name = data.get("template_name")
        pass_percentage = data.get("pass_percentage", 70.0)
        sections_data = data.get("sections", [])

        if not template_name or not sections_data:
            self.stdout.write(self.style.ERROR("JSON must contain 'template_name' and 'sections'."))
            return

        try:
            with transaction.atomic():
                # Get or Create Template
                template, created = AssessmentTemplate.objects.get_or_create(
                    name=template_name,
                    defaults={'pass_percentage': pass_percentage}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created new Template: {template.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Using existing Template: {template.name}"))

                # Process Sections
                for seq_idx, sec_data in enumerate(sections_data, start=1):
                    skill = sec_data.get("skill")
                    title = sec_data.get("title", f"{skill.capitalize()} Section")
                    passage = sec_data.get("passage", "")
                    questions = sec_data.get("questions", [])

                    section, sec_created = AssessmentSection.objects.get_or_create(
                        template=template,
                        skill=skill,
                        defaults={'title': title, 'order': seq_idx, 'instructions': passage}
                    )
                    
                    self.stdout.write(f"  -> Processing Section: {title} ({len(questions)} questions)")

                    # Process Questions
                    for q_idx, q_data in enumerate(questions, start=1):
                        prompt = q_data.get("prompt")
                        q_type = q_data.get("type", "mcq")
                        options = q_data.get("options", [])
                        
                        question = AssessmentQuestion.objects.create(
                            section=section,
                            question_type=q_type,
                            prompt=prompt,
                            order=q_idx,
                            marks=1.00
                        )

                        # Create Options
                        for opt_idx, opt_data in enumerate(options, start=1):
                            AssessmentOption.objects.create(
                                question=question,
                                text=opt_data.get("text"),
                                is_correct=opt_data.get("is_correct", False),
                                order=opt_idx
                            )

            self.stdout.write(self.style.SUCCESS('Successfully imported all questions!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to import data: {str(e)}"))
