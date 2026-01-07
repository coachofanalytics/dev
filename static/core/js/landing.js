/**
 * ============================================================
 * BIASHARA BRIDGES LANDING PAGE JAVASCRIPT
 * ============================================================
 *
 * Features:
 * 1. Hero carousel auto-play
 * 2. Smooth scroll for anchor links
 * 3. Navbar background change on scroll
 * 4. AOS (Animate On Scroll) initialization
 * 5. Mobile menu toggle
 * 6. Contact form validation
 */

(function() {
    'use strict';

    // ============================================================
    // 1. HERO CAROUSEL AUTO-PLAY
    // ============================================================

    let currentHeroIndex = 0;
    const heroImages = [
        '/static/core/images/landing/hero-1.jpg',
        '/static/core/images/landing/hero-2.jpg',
        '/static/core/images/landing/hero-3.jpg',
        '/static/core/images/landing/hero-4.jpg',
        '/static/core/images/landing/hero-5.jpg'
    ];

    function rotateHeroImage() {
        const heroSection = document.getElementById('home');
        if (!heroSection) return;

        currentHeroIndex = (currentHeroIndex + 1) % heroImages.length;

        // Add fade-out effect
        heroSection.style.transition = 'background-image 1s ease-in-out';
        heroSection.style.backgroundImage = `linear-gradient(rgba(17, 21, 24, 0.7), rgba(17, 21, 24, 0.7)), url('${heroImages[currentHeroIndex]}')`;
    }

    // Start carousel on page load
    if (document.getElementById('home')) {
        setInterval(rotateHeroImage, 5000); // Rotate every 5 seconds
    }

    // ============================================================
    // 2. SMOOTH SCROLL FOR ANCHOR LINKS
    // ============================================================

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');

            // Ignore if href is just "#" or empty
            if (!href || href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();

                // Calculate offset for fixed navbar
                const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0;
                const targetPosition = target.offsetTop - navbarHeight - 20; // 20px extra spacing

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });

                // Close mobile menu if open
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                        toggle: true
                    });
                }
            }
        });
    });

    // ============================================================
    // 3. NAVBAR BACKGROUND CHANGE ON SCROLL
    // ============================================================

    const navbar = document.querySelector('.navbar');

    function handleNavbarScroll() {
        if (!navbar) return;

        if (window.scrollY > 100) {
            navbar.classList.add('navbar-scrolled');
            navbar.classList.remove('navbar-transparent');
        } else {
            navbar.classList.remove('navbar-scrolled');
            navbar.classList.add('navbar-transparent');
        }
    }

    // Add scroll event listener with throttling for performance
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        if (scrollTimeout) {
            window.cancelAnimationFrame(scrollTimeout);
        }
        scrollTimeout = window.requestAnimationFrame(handleNavbarScroll);
    });

    // Set initial state
    handleNavbarScroll();

    // ============================================================
    // 4. AOS (ANIMATE ON SCROLL) INITIALIZATION
    // ============================================================

    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,        // Animation duration in ms
            once: true,            // Only animate once
            offset: 100,           // Offset from original trigger point
            easing: 'ease-in-out', // Easing function
            delay: 0,              // Delay between animations
            disable: function() {
                // Disable on mobile for performance
                return window.innerWidth < 768;
            }
        });
    }

    // ============================================================
    // 5. MOBILE MENU TOGGLE & INTERACTIONS
    // ============================================================

    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggler && navbarCollapse) {
        // Add custom behavior when menu opens/closes
        navbarCollapse.addEventListener('show.bs.collapse', function () {
            navbarToggler.setAttribute('aria-expanded', 'true');
        });

        navbarCollapse.addEventListener('hide.bs.collapse', function () {
            navbarToggler.setAttribute('aria-expanded', 'false');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInsideNav = navbar?.contains(event.target);
            const isMenuOpen = navbarCollapse?.classList.contains('show');

            if (!isClickInsideNav && isMenuOpen) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                    toggle: true
                });
            }
        });
    }

    // ============================================================
    // 6. CONTACT FORM VALIDATION & HANDLING
    // ============================================================

    const contactForm = document.getElementById('contactForm');

    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form elements
            const nameInput = document.getElementById('name');
            const emailInput = document.getElementById('email');
            const phoneInput = document.getElementById('phone');
            const subjectInput = document.getElementById('subject');
            const messageInput = document.getElementById('message');

            // Reset previous error states
            [nameInput, emailInput, phoneInput, subjectInput, messageInput].forEach(input => {
                if (input) {
                    input.classList.remove('is-invalid', 'is-valid');
                }
            });

            let isValid = true;

            // Validate Name
            if (!nameInput?.value.trim()) {
                nameInput?.classList.add('is-invalid');
                isValid = false;
            } else {
                nameInput?.classList.add('is-valid');
            }

            // Validate Email
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailInput?.value.trim() || !emailRegex.test(emailInput.value)) {
                emailInput?.classList.add('is-invalid');
                isValid = false;
            } else {
                emailInput?.classList.add('is-valid');
            }

            // Validate Phone (optional but if provided, should be valid)
            const phoneRegex = /^[\d\s\+\-\(\)]+$/;
            if (phoneInput?.value.trim() && !phoneRegex.test(phoneInput.value)) {
                phoneInput?.classList.add('is-invalid');
                isValid = false;
            } else if (phoneInput?.value.trim()) {
                phoneInput?.classList.add('is-valid');
            }

            // Validate Subject
            if (!subjectInput?.value.trim()) {
                subjectInput?.classList.add('is-invalid');
                isValid = false;
            } else {
                subjectInput?.classList.add('is-valid');
            }

            // Validate Message
            if (!messageInput?.value.trim() || messageInput.value.trim().length < 10) {
                messageInput?.classList.add('is-invalid');
                isValid = false;
            } else {
                messageInput?.classList.add('is-valid');
            }

            if (isValid) {
                // Form is valid - show success message
                showFormMessage('success', 'Thank you! Your message has been sent successfully. We will get back to you soon.');

                // Reset form
                contactForm.reset();

                // Remove validation classes after reset
                setTimeout(() => {
                    [nameInput, emailInput, phoneInput, subjectInput, messageInput].forEach(input => {
                        input?.classList.remove('is-valid');
                    });
                }, 3000);

                // TODO: In production, send form data to backend
                // Example AJAX call:
                /*
                fetch('/api/contact/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        name: nameInput.value,
                        email: emailInput.value,
                        phone: phoneInput.value,
                        subject: subjectInput.value,
                        message: messageInput.value
                    })
                })
                .then(response => response.json())
                .then(data => {
                    showFormMessage('success', data.message);
                })
                .catch(error => {
                    showFormMessage('error', 'An error occurred. Please try again.');
                });
                */
            } else {
                // Show error message
                showFormMessage('error', 'Please fill in all required fields correctly.');
            }
        });
    }

    // Helper function to show form messages
    function showFormMessage(type, message) {
        // Remove any existing messages
        const existingMessage = document.querySelector('.form-message');
        if (existingMessage) {
            existingMessage.remove();
        }

        // Create new message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} form-message mt-3`;
        messageDiv.setAttribute('role', 'alert');
        messageDiv.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}-fill me-2"></i>
            ${message}
        `;

        // Insert message after form
        contactForm?.parentNode.insertBefore(messageDiv, contactForm.nextSibling);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);

        // Scroll to message
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // ============================================================
    // 7. UTILITY FUNCTIONS
    // ============================================================

    // Get CSRF token for AJAX requests
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // ============================================================
    // 8. SCROLL INDICATOR (Hero Section)
    // ============================================================

    const scrollIndicator = document.querySelector('.scroll-indicator');

    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', function(e) {
            e.preventDefault();
            const aboutSection = document.getElementById('about');
            if (aboutSection) {
                const navbarHeight = navbar?.offsetHeight || 0;
                window.scrollTo({
                    top: aboutSection.offsetTop - navbarHeight - 20,
                    behavior: 'smooth'
                });
            }
        });

        // Hide scroll indicator when user scrolls
        window.addEventListener('scroll', function() {
            if (scrollIndicator && window.scrollY > 200) {
                scrollIndicator.style.opacity = '0';
            } else if (scrollIndicator) {
                scrollIndicator.style.opacity = '1';
            }
        });
    }

    // ============================================================
    // 9. LAZY LOADING IMAGES (Performance Optimization)
    // ============================================================

    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                }
            });
        });

        // Observe all images with data-src attribute
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // ============================================================
    // 10. NAVBAR ACTIVE LINK HIGHLIGHTING
    // ============================================================

    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    function highlightNavLink() {
        let current = '';
        const scrollPosition = window.scrollY + 200; // Offset for better UX

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;

            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href === `#${current}`) {
                link.classList.add('active');
            }
        });
    }

    // Add scroll event listener for nav highlighting
    let highlightTimeout;
    window.addEventListener('scroll', function() {
        if (highlightTimeout) {
            window.cancelAnimationFrame(highlightTimeout);
        }
        highlightTimeout = window.requestAnimationFrame(highlightNavLink);
    });

    // Set initial active link
    highlightNavLink();

    // ============================================================
    // 11. PERFORMANCE MONITORING (Console Log)
    // ============================================================

    window.addEventListener('load', function() {
        if (window.performance) {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`%cBiashara Bridges Landing Page`, 'color: #b49044; font-size: 16px; font-weight: bold;');
            console.log(`Page Load Time: ${pageLoadTime}ms`);
            console.log(`DOM Ready: ${perfData.domContentLoadedEventEnd - perfData.navigationStart}ms`);
        }
    });

})();
