from students.models import AssessmentQuestion

qs = AssessmentQuestion.objects.select_related('section').all()
count = 0
for q in qs:
    skill = q.section.skill
    changed = False
    if skill == 'reading' and q.question_type != 'passage':
        q.question_type = 'passage'
        changed = True
    elif skill == 'listening' and q.question_type != 'audio':
        q.question_type = 'audio'
        changed = True
    
    if changed:
        q.save()
        count += 1

print(f'Successfully updated {count} assessment questions to their correct types.')
