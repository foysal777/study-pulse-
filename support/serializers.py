from rest_framework import serializers
from support.models import Policy, HelpSupport


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ("id", "title", "content", "updated_at")


class HelpSupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupport
        fields = ("email", "phone_number", "updated_at")
