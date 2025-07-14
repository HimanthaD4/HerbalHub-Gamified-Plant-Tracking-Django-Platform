from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import viewgarden



urlpatterns = [
    path('', views.index, name='index'),
    path('mapsearch', views.mapsearch, name='mapsearch'),
    path('settings', views.settings, name='settings'),
    path('upload', views.upload, name='upload'),
    path('search', views.search, name='search'),
    path('profile/<str:pk>', views.profile, name='profile'),
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('logout', views.logout, name='logout'),
    path('mapgame/', views.map_game, name='mapgame'), 
    path('scoreboard/', views.scoreboard, name='scoreboard'),
    path('farm/', views.farm, name='farm'),
    path('save_garden/', views.save_garden, name='save_garden'),
    path('viewgarden/<int:user_id>/', viewgarden, name='viewgarden'),
    
    
    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  