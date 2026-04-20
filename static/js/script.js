// Form validation
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    });
});

// Format currency in BDT
function formatCurrency(amount) {
    return '৳ ' + parseFloat(amount).toFixed(2);
}

// Confirm delete actions
function confirmDelete() {
    return confirm('এটি মুছে দেবেন নিশ্চিত?');
}

// Add to cart with animation
document.addEventListener('submit', function(e) {
    if (e.target.classList.contains('add-to-cart-form')) {
        const button = e.target.querySelector('button');
        const originalText = button.textContent;
        button.textContent = '✓ যোগ করা হয়েছে';
        button.style.opacity = '0.7';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.opacity = '1';
        }, 2000);
    }
});

// Search functionality
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const products = document.querySelectorAll('.product-card');
        
        products.forEach(product => {
            const productName = product.querySelector('.product-name').textContent.toLowerCase();
            const productDesc = product.querySelector('.product-description').textContent.toLowerCase();
            
            if (productName.includes(searchTerm) || productDesc.includes(searchTerm)) {
                product.style.display = '';
            } else {
                product.style.display = 'none';
            }
        });
    });
}

// Payment form handling
const paymentForm = document.getElementById('paymentForm');
if (paymentForm) {
    paymentForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const button = this.querySelector('button');
        button.disabled = true;
        button.textContent = 'প্রসেস করা হচ্ছে...';
        
        fetch('{{ url_for("process_payment") }}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('✅ পেমেন্ট সফল! অর্ডার #' + data.order_id, 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                showNotification('❌ ' + data.message, 'danger');
                button.disabled = false;
                button.textContent = '✅ পেমেন্ট সম্পন্ন করুন';
            }
        })
        .catch(error => {
            showNotification('❌ একটি ত্রুটি ঘটেছে', 'danger');
            button.disabled = false;
            button.textContent = '✅ পেমেন্ট সম্পন্ন করুন';
        });
    });
}

// Notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 4000);
}

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});