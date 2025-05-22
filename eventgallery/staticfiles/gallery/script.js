document.addEventListener('DOMContentLoaded', () => {
    // Mobile Menu Toggle
    const burgerMenu = document.getElementById('burger-menu');
    const navLinks = document.querySelector('.nav-links');

    burgerMenu.addEventListener('click', () => {
        // Toggle active class for burger menu
        burgerMenu.classList.toggle('active');
        
        // Toggle active class for nav links
        navLinks.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (event) => {
        const isClickInsideNavbar = event.target.closest('.navbar');
        
        if (!isClickInsideNavbar) {
            burgerMenu.classList.remove('active');
            navLinks.classList.remove('active');
        }
    });

    // Close menu when a nav link is clicked
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            burgerMenu.classList.remove('active');
            navLinks.classList.remove('active');
        });
    });

    // Smooth Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Scroll Animations
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.gallery-item, .event-card').forEach(item => {
        observer.observe(item);
    });

    // Lightbox Configuration
    lightbox.option({
        'resizeDuration': 300,
        'wrapAround': true,
        'disableScrolling': true,
        'fadeDuration': 300,
        'albumLabel': 'Image %1 of %2',
        'positionFromTop': 50
    });

    // Optional: Lazy Loading for Images
    const images = document.querySelectorAll('.gallery-item img');
    const lazyLoadOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px 50px 0px'
    };

    const lazyLoadObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    }, lazyLoadOptions);

    images.forEach(img => lazyLoadObserver.observe(img));

    // Zoom Functionality
    const galleryCards = document.querySelectorAll('.gallery-card');

    galleryCards.forEach(card => {
        const image = card.querySelector('img');
        const zoomInBtn = card.querySelector('.zoom-in');
        const zoomOutBtn = card.querySelector('.zoom-out');

        let scale = 1;
        const maxScale = 2;
        const minScale = 1;

        zoomInBtn.addEventListener('click', () => {
            if (scale < maxScale) {
                scale += 0.2;
                image.style.transform = `scale(${scale})`;
            }
        });

        zoomOutBtn.addEventListener('click', () => {
            if (scale > minScale) {
                scale -= 0.2;
                image.style.transform = `scale(${scale})`;
            }
        });
    });

    // Optional: Reset zoom on mouse leave
    galleryCards.forEach(card => {
        card.addEventListener('mouseleave', () => {
            const image = card.querySelector('img');
            image.style.transform = 'scale(1)';
        });
    });

    // 🌐 System Preference Detection
    // Automatically adapt to user's system-level theme preferences
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

    // 👀 System Theme Change Listener
    prefersDarkScheme.addListener(e => {
        const newTheme = e.matches ? 'dark' : 'light';
        applyTheme(newTheme);
    });

    // 🌅 Initial System Theme Detection
    // Apply system theme on first load if no previous preference exists
    if (prefersDarkScheme.matches && !localStorage.getItem('theme')) {
        applyTheme('dark');
    }

    // Add Lightbox Functionality
    const galleryItems = document.querySelectorAll('.gallery-item img');
    
    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            const lightbox = document.createElement('div');
            lightbox.classList.add('lightbox');
            
            const lightboxImg = document.createElement('img');
            lightboxImg.src = this.src;
            lightboxImg.alt = this.alt;
            
            const closeBtn = document.createElement('span');
            closeBtn.innerHTML = '&times;';
            closeBtn.classList.add('lightbox-close');
            
            lightbox.appendChild(lightboxImg);
            lightbox.appendChild(closeBtn);
            
            document.body.appendChild(lightbox);
            
            // Close lightbox
            closeBtn.addEventListener('click', function() {
                document.body.removeChild(lightbox);
            });
            
            lightbox.addEventListener('click', function(e) {
                if (e.target === lightbox) {
                    document.body.removeChild(lightbox);
                }
            });
        });
    });
});
