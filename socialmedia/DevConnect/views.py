from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate , logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Post, Profile, Like, Comment, Follow
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count


def home(request):
    posts = Post.objects.annotate(
        like_count=Count('likes'),
        comment_count=Count('comments')
    )
    return render(request, 'home.html', {'posts': posts})
# Register view (for creating new users)
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user)
        return redirect('login')
    return render(request, 'register.html')
# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})
# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')
# Home view - list posts on home page
@login_required
def home(request):
    posts = Post.objects.all()
    return render(request, 'home.html', {'posts': posts, 'is_myposts': False})
# User profile view
@login_required
def profile(request):
    user_profile = request.user.profile

    # Handle bio editing
    bio_edit = False
    if request.method == 'POST':
        if 'bio_edit' in request.POST:
            bio_edit = True  # Enable bio editing mode
        elif 'bio' in request.POST:
            new_bio = request.POST.get('bio')
            if new_bio:
                user_profile.bio = new_bio
                user_profile.save()
            bio_edit = False  # After saving the new bio, turn off edit mode

    return render(request, 'profile.html', {
        'profile': user_profile,
        'bio_edit': bio_edit  # Pass bio_edit to control the button/form toggle
    })

# Post creation
@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST['content']
        Post.objects.create(author=request.user, content=content)
        return redirect('home')
    return render(request, 'create_post.html')
@login_required
def my_posts(request):
    posts = Post.objects.filter(author=request.user)  # Filter posts for the logged-in user
    return render(request, 'home.html', {'posts': posts, 'is_myposts': True})
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('home')  # Redirect if not the author
    if request.method == 'POST':
        content = request.POST['content']
        post.content = content  # Update the content of the post
        post.save()  # Save the changes
        return redirect('home')  # Redirect to home after edit
    return render(request, 'edit_post.html', {'post': post})
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:
        post.delete()
        return JsonResponse({'deleted': True}) 
    return JsonResponse({'deleted': False, 'error': 'You cannot delete someone else\'s post.'}, status=403)
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()  # If like already exists, delete it (unlike)
        liked = False
    else:
        liked = True  # Like the post
    return JsonResponse({
        'likes': post.likes.count(),  # Total number of likes
        'liked': liked  # Current like state (True/False)
    })
# Comment functionality
@login_required
def comment_on_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Handling the form submission for a new comment
    if request.method == 'POST':
        content = request.POST['content']
        Comment.objects.create(author=request.user, post=post, content=content)
        return redirect('comment_on_post', post_id=post.id)  # Redirect back to the same page to show the new comment
    
    # Get all comments for the post
    comments = Comment.objects.filter(post=post).order_by('-created_at')
    
    return render(request, 'comment_on_post.html', {
        'post': post,
        'comments': comments
    })
@login_required
def author_profile(request, user_id):
    author = get_object_or_404(User, id=user_id)  # Get the author by user_id
    user_profile = author.profile  # Get the user's profile (bio, etc.)
    is_following = Follow.objects.filter(follower=request.user, following=author).exists()
    followers = author.followers.all()
    following = author.following.all()
    return render(request, 'author_profile.html', {
        'author': author,
        'user_profile': user_profile,
        'is_following': is_following,
        'followers_count': followers.count(),
        'following_count': following.count(),
    })
# Follow functionality
@login_required
def follow_user(request, user_id):
    author = get_object_or_404(User, id=user_id)
    if not Follow.objects.filter(follower=request.user, following=author).exists():
        Follow.objects.create(follower=request.user, following=author)
    return redirect('author_profile', user_id=user_id)
@login_required
def unfollow_user(request, user_id):
    author = get_object_or_404(User, id=user_id)
    Follow.objects.filter(follower=request.user, following=author).delete()  
    return redirect('author_profile', user_id=user_id)

#--------------------------------------------------API SECTION-----------------------------------------------------------------

from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Post, Profile, Like, Comment, Follow
from .serializers import (
    UserSerializer, ProfileSerializer, PostSerializer, LikeSerializer,
    CommentSerializer, FollowSerializer
)
# User Registration
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            Profile.objects.create(user=user)  # Create a profile for the new user
            return Response(
                {'message': 'User registered successfully', 'user_id': user.id, 'email': user.email},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'message': 'Error creating profile', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# User Login (with JWT)
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        # Generate JWT token on successful authentication
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response({
            'message': 'Login successful',
            'access': access_token,
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED)

# User Logout
@api_view(['POST'])
@permission_classes([AllowAny])
def api_logout_user(request):
    # Invalidate JWT token on the client side by not supporting token refreshing
    return Response({'message': 'Logout successful, but token still valid until expired'}, 
                    status=status.HTTP_200_OK)

@api_view(['GET'])
def get_user_info(request):
    user = request.user  # Get the currently authenticated user
    serializer = UserSerializer(user)
    return Response(serializer.data)


# Get All Posts
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_list_posts(request):
    posts = Post.objects.annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    )

    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


# Create Post
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_create_post(request):
    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=request.user,image=request.FILES.get('image'))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Post
from .serializers import PostSerializer

