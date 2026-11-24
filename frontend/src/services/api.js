const API_URL = import.meta.env.VITE_API_URL || ''

// Subir una imagen
export async function uploadImage(file) {
    const formData = new FormData()

    formData.append('file', file)

    const response = await fetch(`${API_URL}/images`, {
        method: 'POST',
        body: formData
    })

    if (!response.ok) {
        const errorDetails = await response.text()

        console.error('Error devuelto por FastAPI:', errorDetails)

        throw new Error(
            `Error HTTP ${response.status}: ${errorDetails}`
        )
    }

    return await response.json()
}

// Consultar las imágenes almacenadas
export async function getImages() {
    const response = await fetch(`${API_URL}/images`, {
        method: 'GET'
    })

    if (!response.ok) {
        throw new Error('No fue posible obtener las imágenes')
    }

    return await response.json()
}

// Eliminar una imagen
export async function deleteImage(imageId) {
    const response = await fetch(`${API_URL}/images/${imageId}`, {
        method: 'DELETE'
    })

    if (!response.ok) {
        throw new Error('No fue posible eliminar la imagen')
    }

    return await response.json()
}

// Procesar una imagen y traducir su texto
export async function processImage(imageId, targetLanguage) {
    const response = await fetch(
        `${API_URL}/images/${imageId}/process?target_language=${targetLanguage}`,
        {
            method: 'POST'
        }
    )

    if (!response.ok) {
        throw new Error('No fue posible procesar la imagen')
    }

    return await response.json()
}