// Create a new GCS bucket file upload form
const fileUploadForm = document.createElement('form');
fileUploadForm.method = 'post';
fileUploadForm.enctype = 'multipart/form-data';

// Create an input element for file selection
const fileInput = document.createElement('input');
fileInput.type = 'file';
fileInput.name = 'file';
fileUploadForm.appendChild(fileInput);

// Create a submit button for uploading the file
const submitButton = document.createElement('input');
submitButton.type = 'submit';
submitButton.value = 'Upload';
fileUploadForm.appendChild(submitButton);

// Add the file upload form to the DOM
document.body.appendChild(fileUploadForm);

// Handle form submission
fileUploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Send the file to your backend server
      const response = await fetch('/upload-to-gcs', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        console.log('File uploaded successfully!');
        // Handle the successful upload response
      } else {
        console.error('Failed to upload file:', response.statusText);
        // Handle the upload failure
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      // Handle the upload error
    }
  }
});