# List all posts (GET)
@api_view(['GET'])
@permission_classes([AllowAny])  # Anyone can view posts
def api_list_posts(request):
    posts = Post.objects.annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    )
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)
@api_view(['GET'])
@permission_classes([AllowAny])  # Only authenticated users can access their posts
def api_user_posts(request):
    # Filter posts by the logged-in user
    posts = Post.objects.filter(author=request.user).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    )
    # Serialize the posts data
    serializer = PostSerializer(posts, many=True)
    # Return the serialized data
    return Response(serializer.data)
# Create a new post
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_post(request):
    if request.method == 'POST':
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)  # Set the author to the current user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# Edit an existing post (PUT)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_edit_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the logged-in user is the author of the post
    if post.author != request.user:
        return Response({'detail': 'You are not authorized to edit this post.'}, status=status.HTTP_403_FORBIDDEN)

    # Proceed with updating the post
    serializer = PostSerializer(post, data=request.data, partial=True)  # partial=True allows updating fields
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete a post (DELETE)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_delete_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the logged-in user is the author of the post
    if post.author != request.user:
        return Response({'detail': 'You are not authorized to delete this post.'}, status=status.HTTP_403_FORBIDDEN)

    # Proceed with deleting the post
    post.delete()
    return Response({'detail': 'Post deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST', 'DELETE'])
@permission_classes([AllowAny])
def api_like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        # Check if the user has already liked the post
        is_liked = Like.is_liked(request.user, post)
        
        if is_liked:
            # If the user has already liked the post, unlike it
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            return Response(
                {'liked': False, 'likes_count': Like.get_likes_count(post)}, 
                status=status.HTTP_200_OK
            )
        else:
            # If the user has not liked the post, like it
            Like.objects.create(user=request.user, post=post)
            return Response(
                {'liked': True, 'likes_count': Like.get_likes_count(post)}, 
                status=status.HTTP_201_CREATED
            )
    
    elif request.method == 'DELETE':
        # If it's a DELETE request, unlike the post
        is_liked = Like.is_liked(request.user, post)
        
        if is_liked:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            return Response(
                {'liked': False, 'likes_count': Like.get_likes_count(post)}, 
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'You have not liked this post yet.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    
    # If the user hasn't liked the post, create a like
    Like.objects.create(user=request.user, post=post)
    
    return Response(
        {'liked': True, 'likes_count': Like.get_likes_count(post)}, 
        status=status.HTTP_200_OK
    )
## Check Like Status
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_like_status(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_liked = Like.objects.filter(user=request.user, post=post).exists()
    return Response({'is_liked': is_liked}, status=status.HTTP_200_OK)
# Comment on Post
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # Only authenticated users can post
def api_comment_on_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Handle GET request: Fetch all comments for the post
    if request.method == 'GET':
        comments = Comment.objects.filter(post=post).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    # Handle POST request: Create a new comment
    elif request.method == 'POST':
        content = request.data.get('content', '').strip()
        if not content:
            return Response({"detail": "Comment content cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        # Create the new comment
        comment = Comment.objects.create(author=request.user, post=post, content=content)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



# User Profile
@api_view(['GET'])
@permission_classes([AllowAny])
def api_get_profile(request, user_id=None):
    user = request.user if user_id is None else get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)
    serializer = ProfileSerializer(profile)
    return Response(serializer.data)

# Edit Profile
@api_view(['PATCH'])
@permission_classes([AllowAny])
def api_edit_profile(request):
    profile = request.user.profile
    serializer = ProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Follow a user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)

    if user_to_follow == request.user:
        return Response({'detail': "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    
    if not created:
        return Response({'detail': "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'detail': 'Successfully followed.'}, status=status.HTTP_201_CREATED)

# Unfollow a user
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)

    if user_to_unfollow == request.user:
        return Response({'detail': "You cannot unfollow yourself."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        follow = Follow.objects.get(follower=request.user, following=user_to_unfollow)
        follow.delete()
        return Response({'detail': 'Successfully unfollowed.'}, status=status.HTTP_204_NO_CONTENT)
    except Follow.DoesNotExist:
        return Response({'detail': "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)

# Check Follow Status
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_follow_status(request, user_id):
    user_to_check = get_object_or_404(User, id=user_id)
    is_following = Follow.objects.filter(follower=request.user, following=user_to_check).exists()
    return Response({'is_following': is_following}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_followers(request, username):
    try:
        user = User.objects.get(username=username)
        followers = Follow.objects.filter(following=user).values_list('follower__username', flat=True)
        followers_count = followers.count()  # Get the count of followers
        return Response({"followers": list(followers), "followers_count": followers_count})
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_following(request, username):
    try:
        user = User.objects.get(username=username)
        following = Follow.objects.filter(follower=user).values_list('following__username', flat=True)
        following_count = following.count()  # Get the count of following
        return Response({"following": list(following), "following_count": following_count})
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)



#22222222222222222222222222222222222222222222222222222222222222222222222222222222222

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Call the parent class's post method to generate the tokens
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Create a custom user data dictionary containing user id and username
            user_data = {
                "id": request.user.id,
                "username": request.user.username,
            }
            # Return the response with the access token and custom user data
            return Response({
                "access": response.data.get("access"),
                "user": user_data
            })
        
        # Return the original response if status code isn't 200
        return response


# This will provide the view for refreshing the access token
class CustomTokenRefreshView(TokenRefreshView):
    pass


@api_view(['GET'])
def current_user(request):
    if request.user.is_authenticated:
        return Response({
            "username": request.user.username,
        })
    return Response({"error": "User not authenticated"}, status=401)
