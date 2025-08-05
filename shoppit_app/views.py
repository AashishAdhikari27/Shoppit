from django.conf import settings
from django.shortcuts import render
from django.contrib.auth import get_user_model
from functools import reduce
from operator import or_
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem, Category, CustomerAddress, Order, OrderItem, Product, Review, Wishlist



from .serializers import CartItemSerializer, UpdateCartItemSerializer, CartSerializer, AddToCartSerializer, CategoryDetailSerializer, CategoryListSerializer, CustomerAddressSerializer, OrderSerializer, ProductListSerializer, ProductDetailSerializer, ReviewSerializer, UpdateReviewSerializer, ReviewCreateSerializer, SimpleCartSerializer, UserSerializer, WishlistSerializer, UpdateWishlistSerializer, UserCreateSerializer



from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from drf_spectacular.utils import extend_schema

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

# # Create your views here.
# stripe.api_key = settings.STRIPE_SECRET_KEY
# endpoint_secret = settings.WEBHOOK_SECRET


## Getting custom user model of the project
User = get_user_model()




@api_view(['GET'])
def product_list(request):
    # products = Product.objects.filter(featured=True)
    products = Product.objects.all()
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    serializer = ProductDetailSerializer(product)
    return Response(serializer.data)


@api_view(["GET"])
def category_list(request):
    categories = Category.objects.all()
    serializer = CategoryListSerializer(categories, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def category_detail(request, slug):
    category = Category.objects.get(slug=slug)
    serializer = CategoryDetailSerializer(category)
    return Response(serializer.data)



@extend_schema(
    request=AddToCartSerializer,
    responses=CartSerializer,
)
@api_view(["POST"])
def add_to_cart(request):
    serializer = AddToCartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    cart_code = serializer.validated_data["cart_code"]
    product_id = serializer.validated_data["product_id"]

    cart, created = Cart.objects.get_or_create(cart_code=cart_code)
    product = Product.objects.get(id=product_id)

    cartitem, created = CartItem.objects.get_or_create(product=product, cart=cart)
    cartitem.quantity = 1 
    cartitem.save() 

    serializer = CartSerializer(cart)
    return Response(serializer.data)




@extend_schema(
    request=UpdateCartItemSerializer,
    responses=CartItemSerializer,
)
@api_view(['PUT'])
def update_cartitem_quantity(request):
    serializer = UpdateCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    cartitem_id = serializer.validated_data["item_id"]
    quantity = serializer.validated_data["quantity"]

    cartitem = CartItem.objects.get(id=cartitem_id)
    cartitem.quantity = quantity
    cartitem.save()

    response_serializer = CartItemSerializer(cartitem)
    
    return Response({
        "data": response_serializer.data,
        "message": "Cart item updated successfully!"
    })







@extend_schema(
    request=ReviewCreateSerializer,
    responses=ReviewSerializer,
)
@api_view(["POST"])
def add_review(request):

    serializer = ReviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data.get("product_id")
    email = serializer.validated_data.get("email")
    rating = serializer.validated_data.get("rating")
    review_text = request.data.get("review")

    product = Product.objects.get(id=product_id)
    user = User.objects.get(email=email)

    if Review.objects.filter(product=product, user=user).exists():
        return Response({"error": "You already dropped a review for this product"}, status=400)

    review  = Review.objects.create(product=product, user=user, rating=rating, review=review_text)

    serializer = ReviewSerializer(review)
    
    return Response(serializer.data)








@extend_schema(
    request=UpdateReviewSerializer,  
    responses=ReviewSerializer       
)
@api_view(['PUT'])
def update_review(request, pk):

    serializer = UpdateReviewSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    review = Review.objects.get(id=pk) 

    review.rating = serializer.validated_data["rating"]
    review.review = serializer.validated_data["review"]

    review.save()

    response_serializer = ReviewSerializer(review)

    return Response(response_serializer.data)




@api_view(['DELETE'])
def delete_review(request, pk):
    review = Review.objects.get(id=pk) 
    review.delete()

    return Response("Review deleted successfully!", status=204)

@api_view(['DELETE'])
def delete_cartitem(request, pk):
    cartitem = CartItem.objects.get(id=pk) 
    cartitem.delete()

    return Response("Cartitem deleted successfully!", status=204)



@extend_schema(
    request=UpdateWishlistSerializer,
    responses={201: WishlistSerializer, 204: OpenApiTypes.STR},
)
@api_view(['POST'])
def update_wishlist(request):

    serializer = UpdateWishlistSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    product_id = serializer.validated_data["product_id"]

    user = User.objects.get(email=email)
    product = Product.objects.get(id=product_id)

    wishlist = Wishlist.objects.filter(user=user, product=product)

    if wishlist.exists():
        wishlist.delete()
        return Response("Wishlist deleted successfully !", status=204)

    new_wishlist = Wishlist.objects.create(user=user, product=product)

    response_serializer = WishlistSerializer(new_wishlist)

    return Response(response_serializer.data, status=201)




@extend_schema(
    parameters=[
        OpenApiParameter(
            name='query',
            description='Search keyword(s) for product name, description, or category name',
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses=ProductListSerializer(many=True),
)
@api_view(['GET'])
def product_search(request):
    query = request.query_params.get("query")
    if not query:
        return Response({"detail": "No query provided"}, status=status.HTTP_400_BAD_REQUEST)

    keywords = query.strip().split()

    # Build Q objects for each keyword
    q_objects = [
        Q(name__icontains=kw) |
        Q(description__icontains=kw) |
        Q(category__name__icontains=kw)
        for kw in keywords
    ]

    # Combine all Q objects with OR
    final_query = reduce(or_, q_objects)

    products = Product.objects.filter(final_query).distinct()
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)
    






@api_view(['POST'])
def create_checkout_session(request):
    cart_code = request.data.get("cart_code")
    email = request.data.get("email")
    cart = Cart.objects.get(cart_code=cart_code)
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email= email,
            payment_method_types=['card'],


            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': item.product.name},
                        'unit_amount': int(item.product.price * 100),  # Amount in cents
                    },
                    'quantity': item.quantity,
                }
                for item in cart.cartitems.all()
            ] + [
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'VAT Fee'},
                        'unit_amount': 500,  # $5 in cents
                    },
                    'quantity': 1,
                }
            ],


           
            mode='payment',
            # success_url="http://localhost:3000/success",
            # cancel_url="http://localhost:3000/cancel",

            success_url="https://next-shop-self.vercel.app/success",
            cancel_url="https://next-shop-self.vercel.app/failed",
            metadata = {"cart_code": cart_code}
        )
        return Response({'data': checkout_session})
    except Exception as e:
        return Response({'error': str(e)}, status=400)




