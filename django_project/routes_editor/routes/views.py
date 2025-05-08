from PIL import Image, ImageDraw
from io import BytesIO
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BackgroundImage, Route, Point
from .forms import RouteForm, PointForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

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

#@login_required
#def route_detail(request, pk):
#    route = get_object_or_404(Route, pk=pk, user=request.user)
#    return render(request, 'routes/route_detail.html', {'route': route})
@login_required
def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk, user=request.user)
    
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
    
    return render(request, 'routes/route_detail.html', {
        'route': route,
        'route_image': img_str,
        'points': points
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