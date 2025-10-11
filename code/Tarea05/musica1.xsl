<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html lang="es">
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <title>Catálogo de Música - Álbumes por Artista</title>
                <link rel="stylesheet" href="musica.css"/>
            </head>
            <body>
                <div class="container">
                    <h1>Catálogo de Música - Álbumes por Artista</h1>
                    
                    <!-- Agrupar álbumes por artista -->
                    <xsl:for-each select="catalogo_musica/artistas/artista">
                        <xsl:sort select="nombre"/>
                        <xsl:variable name="artista-id" select="@id"/>
                        <xsl:variable name="artista-nombre" select="nombre"/>
                        <xsl:variable name="artista-pais" select="pais_origen"/>
                        
                        <!-- Verificar si el artista tiene álbumes -->
                        <xsl:if test="count(//album[id_artista = $artista-id]) > 0">
                            <div class="artist-section">
                                <!-- Encabezado del artista -->
                                <div class="artist-header">
                                    <xsl:value-of select="$artista-nombre"/>
                                </div>
                                
                                <!-- Información del artista -->
                                <div class="artist-info">
                                    País de origen: <xsl:value-of select="$artista-pais"/>
                                </div>
                                
                                <!-- Contenedor de álbumes -->
                                <div class="albums-container">
                                    <!-- Listar álbumes del artista -->
                                    <xsl:for-each select="//album[id_artista = $artista-id]">
                                        <xsl:sort select="año_lanzamiento"/>
                                        <xsl:variable name="album-id" select="@id"/>
                                        <xsl:variable name="genero-id" select="id_genero"/>
                                        
                                        <div class="album-item">
                                            <div class="album-title">
                                                <xsl:value-of select="titulo"/>
                                            </div>
                                            <div class="album-details">
                                                <span class="year">Año: <xsl:value-of select="año_lanzamiento"/></span>
                                                <span class="genre">Género: <xsl:value-of select="//genero[@id = $genero-id]/nombre"/></span>
                                            </div>
                                        </div>
                                    </xsl:for-each>
                                </div>
                            </div>
                        </xsl:if>
                    </xsl:for-each>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
