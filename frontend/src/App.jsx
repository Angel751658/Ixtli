import { useState } from 'react'

// Componentes de React
import Header from './components/Header'
import ImageUploader from './components/ImageUploader'
import ImageGallery from './components/ImageGallery'
import TranslationResult from './components/TranslationResult'

// Funciones para conectar con Fast API
import { uploadImage } from './services/api'

import './App.css'

function App() {
    const [isUploading, setIsUploading] = useState(false)

    const [galleryVersion, setGalleryVersion] = useState(0)

    const [targetLanguage, setTargetLanguage] = useState('es')
    const [translationResult, setTranslationResult] = useState(null)

    async function handleUpload(file) {
        try {
            setIsUploading(true)

            await uploadImage(file)
            setGalleryVersion(current => current + 1)

            alert('¡Imagen subida correctamente!')

            return true
        } 
        
        catch (error) {
            console.error('Error al subir la imagen:', error)
            alert('No fue posible subir la imagen')

            return false
        } 
        
        finally {
            setIsUploading(false)
        }
    }

    async function handleTranslationResult(result) {
        setTranslationResult(result)
    }

    return (
        <div className="app">

            <Header />

            <main className="main-content">
                <section className="workspace">
                    <ImageUploader
                        targetLanguage={targetLanguage}
                        onTargetLanguageChange={setTargetLanguage}
                        onUpload={handleUpload}
                        isUploading={isUploading}
                    />

                    <TranslationResult
                        result={translationResult}
                    />
                </section>

                <ImageGallery
                    refreshTrigger={galleryVersion}
                    targetLanguage={targetLanguage}
                    onTranslationResult={handleTranslationResult}
                />
            </main>
        </div>
    )
}

export default App