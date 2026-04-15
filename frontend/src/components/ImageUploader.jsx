import { useEffect, useRef } from 'react'

export default function ImageUploader({ file, previewUrl, loading, onFileSelect, onSubmit }) {
  const inputRef = useRef(null)

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const handleChange = (event) => {
    const selectedFile = event.target.files?.[0] || null
    const nextPreviewUrl = selectedFile ? URL.createObjectURL(selectedFile) : ''

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    onFileSelect(selectedFile, nextPreviewUrl)
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Image Upload</h2>
        <p>Select one image, preview it, then send it to the backend.</p>
      </div>

      <label className="upload-dropzone" htmlFor="mask-image-input">
        <input
          id="mask-image-input"
          name="mask_image"
          ref={inputRef}
          type="file"
          accept="image/*"
          className="file-input"
          onChange={handleChange}
          disabled={loading}
        />
        <span className="dropzone-title">{file ? file.name : 'Choose an image file'}</span>
        <span className="dropzone-subtitle">PNG, JPG, JPEG and other image formats are accepted.</span>
      </label>

      <div className="preview-frame">
        {previewUrl ? <img src={previewUrl} alt="Selected preview" className="preview-image" /> : <p>No image selected yet.</p>}
      </div>

      <button type="button" className="primary-button" onClick={onSubmit} disabled={loading || !file}>
        {loading ? 'Processing...' : 'Send to Backend'}
      </button>
    </section>
  )
}
