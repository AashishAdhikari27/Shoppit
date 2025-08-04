// Initialize cart
function initializeCart() {
    let cartCode = localStorage.getItem('cart_code');
    if (!cartCode) {
        cartCode = 'cart_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('cart_code', cartCode);
    }
    return cartCode;
}

// Update cart counter
function updateCartCounter() {
    const cartCode = initializeCart();
    fetch(`/get_cart_stat?cart_code=${cartCode}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('cartCounter').textContent = data.num_of_items || '0';
        });
}

// Add to cart
document.addEventListener('click', function(e) {
    if (e.target.closest('.add-to-cart')) {
        const productId = e.target.closest('.add-to-cart').dataset.id;
        const cartCode = initializeCart();
        
        fetch('/add_to_cart/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                cart_code: cartCode,
                product_id: productId
            })
        }).then(() => {
            updateCartCounter();
            showToast('Added to cart!');
        });
    }
});

// Initialize on load
document.addEventListener('DOMContentLoaded', function() {
    initializeCart();
    updateCartCounter();
});