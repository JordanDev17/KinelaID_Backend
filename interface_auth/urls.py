from django.urls import path
from .views import LoginStepOneView, LoginStepTwoFaceView

urlpatterns = [
    path('step-one/', LoginStepOneView.as_view(), name='login-step-one'),
    path('step-two-face/', LoginStepTwoFaceView.as_view(), name='login-step-two-face'),
]