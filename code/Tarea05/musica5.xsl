<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <!-- Parámetro para el género a filtrar (por defecto "Rock") -->
    <xsl:param name="genero-filtro" select="'Rock'"/>
    
    <xsl:template match="/">
        <html lang="es">
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <title>Catálogo de Música - Filtro por Género: <xsl:value-of select="$genero-filtro"/></title>
                <link rel="stylesheet" href="musica5.css"/>
                <script>
                    // Función para filtrar por género
                    function filtrarPorGenero(genero) {
                        // Ocultar todos los álbumes
                        const albumCards = document.querySelectorAll('.album-card');
                        albumCards.forEach(card => card.style.display = 'none');
                        
                        // Mostrar solo los álbumes del género seleccionado
                        const generoId = getGeneroId(genero);
                        const albumesGenero = document.querySelectorAll(`[data-genero-id="${generoId}"]`);
                        albumesGenero.forEach(card => card.style.display = 'block');
                        
                        // Actualizar información del género
                        actualizarInfoGenero(genero);
                        
                        // Actualizar botones activos
                        actualizarBotonesActivos(genero);
                    }
                    
                    function getGeneroId(genero) {
                        const generos = {
                            'Pop': '1',
                            'Rock': '2', 
                            'Hard Rock': '3',
                            'Progressive Rock': '4',
                            'Pop Rock': '5',
                            'Grunge': '6',
                            'Alternative Rock': '7'
                        };
                        return generos[genero] || '2';
                    }
                    
                    function actualizarInfoGenero(genero) {
                        const generoInfo = {
                            'Pop': { descripcion: 'Música popular comercial' },
                            'Rock': { descripcion: 'Música rock clásica' },
                            'Hard Rock': { descripcion: 'Rock pesado y agresivo' },
                            'Progressive Rock': { descripcion: 'Rock progresivo experimental' },
                            'Pop Rock': { descripcion: 'Fusión de pop y rock' },
                            'Grunge': { descripcion: 'Rock alternativo de los 90s' },
                            'Alternative Rock': { descripcion: 'Rock alternativo independiente' }
                        };
                        
                        const info = generoInfo[genero] || { descripcion: 'Género musical' };
                        document.getElementById('current-genre-description').textContent = info.descripcion;
                        document.getElementById('current-genre-title').innerHTML = `🎵 ${genero}`;
                        
                        // Actualizar contador
                        const generoId = getGeneroId(genero);
                        const count = document.querySelectorAll(`[data-genero-id="${generoId}"]`).length;
                        const countText = count === 1 ? '1 álbum encontrado' : `${count} álbumes encontrados`;
                        document.getElementById('album-count').textContent = countText;
                    }
                    
                    function actualizarBotonesActivos(genero) {
                        const botones = document.querySelectorAll('.genre-button');
                        botones.forEach(boton => {
                            boton.classList.remove('active');
                            // Verificar que el botón contenga exactamente el nombre del género
                            const nombreGenero = boton.querySelector('.genre-name').textContent.trim();
                            if (nombreGenero === genero) {
                                boton.classList.add('active');
                            }
                        });
                    }
                    
                    // Inicializar sin filtro
                    document.addEventListener('DOMContentLoaded', function() {
                        // Ocultar todos los álbumes inicialmente
                        const albumCards = document.querySelectorAll('.album-card');
                        albumCards.forEach(card => card.style.display = 'none');
                        
                        // Mostrar mensaje inicial
                        document.getElementById('album-count').textContent = 'Selecciona un género para ver los álbumes';
                    });
                </script>
            </head>
            <body>
                <div class="container">
                    <h1>Catálogo de Música - Filtro por Género</h1>
                    
                    <!-- Navegación de géneros -->
                    <div class="genre-nav">
                        <h3>Filtrar por Género</h3>
                        <div class="genre-buttons">
                            <xsl:for-each select="catalogo_musica/generos/genero">
                                <xsl:sort select="nombre"/>
                                <xsl:variable name="genero-nombre" select="nombre"/>
                                <xsl:variable name="genero-id" select="@id"/>
                                <xsl:variable name="album-count" select="count(//album[id_genero = $genero-id])"/>
                                
                                <xsl:if test="$album-count > 0">
                                    <button onclick="filtrarPorGenero('{$genero-nombre}')" class="genre-button">
                                        <span class="genre-name"><xsl:value-of select="$genero-nombre"/></span>
                                        <span class="genre-count">(<xsl:value-of select="$album-count"/>)</span>
                                    </button>
                                </xsl:if>
                            </xsl:for-each>
                        </div>
                    </div>
                    
                    <!-- Información del género actual -->
                    <div class="current-genre">
                        <h2 id="current-genre-title">
                            <span class="genre-icon">🎵</span>
                            Selecciona un género
                        </h2>
                        <p class="genre-description" id="current-genre-description">
                            Haz clic en un género de arriba para ver sus álbumes
                        </p>
                    </div>
                    
                    <!-- Lista de todos los álbumes (JavaScript los filtrará) -->
                    <div class="albums-section">
                        <div class="albums-header">
                            <h3 id="album-count">Álbumes encontrados</h3>
                        </div>
                        
                        <div class="albums-grid">
                            <xsl:for-each select="catalogo_musica/albumes/album">
                                <xsl:sort select="año_lanzamiento" data-type="number"/>
                                <xsl:variable name="album-id" select="@id"/>
                                <xsl:variable name="artista-id" select="id_artista"/>
                                <xsl:variable name="genero-id" select="id_genero"/>
                                
                                <div class="album-card" data-genero-id="{$genero-id}">
                                    <div class="album-header">
                                        <h4 class="album-title">
                                            <xsl:value-of select="titulo"/>
                                        </h4>
                                        <div class="album-year">
                                            <xsl:value-of select="año_lanzamiento"/>
                                        </div>
                                    </div>
                                    
                                    <div class="album-info">
                                        <div class="artist-info">
                                            <span class="artist-icon">🎤</span>
                                            <span class="artist-name">
                                                <xsl:value-of select="//artista[@id = $artista-id]/nombre"/>
                                            </span>
                                        </div>
                                        <div class="country-info">
                                            <span class="flag-icon">🌍</span>
                                            <span class="country">
                                                <xsl:value-of select="//artista[@id = $artista-id]/pais_origen"/>
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <div class="album-stats">
                                        <div class="stat-item">
                                            <span class="stat-label">Canciones:</span>
                                            <span class="stat-value">
                                                <xsl:value-of select="count(//cancion[id_album = $album-id])"/>
                                            </span>
                                        </div>
                                        <div class="stat-item">
                                            <span class="stat-label">Sencillos:</span>
                                            <span class="stat-value">
                                                <xsl:value-of select="count(//cancion[id_album = $album-id and es_sencillo = 'true'])"/>
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <div class="album-actions">
                                        <button class="view-album-btn">Ver Detalles</button>
                                    </div>
                                </div>
                            </xsl:for-each>
                        </div>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
