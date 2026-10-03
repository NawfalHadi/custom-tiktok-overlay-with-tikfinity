let websocket = null;

function connect() {
    if (websocket) return; // Already connected

    websocket = new WebSocket("ws://localhost:21213/");

    websocket.onopen = function () {
        document.getElementById("status").innerHTML = "Connected";
    }

    websocket.onclose = function () {
        document.getElementById("status").innerHTML = "Disconnected";
        websocket = null;
        setTimeout(connect, 1000); // Schedule a reconnect attempt
    }

    websocket.onerror = function () {
        document.getElementById("status").innerHTML = "Connection Failed";
        websocket = null;
        setTimeout(connect, 1000); // Schedule a reconnect attempt
    }

    websocket.onmessage = function (event) {
        let parsedData = JSON.parse(event.data); // Parse the JSON data

        console.log("Data received", parsedData);

        let eventLog = document.getElementById("eventLog");
        let newEvent = document.createElement("div");

        // create expandable div
        newEvent.innerHTML = `
            <details>
                <summary>Event: ${parsedData.event} ${parsedData.data?.uniqueId ? ('(@' + parsedData.data.uniqueId + ')') : ''}</summary>
                <p><pre>${JSON.stringify(parsedData, null, 2)}</pre></p>
            </details>
            <br>
        `;

        eventLog.appendChild(newEvent);
    }
}

// Try connect when window is loaded
window.addEventListener('load', connect);