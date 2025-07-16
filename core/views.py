from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Profile, Plant, GardenBox
import exifread
from itertools import chain
import random
import os
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from geopy.distance import geodesic
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import tensorflow as tf
import numpy as np
from django.core.files.storage import FileSystemStorage


@login_required
def save_garden(request):
    if request.method == "POST":
        garden_data = json.loads(request.body).get("garden", [])
        
        profile = Profile.objects.get(user=request.user)
        total_price = 0
        
        for box_data in garden_data:
            plant = box_data.get("plant")
            row = box_data.get("row")
            col = box_data.get("col")
            price_map = {
                "Aloe": 10,
                "Mint": 15,
            }
            total_price += price_map.get(plant, 0)  
            
            garden_box, created = GardenBox.objects.update_or_create(
                user=request.user,
                row=row,
                col=col,
                defaults={'plant': plant}
            )
        
        if profile.score >= total_price:
            profile.score -= total_price
            profile.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Not enough score"})
    
    return JsonResponse({"success": False})


@login_required
def viewgarden(request, user_id):
    profile = get_object_or_404(Profile, user__id=user_id)
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    
    rows = list(range(1, 15))
    cols = list(range(1, 11))
    
    garden_boxes = GardenBox.objects.filter(user__id=user_id)
    
    return render(request, 'viewgarden.html', {
        'profile': profile,
        'rows': rows,
        'cols': cols,
        'garden_boxes': garden_boxes,  
        'user_profile': user_profile,
        'profile': user_profile,
    })


@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    username_profile = []
    username_profile_list = []

    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    return render(request, 'index.html', {
        'user_profile': user_profile,
        'profile': user_profile,
        'user_score': user_profile.score,
    })


