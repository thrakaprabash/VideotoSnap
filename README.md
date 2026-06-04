# Video to Snap

![Video to Snap Header](./header.png)

**Video to Snap** is a powerful, modern web application that allows you to easily extract evenly-spaced, high-quality snapshot frames from your video files. Built with a sleek dark-mode glassmorphism aesthetic, it acts as a comprehensive curation tool rather than just a simple extraction script.

## ✨ Key Features

*   **Beautiful UI/UX:** A stunning glassmorphism interface with drag-and-drop file upload support.
*   **Asynchronous Processing:** Heavy video processing is offloaded to a background thread. Real-time progress is streamed back to the browser via Server-Sent Events (SSE) to update a sleek progress bar.
*   **Interactive Preview & Curation:** Instead of forcing a blind download, extracted frames are displayed in a gorgeous masonry grid in your browser. You can hover over frames to delete blurry or unwanted ones before downloading the final batch.
*   **Dynamic ZIP Generation:** The final `.zip` file is dynamically generated on-the-fly containing only the curated images you chose to keep.
*   **Advanced Settings Control:**
    *   **Time Ranges:** Target a specific segment of the video using Start and End times.
    *   **Multiple Formats:** Export snapshots as `JPG`, `PNG`, or `WebP`.
    *   **Adjustable Quality:** Dial in your preferred image compression quality (1-100%).
    *   **Timestamp Watermarking:** Optionally burn the exact video timestamp (`MM:SS.ms`) onto the bottom-right corner of the extracted frames.
*   **Server Hygiene:** Automated background cleanup scripts ensure that abandoned temporary processing folders are wiped from the server to preserve disk space.

## 🛠️ Technology Stack

*   **Backend:** Python 3, Flask (Web Framework), OpenCV (`cv2` for video processing)
*   **Frontend:** HTML5, Vanilla JavaScript (ES6+), CSS3 (CSS Variables, Flexbox/Grid)

## 🚀 Installation & Setup

1.  **Clone or Download the Repository**
    Make sure you have all the project files in a single directory.

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    
    # Activate on Windows
    venv\Scripts\activate
    
    # Activate on macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    Ensure you have `opencv-python`, `flask`, and `werkzeug` installed. You can install them via the `requirements.txt` file (if available) or manually:
    ```bash
    pip install Flask opencv-python Werkzeug
    ```

4.  **Run the Application**
    Start the Flask development server:
    ```bash
    python app.py
    ```

5.  **Access the App**
    Open your web browser and navigate to:
    `http://127.0.0.1:5000/`

## 💡 How to Use

1.  **Upload:** Drag and drop a video file into the upload zone (or click to browse).
2.  **Configure:** 
    * Set the number of snapshots you want to extract.
    * Select your desired output format (JPG, PNG, WebP).
    * Click **Advanced Settings** if you wish to set a specific time range, adjust image quality, or add a timestamp watermark.
3.  **Generate:** Click "Generate Snapshots". Watch the real-time progress bar as the server processes the video.
4.  **Curate:** Review the generated frames in the preview grid. Hover over any image and click the red trash can icon to delete frames you don't want.
5.  **Download:** Click **Download All (.zip)** to save your curated collection!

## 🤝 Contributing
Feel free to open issues or submit pull requests if you want to add new features, fix bugs, or improve the UI/UX.

## 📝 License
This project is open-source and available under the [MIT License](LICENSE).
