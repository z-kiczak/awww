from django import forms
from .models import Route, Point

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['title', 'background']
        labels = {
            'title': 'Nazwa trasy',
            'background': 'Obraz tła',
        }

class PointForm(forms.ModelForm):
    class Meta:
        model = Point
        fields = ['x', 'y']
        labels = {
            'x': 'Współrzędna X',
            'y': 'Współrzędna Y',
        }
        widgets = {
            'x': forms.NumberInput(attrs={'min': 0}),
            'y': forms.NumberInput(attrs={'min': 0}),
        }