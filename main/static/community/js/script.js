// Community Page Image Loader
window.onload = function() {
    const images = [
        { id: 'image-hero', defaultAlt: 'Community Hero Image' },
        { id: 'image-forums', defaultAlt: 'Forums and Networking' },
        { id: 'image-events', defaultAlt: 'Community Events' }
    ];

    images.forEach(imgData => {
        const imgElement = document.getElementById(imgData.id);
        if (!imgElement) return;

        // Set src from data-src attribute
        const staticPath = imgElement.dataset.src;
        if (staticPath) {
            imgElement.src = staticPath;
            imgElement.alt = imgData.defaultAlt;
        }
    });
};
