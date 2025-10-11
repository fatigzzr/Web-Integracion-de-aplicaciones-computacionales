<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html lang="es">
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <title>Catálogo de Música - Sencillos por Álbum</title>
                <link rel="stylesheet" href="musica3.css"/>
            </head>
            <body>
                <div class="container">
                    <h1>Catálogo de Música - Sencillos por Álbum</h1>
                    <p class="description">Esta página muestra únicamente las canciones que son sencillos (singles) de cada álbum.</p>
                    
                    <!-- Iterar sobre cada álbum -->
                    <xsl:for-each select="catalogo_musica/albumes/album">
                        <xsl:sort select="titulo"/>
                        <xsl:variable name="album-id" select="@id"/>
                        <xsl:variable name="album-titulo" select="titulo"/>
                        <xsl:variable name="album-año" select="año_lanzamiento"/>
                        <xsl:variable name="artista-id" select="id_artista"/>
                        <xsl:variable name="genero-id" select="id_genero"/>
                        
                        <!-- Verificar si el álbum tiene sencillos -->
                        <xsl:if test="count(//cancion[id_album = $album-id and es_sencillo = 'true']) > 0">
                            <div class="album-section">
                                <!-- Encabezado del álbum -->
                                <div class="album-header">
                                    <h2><xsl:value-of select="$album-titulo"/></h2>
                                    <div class="album-info">
                                        <span class="year">Año: <xsl:value-of select="$album-año"/></span>
                                        <span class="artist">Artista: <xsl:value-of select="//artista[@id = $artista-id]/nombre"/></span>
                                        <span class="genre">Género: <xsl:value-of select="//genero[@id = $genero-id]/nombre"/></span>
                                    </div>
                                </div>
                                
                                <!-- Lista de sencillos -->
                                <div class="singles-container">
                                    <h3 class="singles-title">
                                        <span class="single-icon">🎵</span>
                                        Sencillos del Álbum
                                        <span class="count">(<xsl:value-of select="count(//cancion[id_album = $album-id and es_sencillo = 'true'])"/> sencillo<xsl:if test="count(//cancion[id_album = $album-id and es_sencillo = 'true']) != 1">s</xsl:if>)</span>
                                    </h3>
                                    
                                    <div class="singles-list">
                                        <!-- Mostrar solo los sencillos del álbum -->
                                        <xsl:for-each select="//cancion[id_album = $album-id]">
                                            <xsl:sort select="@id"/>
                                            <!-- Condición: Solo mostrar si es sencillo -->
                                            <xsl:if test="es_sencillo = 'true'">
                                                <div class="single-item">
                                                    <div class="single-number">
                                                        <xsl:value-of select="position()"/>
                                                    </div>
                                                    <div class="single-details">
                                                        <div class="single-title">
                                                            <xsl:value-of select="titulo"/>
                                                        </div>
                                                        <div class="single-duration">
                                                            <span class="duration-icon">⏱️</span>
                                                            <xsl:value-of select="duracion"/>
                                                        </div>
                                                    </div>
                                                    <div class="single-badge">
                                                        <span class="badge">SINGLE</span>
                                                    </div>
                                                </div>
                                            </xsl:if>
                                        </xsl:for-each>
                                    </div>
                                    
                                    <!-- Resumen de duración total de sencillos -->
                                    <div class="singles-summary">
                                        <div class="summary-item">
                                            <span class="summary-label">Duración total de sencillos:</span>
                                            <span class="summary-value">
                                                <xsl:call-template name="sum-singles-durations">
                                                    <xsl:with-param name="songs" select="//cancion[id_album = $album-id and es_sencillo = 'true']"/>
                                                </xsl:call-template>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </xsl:if>
                    </xsl:for-each>
                    
                    <!-- Mensaje si no hay álbumes con sencillos -->
                    <xsl:if test="count(//cancion[es_sencillo = 'true']) = 0">
                        <div class="no-singles">
                            <h2>No se encontraron sencillos</h2>
                            <p>No hay canciones marcadas como sencillos en el catálogo.</p>
                        </div>
                    </xsl:if>
                </div>
            </body>
        </html>
    </xsl:template>
    
    <!-- Template para sumar duraciones de sencillos -->
    <xsl:template name="sum-singles-durations">
        <xsl:param name="songs"/>
        <xsl:param name="total-minutes" select="0"/>
        <xsl:param name="total-seconds" select="0"/>
        
        <xsl:choose>
            <xsl:when test="count($songs) = 0">
                <!-- Convertir segundos a minutos si es necesario -->
                <xsl:variable name="final-minutes" select="$total-minutes + floor($total-seconds div 60)"/>
                <xsl:variable name="final-seconds" select="$total-seconds mod 60"/>
                <xsl:value-of select="concat($final-minutes, ':', format-number($final-seconds, '00'))"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- Procesar la primera canción -->
                <xsl:variable name="duration" select="$songs[1]/duracion"/>
                <xsl:variable name="minutes" select="substring-before($duration, ':')"/>
                <xsl:variable name="seconds" select="substring-after($duration, ':')"/>
                
                <!-- Llamar recursivamente con el resto de canciones -->
                <xsl:call-template name="sum-singles-durations">
                    <xsl:with-param name="songs" select="$songs[position() > 1]"/>
                    <xsl:with-param name="total-minutes" select="$total-minutes + number($minutes)"/>
                    <xsl:with-param name="total-seconds" select="$total-seconds + number($seconds)"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
