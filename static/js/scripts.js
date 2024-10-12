document.addEventListener('DOMContentLoaded', function() {
    const addPairButton = document.getElementById('add-pair');
    const messagePairsDiv = document.getElementById('message-pairs');

    addPairButton.addEventListener('click', function() {
        const pairHTML = `
            <div class="message-pair mb-4">
                <div class="mb-2">
                    <label class="form-label">User Message:</label>
                    <textarea class="form-control" name="user_message" rows="3" required></textarea>
                </div>
                <div class="mb-2">
                    <label class="form-label">Assistant Message:</label>
                    <textarea class="form-control" name="assistant_message" rows="3" required></textarea>
                </div>
                <div class="mb-2">
                    <label class="form-label">Weight:</label>
                    <input type="number" class="form-control" name="weight" value="1" min="0" max="1" required>
                </div>
                <button type="button" class="btn btn-danger remove-pair">Remove</button>
            </div>
        `;
        messagePairsDiv.insertAdjacentHTML('beforeend', pairHTML);
    });

    // Event delegation for removing message pairs
    messagePairsDiv.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('remove-pair')) {
            e.target.parentElement.remove();
        }
    });
});
