<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html lang="es">
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <title>Catálogo de Música - Índice Alfabético de Artistas</title>
                <link rel="stylesheet" href="musica4.css"/>
            </head>
            <body>
                <div class="container">
                    <h1>Catálogo de Música - Índice Alfabético de Artistas</h1>
                    <p class="description">Índice alfabético de artistas con sus álbumes ordenados por año de lanzamiento.</p>
                    
                    <!-- Navegación alfabética -->
                    <div class="alphabet-nav">
                        <h3>Navegación Rápida</h3>
                        <div class="alphabet-links">
                            <xsl:for-each select="catalogo_musica/artistas/artista">
                                <xsl:sort select="nombre"/>
                                <xsl:variable name="first-letter" select="substring(nombre, 1, 1)"/>
                                <xsl:if test="not(preceding-sibling::artista[substring(nombre, 1, 1) = $first-letter])">
                                    <a href="#letter-{$first-letter}" class="alphabet-link">
                                        <xsl:value-of select="$first-letter"/>
                                    </a>
                                </xsl:if>
                            </xsl:for-each>
                        </div>
                    </div>
                    
                    <!-- Índice alfabético de artistas -->
                    <div class="artists-index">
                        <xsl:for-each select="catalogo_musica/artistas/artista">
                            <xsl:sort select="nombre"/>
                            <xsl:variable name="artista-id" select="@id"/>
                            <xsl:variable name="artista-nombre" select="nombre"/>
                            <xsl:variable name="artista-pais" select="pais_origen"/>
                            <xsl:variable name="first-letter" select="substring(nombre, 1, 1)"/>
                            
                            <!-- Verificar si el artista tiene álbumes -->
                            <xsl:if test="count(//album[id_artista = $artista-id]) > 0">
                                <div class="artist-entry">
                                    <!-- Letra del alfabeto (solo si es la primera vez que aparece) -->
                                    <xsl:if test="not(preceding-sibling::artista[substring(nombre, 1, 1) = $first-letter])">
                                        <div class="alphabet-section" id="letter-{$first-letter}">
                                            <h2 class="alphabet-header">
                                                <span class="alphabet-letter"><xsl:value-of select="$first-letter"/></span>
                                            </h2>
                                        </div>
                                    </xsl:if>
                                    
                                    <!-- Información del artista -->
                                    <div class="artist-info">
                                        <h3 class="artist-name">
                                            <span class="artist-icon">🎤</span>
                                            <xsl:value-of select="$artista-nombre"/>
                                        </h3>
                                        <div class="artist-details">
                                            <span class="country">
                                                <span class="flag-icon">🌍</span>
                                                <xsl:value-of select="$artista-pais"/>
                                            </span>
                                            <span class="album-count">
                                                <xsl:value-of select="count(//album[id_artista = $artista-id])"/>
                                                <xsl:choose>
                                                    <xsl:when test="count(//album[id_artista = $artista-id]) = 1"> álbum</xsl:when>
                                                    <xsl:otherwise> álbumes</xsl:otherwise>
                                                </xsl:choose>
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <!-- Lista de álbumes ordenados por año -->
                                    <div class="albums-list">
                                        <xsl:for-each select="//album[id_artista = $artista-id]">
                                            <xsl:sort select="año_lanzamiento" data-type="number"/>
                                            <xsl:variable name="album-id" select="@id"/>
                                            <xsl:variable name="genero-id" select="id_genero"/>
                                            
                                            <div class="album-item">
                                                <div class="album-year">
                                                    <span class="year-badge"><xsl:value-of select="año_lanzamiento"/></span>
                                                </div>
                                                <div class="album-details">
                                                    <div class="album-title">
                                                        <xsl:value-of select="titulo"/>
                                                    </div>
                                                    <div class="album-genre">
                                                        <span class="genre-icon">🎵</span>
                                                        <xsl:value-of select="//genero[@id = $genero-id]/nombre"/>
                                                    </div>
                                                </div>
                                                <div class="album-stats">
                                                    <div class="song-count">
                                                        <xsl:value-of select="count(//cancion[id_album = $album-id])"/>
                                                        <xsl:choose>
                                                            <xsl:when test="count(//cancion[id_album = $album-id]) = 1"> canción</xsl:when>
                                                            <xsl:otherwise> canciones</xsl:otherwise>
                                                        </xsl:choose>
                                                    </div>
                                                </div>
                                            </div>
                                        </xsl:for-each>
                                    </div>
                                </div>
                            </xsl:if>
                        </xsl:for-each>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
