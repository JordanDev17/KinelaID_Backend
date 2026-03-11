from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginStepOneView, LoginStepTwoFaceView, InterfazUsuarioViewSet

router = DefaultRouter()
router.register(r'usuarios', InterfazUsuarioViewSet)

urlpatterns = [
    path('step-one/', LoginStepOneView.as_view(), name='login-step-one'),
    path('step-two-face/', LoginStepTwoFaceView.as_view(), name='login-step-two-face'),
    path('',               include(router.urls)),
]