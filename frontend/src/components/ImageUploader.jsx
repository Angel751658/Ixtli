import { useEffect, useState } from 'react'
import './ImageUploader.css'

function ImageUploader({
    targetLanguage,         //  Idioma seleccionado
    onTargetLanguageChange, // Funcion para cambiar el idioma
    onUpload,               // Funcion que ejecutar cuando se suba una imagen
    isUploading            // Indica si actualmente se esta subiendo una imagen
}) {

    const [selectedFile, setSelectedFile] = useState(null)
    const [previewUrl, setPreviewUrl] = useState(null)
    const [error, setError] = useState('')

    // Liberar la URL de la vista previa cuando cambie
    useEffect(() => {
        return () => {
            if (previewUrl) {
                URL.revokeObjectURL(previewUrl)
            }
        }
    }, [previewUrl])

    // Validar la imagen seleccionada (con las especificaciones del back-end)
    function processFile(file) {
        if (!file) return

        const allowedTypes = [
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/webp'
        ]

        if (!allowedTypes.includes(file.type)) {
            setSelectedFile(null)
            setPreviewUrl(null)
            setError('Formato de imagen no permitido')
            return
        }

        if (file.size > 10 * 1024 * 1024) {
            setSelectedFile(null)
            setPreviewUrl(null)
            setError('La imagen no puede superar los 10 MB')
            return
        }

        setSelectedFile(file)
        setPreviewUrl(URL.createObjectURL(file))
        setError('')
    }

    // Validar y guardar la imagen seleccionada
    function handleFileChange(event) {
        const file = event.target.files[0]
        
        processFile(file)
    }

    // Cancelar la selección
    function handleCancel() {
        setSelectedFile(null)
        setPreviewUrl(null)
        setError('')
    }

    // Arrastrar una imagen
    function handleDrop(event) {
        event.preventDefault()

        const file = event.dataTransfer.files[0]

        processFile(file)
    }

    return (
        <section className="panel image-panel">

            <div className="uploader-header panel-header">
                <span className="panel-icon">文A</span>
                <h3>Idiomas</h3>
            </div>

            <div className="language-selector">
                <label htmlFor="target-language">
                    Idioma a traducir:
                </label>

                <select
                    id="target-language"
                    value={targetLanguage}
                    onChange={(event) =>
                        onTargetLanguageChange(event.target.value)
                    }
                >
                    <option value="es">Español</option>
                    <option value="en">Inglés</option>
                    <option value="fr">Francés</option>
                    <option value="de">Alemán</option>
                    <option value="it">Italiano</option>
                    <option value="pt">Portugués</option>
                    <option value="ja">Japonés</option>
                </select>
            </div>

            <input
                id="image-input"
                type="file"
                accept="image/jpeg,image/jpg,image/png,image/webp"
                onChange={handleFileChange}
                hidden
            />

            <label
                htmlFor="image-input"
                className="upload-area"
                onDragOver={(event) => event.preventDefault()}
                onDrop={handleDrop}
            >
                {!previewUrl ? (
                    <>
                        <span className="upload-icon">☁</span>

                        <h4>Arrastra tu imagen aquí</h4>

                        <p>
                            o haz clic para seleccionar un archivo
                        </p>
                    </>
                ) : (
                    <div className="preview-container">
                        <img
                            src={previewUrl}
                            alt="Vista previa de la imagen"
                            className="image-preview"
                        />
                    </div>
                )}
            </label>

            {error && (
                <p className="upload-error">{error}</p>
            )}

            <div className="upload-actions">
                <button
                    type="button"
                    className="cancel-button"
                    onClick={handleCancel}
                    disabled={!selectedFile || isUploading}
                >
                    Cancelar
                </button>

                <button
                    type="button"
                    className="upload-button"
                    onClick={async () => {
                        const sucess = await onUpload(selectedFile, targetLanguage)
                        
                        if (sucess) {
                            handleCancel()
                        }          
                    }}
                    disabled={!selectedFile || isUploading}
                >
                    {isUploading ? 'Subiendo...' : 'Subir'}
                </button>
            </div>
        </section>
    )
}

export default ImageUploader