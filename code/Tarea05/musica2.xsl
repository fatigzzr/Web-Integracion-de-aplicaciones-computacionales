<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html lang="es">
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <title>Catálogo de Música - Canciones por Álbum</title>
                <link rel="stylesheet" href="musica2.css"/>
            </head>
            <body>
                <div class="container">
                    <h1>Catálogo de Música - Canciones por Álbum</h1>
                    
                    <!-- Iterar sobre cada álbum -->
                    <xsl:for-each select="catalogo_musica/albumes/album">
                        <xsl:sort select="titulo"/>
                        <xsl:variable name="album-id" select="@id"/>
                        <xsl:variable name="album-titulo" select="titulo"/>
                        <xsl:variable name="album-año" select="año_lanzamiento"/>
                        <xsl:variable name="artista-id" select="id_artista"/>
                        <xsl:variable name="genero-id" select="id_genero"/>
                        
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
                            
                            <!-- Tabla de canciones -->
                            <div class="songs-container">
                                <table class="songs-table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Título de la Canción</th>
                                            <th>Duración</th>
                                            <th>Sencillo</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <!-- Mostrar canciones del álbum -->
                                        <xsl:for-each select="//cancion[id_album = $album-id]">
                                            <xsl:sort select="@id"/>
                                            <tr>
                                                <td class="track-number"><xsl:value-of select="position()"/></td>
                                                <td class="song-title"><xsl:value-of select="titulo"/></td>
                                                <td class="duration"><xsl:value-of select="duracion"/></td>
                                                <td class="single">
                                                    <xsl:choose>
                                                        <xsl:when test="es_sencillo = 'true'">
                                                            <span class="single-yes">Sí</span>
                                                        </xsl:when>
                                                        <xsl:otherwise>
                                                            <span class="single-no">No</span>
                                                        </xsl:otherwise>
                                                    </xsl:choose>
                                                </td>
                                            </tr>
                                        </xsl:for-each>
                                        
                                        <!-- Fila de total -->
                                        <tr class="total-row">
                                            <td colspan="3" class="total-label">Duración Total del Álbum:</td>
                                            <td class="total-duration">
                                                <xsl:call-template name="sum-durations">
                                                    <xsl:with-param name="songs" select="//cancion[id_album = $album-id]"/>
                                                </xsl:call-template>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </xsl:for-each>
                </div>
            </body>
        </html>
    </xsl:template>
    
    <!-- Template para sumar duraciones -->
    <xsl:template name="sum-durations">
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
                <xsl:call-template name="sum-durations">
                    <xsl:with-param name="songs" select="$songs[position() > 1]"/>
                    <xsl:with-param name="total-minutes" select="$total-minutes + number($minutes)"/>
                    <xsl:with-param name="total-seconds" select="$total-seconds + number($seconds)"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
