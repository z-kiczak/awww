document.addEventListener("DOMContentLoaded", () => {

    function initImageHandlers() {
        console.log("Image loaded, dimensions:", image.naturalWidth, image.naturalHeight);
        // Move your click handler setup here
        image.addEventListener("click", async (event: MouseEvent) => {
            // ... existing click handler code ...
        });
    }

    const image = document.getElementById("background-image") as HTMLImageElement;
    if (image.complete) {
        initImageHandlers();
    } else {
        image.addEventListener('load', initImageHandlers);
    }


    const imageContainer = document.getElementById("image-container") as HTMLElement;
    const csrfToken = document.querySelector("input[name=csrfmiddlewaretoken]") as HTMLInputElement;
    if (!csrfToken) {
        console.error("CSRF token not found!");
        return;
    }

    // DEBUGS
    console.log("Image click detected"); // [!++]
    const rect = image.getBoundingClientRect();
    console.log("Image dimensions:", rect); // [!++]

    if (!image || !imageContainer || !csrfToken) {
        console.error('Missing required elements');
        return;
    }

    image.addEventListener("click", async (event: MouseEvent) => {
        const rect = image.getBoundingClientRect();
        const scaleX = image.naturalWidth / rect.width;
        const scaleY = image.naturalHeight / rect.height;

        const clickX = Math.round(event.offsetX * scaleX);
        const clickY = Math.round(event.offsetY * scaleY);

        console.log("Calculated coordinates:", clickX, clickY); // [!++]
        showTemporaryMarker(event.offsetX, event.offsetY);

        try {
            const routeId = imageContainer.dataset.routeId;
            console.log("Attempting to create point for route:", routeId); // [!++]
            
            const response = await fetch(`/api/routes/${routeId}/points/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken.value
                },
                body: JSON.stringify({
                    x: clickX,
                    y: clickY
                })
            });
        
            console.log("Response status:", response.status); // [!++]
            const responseBody = await response.text(); // [!++]
            console.log("Response body:", responseBody); // [!++]
            
            if (response.ok) {
                window.location.reload(); // Przeładuj stronę
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });

    let currentMarker: HTMLElement | null = null;

    function showTemporaryMarker(x: number, y: number) {
        // Usuń istniejący znacznik
        if (currentMarker) {
            currentMarker.remove();
        }

        // Stwórz nowy znacznik
        currentMarker = document.createElement("div");
        currentMarker.style.position = "absolute";
        currentMarker.style.left = `${x}px`;
        currentMarker.style.top = `${y}px`;
        currentMarker.style.width = "20px";
        currentMarker.style.height = "20px";
        currentMarker.style.backgroundColor = "rgba(255, 0, 0, 0.8)";
        currentMarker.style.border = "2px solid white";
        currentMarker.style.borderRadius = "50%";
        currentMarker.style.transform = "translate(-50%, -50%)";
        currentMarker.style.pointerEvents = "none";
        currentMarker.style.zIndex = "10000";

        imageContainer.appendChild(currentMarker);
    }

    function showPointHandler(this: HTMLButtonElement, e: Event) {
        e.preventDefault();
        const parent = this.closest(".point-row") as HTMLElement;
        if (!parent) return;

        const x = parseFloat(parent.dataset.x || "0");
        const y = parseFloat(parent.dataset.y || "0");
        
        const rect = image.getBoundingClientRect();
        const posX = (x / image.naturalWidth) * rect.width;
        const posY = (y / image.naturalHeight) * rect.height;

        showTemporaryMarker(posX, posY);
    }

    // Initialize existing buttons
    document.querySelectorAll(".show-point-btn").forEach(btn => {
        btn.addEventListener("click", showPointHandler);
    });
});