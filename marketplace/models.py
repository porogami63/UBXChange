from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class School(models.Model):
    """University Belt schools in Manila with official color motifs."""
    name = models.CharField(max_length=120)
    short_name = models.CharField(max_length=20, blank=True)
    primary_color = models.CharField(max_length=7, default='#1a2b4a', help_text='Hex color (e.g. #FFD700)')
    secondary_color = models.CharField(max_length=7, default='#ffffff', blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.short_name or self.name


class Category(models.Model):
    """Listing categories (textbooks, electronics, etc.)."""
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=30, default='box')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Listing(models.Model):
    """Marketplace listing."""
    CONDITION_CHOICES = [
        ('new', 'Brand New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('used', 'Well Used'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    image = models.ImageField(upload_to='listings/', blank=True, null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    contact_info = models.CharField(max_length=200, blank=True, help_text='Phone or social media')
    is_sold = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('marketplace:listing_detail', kwargs={'pk': self.pk})


class Profile(models.Model):
    """Extended user profile for students."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=120, blank=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    contact_info = models.CharField(max_length=200, blank=True, help_text='Social media or alternate contact')
    address = models.CharField(max_length=255, blank=True, help_text='General meetup area or barangay')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    google_avatar_url = models.URLField(blank=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    review_count = models.PositiveIntegerField(default=0)
    total_sold = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def display_name(self):
        return self.full_name or self.user.get_full_name() or self.user.username

    def update_rating(self):
        """Recalculate average rating from reviews."""
        reviews = self.user.reviews_received.all()
        if reviews.exists():
            self.average_rating = sum(r.rating for r in reviews) / reviews.count()
            self.review_count = reviews.count()
        else:
            self.average_rating = 5.0
            self.review_count = 0
        self.save(update_fields=['average_rating', 'review_count'])


class Favorite(models.Model):
    """User's saved/favorited listings."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'listing']


class Conversation(models.Model):
    """Private conversation between two users, optionally about a listing."""
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    participants = models.ManyToManyField(User, related_name='conversations', through='ConversationParticipant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()


class ConversationParticipant(models.Model):
    """Links users to conversations."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['conversation', 'user']


class Message(models.Model):
    """Private message within a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class ForumPost(models.Model):
    """Live forum post - users can promote their listings here."""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    title = models.CharField(max_length=200)
    body = models.TextField()
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='forum_promotions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ForumReply(models.Model):
    """Reply to a forum post."""
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_replies')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Forum replies'


class Notification(models.Model):
    """Simple notification for users (messages, forum replies, etc.)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Transaction(models.Model):
    """Track completed sales between buyer and seller."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.buyer.username} → {self.seller.username} ({self.listing.title if self.listing else 'Deleted'})"


class Review(models.Model):
    """User review/rating for a seller."""
    RATING_CHOICES = [
        (1, '⭐ Poor'),
        (2, '⭐⭐ Fair'),
        (3, '⭐⭐⭐ Good'),
        (4, '⭐⭐⭐⭐ Very Good'),
        (5, '⭐⭐⭐⭐⭐ Excellent'),
    ]

    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='review')
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['reviewer', 'seller', 'listing']

    def __str__(self):
        return f"{self.reviewer.username} → {self.seller.username} ({self.rating}★)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update seller's average rating
        if hasattr(self.seller, 'profile'):
            self.seller.profile.update_rating()