import { useEffect, useState } from 'react'
import { deleteImage, processImage, getImages } from '../services/api'
import './ImageGallery.css'

const API_URL = 'http://127.0.0.1:8000'

function ImageGallery({ refreshTrigger, targetLanguage, onTranslationResult }) {
    const [images, setImages] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [deletingId, setDeletingId] = useState(null)
    const [processingId, setProcessingId] = useState(null)

    // Obtener las imágenes almacenadas en S3
    useEffect(() => {
        async function fetchImages() {
            try {
                const data = await getImages()

                setImages(data.imagenes.slice(0, 5))
            } 
            
            catch (err) {
                setError(err.message)
            } 
            
            finally {
                setLoading(false)
            }
        }

        fetchImages()
    }, [refreshTrigger])

    // Eliminar una imagen de S3
    async function handleDelete(imageId) {
        try {
            setDeletingId(imageId)
            setError('')

            await deleteImage(imageId)

            // Actualizar la galería sin volver a consultar la API
            setImages(currentImages =>
                currentImages.filter(
                    image => image.image_id !== imageId
                )
            )

        } 
        
        catch (err) {
            setError(err.message)
        } 
        
        finally {
            setDeletingId(null)
        }
    }

    async function handleProcess(imageId) {
        try {
            setProcessingId(imageId)
            setError('')

            const result = await processImage(imageId, targetLanguage)

            onTranslationResult(result)
        }

        catch (err) {
            console.error("Error al procesar la imagen:", err)
            setError(err.message)
        }

        finally {
            setProcessingId(null)
        }
    }

    return (
        <section className="gallery">

            <div className="gallery-header">
                <span className="gallery-icon">▧</span>
                <h2>Imágenes almacenadas en el bucket</h2>
            </div>

            {loading && (
                <p className="gallery-message">
                    Cargando imágenes...
                </p>
            )}

            {!loading && error && (
                <p className="gallery-error">
                    {error}
                </p>
            )}

            {!loading && !error && images.length === 0 && (
                <p className="gallery-message">
                    Todavía no hay imágenes almacenadas.
                </p>
            )}

            {!loading && images.length > 0 && (
                <div className="gallery-grid">
                    {images.map(image => (
                        <div
                            className="gallery-card"
                            key={image.image_id}
                        >
                            <img
                                src={`${API_URL}/images/${image.image_id}`}
                                alt="Imagen almacenada en IXTLI"
                            />

                            <div className="gallery-actions">
                                <button
                                    className='process-button'
                                    type='button'
                                    onClick={() => handleProcess(image.image_id)}
                                    disabled={processingId === image.image_id}
                                    title='Procesar imagen'
                                >
                                    {processingId === image.image_id
                                        ? 'Procesando...'
                                        : 'Procesar'
                                    }
                                </button>

                                <button
                                    className="delete-button"
                                    type="button"
                                    onClick={() => handleDelete(image.image_id)}
                                    disabled={deletingId === image.image_id}
                                    title="Borrar imagen"
                                >
                                    {deletingId === image.image_id
                                        ? '...'
                                        : '✖'}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </section>
    )
}

export default ImageGallery