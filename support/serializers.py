from rest_framework import serializers
from support.models import Policy, HelpSupport, PlayStoreQRCode



class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ("id", "title", "content", "updated_at")


class HelpSupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpSupport
        fields = ("email", "phone_number", "updated_at")


class PlayStoreQRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayStoreQRCode
        fields = ("id", "pdf_file", "uploaded_at", "updated_at")