@csrf_exempt
def my_webhook_view(request):
  payload = request.body
  sig_header = request.META['HTTP_STRIPE_SIGNATURE']
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    return HttpResponse(status=400)

  if (
    event['type'] == 'checkout.session.completed'
    or event['type'] == 'checkout.session.async_payment_succeeded'
  ):
    session = event['data']['object']
    cart_code = session.get("metadata", {}).get("cart_code")

    fulfill_checkout(session, cart_code)


  return HttpResponse(status=200)



def fulfill_checkout(session, cart_code):
    
    order = Order.objects.create(stripe_checkout_id=session["id"],
        amount=session["amount_total"],
        currency=session["currency"],
        customer_email=session["customer_email"],
        status="Paid")
    

    print(session)


    cart = Cart.objects.get(cart_code=cart_code)
    cartitems = cart.cartitems.all()

    for item in cartitems:
        orderitem = OrderItem.objects.create(order=order, product=item.product, 
                                             quantity=item.quantity)
    
    cart.delete()




# Newly Added


@extend_schema(
    request=UserCreateSerializer,
    responses={201: UserSerializer},
    description="Create a new user with username, email, first_name, last_name, and profile_picture_url"
)
@api_view(["POST"])
def create_user(request):
    serializer = UserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    new_user = serializer.save()
    output_serializer = UserSerializer(new_user)
    return Response(output_serializer.data, status=status.HTTP_201_CREATED)





@api_view(["GET"])
def existing_user(request, email):
    try:
        User.objects.get(email=email)
        return Response({"exists": True}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"exists": False}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_orders(request):
    email = request.query_params.get("email")
    orders = Order.objects.filter(customer_email=email)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def add_address(request):
    email = request.data.get("email")
    street = request.data.get("street")
    city = request.data.get("city")
    state = request.data.get("state")
    phone = request.data.get("phone")

    if not email:
        return Response({"error": "Email is required"}, status=400)
    
    customer = User.objects.get(email=email)

    address, created = CustomerAddress.objects.get_or_create(
        customer=customer)
    address.email = email 
    address.street = street 
    address.city = city 
    address.state = state
    address.phone = phone 
    address.save()

    serializer = CustomerAddressSerializer(address)
    return Response(serializer.data)


@api_view(["GET"])
def get_address(request):
    email = request.query_params.get("email") 
    address = CustomerAddress.objects.filter(customer__email=email)
    if address.exists():
        address = address.last()
        serializer = CustomerAddressSerializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({"error": "Address not found"}, status=200)





@extend_schema(
    parameters=[
        OpenApiParameter(
            name="email",
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.QUERY,
            required=True,
            description="User email to filter wishlists"
        ),
    ],
    responses=WishlistSerializer(many=True),
)
@api_view(["GET"])
def my_wishlists(request):

    email = request.query_params.get("email")

    if not email:
        return Response({"error": "Email is required"}, status=400)


    wishlists = Wishlist.objects.filter(user__email=email)

    serializer = WishlistSerializer(wishlists, many=True)

    return Response(serializer.data)



@api_view(["GET"])
def product_in_wishlist(request):
    email = request.query_params.get("email")
    product_id = request.query_params.get("product_id")

    if Wishlist.objects.filter(product__id=product_id, user__email=email).exists():
        return Response({"product_in_wishlist": True})
    return Response({"product_in_wishlist": False})



@api_view(['GET'])
def get_cart(request, cart_code):
    cart = Cart.objects.filter(cart_code=cart_code).first()
    
    if cart:
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)




@api_view(['GET'])
def get_cart_stat(request):
    cart_code = request.query_params.get("cart_code")
    cart = Cart.objects.filter(cart_code=cart_code).first()

    if cart:
        serializer = SimpleCartSerializer(cart)
        return Response(serializer.data)
    return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)





@extend_schema(
    parameters=[
        OpenApiParameter(name='cart_code', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name='product_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True),
    ],
    responses={"200": OpenApiTypes.OBJECT},  # or you can define a response schema too
)
@api_view(['GET'])
def product_in_cart(request):
    cart_code = request.query_params.get("cart_code")
    product_id = request.query_params.get("product_id")
    
    cart = Cart.objects.filter(cart_code=cart_code).first()
    product = Product.objects.get(id=product_id)
    
    # product_exists_in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

    product_exists_in_cart = CartItem.objects.filter(cart=cart, product=product)

    serializer = CartItemSerializer(product_exists_in_cart, many=True)
    return Response(serializer.data)