@login_required(login_url='signin')
def map_game(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        plant_name = request.POST.get('plantName')
        image = request.FILES.get('image_upload')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if image:
            image_name = image.name
            image_path = default_storage.save(f'images/{image_name}', image)
            try:
                with default_storage.open(image_path, 'rb') as img_file:
                    tags = exifread.process_file(img_file)
                    if 'GPSLatitude' in tags and 'GPSLongitude' in tags:
                        latitude_exif = tags['GPSLatitude'].values
                        longitude_exif = tags['GPSLongitude'].values
                        lat = latitude_exif[0] + latitude_exif[1] / 60 + latitude_exif[2] / 3600
                        lon = longitude_exif[0] + longitude_exif[1] / 60 + longitude_exif[2] / 3600
                        if tags.get('GPSLatitudeRef') and tags['GPSLatitudeRef'].values == 'S':
                            lat = -lat
                        if tags.get('GPSLongitudeRef') and tags['GPSLongitudeRef'].values == 'W':
                            lon = -lon
                        latitude = lat
                        longitude = lon
            finally:
                default_storage.delete(image_path)

        if not latitude or not longitude:
            return render(request, 'mapgame.html', {
                'error': 'Please mark the location on the map',
                'plants_data': Plant.objects.all(),
                'user_profile': user_profile,
                'profile': user_profile  
            })

        plant = Plant.objects.create(
            user=request.user,
            latitude=latitude,
            longitude=longitude,
            plant_name=plant_name
        )

        user_profile.add_score(10)

        return redirect('mapgame')

    plants = Plant.objects.all()
    plants_data = [{
        'lat': plant.latitude,
        'lng': plant.longitude,
        'plant_name': plant.plant_name,
        'username': plant.user.username
    } for plant in plants]

    messages = [f'New plant "{plant.plant_name}" discovered by {plant.user.username}!' for plant in plants]

    return render(request, 'mapgame.html', {
        'plants_data': plants_data,
        'user_profile': user_profile,
        'profile': user_profile,
        'messages': messages
    })


@login_required(login_url='signin')
def scoreboard(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    profiles = Profile.objects.all().order_by('-score')
    user_rank = list(profiles.values_list('id', flat=True)).index(user_profile.id) + 1
    plants_count = Plant.objects.filter(user=request.user).count()
    chart_data = [
        {"username": prof.user.username, "score": prof.score}
        for prof in profiles
    ]

    return render(request, 'scoreboard.html', {
        'profiles': profiles,
        'user_profile': user_profile,
        'profile': user_profile,
        'user_score': user_profile.score,
        'user_rank': user_rank,
        'plants_count': plants_count,
        'chart_data': chart_data
    })


@login_required
def farm(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    profile = Profile.objects.get(user=request.user)
    rows = list(range(1, 15))
    cols = list(range(1, 11))
    
    garden_boxes = GardenBox.objects.filter(user=request.user)
    
    return render(request, 'farm.html', {
        'profile': profile,
        'user_profile': user_profile,
        'rows': rows,
        'cols': cols,
        'garden_boxes': garden_boxes, 
        'user_score': user_profile.score,
    })


@login_required(login_url='signin')
def mapsearch(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    
    plants_data = []
    user_score = user_profile.score

    if request.method == 'GET':
        search_username = request.GET.get('username', '')
        search_plant_name = request.GET.get('plant_name', '')
        search_latitude = request.GET.get('latitude', '')
        search_longitude = request.GET.get('longitude', '')

        if search_latitude and search_longitude:
            try:
                lat = float(search_latitude)
                lon = float(search_longitude)
                plants = Plant.objects.all()

                for plant in plants:
                    if plant.latitude and plant.longitude:
                        distance = geodesic((lat, lon), (plant.latitude, plant.longitude)).km
                        if distance <= 50:
                            plants_data.append({
                                'lat': plant.latitude,
                                'lng': plant.longitude,
                                'plant_name': plant.plant_name,
                                'username': plant.user.username,
                                'distance': distance
                            })
            except ValueError:
                pass  
        else:
            plants = Plant.objects.filter(
                Q(user__username__icontains=search_username) |
                Q(plant_name__icontains=search_plant_name)
            )
            for plant in plants:
                if plant.latitude and plant.longitude:
                    plants_data.append({
                        'lat': plant.latitude,
                        'lng': plant.longitude,
                        'plant_name': plant.plant_name,
                        'username': plant.user.username
                    })

    return render(request, 'mapsearch.html', {
        'plants_data': plants_data,
        'user_profile': user_profile,
        'profile': user_profile,
        'user_score': user_score,
    })


@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')


@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)
        
        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})


@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
    }
    return render(request, 'profile.html', context)


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('signup')
        
    else:
        return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('signin')

    else:
        return render(request, 'signin.html')


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        # Handle profile information update
        if 'profile_form' in request.POST:
            user_profile.bio = request.POST.get('bio', '')
            user_profile.location = request.POST.get('location', '')
            
            if 'image' in request.FILES:
                user_profile.profileimg = request.FILES['image']
            
            user_profile.save()
            return redirect('settings')

        # Handle preferences update
        elif 'preferences_form' in request.POST:
            user_profile.dark_mode = 'dark_mode' in request.POST
            user_profile.email_notifications = 'email_notifications' in request.POST
            user_profile.push_notifications = 'push_notifications' in request.POST
            user_profile.location_services = 'location_services' in request.POST
            user_profile.language = request.POST.get('language', 'en')
            user_profile.save()
            return redirect('settings')

        # Handle password change
        elif 'password_form' in request.POST:
            current_password = request.POST.get('currentPassword')
            new_password = request.POST.get('newPassword')
            confirm_password = request.POST.get('confirmPassword')
            
            if (new_password == confirm_password and 
                request.user.check_password(current_password)):
                request.user.set_password(new_password)
                request.user.save()
                # Log the user back in after password change
                from django.contrib.auth import login
                login(request, request.user)
                return redirect('settings')
            else:
                messages.error(request, 'Password change failed')
                return redirect('settings')

        # Handle account deletion
        elif 'delete_account' in request.POST:
            request.user.delete()
            return redirect('signin')

    context = {
        'user_profile': user_profile,
        'user': request.user
    }
    return render(request, 'setting.html', context)


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')