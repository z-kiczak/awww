from PIL import Image, ImageDraw
from io import BytesIO
import base64
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BackgroundImage, Route, Point
from .forms import RouteForm, PointForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import RouteSerializer, PointSerializer

def home(request):
    return render(request, 'routes/home.html')

@login_required
def route_list(request):
    routes = Route.objects.filter(user=request.user)
    return render(request, 'routes/route_list.html', {'routes': routes})

@login_required
def route_create(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            route.user = request.user
            route.save()
            return redirect('route_detail', pk=route.pk)
    else:
        form = RouteForm()
    return render(request, 'routes/route_form.html', {'form': form})

    
def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk, user=request.user)
    img_str = None
    
    try:
        # Use file storage API
        with route.background.image.open() as img_file:
            # Open background image
            bg_image = Image.open(route.background.image.path)
            draw = ImageDraw.Draw(bg_image)
            
            # Draw points and lines
            points = list(route.points.all().order_by('order'))
            for i, point in enumerate(points):
                # Draw point
                draw.ellipse([(point.x-5, point.y-5), (point.x+5, point.y+5)], fill='red')
                
                # Draw line to previous point
                if i > 0:
                    prev_point = points[i-1]
                    draw.line([(prev_point.x, prev_point.y), (point.x, point.y)], fill='blue', width=3)
            
            # Convert to base64 for HTML
            buffered = BytesIO()
            bg_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
    except (FileNotFoundError, IOError, ValueError) as e:
        print(f"Error processing image: {e}")
    
    return render(request, 'routes/route_detail.html', {
        'route': route,
        'route_image': img_str,
        'points': points if 'points' in locals() else []
    })


@login_required
def add_point(request, pk):
    route = get_object_or_404(Route, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PointForm(request.POST)
        if form.is_valid():
            point = form.save(commit=False)
            point.route = route
            
            last_point = route.points.last()
            point.order = last_point.order + 1 if last_point else 0
            point.save()
            return redirect('route_detail', pk=route.pk)
    else:
        form = PointForm()
    return render(request, 'routes/point_form.html', {'form': form, 'route': route})

@login_required
def delete_point(request, route_pk, point_pk):
    route = get_object_or_404(Route, pk=route_pk, user=request.user)
    point = get_object_or_404(Point, pk=point_pk, route=route)
    if request.method == 'POST':
        point.delete()
        return redirect('route_detail', pk=route.pk)
    return render(request, 'routes/point_confirm_delete.html', {'point': point})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

class RouteViewSet(viewsets.ModelViewSet):
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Tylko trasy zalogowanego użytkownika
        return Route.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatyczne przypisanie użytkownika przy tworzeniu
        serializer.save(user=self.request.user)
    
    def get_object(self):
        # Get the object and verify ownership
        obj = super().get_object()
        if obj.user != self.request.user:
            raise Http404
        return obj



class PointViewSet(viewsets.ModelViewSet):
    serializer_class = PointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # First verify the parent route exists and belongs to user
        try:
            Route.objects.get(
                pk=self.kwargs['route_pk'],
                user=self.request.user
            )
        except Route.DoesNotExist:
            raise Http404
        
        return Point.objects.filter(
            route_id=self.kwargs['route_pk']
    )
    def perform_create(self, serializer):
        # Automatycznie przypisujemy punkt do trasy z URL
        route = get_object_or_404(Route, pk=self.kwargs['route_pk'])
        last_point = route.points.order_by('-order').first()
        order = last_point.order + 1 if last_point else 0
        serializer.save(route=route, order=order)
    
    def get_object(self):
        # Verify both point and route ownership
        queryset = self.filter_queryset(self.get_queryset())
        try:
            obj = queryset.get(pk=self.kwargs['pk'])
        except (Point.DoesNotExist, Route.DoesNotExist):
            raise Http404
        return obj