from rest_framework import serializers

from students.models import AssessmentTemplate, AssessmentSection, AssessmentQuestion, AssessmentOption, StudentAssessmentAttempt


class StudentProfileSetupUpsertSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    age = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=120)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    last_achieved_degree = serializers.CharField(max_length=255, required=False, allow_blank=True)
    parents_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    parents_phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    core_reasons_of_learning = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
    )
    preferred_study_time = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
    )
    preferred_study_mode = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
    )
    preferred_study_language = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
    )

    @staticmethod
    def _normalize_list(values):
        normalized = []
        seen = set()
        for item in values:
            value = str(item).strip()
            if not value:
                continue
            if value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    def validate_core_reasons_of_learning(self, value):
        return self._normalize_list(value)

    def validate_preferred_study_time(self, value):
        return self._normalize_list(value)

    def validate_preferred_study_mode(self, value):
        return self._normalize_list(value)

    def validate_preferred_study_language(self, value):
        return self._normalize_list(value)


class StudentProfileSetupDataSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone_number = serializers.CharField(allow_blank=True)
    age = serializers.IntegerField(allow_null=True)
    gender = serializers.CharField(allow_blank=True)
    last_achieved_degree = serializers.CharField(allow_blank=True)
    parents_name = serializers.CharField(allow_blank=True)
    parents_phone_number = serializers.CharField(allow_blank=True)
    core_reasons_of_learning = serializers.ListField(child=serializers.CharField())
    preferred_study_time = serializers.ListField(child=serializers.CharField())
    preferred_study_mode = serializers.ListField(child=serializers.CharField())
    preferred_study_language = serializers.ListField(child=serializers.CharField())
    core_reasons_options = serializers.ListField(child=serializers.CharField())
    interest_options = serializers.ListField(child=serializers.CharField())


class StudentProfileSetupSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = StudentProfileSetupDataSerializer()


class StudentErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.JSONField(required=False)


class StudentInterestOptionsDataSerializer(serializers.Serializer):
    interests = serializers.ListField(child=serializers.CharField())


class StudentInterestOptionsSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = StudentInterestOptionsDataSerializer()


class AssessmentOptionDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentOption
        fields = ["id", "text", "order"]


class AssessmentQuestionDisplaySerializer(serializers.ModelSerializer):
    options = AssessmentOptionDisplaySerializer(many=True, read_only=True)
    question_type = serializers.SerializerMethodField()

    def get_question_type(self, obj):
        skill = obj.section.skill
        if skill == "reading":
            return "passage"
        elif skill == "listening":
            return "audio"
        return obj.question_type

    class Meta:
        model = AssessmentQuestion
        fields = ["id", "question_type", "prompt", "audio_file", "max_listens", "transcript", "marks", "options"]


class AssessmentSectionDisplaySerializer(serializers.ModelSerializer):
    questions = AssessmentQuestionDisplaySerializer(many=True, read_only=True)
    
    class Meta:
        model = AssessmentSection
        fields = ["id", "title", "skill", "instructions", "weight", "questions"]


class AssessmentTemplateDisplaySerializer(serializers.ModelSerializer):
    sections = AssessmentSectionDisplaySerializer(many=True, read_only=True)
    
    class Meta:
        model = AssessmentTemplate
        fields = ["id", "name", "version", "pass_percentage", "sections"]


class AssessmentTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentTemplate
        fields = ["id", "name", "version", "pass_percentage"]


class AssessmentTemplateSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = AssessmentTemplateDisplaySerializer()


class AssessmentTemplateListSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = AssessmentTemplateListSerializer(many=True)


# ─── Exam Submit Serializers ───────────────────────────────────────────────────

class AnswerSubmitSerializer(serializers.Serializer):
    """Single answer: question id + selected option id (MCQ) or text."""
    question_id = serializers.IntegerField()
    selected_option_id = serializers.IntegerField(required=False, allow_null=True)
    text_answer = serializers.CharField(required=False, allow_blank=True, default="")


class ExamSubmitRequestSerializer(serializers.Serializer):
    answers = AnswerSubmitSerializer(many=True)


class SkillScoreSerializer(serializers.Serializer):
    skill = serializers.CharField()
    score = serializers.DecimalField(max_digits=8, decimal_places=2)
    max_score = serializers.DecimalField(max_digits=8, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class AssessmentResultDataSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    template_name = serializers.CharField()
    total_score = serializers.DecimalField(max_digits=8, decimal_places=2)
    max_total_score = serializers.DecimalField(max_digits=8, decimal_places=2)
    overall_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_passed = serializers.BooleanField()
    pass_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    mapped_level = serializers.CharField(allow_null=True)
    skill_scores = SkillScoreSerializer(many=True)


class AssessmentResultSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = AssessmentResultDataSerializer()
