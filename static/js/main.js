document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('video-upload');
    const loadingState = document.getElementById('loading-state');
    const errorMessage = document.getElementById('error-message');

    // Drag and drop styles
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
    });

    // File input change handler to show selected file name
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const fileName = e.target.files[0].name;
            dropzone.querySelector('p').textContent = fileName;
            dropzone.querySelector('span').textContent = 'Ready to upload';
        }
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        
        if (files.length > 0) {
            const fileName = files[0].name;
            dropzone.querySelector('p').textContent = fileName;
            dropzone.querySelector('span').textContent = 'Ready to upload';
        }
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (fileInput.files.length === 0) {
            showError("Please select a video file first.");
            return;
        }

        const formData = new FormData(form);
        
        // Update UI
        form.classList.add('hidden');
        loadingState.classList.remove('hidden');
        errorMessage.classList.add('hidden');

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Server error occurred');
            }

            // Get filename from Content-Disposition header if possible
            const disposition = response.headers.get('Content-Disposition');
            let filename = 'snapshots.zip';
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Reset UI
            resetUI();
            
        } catch (error) {
            showError(error.message);
            resetUI(false);
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function resetUI(success = true) {
        if (success) {
            form.reset();
            dropzone.querySelector('p').textContent = 'Drag & Drop your video here';
            dropzone.querySelector('span').textContent = 'or click to browse';
        }
        form.classList.remove('hidden');
        loadingState.classList.add('hidden');
    }
});
