document.addEventListener('DOMContentLoaded', function() {
    const addPairButton = document.getElementById('add-pair');
    const messagePairsDiv = document.getElementById('message-pairs');

    let pairCount = document.querySelectorAll('.message-pair').length;

    addPairButton.addEventListener('click', function() {
        const pairHTML = `
            <div class="message-pair mb-4">
                <div class="mb-2">
                    <label class="form-label">User Message:</label>
                    <textarea class="form-control user-message" name="user_message" rows="3" required></textarea>
                </div>
                <div class="mb-2">
                    <label class="form-label">Assistant Message:</label>
                    <textarea class="form-control assistant-message" name="assistant_message" rows="3" required></textarea>
                </div>
                <div class="mb-2 form-check">
                    <input type="checkbox" class="form-check-input" name="weight_${pairCount}" id="weight-${pairCount}" checked>
                    <label class="form-check-label" for="weight-${pairCount}">Include Weight</label>
                </div>
                <button type="button" class="btn btn-danger remove-pair"><i class="bi bi-x-circle"></i> Remove</button>
            </div>
        `;
        messagePairsDiv.insertAdjacentHTML('beforeend', pairHTML);
        pairCount++;
    });

    // Event delegation for removing message pairs
    messagePairsDiv.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('remove-pair')) {
            e.target.parentElement.remove();
        } else if (e.target && e.target.parentElement.classList.contains('remove-pair')) {
            e.target.parentElement.parentElement.remove();
        }
    });

    // Keyboard navigation and markdown support
    document.addEventListener('keydown', function(e) {
        const target = e.target;
        if (target.tagName.toLowerCase() !== 'textarea') {
            return;
        }

        if (target.classList.contains('user-message')) {
            if (e.key === 'Enter') {
                if (e.shiftKey) {
                    // Insert newline (default behavior)
                    // No need to prevent default
                } else {
                    e.preventDefault();
                    // Move focus to the corresponding assistant-message textarea
                    const messagePairDiv = target.closest('.message-pair');
                    if (messagePairDiv) {
                        const assistantTextarea = messagePairDiv.querySelector('textarea.assistant-message');
                        if (assistantTextarea) {
                            assistantTextarea.focus();
                        }
                    }
                }
            }
        }

        if (target.classList.contains('assistant-message')) {
            if (e.key === 'Enter') {
                if (e.shiftKey) {
                    // Insert newline (default behavior)
                    // No need to prevent default
                } else {
                    e.preventDefault();
                    // Submit the form
                    const form = target.closest('form');
                    if (form) {
                        form.submit();
                    }
                }
            }
        }
    });
});
