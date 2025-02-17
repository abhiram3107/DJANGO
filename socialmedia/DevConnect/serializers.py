from rest_framework import serializers
from .models import Profile, Post, Like, Comment, Follow
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']  # Include password for validation but mark it as write-only
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],  # This will be hashed by create_user()
        )
        return user



class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nesting user information in the profile
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio','profile_picture', 'followers_count', 'following_count','followers','following']

    def get_followers_count(self, obj):
        return Follow.objects.filter(following=obj.user).count()

    def get_following_count(self, obj):
        return Follow.objects.filter(follower=obj.user).count()



class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # Nesting author information
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)  # Count of likes
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)  # Count of comments

    class Meta:
        model = Post
        fields = ['id', 'author', 'content','image', 'created_at', 'updated_at', 'likes_count', 'comments_count']


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nesting user information
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())  # Reference to Post
    liked = serializers.SerializerMethodField()  # To determine if the current user has liked the post
    likes_count = serializers.IntegerField(source='post.likes.count', read_only=True)  # To show like count for post

    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at', 'liked', 'likes_count']

    def get_liked(self, obj):
        # Determine if the current user has liked the post
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj.post).exists()
        return False



class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # Nesting author information
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())  # Reference to Post

    class Meta:
        model = Comment
        fields = ['id', 'author', 'post', 'content', 'created_at']


class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)  # Nesting follower information
    following = UserSerializer(read_only=True)  # Nesting following information

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
