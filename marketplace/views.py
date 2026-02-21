from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import (
    Listing,
    Category,
    School,
    Profile,
    Favorite,
    Conversation,
    ConversationParticipant,
    Message,
    ForumPost,
    ForumReply,
    Notification,
    Review,
    Transaction,
)
from .forms import CustomUserCreationForm, ListingForm, ProfileForm, MessageForm, ForumPostForm, ForumReplyForm, PurchaseForm, TransactionConfirmForm
from .utils import get_similar_listings_price_stats


def home(request):
    """Homepage with featured and recent listings."""
    listings = Listing.objects.filter(is_sold=False).select_related(
        'category', 'seller', 'school'
    )[:12]
    return render(request, 'marketplace/home.html', {'listings': listings})


def listing_list(request):
    """Browse all listings with search and filters."""
    listings = Listing.objects.filter(is_sold=False).select_related(
        'category', 'seller', 'school'
    )

    q = request.GET.get('q', '').strip()
    if q:
        listings = listings.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )

    category_slug = request.GET.get('category')
    if category_slug:
        listings = listings.filter(category__slug=category_slug)

    school_id = request.GET.get('school')
    if school_id:
        listings = listings.filter(school_id=school_id)

    min_price = request.GET.get('min_price')
    if min_price and min_price.isdigit():
        listings = listings.filter(price__gte=min_price)

    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        listings = listings.filter(price__lte=max_price)

    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        listings = listings.order_by('price')
    elif sort == 'price_high':
        listings = listings.order_by('-price')
    else:
        listings = listings.order_by('-created_at')

    return render(request, 'marketplace/listing_list.html', {
        'listings': listings,
        'query': q,
        'selected_category': category_slug,
        'selected_school': school_id,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'sort': sort,
    })


def listing_detail(request, pk):
    """View a single listing."""
    listing = get_object_or_404(Listing.objects.select_related(
        'category', 'seller', 'school'
    ), pk=pk)

    # Ensure seller has profile for display
    seller_profile, _ = Profile.objects.get_or_create(user=listing.seller)

    # Increment view count
    listing.view_count += 1
    listing.save(update_fields=['view_count'])

    # Seller's other active listings
    other_listings = Listing.objects.filter(seller=listing.seller, is_sold=False).exclude(pk=pk).select_related('category', 'school')[:4]

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, listing=listing).exists()

    # Price statistics for similar items
    price_stats = get_similar_listings_price_stats(listing)

    return render(request, 'marketplace/listing_detail.html', {
        'listing': listing,
        'seller_profile': seller_profile,
        'other_listings': other_listings,
        'is_favorited': is_favorited,
        'price_stats': price_stats,
    })


def register(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect('marketplace:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created.')
            return redirect('marketplace:home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'marketplace/register.html', {'form': form})


@login_required
def listing_create(request):
    """Create a new listing."""
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            if not listing.contact_info and profile:
                listing.contact_info = profile.phone or profile.contact_info or ''
            if not listing.school and profile:
                listing.school = profile.school
            listing.save()
            messages.success(request, 'Your listing has been posted!')
            return redirect(listing.get_absolute_url())
    else:
        initial = {}
        if profile:
            initial = {
                'school': profile.school,
                'contact_info': profile.phone or profile.contact_info,
            }
        form = ListingForm(initial=initial)

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'title': 'Sell an Item',
    })


@login_required
def listing_edit(request, pk):
    """Edit a listing."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user:
        messages.error(request, "You can't edit this listing.")
        return redirect(listing.get_absolute_url())

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, 'Listing updated.')
            return redirect(listing.get_absolute_url())
    else:
        form = ListingForm(instance=listing)

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'listing': listing,
        'title': 'Edit Listing',
    })


@login_required
def listing_delete(request, pk):
    """Delete a listing."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user:
        messages.error(request, "You can't delete this listing.")
        return redirect(listing.get_absolute_url())

    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Listing deleted.')
        return redirect('marketplace:listing_list')

    return render(request, 'marketplace/listing_confirm_delete.html', {'listing': listing})


@login_required
def listing_mark_sold(request, pk):
    """Mark listing as sold."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user:
        messages.error(request, "You can't modify this listing.")
        return redirect(listing.get_absolute_url())

    listing.is_sold = True
    listing.save()
    messages.success(request, 'Listing marked as sold.')
    return redirect('marketplace:my_listings')


@login_required
def my_listings(request):
    """User's own listings."""
    listings = request.user.listings.select_related('category', 'school').order_by('-created_at')
    return render(request, 'marketplace/my_listings.html', {'listings': listings})


