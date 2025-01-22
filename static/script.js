document.getElementById("mcq-form").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent page refresh

    // Create an array to store the answers
    let answers = [];
    
    // Get all select elements and extract their values
    for(let i = 1; i <= 9; i++) {
        const select = document.querySelector(`select[name="q${i}"]`);
        if(select) {
            answers.push(parseInt(select.value));
        }
    }

    // Check if we have all 9 answers
    if(answers.length !== 9) {
        document.getElementById("result").textContent = "Please answer all questions";
        return;
    }

    // Send the data to the server
    fetch("/quiz_predict", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            // Add CSRF token if you're using Flask-WTF
        },
        body: JSON.stringify({ answers: answers })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        document.getElementById("result").textContent = "Depression Level: " + data.depression_level;
    })
    .catch(error => {
        console.error("Error:", error);
        document.getElementById("result").textContent = "An error occurred. Please try again.";
    });
});