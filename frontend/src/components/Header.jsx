import './Header.css'

function Header() {
    return (
        <header className="header">
            <div className="header-title">
                <div className="header-line"></div>
                <h1>IXTLI</h1>
                <div className="header-line"></div>
            </div>

            <p className="header-subtitle">
                Tu compañero para entender el mundo
            </p>
        </header>
    )
}

export default Header