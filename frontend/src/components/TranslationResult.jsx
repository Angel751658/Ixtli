import './TranslationResult.css'

function TranslationResult({ result }) {
    const translations = result?.traducción ?? []

    // Agrupar las lineas del texto original
    const originalText = translations
        .map(item => item.texto_original)
        .join(' ')

    // Agrupar las lineas del texto traducido
    const translatedText = translations
        .map(item => item.traducción)
        .join(' ')

    // Calcular el promedio de confianza
    const avgConfidence = translations.length > 0
        ? translations.reduce(
            (total, item) => total + item.confianza,
            0
        ) / translations.length
        : 0

    // Conservar el idioma de la primera linea detectada
    const detectedLanguage = translations[0]?.idioma_original ?? "No identificado"

    return (
        <section className="panel translation-panel">

            <div className="panel-header">
                <span className="panel-icon">⇄</span>
                <h3>Texto traducido</h3>
            </div>

            {!result ? (
                <div className="placeholder">
                    <span>🌐</span>
                    <p>
                        Tu traducción aparecerá aquí.
                    </p>
                </div>
            ) : translations.length === 0 ? (
                <div className="placeholder">
                    <p>No se detectó texto en la imagen.</p>
                </div>
            ) : (
                <div className="translation-content">
                    <div className="detected-language">
                        <span>
                            Idioma detectado: <strong>{detectedLanguage}</strong>
                        </span>

                        <span>
                            Confianza promedio: {(avgConfidence * 100).toFixed(1)}%
                        </span>
                    </div>

                    <div className="text-section">
                        <h4>Texto original</h4>
                        <p>{originalText}</p>
                    </div>

                    <div className="text-section">
                        <h4>
                            Traducción ({result.idioma_destino})
                        </h4>
                        <p>{translatedText}</p>
                    </div>
                </div>
            )}
        </section>
    )
}

export default TranslationResult