@login_required
def profile_view(request):
    """View and edit profile."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('marketplace:profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'marketplace/profile.html', {'form': form, 'profile': profile})


def public_profile_view(request, username):
    """View another user's public profile."""
    user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=user)
    listings = user.listings.filter(is_sold=False).select_related('category', 'school')
    reviews = Review.objects.filter(seller=user).select_related('reviewer').order_by('-created_at')[:10]
    
    # Check if current user has bought from this seller
    has_purchased = False
    if request.user.is_authenticated and request.user != user:
        has_purchased = Transaction.objects.filter(buyer=request.user, seller=user).exists()
    
    # Check if user has already reviewed this seller
    has_reviewed = False
    if request.user.is_authenticated and request.user != user:
        has_reviewed = Review.objects.filter(reviewer=request.user, seller=user).exists()

    return render(request, 'marketplace/public_profile.html', {
        'profile_user': user,
        'profile': profile,
        'listings': listings,
        'reviews': reviews,
        'has_purchased': has_purchased,
        'has_reviewed': has_reviewed,
    })


@login_required
def leave_review(request, username):
    """Leave a review for a seller."""
    seller = get_object_or_404(User, username=username)
    
    if seller == request.user:
        messages.error(request, "You can't review yourself.")
        return redirect('marketplace:public_profile', username=username)
    
    # Check if user has already reviewed
    existing_review = Review.objects.filter(reviewer=request.user, seller=seller).first()
    
    if request.method == 'POST':
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                messages.error(request, 'Rating must be between 1 and 5.')
                return redirect('marketplace:leave_review', username=username)
        except ValueError:
            messages.error(request, 'Invalid rating.')
            return redirect('marketplace:leave_review', username=username)
        
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, 'Your review has been updated.')
        else:
            Review.objects.create(
                reviewer=request.user,
                seller=seller,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Your review has been posted!')
        
        return redirect('marketplace:public_profile', username=username)
    
    context = {
        'seller': seller,
        'existing_review': existing_review,
        'rating_choices': Review._meta.get_field('rating').choices,
    }
    return render(request, 'marketplace/leave_review.html', context)


@login_required
def favorite_toggle(request, pk):
    """Add or remove listing from favorites."""
    listing = get_object_or_404(Listing, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        fav.delete()
        messages.info(request, 'Removed from favorites.')
    else:
        messages.success(request, 'Added to favorites!')
    next_url = request.META.get('HTTP_REFERER') or listing.get_absolute_url()
    return redirect(next_url)


@login_required
def favorites_list(request):
    """View user's favorited listings."""
    favs = Favorite.objects.filter(user=request.user).select_related(
        'listing', 'listing__category', 'listing__school'
    ).order_by('-created_at')
    listings = [f.listing for f in favs]
    return render(request, 'marketplace/favorites.html', {'listings': listings})


# ----- Transactions -----

@login_required
def initiate_purchase(request, pk):
    """Buyer initiates a purchase by selecting exchange method and adding notes."""
    listing = get_object_or_404(Listing, pk=pk)
    
    # Can't buy own listing
    if listing.seller == request.user:
        messages.error(request, "You can't buy your own listing!")
        return redirect(listing.get_absolute_url())
    
    # Can't buy sold listings
    if listing.is_sold:
        messages.error(request, "This listing is no longer available.")
        return redirect(listing.get_absolute_url())
    
    # Check if user already has a pending transaction for this listing
    existing_txn = Transaction.objects.filter(
        buyer=request.user,
        listing=listing,
        status__in=['pending', 'confirmed']
    ).first()
    
    if existing_txn:
        messages.info(request, "You already have a pending transaction for this item. View it in your inbox.")
        return redirect('marketplace:transaction_detail', transaction_id=existing_txn.pk)
    
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            transaction = Transaction.objects.create(
                buyer=request.user,
                seller=listing.seller,
                listing=listing,
                price=listing.price,
                exchange_method=form.cleaned_data['exchange_method'],
                notes=form.cleaned_data['notes'],
                status='pending'
            )
            
            # Create notification for seller
            from django.urls import reverse
            Notification.objects.create(
                user=listing.seller,
                message=f"{request.user.username} wants to buy {listing.title}",
                url=reverse('marketplace:transaction_detail', kwargs={'transaction_id': transaction.pk})
            )
            
            messages.success(request, 'Purchase initiated! Waiting for seller confirmation.')
            return redirect('marketplace:transaction_detail', transaction_id=transaction.pk)
    else:
        form = PurchaseForm()
    
    return render(request, 'marketplace/purchase_form.html', {
        'form': form,
        'listing': listing,
        'seller': listing.seller,
    })


@login_required
def transaction_detail(request, transaction_id):
    """View transaction details and receipt."""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    # Only buyer or seller can view
    if request.user not in [transaction.buyer, transaction.seller]:
        messages.error(request, "You don't have access to this transaction.")
        return redirect('marketplace:inbox')
    
    is_buyer = request.user == transaction.buyer
    is_seller = request.user == transaction.seller
    
    # Form for seller to confirm
    confirm_form = None
    if is_seller and transaction.status == 'pending':
        if request.method == 'POST':
            confirm_form = TransactionConfirmForm(request.POST, instance=transaction)
            if confirm_form.is_valid():
                from django.utils import timezone
                transaction = confirm_form.save(commit=False)
                transaction.status = 'confirmed'
                transaction.confirmed_at = timezone.now()
                transaction.save()
                
                # Notify buyer
                from django.urls import reverse
                Notification.objects.create(
                    user=transaction.buyer,
                    message=f"{transaction.seller.username} confirmed your purchase!",
                    url=reverse('marketplace:transaction_detail', kwargs={'transaction_id': transaction.pk})
                )
                
                messages.success(request, 'Purchase confirmed! Buyer and seller can now exchange contact details.')
                return redirect('marketplace:transaction_detail', transaction_id=transaction.pk)
        else:
            confirm_form = TransactionConfirmForm(instance=transaction)
    
    buyer_profile = getattr(transaction.buyer, 'profile', None) or Profile.objects.filter(user=transaction.buyer).first()
    seller_profile = getattr(transaction.seller, 'profile', None) or Profile.objects.filter(user=transaction.seller).first()
    
    return render(request, 'marketplace/transaction_detail.html', {
        'transaction': transaction,
        'buyer_profile': buyer_profile,
        'seller_profile': seller_profile,
        'is_buyer': is_buyer,
        'is_seller': is_seller,
        'confirm_form': confirm_form,
    })


@login_required
def confirm_transaction(request, transaction_id):
    """Allow seller to confirm transaction and move to exchange stage."""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    if transaction.seller != request.user:
        messages.error(request, "Only the seller can confirm this transaction.")
        return redirect('marketplace:inbox')
    
    if transaction.status != 'pending':
        messages.error(request, "This transaction cannot be confirmed.")
        return redirect('marketplace:transaction_detail', transaction_id=transaction.pk)
    
    if request.method == 'POST':
        form = TransactionConfirmForm(request.POST, instance=transaction)
        if form.is_valid():
            from django.utils import timezone
            transaction = form.save(commit=False)
            transaction.status = 'confirmed'
            transaction.confirmed_at = timezone.now()
            transaction.save()
            
            # Notify buyer
            from django.urls import reverse
            Notification.objects.create(
                user=transaction.buyer,
                message=f"{transaction.seller.username} confirmed your purchase!",
                url=reverse('marketplace:transaction_detail', kwargs={'transaction_id': transaction.pk})
            )
            
            messages.success(request, 'Purchase confirmed!')
            return redirect('marketplace:transaction_detail', transaction_id=transaction.pk)
    else:
        form = TransactionConfirmForm(instance=transaction)
    
    return render(request, 'marketplace/transaction_confirm.html', {
        'form': form,
        'transaction': transaction,
    })


@login_required
def complete_transaction(request, transaction_id):
    """Mark transaction as complete and prompt buyer to rate the seller."""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    # Only buyer can complete
    if transaction.buyer != request.user:
        messages.error(request, "Only the buyer can mark this as complete.")
        return redirect('marketplace:inbox')
    
    if transaction.status != 'confirmed':
        messages.error(request, "Transaction must be confirmed first.")
        return redirect('marketplace:transaction_detail', transaction_id=transaction.pk)
    
    from django.utils import timezone
    transaction.status = 'completed'
    transaction.completed_at = timezone.now()
    transaction.save()
    
    if transaction.listing:
        transaction.listing.is_sold = True
        transaction.listing.save()
    
    # Update seller's sold count
    seller_profile = getattr(transaction.seller, 'profile', None) or Profile.objects.filter(user=transaction.seller).first()
    if seller_profile:
        seller_profile.total_sold += 1
        seller_profile.save(update_fields=['total_sold'])
    
    # Notify seller
    from django.urls import reverse
    Notification.objects.create(
        user=transaction.seller,
        message=f"{transaction.buyer.username} completed the purchase!",
        url=reverse('marketplace:transaction_detail', kwargs={'transaction_id': transaction.pk})
    )
    
    messages.success(request, '✓ Transaction completed! Please rate your experience with the seller.')
    return redirect('marketplace:leave_review', username=transaction.seller.username)


@login_required
def notifications_list(request):
    """Show user's notifications and mark them as read."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Mark all unread as read
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'marketplace/notifications.html', {'notifications': notifications})


# ----- Messaging -----

def _get_or_create_conversation(user1, user2, listing=None):
    """Get existing conversation or create new one between two users."""
    from django.db.models import Q
    convs = Conversation.objects.filter(
        participants=user1
    ).filter(
        participants=user2
    )
    if listing:
        convs = convs.filter(listing=listing)
    else:
        convs = convs.filter(listing__isnull=True)
    conv = convs.first()
    if not conv:
        conv = Conversation.objects.create(listing=listing)
        ConversationParticipant.objects.create(conversation=conv, user=user1)
        ConversationParticipant.objects.create(conversation=conv, user=user2)
    return conv


@login_required
def inbox(request):
    """List user's conversations and transactions."""
    # Get conversations
    convs = Conversation.objects.filter(participants=request.user).prefetch_related(
        'participants', 'messages__sender', 'listing'
    ).order_by('-updated_at')
    convs_with_preview = []
    for conv in convs:
        other = conv.get_other_participant(request.user)
        if not other:
            continue
        prof = getattr(other, 'profile', None) or Profile.objects.filter(user=other).first()
        last_msg = conv.messages.order_by('-created_at').first()
        convs_with_preview.append({
            'conversation': conv,
            'other': other,
            'other_display_name': (prof.display_name if prof else None) or other.username,
            'last_message': last_msg,
        })
    
    # Get pending and confirmed transactions
    transactions = Transaction.objects.filter(
        status__in=['pending', 'confirmed']
    ).filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).select_related('listing', 'buyer', 'seller').order_by('-created_at')
    
    return render(request, 'marketplace/inbox.html', {
        'conversations': convs_with_preview,
        'transactions': transactions,
    })


@login_required
def conversation_view(request, pk):
    """View a conversation and send messages."""
    conv = get_object_or_404(Conversation.objects.prefetch_related('participants', 'messages__sender'), pk=pk)
    if request.user not in conv.participants.all():
        messages.error(request, "You don't have access to this conversation.")
        return redirect('marketplace:inbox')

    other = conv.get_other_participant(request.user)
    other_prof = None
    if other:
        other_prof = getattr(other, 'profile', None) or Profile.objects.filter(user=other).first()
    msgs = conv.messages.select_related('sender').all()

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(conversation=conv, sender=request.user, body=form.cleaned_data['body'])
            return redirect('marketplace:conversation', pk=pk)
    else:
        form = MessageForm()

    return render(request, 'marketplace/conversation.html', {
        'conversation': conv,
        'other': other,
        'other_display_name': (other_prof.display_name if other_prof else None) or (other.username if other else ''),
        'messages': msgs,
        'form': form,
    })


@login_required
def message_send(request, pk):
    """Start a conversation with a listing seller (from listing page)."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller == request.user:
        messages.error(request, "You can't message yourself.")
        return redirect(listing.get_absolute_url())

    conv = _get_or_create_conversation(request.user, listing.seller, listing=listing)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(conversation=conv, sender=request.user, body=form.cleaned_data['body'])
            messages.success(request, 'Message sent!')
            return redirect('marketplace:conversation', pk=conv.pk)
    else:
        form = MessageForm()

    return render(request, 'marketplace/message_send.html', {
        'form': form,
        'listing': listing,
        'conversation': conv,
    })


# ----- Live Forum -----

def forum_index(request):
    """Live forum - list posts, auto-refresh for 'live' feel."""
    posts = ForumPost.objects.select_related('author', 'listing', 'listing__category', 'listing__school').prefetch_related('replies').order_by('-created_at')[:50]
    return render(request, 'marketplace/forum_index.html', {'posts': posts})


def forum_post_detail(request, pk):
    """View a forum post and its replies."""
    post = get_object_or_404(ForumPost.objects.select_related('author', 'listing', 'listing__category', 'listing__school'), pk=pk)
    replies = post.replies.select_related('author').order_by('created_at')

    form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = ForumReplyForm(request.POST)
            if form.is_valid():
                ForumReply.objects.create(post=post, author=request.user, body=form.cleaned_data['body'])
                messages.success(request, 'Reply posted!')
                return redirect('marketplace:forum_post', pk=pk)
        else:
            form = ForumReplyForm()

    return render(request, 'marketplace/forum_post.html', {
        'post': post,
        'replies': replies,
        'form': form,
    })


@login_required
def forum_create_post(request):
    """Create a new forum post, optionally linking a listing."""
    if request.method == 'POST':
        form = ForumPostForm(request.POST, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created!')
            return redirect('marketplace:forum_post', pk=post.pk)
    else:
        form = ForumPostForm(user=request.user)

    return render(request, 'marketplace/forum_form.html', {'form': form, 'title': 'New Post'})
