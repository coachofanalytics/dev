// Healthcare page JS (image placeholder generation)
function generateImageFallback(imgElementId, placeholderUrl) {
    const imgElement = document.getElementById(imgElementId);
    if (!imgElement) return;
    // If the img already has a non-placeholder src (e.g. /static/... or an uploaded file), do not overwrite it.
    const currentSrc = imgElement.getAttribute('src') || '';
    // Treat data URIs or placehold.co placeholders as empty; otherwise assume it's a real image and keep it
    const isPlaceholder = /placehold\.co|data:image|IMAGE%20UNAVAILABLE/.test(currentSrc);
    if (!currentSrc || isPlaceholder) {
        imgElement.classList.remove('animate-pulse-custom');
        imgElement.src = placeholderUrl;
    }
}

window.addEventListener('load', function() {
    // Provide default placeholders if images don't resolve to srcset/media model
    generateImageFallback('image-hero', 'https://placehold.co/800x400/0a926d/ffffff?text=Healthcare%20Hero');
    generateImageFallback('image-services', 'https://placehold.co/600x400/e0f2f1/000000?text=Healthcare%20Services');
    generateImageFallback('image-insurance', 'https://placehold.co/600x400/fff7e6/000000?text=Insurance%20Options');
});