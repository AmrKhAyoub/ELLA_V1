const socket = new WebSocket('ws://127.0.0.1:8000/ws/notifications/1/');

socket.onopen = function(e) {
  console.log("[open] Connection established. Waiting for notifications...");
};

socket.onmessage = function(event) {
  console.log(`[message] NOTIFICATION RECEIVED: ${event.data}`);
};