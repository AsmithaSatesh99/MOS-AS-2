document.addEventListener('DOMContentLoaded', function() {
    // Lazy loading for images
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add animation to cards when they come into view
    const animateOnScroll = () => {
        const cards = document.querySelectorAll('.image-card, .result-card');
        cards.forEach(card => {
            const cardPosition = card.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.2;
            
            if (cardPosition < screenPosition) {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    };

    // Set initial state
    const cards = document.querySelectorAll('.image-card, .result-card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });

    // Run on load and scroll
    window.addEventListener('load', animateOnScroll);
    window.addEventListener('scroll', animateOnScroll);
});

// Header animation
document.addEventListener('DOMContentLoaded', function() {
    // Animate bubbles
    const bubbles = document.querySelectorAll('.header-bubble');
    
    bubbles.forEach((bubble, index) => {
        // Random initial position adjustments
        const randomX = Math.random() * 20 - 10;
        const randomY = Math.random() * 20 - 10;
        bubble.style.transform = `translate(${randomX}px, ${randomY}px)`;
        
        // Animate bubbles continuously
        setInterval(() => {
            const moveX = Math.random() * 4 - 2;
            const moveY = Math.random() * 4 - 2;
            bubble.style.transform = `translate(${moveX}px, ${moveY}px)`;
        }, 3000 + index * 1000);
    });
    
    // Header scroll effect
    const header = document.querySelector('.vibrant-header');
    let lastScroll = 0;
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        if (currentScroll <= 0) {
            header.style.transform = 'translateY(0)';
            header.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.1)';
        } 
        
        if (currentScroll > lastScroll && currentScroll > 100) {
            header.style.transform = 'translateY(-100%)';
        } else if (currentScroll < lastScroll) {
            header.style.transform = 'translateY(0)';
            header.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.2)';
        }
        lastScroll = currentScroll;
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Initialize method selection
    const methodRadios = document.querySelectorAll('input[name="search-method"]');
    const searchForms = document.querySelectorAll('.search-form');
    
    // Set initial method from localStorage or default to 'semantic'
    const initialMethod = localStorage.getItem('searchMethod') || 'vsm';
    
    // Update all forms with the current method
    function updateFormsWithMethod(method) {
        searchForms.forEach(form => {
            // Remove any existing hidden method input
            const existingInput = form.querySelector('input[name="method"]');
            if (existingInput) {
                form.removeChild(existingInput);
            }
            
            // Add new hidden input with current method
            const methodInput = document.createElement('input');
            methodInput.type = 'hidden';
            methodInput.name = 'method';
            methodInput.value = method;
            form.appendChild(methodInput);
        });
    }
    
    // Set initial state
    methodRadios.forEach(radio => {
        if (radio.value === initialMethod) {
            radio.checked = true;
        }
        
        radio.addEventListener('change', function() {
            const selectedMethod = this.value;
            localStorage.setItem('searchMethod', selectedMethod);
            updateFormsWithMethod(selectedMethod);
        });
    });
    
    // Initialize forms with the current method
    updateFormsWithMethod(initialMethod);
});