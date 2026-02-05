from rest_framework import serializers


class OffsetLimitSerializer(serializers.Serializer):
    offset = serializers.IntegerField(required=False, min_value=0, default=0)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
