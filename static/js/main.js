document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('video-upload');
    const loadingState = document.getElementById('loading-state');
    const errorMessage = document.getElementById('error-message');
    const previewSection = document.getElementById('preview-section');
    const previewGrid = document.getElementById('preview-grid');
    
    const toggleAdvanced = document.getElementById('toggle-advanced');
    const advancedSettings = document.getElementById('advanced-settings');
    const qualityInput = document.getElementById('quality');
    const qualityVal = document.getElementById('quality-val');
    
    const loadingText = document.getElementById('loading-text');
    const progressBar = document.getElementById('progress-bar');
    
    const downloadAllBtn = document.getElementById('download-all-btn');
    const startOverBtn = document.getElementById('start-over-btn');
    
    let currentTaskId = null;

    // Toggle advanced settings
    if (toggleAdvanced && advancedSettings) {
        toggleAdvanced.addEventListener('click', () => {
            advancedSettings.classList.toggle('hidden');
            if (advancedSettings.classList.contains('hidden')) {
                toggleAdvanced.textContent = 'Advanced Settings ▾';
            } else {
                toggleAdvanced.textContent = 'Advanced Settings ▴';
            }
        });
    }

    // Update quality value
    if (qualityInput && qualityVal) {
        qualityInput.addEventListener('input', (e) => {
            qualityVal.textContent = e.target.value;
        });
    }

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

        // Client side size validation
        const file = fileInput.files[0];
        if (file.size > 500 * 1024 * 1024) {
            showError("File size exceeds 500MB limit.");
            return;
        }

        const formData = new FormData(form);
        
        // Update UI
        form.classList.add('hidden');
        loadingState.classList.remove('hidden');
        errorMessage.classList.add('hidden');
        previewSection.classList.add('hidden');
        loadingText.textContent = "Uploading your video...";
        progressBar.style.width = '0%';

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Server error occurred');
            }
            
            const data = await response.json();
            currentTaskId = data.task_id;
            
            loadingText.textContent = "Processing video...";
            
            // Listen to SSE for progress
            const eventSource = new EventSource(`/status/${currentTaskId}`);
            
            eventSource.onmessage = function(event) {
                const taskData = JSON.parse(event.data);
                
                if (taskData.status === 'processing') {
                    progressBar.style.width = `${taskData.progress}%`;
                    loadingText.textContent = `Extracting frames (${taskData.progress}%)...`;
                } else if (taskData.status === 'completed') {
                    eventSource.close();
                    loadingText.textContent = "Loading previews...";
                    progressBar.style.width = '100%';
                    loadPreviews(currentTaskId);
                } else if (taskData.status === 'error') {
                    eventSource.close();
                    showError(taskData.error || "An error occurred during processing.");
                    resetUI(false);
                }
            };
            
            eventSource.onerror = function() {
                eventSource.close();
                showError("Lost connection to server while processing.");
                resetUI(false);
            };

        } catch (error) {
            showError(error.message);
            resetUI(false);
        }
    });
    
    async function loadPreviews(taskId) {
        try {
            const response = await fetch(`/results/${taskId}`);
            if (!response.ok) throw new Error("Failed to load results");
            const data = await response.json();
            
            previewGrid.innerHTML = '';
            
            if (data.files && data.files.length > 0) {
                data.files.forEach(file => {
                    const card = document.createElement('div');
                    card.className = 'image-card';
                    card.dataset.filename = file;
                    
                    const img = document.createElement('img');
                    img.src = `/results/${taskId}/${file}`;
                    img.loading = 'lazy';
                    
                    const deleteBtn = document.createElement('button');
                    deleteBtn.className = 'delete-btn';
                    deleteBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>';
                    
                    deleteBtn.addEventListener('click', () => deleteImage(taskId, file, card));
                    
                    card.appendChild(img);
                    card.appendChild(deleteBtn);
                    previewGrid.appendChild(card);
                });
            } else {
                previewGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">No frames extracted.</p>';
            }
            
            loadingState.classList.add('hidden');
            previewSection.classList.remove('hidden');
            
        } catch (error) {
            showError("Error loading previews: " + error.message);
            resetUI(false);
        }
    }
    
    async function deleteImage(taskId, filename, cardElement) {
        try {
            const response = await fetch(`/results/${taskId}/${filename}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                cardElement.remove();
            } else {
                alert("Failed to delete image");
            }
        } catch (error) {
            console.error("Delete error:", error);
            alert("Error deleting image");
        }
    }

    if (downloadAllBtn) {
        downloadAllBtn.addEventListener('click', () => {
            if (currentTaskId) {
                window.location.href = `/download/${currentTaskId}`;
                downloadAllBtn.textContent = "Downloading...";
                setTimeout(() => {
                    downloadAllBtn.textContent = "Download All (.zip)";
                }, 3000);
            }
        });
    }
    
    if (startOverBtn) {
        startOverBtn.addEventListener('click', () => {
            resetUI(true);
        });
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function resetUI(success = true) {
        if (success) {
            form.reset();
            dropzone.querySelector('p').textContent = 'Drag & Drop your video here';
            dropzone.querySelector('span').textContent = 'or click to browse';
            if (qualityVal) qualityVal.textContent = '95';
        }
        form.classList.remove('hidden');
        loadingState.classList.add('hidden');
        previewSection.classList.add('hidden');
        if (progressBar) progressBar.style.width = '0%';
        currentTaskId = null;
    }
});
