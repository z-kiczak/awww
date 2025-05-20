from rest_framework import serializers
from .models import BackgroundImage, Route, Point

class PointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Point
        fields = ['id', 'x', 'y', 'order']
        read_only_fields = ['order'] 
    
    def validate_x(self, value):
        if value < 0:
            raise serializers.ValidationError("X must be >= 0")
        return value

    def validate_y(self, value):
        if value < 0:
            raise serializers.ValidationError("Y must be >= 0")
        return value

class RouteSerializer(serializers.ModelSerializer):
    points = PointSerializer(many=True, read_only=True)
    
    class Meta:
        model = Route
        fields = ['id', 'title', 'background', 'points']

class BackgroundImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackgroundImage
        fields = ['id', 'title', 'image']