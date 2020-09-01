from rest_framework import serializers

from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import UserProfileBaseSerializer


class UserProfileLastChangeInCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'full_name', 'last_change_in_catalog')


class ParentLastOnlineSerializer(serializers.ModelSerializer):
    children = UserProfileBaseSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'full_name', 'children', 'last_online')
