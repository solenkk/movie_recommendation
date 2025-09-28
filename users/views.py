from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user and create their profile
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            logger.info(f"User registered successfully: {user.username}")
            return Response(
                {'message': 'User created successfully', 'user_id': user.id},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return Response(
                {'error': 'Failed to create user'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    logger.warning(f"User registration failed: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Authenticate user and return user info
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    if user:
        if user.is_active:
            logger.info(f"User logged in successfully: {username}")
            return Response({
                'message': 'Login successful',
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            })
        else:
            logger.warning(f"Login attempt for inactive user: {username}")
            return Response(
                {'error': 'Account is inactive'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    logger.warning(f"Failed login attempt for user: {username}")
    return Response(
        {'error': 'Invalid credentials'},
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get current user's profile information
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        logger.info(f"Profile retrieved for user: {request.user.username}")
        return Response(serializer.data)
    except UserProfile.DoesNotExist:
        logger.error(f"Profile not found for user: {request.user.username}")
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user information
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)