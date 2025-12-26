const socket = io();  // Connect to backend

// Get session_id from a meta tag or global JS variable
const currentSessionId = window.SESSION_ID || null;

// Listen for checklist updates from server
socket.on("sop_update", data => {
    if (data.session_id !== currentSessionId) return;
    renderChecklist(data.checklist);
});

// Send checkbox changes to server
function updateStep(stepId, checked) {
    socket.emit("checklist_update", {
        session_id: currentSessionId,
        step_id: stepId,
        checked: checked,
        timestamp: new Date().toISOString()
    });
}

// Render checklist in the page
function renderChecklist(checklist) {
    const container = document.getElementById("checklist-container");
    container.innerHTML = "";

    checklist.forEach(step => {
        const div = document.createElement("div");
        div.className = "step";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = step.step_id;
        checkbox.checked = step.checked;

        checkbox.addEventListener("change", () => updateStep(step.step_id, checkbox.checked));

        const label = document.createElement("label");
        label.htmlFor = step.step_id;
        label.innerText = step.description;
        if(step.checked) label.classList.add("checked");

        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });
}
