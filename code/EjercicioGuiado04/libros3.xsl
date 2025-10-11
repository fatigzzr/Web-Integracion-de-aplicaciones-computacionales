<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/css" href="libros3.css"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Catálogo de Libros - Librería Digital</title>
                <link rel="stylesheet" type="text/css" href="libros3.css"/>
            </head>
            <body>
                <div class="library">
                    <h1>Catálogo de Libros - Librería Digital</h1>
                    
                    <div class="books">
                        <xsl:for-each select="library/book">
                            <div class="book">
                                <div class="book-info">
                                    <div class="isbn">ISBN: <xsl:value-of select="@isbn"/></div>
                                    <div class="title"><xsl:value-of select="title"/></div>
                                    <div class="author"><xsl:value-of select="author"/></div>
                                    <div class="year">Año: <xsl:value-of select="publication_year"/></div>
                                    <div class="genre">Género: <xsl:value-of select="genre"/></div>
                                    <div class="format">Formato: <xsl:value-of select="format"/></div>
                                    <div class="stock">Stock: <xsl:value-of select="stock"/></div>
                                    
                                    <div class="prices">
                                        <div class="original-price">Precio Original: $<xsl:value-of select="price"/></div>
                                        <div class="discounted-price">Precio con Descuento (10%): $<xsl:value-of select="format-number(price * 0.9, '0.00')"/></div>
                                    </div>
                                </div>
                            </div>
                        </xsl:for-each>
                    </div>
                    
                    <div class="summary">
                        <h2>Resumen de Precios</h2>
                        <div class="total-original">Total Precios Originales: $<xsl:value-of select="format-number(sum(library/book/price), '0.00')"/></div>
                        <div class="total-discounted">Total con Descuento (10%): $<xsl:value-of select="format-number(sum(library/book/price) * 0.9, '0.00')"/></div>
                        <div class="savings">Ahorro Total: $<xsl:value-of select="format-number(sum(library/book/price) * 0.1, '0.00')"/></div>
                        <div class="book-count">Total de Libros: <xsl:value-of select="count(library/book)"/></div>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
    
</xsl:stylesheet>
