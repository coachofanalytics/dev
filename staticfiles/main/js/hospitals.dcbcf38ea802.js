function findNearbyHospitals() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                // Create Google Maps URL for nearby hospitals
                const mapsUrl = `https://www.google.com/maps/search/hospitals/@${lat},${lng},13z`;
                // Open in new tab
                window.open(mapsUrl, '_blank');
            },
            // Error callback
            function(error) {
                // If geolocation fails, open a generic "hospitals near me" search
                window.open('https://www.google.com/maps/search/hospitals/', '_blank');
                console.error("Error getting location:", error);
            },
            // Options
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        // If geolocation is not supported, open generic search
        window.open('https://www.google.com/maps/search/hospitals/', '_blank');
    }
}