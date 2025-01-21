document.getElementById("mcq-form").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent page refresh

    let answers = [];
    document.querySelectorAll("select").forEach(select => {
        answers.push(parseInt(select.value));
    });

    fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: answers })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("result").textContent = "Depression Level: " + data.depression_level;
    })
    .catch(error => console.error("Error:", error));
});
