from django.urls import path

from . import views

app_name = 'clinic_queue'

urlpatterns = [
    path('', views.reception_dashboard, name='reception_dashboard'),
    path('display/', views.display_board, name='display_board'),
    path('patient/<str:token_number>/', views.patient_status, name='patient_status'),
    path('tokens/create/', views.create_patient_token, name='create_patient_token'),
    path('tokens/call-next/', views.call_next, name='call_next'),
    path('tokens/<int:token_id>/complete/', views.complete_patient_token, name='complete_token'),
    path('tokens/<int:token_id>/cancel/', views.cancel_patient_token, name='cancel_token'),
    path('settings/', views.queue_settings, name='queue_settings'),
]
