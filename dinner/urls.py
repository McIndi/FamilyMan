from django.urls import path

from . import views


urlpatterns = [
    path('', views.dinner_index, name='dinner_index'),
    path('past/', views.dinner_past, name='dinner_past'),
    path('add-option/', views.add_dinner_option, name='dinner_add_option'),
    path('option/<int:option_id>/edit/', views.edit_dinner_option, name='dinner_edit_option'),
    path('option/<int:option_id>/delete/', views.delete_dinner_option, name='dinner_delete_option'),
    path('<int:dinner_day_id>/vote/', views.vote_dinner_option, name='dinner_vote'),
    path('<int:dinner_day_id>/record/', views.record_dinner_result, name='dinner_record_result'),
]
